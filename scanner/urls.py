from django.urls import path
from . import views

app_name = 'scanner'

urlpatterns = [
    # Frontend views
    path('', views.index, name='index'),
    path('history/', views.scan_history, name='history'),
    path('detail/<int:scan_id>/', views.scan_detail, name='detail'),

    # API endpoints - Existing scanners
    path('api/scan/', views.scan_target, name='api_scan'),
    path('api/stats/', views.dashboard_stats, name='api_stats'),
    path('api/scan-url/', views.scan_url, name='api_scan_url'),
    path('api/nmap-scan/', views.nmap_scan, name='api_nmap_scan'),
    path('api/scan-headers/', views.scan_headers, name='api_scan_headers'),

    # API endpoints - New scanners
    path('api/ping/', views.ping_scan, name='api_ping'),
    path('api/traceroute/', views.traceroute_scan, name='api_traceroute'),
    path('api/ssl/', views.ssl_scan, name='api_ssl'),
    path('api/whois/', views.whois_scan, name='api_whois'),
    path('api/webpage/', views.webpage_scan, name='api_webpage'),
]
