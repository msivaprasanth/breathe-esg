import json
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from .models import (
    Tenant, TenantMembership, IngestionBatch,
    EmissionRecord, AuditTrail
)
from .serializers import (
    IngestionBatchSerializer, EmissionRecordListSerializer,
    EmissionRecordDetailSerializer, UploadSerializer,
    ApproveSerializer, RejectSerializer, EditRecordSerializer,
    TenantSerializer,
)
from .parsers.sap_parser import parse as parse_sap
from .parsers.utility_parser import parse as parse_utility
from .parsers.travel_parser import parse as parse_travel


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_tenant(request):
    """Get tenant from header X-Tenant-Slug or first membership."""
    slug = request.headers.get('X-Tenant-Slug')
    if slug:
        try:
            return Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return None
    membership = TenantMembership.objects.filter(user=request.user).select_related('tenant').first()
    return membership.tenant if membership else None


def snapshot(record: EmissionRecord) -> dict:
    """Capture a record's current mutable state for audit trail."""
    return {
        'status': record.status,
        'quantity': record.quantity,
        'quantity_unit': record.quantity_unit,
        'period_start': str(record.period_start),
        'period_end': str(record.period_end),
        'flag_reasons': record.flag_reasons,
        'reviewer_note': record.reviewer_note,
    }


PARSER_MAP = {
    'SAP_FUEL_PROCUREMENT': parse_sap,
    'UTILITY_ELECTRICITY': parse_utility,
    'CORPORATE_TRAVEL': parse_travel,
}


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ─── 1. Upload API ────────────────────────────────────────────────────────────

