from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Tenant, TenantMembership, IngestionBatch,
    EmissionRecord, AuditTrail, PlantCodeLookup
)


# ─── Auth ───────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


# ─── Tenant ──────────────────────────────────────────────────────────────────

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'created_at']


# ─── Batch ───────────────────────────────────────────────────────────────────

class IngestionBatchSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    source_type_display = serializers.CharField(
        source='get_source_type_display', read_only=True
    )
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = IngestionBatch
        fields = [
            'id', 'source_type', 'source_type_display',
            'original_filename', 'status',
            'total_rows', 'parsed_rows', 'failed_rows', 'flagged_rows',
            'error_log', 'uploaded_by', 'created_at', 'completed_at',
            'success_rate',
        ]
        read_only_fields = fields

    def get_success_rate(self, obj):
        if obj.total_rows == 0:
            return None
        return round(obj.parsed_rows / obj.total_rows * 100, 1)


# ─── Audit Trail ─────────────────────────────────────────────────────────────

class AuditTrailSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditTrail
        fields = [
            'id', 'action', 'action_display',
            'actor', 'before_snapshot', 'after_snapshot',
            'note', 'timestamp',
        ]
        read_only_fields = fields


# ─── Emission Record (list view — lightweight) ───────────────────────────────

class EmissionRecordListSerializer(serializers.ModelSerializer):
    batch_filename = serializers.CharField(source='batch.original_filename', read_only=True)
    source_type = serializers.CharField(source='batch.source_type', read_only=True)
    source_type_display = serializers.CharField(
        source='batch.get_source_type_display', read_only=True
    )
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    is_flagged = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'scope', 'scope_display', 'category', 'category_display',
            'period_start', 'period_end',
            'quantity', 'quantity_unit',
            'raw_quantity', 'raw_unit',
            'source_metadata',
            'status', 'status_display',
            'flag_reasons', 'is_flagged',
            'reviewed_by', 'reviewed_at', 'reviewer_note',
            'batch_filename', 'source_type', 'source_type_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_is_flagged(self, obj):
        return len(obj.flag_reasons) > 0


# ─── Emission Record (detail view — includes audit trail) ────────────────────

class EmissionRecordDetailSerializer(EmissionRecordListSerializer):
    audit_trail = AuditTrailSerializer(many=True, read_only=True)

    class Meta(EmissionRecordListSerializer.Meta):
        fields = EmissionRecordListSerializer.Meta.fields + ['audit_trail']


# ─── Upload input ─────────────────────────────────────────────────────────────

class UploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    source_type = serializers.ChoiceField(choices=[
        ('SAP_FUEL_PROCUREMENT', 'SAP Fuel & Procurement'),
        ('UTILITY_ELECTRICITY', 'Utility Electricity'),
        ('CORPORATE_TRAVEL', 'Corporate Travel'),
    ])


# ─── Approve / Reject inputs ─────────────────────────────────────────────────

class ApproveSerializer(serializers.Serializer):
    record_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of EmissionRecord UUIDs to approve."
    )
    note = serializers.CharField(required=False, allow_blank=True, default='')


class RejectSerializer(serializers.Serializer):
    record_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )
    note = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Rejection reason is mandatory."
    )


class EditRecordSerializer(serializers.Serializer):
    """Allows analyst to correct a field value with a note (creates audit trail)."""
    quantity = serializers.FloatField(required=False)
    quantity_unit = serializers.CharField(required=False)
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
    note = serializers.CharField(required=True, allow_blank=False)


# ─── Dashboard metrics ───────────────────────────────────────────────────────

class DashboardMetricsSerializer(serializers.Serializer):
    # Status counts
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    flagged = serializers.IntegerField()

    # Batch counts
    total_batches = serializers.IntegerField()
    failed_batches = serializers.IntegerField()

    # Scope breakdown
    scope_breakdown = serializers.DictField()

    # Source breakdown
    source_breakdown = serializers.DictField()

    # Recent batches
    recent_batches = IngestionBatchSerializer(many=True)