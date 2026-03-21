from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import json
import logging
import subprocess
import shutil
import time
import requests as http_requests

from .scanner_utils import NetworkScanner
from .url_scanner import URLScanner
from .ping_utils import PingScanner
from .traceroute_utils import TracerouteScanner
from .ssl_utils import SSLScanner
from .whois_utils import WhoisScanner
from .webpage_scanner import WebpageScanner
from .models import ScanResult, ScanHistory

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def index(request):
    """Home page - scan input form"""
    recent_scans = ScanResult.objects.all()[:10]
    risk_stats = {
        'critical': ScanResult.objects.filter(overall_risk='CRITICAL').count(),
        'high': ScanResult.objects.filter(overall_risk='HIGH').count(),
        'medium': ScanResult.objects.filter(overall_risk='MEDIUM').count(),
        'low': ScanResult.objects.filter(overall_risk='LOW').count(),
    }

    context = {
        'recent_scans': recent_scans,
        'risk_stats': risk_stats,
    }
    return render(request, 'scanner/index.html', context)


@require_http_methods(["POST"])
@csrf_protect
def scan_target(request):
    """Perform network scan on target"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()

        # Input validation
        if not target:
            return JsonResponse({
                'success': False,
                'error': 'Target IP or domain is required'
            }, status=400)

        if len(target) > 255:
            return JsonResponse({
                'success': False,
                'error': 'Target input too long'
            }, status=400)

        # Perform scan
        scanner = NetworkScanner()
        result = scanner.full_scan(target)

        if result.get('error'):
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)

        # Store result in database
        try:
            target_ip = result['scan_info']['target']
            open_ports = result['scan_info'].get('ports', [])

            critical_count = sum(1 for p in open_ports if p.get('risk_level') == 'CRITICAL')
            high_count = sum(1 for p in open_ports if p.get('risk_level') == 'HIGH')
            medium_count = sum(1 for p in open_ports if p.get('risk_level') == 'MEDIUM')

            scan_obj = ScanResult.objects.create(
                target=target,
                target_ip=target_ip,
                is_private=result['is_private'],
                dns_success=result['dns_info']['success'] if result['dns_info'] else False,
                dns_resolved_ips=result['dns_info']['ips'] if result['dns_info'] else [],
                open_ports=open_ports,
                overall_risk=result['assessment']['overall_risk'],
                critical_ports_count=critical_count,
                high_ports_count=high_count,
                medium_ports_count=medium_count,
                full_result=result
            )

            # Log scan
            ScanHistory.objects.create(
                ip_address=request.META.get('REMOTE_ADDR'),
                target_scanned=target,
                scan_result=scan_obj
            )

        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Continue even if DB fails, return results

        return JsonResponse({
            'success': True,
            'data': result
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Scan failed: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def scan_history(request):
    """Get scan history"""
    page = request.GET.get('page', 1)
    per_page = 20

    try:
        page = int(page)
    except ValueError:
        page = 1

    start = (page - 1) * per_page
    end = start + per_page

    scans = ScanResult.objects.all()[start:end]
    total = ScanResult.objects.count()

    scan_data = []
    for scan in scans:
        scan_data.append({
            'id': scan.id,
            'target': scan.target,
            'target_ip': scan.target_ip,
            'overall_risk': scan.overall_risk,
            'open_ports_count': len(scan.open_ports),
            'created_at': scan.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'data': scan_data,
        'total': total,
        'page': page,
        'per_page': per_page
    })


@require_http_methods(["GET"])
def scan_detail(request, scan_id):
    """Get detailed scan result"""
    try:
        scan = ScanResult.objects.get(id=scan_id)

        return JsonResponse({
            'success': True,
            'data': {
                'id': scan.id,
                'target': scan.target,
                'target_ip': scan.target_ip,
                'is_private': scan.is_private,
                'dns_info': {
                    'success': scan.dns_success,
                    'resolved_ips': scan.dns_resolved_ips,
                },
                'scan_info': {
                    'ports': scan.open_ports,
                },
                'assessment': {
                    'overall_risk': scan.overall_risk,
                    'critical_ports': [p for p in scan.open_ports if p.get('risk_level') == 'CRITICAL'],
                    'high_risk_ports': [p for p in scan.open_ports if p.get('risk_level') == 'HIGH'],
                    'medium_risk_ports': [p for p in scan.open_ports if p.get('risk_level') == 'MEDIUM'],
                    'recommendations': NetworkScanner().RECOMMENDATIONS.get(scan.overall_risk, []),
                },
                'created_at': scan.created_at.isoformat(),
            }
        })
    except ScanResult.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Scan not found'
        }, status=404)


@require_http_methods(["GET"])
def dashboard_stats(request):
    """Get dashboard statistics"""
    total_scans = ScanResult.objects.count()
    critical_scans = ScanResult.objects.filter(overall_risk='CRITICAL').count()
    high_scans = ScanResult.objects.filter(overall_risk='HIGH').count()

    return JsonResponse({
        'success': True,
        'stats': {
            'total_scans': total_scans,
            'critical_risk': critical_scans,
            'high_risk': high_scans,
            'medium_risk': ScanResult.objects.filter(overall_risk='MEDIUM').count(),
            'low_risk': ScanResult.objects.filter(overall_risk='LOW').count(),
        }
    })


@require_http_methods(["POST"])
@csrf_protect
def scan_url(request):
    """Scan URL/Domain for DNS information and security issues"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()

        if not url:
            return JsonResponse({
                'success': False,
                'error': 'URL cannot be empty'
            }, status=400)

        if len(url) > 255:
            return JsonResponse({
                'success': False,
                'error': 'URL is too long'
            }, status=400)

        # Perform URL scan
        scanner = URLScanner()
        result = scanner.scan_url(url)

        if result.get('error'):
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)

        return JsonResponse({
            'success': True,
            'data': result
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"URL scan error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Scan failed: {str(e)}'
        }, status=500)


