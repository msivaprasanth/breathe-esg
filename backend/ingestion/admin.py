from django.contrib import admin
from .models import Tenant, TenantMembership, IngestionBatch, EmissionRecord, AuditTrail, PlantCodeLookup

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']

@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role']

@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'source_type', 'status', 'parsed_rows', 'failed_rows', 'created_at']
    list_filter = ['source_type', 'status']

@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ['scope', 'category', 'quantity', 'quantity_unit', 'status', 'period_start', 'created_at']
    list_filter = ['scope', 'category', 'status']

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['record', 'actor', 'action', 'timestamp']
    list_filter = ['action']

@admin.register(PlantCodeLookup)
class PlantCodeLookupAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'code', 'name', 'country'] 