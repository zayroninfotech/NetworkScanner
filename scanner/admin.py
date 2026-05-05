from django.contrib import admin
from .models import ScanResult, ScanHistory


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('target', 'target_ip', 'overall_risk', 'is_private', 'created_at')
    list_filter = ('overall_risk', 'is_private', 'created_at')
    search_fields = ('target', 'target_ip')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Target Information', {
            'fields': ('target', 'target_ip', 'is_private')
        }),
        ('DNS Resolution', {
            'fields': ('dns_success', 'dns_resolved_ips')
        }),
        ('Scan Results', {
            'fields': ('open_ports', 'overall_risk', 'critical_ports_count', 'high_ports_count', 'medium_ports_count')
        }),
        ('Full Result', {
            'fields': ('full_result',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ('target_scanned', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('target_scanned', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
