from django.db import models
from django.contrib.auth.models import User
import uuid


class Tenant(models.Model):
    """Multi-tenancy: one tenant = one enterprise client."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('analyst', 'Analyst'), ('viewer', 'Viewer')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')

    class Meta:
        unique_together = ('user', 'tenant')


class IngestionBatch(models.Model):
    """One file upload = one batch. Tracks source file and parse outcome."""
    SOURCE_TYPES = [
        ('SAP_FUEL_PROCUREMENT', 'SAP Fuel & Procurement'),
        ('UTILITY_ELECTRICITY', 'Utility Electricity'),
        ('CORPORATE_TRAVEL', 'Corporate Travel'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='batches')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    original_filename = models.CharField(max_length=500)
    file = models.FileField(upload_to='uploads/%Y/%m/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_rows = models.IntegerField(default=0)
    parsed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)
    error_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_type} — {self.original_filename} ({self.status})"


class EmissionRecord(models.Model):
    """
    Core normalized record. Every row from every source lands here.
    Quantities stored in canonical units:
      - energy: kWh
      - fuel volume: liters
      - fuel mass: kg
      - distance: km
    """
    SCOPE_CHOICES = [('1', 'Scope 1'), ('2', 'Scope 2'), ('3', 'Scope 3')]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
        # Scope 1
        ('STATIONARY_COMBUSTION', 'Stationary Combustion'),
        ('MOBILE_COMBUSTION', 'Mobile Combustion'),
        # Scope 2
        ('PURCHASED_ELECTRICITY', 'Purchased Electricity'),
        # Scope 3
        ('PURCHASED_GOODS', 'Purchased Goods & Services'),
        ('BUSINESS_TRAVEL_AIR', 'Business Travel — Air'),
        ('BUSINESS_TRAVEL_HOTEL', 'Business Travel — Hotel'),
        ('BUSINESS_TRAVEL_GROUND', 'Business Travel — Ground'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='records')
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='records')

    # Classification
    scope = models.CharField(max_length=5, choices=SCOPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Timing
    period_start = models.DateField()
    period_end = models.DateField()

    # Normalized quantity (canonical unit stored in quantity_unit)
    quantity = models.FloatField()
    quantity_unit = models.CharField(max_length=20)  # kWh, L, kg, km, nights

    # Original values before normalization (for traceability)
    raw_quantity = models.FloatField(null=True, blank=True)
    raw_unit = models.CharField(max_length=50, blank=True)

    # Source-specific metadata (flexible JSON)
    source_metadata = models.JSONField(default=dict)
    # e.g. SAP: {"plant_code": "1100", "plant_name": "Mumbai Plant", "material": "DIESE001",
    #             "movement_type": "261", "vendor": "4500012345", "cost_center": "CC-MFG-01"}
    # e.g. Utility: {"meter_id": "MTR-BLR-004", "site": "Bangalore HQ", "tariff": "HT-2"}
    # e.g. Travel: {"employee_id": "EMP-234", "origin": "BLR", "destination": "DEL",
    #               "class": "Economy", "vendor": "IndiGo"}

    # Review workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    flag_reasons = models.JSONField(default=list)  # list of strings
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_records'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_note = models.TextField(blank=True)

    # Row identity for deduplication
    source_row_hash = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scope}/{self.category} — {self.quantity} {self.quantity_unit} [{self.status}]"


class AuditTrail(models.Model):
    """Immutable log. Every state change on an EmissionRecord is recorded here."""
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EDITED', 'Edited'),
        ('FLAGGED', 'Flagged'),
        ('UNFLAGGED', 'Unflagged'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_trail')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    before_snapshot = models.JSONField(default=dict)  # full record state before change
    after_snapshot = models.JSONField(default=dict)   # full record state after change
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


class PlantCodeLookup(models.Model):
    """SAP plant code → human name mapping per tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='plant_codes')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('tenant', 'code')