class UploadView(APIView):
    """
    POST /api/upload/
    Accepts: multipart/form-data with `file` and `source_type`.
    Parses the file, creates EmissionRecords, returns batch summary.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        ser = UploadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': 'No tenant found for this user.'}, status=400)

        uploaded_file = ser.validated_data['file']
        source_type = ser.validated_data['source_type']
        file_content = uploaded_file.read()
        filename = uploaded_file.name

        # Create batch record immediately
        batch = IngestionBatch.objects.create(
            tenant=tenant,
            uploaded_by=request.user,
            source_type=source_type,
            original_filename=filename,
            status='PROCESSING',
        )

        # Run parser
        parse_fn = PARSER_MAP[source_type]
        try:
            records_data, parse_errors = parse_fn(file_content, filename)
        except ValueError as e:
            batch.status = 'FAILED'
            batch.error_log = [{'error': str(e)}]
            batch.save()
            return Response({
                'batch_id': str(batch.id),
                'status': 'FAILED',
                'error': str(e),
            }, status=400)

        # Bulk-create EmissionRecords
        to_create = []
        flagged_count = 0

        for rd in records_data:
            has_flags = len(rd.get('flag_reasons', [])) > 0
            rec_status = 'FLAGGED' if has_flags else 'PENDING'
            if has_flags:
                flagged_count += 1

            to_create.append(EmissionRecord(
                tenant=tenant,
                batch=batch,
                scope=rd['scope'],
                category=rd['category'],
                period_start=rd['period_start'],
                period_end=rd['period_end'],
                quantity=rd['quantity'],
                quantity_unit=rd['quantity_unit'],
                raw_quantity=rd.get('raw_quantity'),
                raw_unit=rd.get('raw_unit', ''),
                source_metadata=rd.get('source_metadata', {}),
                flag_reasons=rd.get('flag_reasons', []),
                status=rec_status,
                source_row_hash=rd.get('source_row_hash', ''),
            ))

        with transaction.atomic():
            created = EmissionRecord.objects.bulk_create(to_create, ignore_conflicts=True)

            # Audit trail for each created record
            audit_entries = [
                AuditTrail(
                    record=r,
                    actor=request.user,
                    action='CREATED',
                    before_snapshot={},
                    after_snapshot=snapshot(r),
                    note=f'Ingested from {filename}',
                )
                for r in created
            ]
            AuditTrail.objects.bulk_create(audit_entries)

            # Update batch stats
            batch.status = 'DONE'
            batch.total_rows = len(records_data) + len(parse_errors)
            batch.parsed_rows = len(created)
            batch.failed_rows = len(parse_errors)
            batch.flagged_rows = flagged_count
            batch.error_log = parse_errors
            batch.completed_at = timezone.now()
            batch.save()

        return Response({
            'batch_id': str(batch.id),
            'status': 'DONE',
            'total_rows': batch.total_rows,
            'parsed_rows': batch.parsed_rows,
            'failed_rows': batch.failed_rows,
            'flagged_rows': batch.flagged_rows,
            'parse_errors': parse_errors[:20],  # cap to avoid huge response
        }, status=201)


# ─── 2. Review API ────────────────────────────────────────────────────────────

class ReviewListView(APIView):
    """
    GET /api/review/
    Query params:
      status    — PENDING | FLAGGED | APPROVED | REJECTED
      scope     — 1 | 2 | 3
      source    — SAP_FUEL_PROCUREMENT | UTILITY_ELECTRICITY | CORPORATE_TRAVEL
      batch_id  — UUID
      search    — free text against source_metadata JSON
      page, page_size
    """

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': 'No tenant.'}, status=400)

        qs = EmissionRecord.objects.filter(tenant=tenant).select_related(
            'batch', 'reviewed_by'
        )

        # Filters
        status_f = request.query_params.get('status')
        if status_f:
            qs = qs.filter(status=status_f.upper())

        scope_f = request.query_params.get('scope')
        if scope_f:
            qs = qs.filter(scope=scope_f)

        source_f = request.query_params.get('source')
        if source_f:
            qs = qs.filter(batch__source_type=source_f.upper())

        batch_f = request.query_params.get('batch_id')
        if batch_f:
            qs = qs.filter(batch_id=batch_f)

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(source_metadata__icontains=search) |
                Q(category__icontains=search) |
                Q(scope__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = EmissionRecordListSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class ReviewDetailView(APIView):
    """GET /api/review/<uuid:pk>/"""

    def get(self, request, pk):
        tenant = get_tenant(request)
        try:
            record = EmissionRecord.objects.prefetch_related('audit_trail__actor').get(
                id=pk, tenant=tenant
            )
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        return Response(EmissionRecordDetailSerializer(record).data)


# ─── 3. Approve API ───────────────────────────────────────────────────────────

class ApproveView(APIView):
    """
    POST /api/approve/
    Body: { "record_ids": ["uuid", ...], "note": "optional" }
    Bulk-approves records. Only PENDING or FLAGGED records can be approved.
    """

    def post(self, request):
        tenant = get_tenant(request)
        ser = ApproveSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        ids = ser.validated_data['record_ids']
        note = ser.validated_data.get('note', '')

        records = EmissionRecord.objects.filter(
            id__in=ids,
            tenant=tenant,
            status__in=['PENDING', 'FLAGGED'],
        )

        approved_ids = []
        audit_entries = []
        now = timezone.now()

        with transaction.atomic():
            for r in records:
                before = snapshot(r)
                r.status = 'APPROVED'
                r.reviewed_by = request.user
                r.reviewed_at = now
                r.reviewer_note = note
                r.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_note', 'updated_at'])

                audit_entries.append(AuditTrail(
                    record=r,
                    actor=request.user,
                    action='APPROVED',
                    before_snapshot=before,
                    after_snapshot=snapshot(r),
                    note=note,
                    timestamp=now,
                ))
                approved_ids.append(str(r.id))

            AuditTrail.objects.bulk_create(audit_entries)

        skipped = [str(i) for i in ids if str(i) not in approved_ids]
        return Response({
            'approved': len(approved_ids),
            'approved_ids': approved_ids,
            'skipped': skipped,
            'skip_reason': 'Already approved/rejected or not found' if skipped else None,
        })


# ─── 4. Reject API ────────────────────────────────────────────────────────────

class RejectView(APIView):
    """
    POST /api/reject/
    Body: { "record_ids": ["uuid", ...], "note": "reason (required)" }
    """

    def post(self, request):
        tenant = get_tenant(request)
        ser = RejectSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        ids = ser.validated_data['record_ids']
        note = ser.validated_data['note']

        records = EmissionRecord.objects.filter(
            id__in=ids,
            tenant=tenant,
            status__in=['PENDING', 'FLAGGED'],
        )

        rejected_ids = []
        audit_entries = []
        now = timezone.now()

        with transaction.atomic():
            for r in records:
                before = snapshot(r)
                r.status = 'REJECTED'
                r.reviewed_by = request.user
                r.reviewed_at = now
                r.reviewer_note = note
                r.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_note', 'updated_at'])

                audit_entries.append(AuditTrail(
                    record=r,
                    actor=request.user,
                    action='REJECTED',
                    before_snapshot=before,
                    after_snapshot=snapshot(r),
                    note=note,
                    timestamp=now,
                ))
                rejected_ids.append(str(r.id))

            AuditTrail.objects.bulk_create(audit_entries)

        skipped = [str(i) for i in ids if str(i) not in rejected_ids]
        return Response({
            'rejected': len(rejected_ids),
            'rejected_ids': rejected_ids,
            'skipped': skipped,
        })


# ─── 5. Edit API ──────────────────────────────────────────────────────────────

class EditRecordView(APIView):
    """
    PATCH /api/review/<uuid:pk>/edit/
    Lets an analyst correct quantity/dates with an audit note.
    Approved records cannot be edited (locked for audit).
    """

    def patch(self, request, pk):
        tenant = get_tenant(request)
        try:
            record = EmissionRecord.objects.get(id=pk, tenant=tenant)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        if record.status == 'APPROVED':
            return Response(
                {'error': 'Approved records are locked. Contact admin to unlock.'},
                status=403
            )

        ser = EditRecordSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        before = snapshot(record)
        note = ser.validated_data.pop('note')

        for field, value in ser.validated_data.items():
            setattr(record, field, value)

        # Re-flag status to PENDING after edit so analyst re-reviews
        record.status = 'PENDING'
        record.save()

        AuditTrail.objects.create(
            record=record,
            actor=request.user,
            action='EDITED',
            before_snapshot=before,
            after_snapshot=snapshot(record),
            note=note,
        )

        return Response(EmissionRecordDetailSerializer(record).data)


# ─── 6. Dashboard Metrics API ─────────────────────────────────────────────────

class DashboardMetricsView(APIView):
    """
    GET /api/dashboard/
    Returns counts, breakdowns, and recent batch summaries for the analyst dashboard.
    """

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': 'No tenant.'}, status=400)

        records_qs = EmissionRecord.objects.filter(tenant=tenant)
        batches_qs = IngestionBatch.objects.filter(tenant=tenant)

        # Status counts
        status_counts = dict(
            records_qs.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
        )

        # Scope breakdown
        scope_raw = records_qs.values('scope', 'status').annotate(c=Count('id'))
        scope_breakdown = {}
        for row in scope_raw:
            s = f"Scope {row['scope']}"
            if s not in scope_breakdown:
                scope_breakdown[s] = {'total': 0, 'pending': 0, 'approved': 0, 'flagged': 0, 'rejected': 0}
            scope_breakdown[s]['total'] += row['c']
            scope_breakdown[s][row['status'].lower()] += row['c']

        # Source type breakdown
        source_raw = (
            records_qs
            .values('batch__source_type', 'status')
            .annotate(c=Count('id'))
        )
        source_breakdown = {}
        for row in source_raw:
            src = row['batch__source_type']
            if src not in source_breakdown:
                source_breakdown[src] = {'total': 0, 'pending': 0, 'approved': 0, 'flagged': 0, 'rejected': 0}
            source_breakdown[src]['total'] += row['c']
            source_breakdown[src][row['status'].lower()] += row['c']

        # Batch stats
        batch_status_counts = dict(
            batches_qs.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
        )

        recent_batches = batches_qs.order_by('-created_at')[:5]

        return Response({
            'total': records_qs.count(),
            'pending': status_counts.get('PENDING', 0),
            'approved': status_counts.get('APPROVED', 0),
            'rejected': status_counts.get('REJECTED', 0),
            'flagged': status_counts.get('FLAGGED', 0),
            'total_batches': batches_qs.count(),
            'failed_batches': batch_status_counts.get('FAILED', 0),
            'scope_breakdown': scope_breakdown,
            'source_breakdown': source_breakdown,
            'recent_batches': IngestionBatchSerializer(recent_batches, many=True).data,
        })


# ─── 7. Batch List ────────────────────────────────────────────────────────────

class BatchListView(APIView):
    """GET /api/batches/ — list all ingestion batches for tenant."""

    def get(self, request):
        tenant = get_tenant(request)
        qs = IngestionBatch.objects.filter(tenant=tenant)
        ser = IngestionBatchSerializer(qs, many=True)
        return Response(ser.data)


# ─── 8. Tenant Info ───────────────────────────────────────────────────────────

class TenantInfoView(APIView):
    """GET /api/tenant/ — returns tenant info for current user."""

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': 'No tenant.'}, status=400)
        return Response(TenantSerializer(tenant).data)