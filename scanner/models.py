from django.db import models
from django.utils import timezone
import json


class ScanResult(models.Model):
    """Model to store network scan results"""

    RISK_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    target = models.CharField(max_length=255)
    target_ip = models.CharField(max_length=255, null=True, blank=True)
    is_private = models.BooleanField(default=False)

    # DNS Resolution
    dns_success = models.BooleanField(default=False)
    dns_resolved_ips = models.JSONField(default=list, blank=True)

    # Port Scan Data
    open_ports = models.JSONField(default=list)

    # Risk Assessment
    overall_risk = models.CharField(max_length=20, choices=RISK_CHOICES, default='LOW')
    critical_ports_count = models.IntegerField(default=0)
    high_ports_count = models.IntegerField(default=0)
    medium_ports_count = models.IntegerField(default=0)

    # Full scan result
    full_result = models.JSONField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target', '-created_at']),
            models.Index(fields=['overall_risk']),
        ]

    def __str__(self):
        return f"Scan: {self.target} - {self.overall_risk}"

    def save(self, *args, **kwargs):
        self.target = self.target.lower()
        super().save(*args, **kwargs)


class ScanHistory(models.Model):
    """Track user scan activity"""

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    target_scanned = models.CharField(max_length=255)
    scan_result = models.ForeignKey(ScanResult, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Scan History"

    def __str__(self):
        return f"{self.target_scanned} - {self.created_at}"