# Allowed nmap scan profiles (no shell injection possible)
NMAP_SCAN_PROFILES = {
    'quick':   ['-F', '--open'],
    'service': ['-sV', '--open'],
    'os':      ['-O', '--open'],
    'intense': ['-A', '--open'],
}

NMAP_PROFILE_LABELS = {
    'quick':   'Quick Scan (-F)',
    'service': 'Service Detection (-sV)',
    'os':      'OS Detection (-O)',
    'intense': 'Intense Scan (-A)',
}


@require_http_methods(["POST"])
@csrf_protect
def nmap_scan(request):
    """Run nmap scan on target"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()
        scan_type = data.get('scan_type', 'quick').strip()

        if not target:
            return JsonResponse({'success': False, 'error': 'Target is required'}, status=400)

        if len(target) > 255:
            return JsonResponse({'success': False, 'error': 'Target input too long'}, status=400)

        # Validate target is a legitimate IP or domain
        scanner = NetworkScanner()
        if not scanner.is_valid_ip(target) and not scanner.is_valid_domain(target):
            return JsonResponse({'success': False, 'error': 'Invalid IP address or domain name'}, status=400)

        if scan_type not in NMAP_SCAN_PROFILES:
            return JsonResponse({'success': False, 'error': 'Invalid scan type'}, status=400)

        nmap_path = shutil.which('nmap')
        if not nmap_path:
            return JsonResponse({'success': False, 'error': 'Nmap is not installed or not found in PATH'}, status=500)

        flags = NMAP_SCAN_PROFILES[scan_type]
        cmd = [nmap_path] + flags + [target]

        start = time.time()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        duration = round(time.time() - start, 2)

        output = proc.stdout or proc.stderr or 'No output returned.'

        return JsonResponse({
            'success': True,
            'data': {
                'target': target,
                'scan_type': NMAP_PROFILE_LABELS.get(scan_type, scan_type),
                'duration': f'{duration}s',
                'output': output,
            }
        })

    except subprocess.TimeoutExpired:
        return JsonResponse({'success': False, 'error': 'Nmap scan timed out (120s limit)'}, status=408)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Nmap scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


# Security headers to check
SECURITY_HEADERS = {
    'Strict-Transport-Security': {
        'label': 'HSTS',
        'description': 'Forces HTTPS connections',
        'severity_missing': 'HIGH',
    },
    'Content-Security-Policy': {
        'label': 'CSP',
        'description': 'Prevents XSS and data injection attacks',
        'severity_missing': 'HIGH',
    },
    'X-Frame-Options': {
        'label': 'X-Frame-Options',
        'description': 'Protects against clickjacking',
        'severity_missing': 'MEDIUM',
    },
    'X-Content-Type-Options': {
        'label': 'X-Content-Type-Options',
        'description': 'Prevents MIME-type sniffing',
        'severity_missing': 'MEDIUM',
    },
    'Referrer-Policy': {
        'label': 'Referrer-Policy',
        'description': 'Controls referrer information leakage',
        'severity_missing': 'LOW',
    },
    'Permissions-Policy': {
        'label': 'Permissions-Policy',
        'description': 'Controls browser feature access (camera, mic, etc.)',
        'severity_missing': 'LOW',
    },
    'X-XSS-Protection': {
        'label': 'X-XSS-Protection',
        'description': 'Legacy XSS filter (older browsers)',
        'severity_missing': 'LOW',
    },
}


@require_http_methods(["POST"])
@csrf_protect
def scan_headers(request):
    """Analyze HTTP security headers of a URL"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()

        if not url:
            return JsonResponse({'success': False, 'error': 'URL is required'}, status=400)

        if len(url) > 512:
            return JsonResponse({'success': False, 'error': 'URL is too long'}, status=400)

        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Validate URL structure
        scanner = NetworkScanner()
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        if not (scanner.is_valid_ip(hostname) or scanner.is_valid_domain(hostname)):
            return JsonResponse({'success': False, 'error': 'Invalid URL or domain'}, status=400)

        try:
            resp = http_requests.get(
                url,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'NetworkScanner/1.0 SecurityAudit'},
                verify=False,
            )
        except http_requests.exceptions.SSLError:
            return JsonResponse({'success': False, 'error': 'SSL certificate error on target'}, status=400)
        except http_requests.exceptions.ConnectionError:
            return JsonResponse({'success': False, 'error': 'Could not connect to the target'}, status=400)
        except http_requests.exceptions.Timeout:
            return JsonResponse({'success': False, 'error': 'Connection timed out'}, status=408)

        headers = dict(resp.headers)
        present = []
        missing = []

        for header_name, meta in SECURITY_HEADERS.items():
            matched_key = next((k for k in headers if k.lower() == header_name.lower()), None)
            if matched_key:
                present.append({
                    'name': header_name,
                    'label': meta['label'],
                    'value': headers[matched_key],
                    'description': meta['description'],
                    'status': 'present',
                })
            else:
                missing.append({
                    'name': header_name,
                    'label': meta['label'],
                    'description': meta['description'],
                    'severity': meta['severity_missing'],
                    'status': 'missing',
                })

        # Info headers
        info_headers = {}
        for key in ['Server', 'X-Powered-By', 'Via', 'X-AspNet-Version', 'X-AspNetMvc-Version']:
            matched = next((k for k in headers if k.lower() == key.lower()), None)
            if matched:
                info_headers[key] = headers[matched]

        # Overall grade
        high_missing = sum(1 for m in missing if m['severity'] == 'HIGH')
        med_missing = sum(1 for m in missing if m['severity'] == 'MEDIUM')
        if high_missing >= 2:
            grade = 'F'
        elif high_missing == 1:
            grade = 'D'
        elif med_missing >= 2:
            grade = 'C'
        elif med_missing == 1:
            grade = 'B'
        elif len(missing) > 0:
            grade = 'B+'
        else:
            grade = 'A'

        return JsonResponse({
            'success': True,
            'data': {
                'url': resp.url,
                'status_code': resp.status_code,
                'grade': grade,
                'present': present,
                'missing': missing,
                'info_headers': info_headers,
                'total_headers': len(headers),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Headers scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_protect
@require_http_methods(["POST"])
@csrf_protect
def ping_scan(request):
    """Perform ICMP ping on target"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()

        if not target:
            return JsonResponse({'success': False, 'error': 'Target is required'}, status=400)

        if len(target) > 255:
            return JsonResponse({'success': False, 'error': 'Target input too long'}, status=400)

        scanner = PingScanner()
        result = scanner.ping(target)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Ping failed')}, status=400)

        return JsonResponse({'success': True, 'data': result})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Ping scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def traceroute_scan(request):
    """Perform traceroute to target"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()

        if not target:
            return JsonResponse({'success': False, 'error': 'Target is required'}, status=400)

        if len(target) > 255:
            return JsonResponse({'success': False, 'error': 'Target input too long'}, status=400)

        scanner = TracerouteScanner()
        result = scanner.traceroute(target)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Traceroute failed')}, status=400)

        return JsonResponse({'success': True, 'data': result})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Traceroute scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def ssl_scan(request):
    """Analyze SSL/TLS certificate"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()
        port = data.get('port', 443)

        if not target:
            return JsonResponse({'success': False, 'error': 'Target is required'}, status=400)

        if len(target) > 255:
            return JsonResponse({'success': False, 'error': 'Target input too long'}, status=400)

        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError('Port out of range')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid port number (1-65535)'}, status=400)

        scanner = SSLScanner()
        result = scanner.scan_certificate(target, port)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'SSL scan failed')}, status=400)

        return JsonResponse({'success': True, 'data': result})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"SSL scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_protect
@require_http_methods(["POST"])
@csrf_protect
def whois_scan(request):
    """Lookup WHOIS information for domain"""
    try:
        data = json.loads(request.body)
        target = data.get('target', '').strip()

        if not target:
            return JsonResponse({'success': False, 'error': 'Target domain is required'}, status=400)

        if len(target) > 255:
            return JsonResponse({'success': False, 'error': 'Target input too long'}, status=400)

        scanner = WhoisScanner()
        result = scanner.lookup_whois(target)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Whois lookup failed')}, status=400)

        return JsonResponse({'success': True, 'data': result})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Whois scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def webpage_scan(request):
    """Analyze webpage content and security"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()

        if not url:
            return JsonResponse({'success': False, 'error': 'URL is required'}, status=400)

        if len(url) > 512:
            return JsonResponse({'success': False, 'error': 'URL input too long'}, status=400)

        scanner = WebpageScanner()
        result = scanner.scan_webpage(url)

        if not result.get('success'):
            return JsonResponse({'success': False, 'error': result.get('error', 'Webpage scan failed')}, status=400)

        return JsonResponse({'success': True, 'data': result})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Webpage scan error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Scan failed: {str(e)}'}, status=500)
