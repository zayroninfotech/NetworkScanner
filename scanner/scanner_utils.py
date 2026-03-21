import socket
import dns.resolver
import ipaddress
from typing import Dict, List, Tuple
import re

class NetworkScanner:
    """Entry-level network scanning utility for security assessment"""

    # Common ports to scan
    COMMON_PORTS = {
        21: {'name': 'FTP', 'risk': 'HIGH', 'reason': 'Unencrypted file transfer'},
        22: {'name': 'SSH', 'risk': 'LOW', 'reason': 'Secure shell - usually safe'},
        23: {'name': 'Telnet', 'risk': 'CRITICAL', 'reason': 'Unencrypted remote access'},
        25: {'name': 'SMTP', 'risk': 'MEDIUM', 'reason': 'Email relay - can be abused'},
        53: {'name': 'DNS', 'risk': 'MEDIUM', 'reason': 'DNS queries - info disclosure'},
        80: {'name': 'HTTP', 'risk': 'MEDIUM', 'reason': 'Unencrypted web traffic'},
        110: {'name': 'POP3', 'risk': 'HIGH', 'reason': 'Unencrypted email access'},
        143: {'name': 'IMAP', 'risk': 'HIGH', 'reason': 'Unencrypted email access'},
        443: {'name': 'HTTPS', 'risk': 'LOW', 'reason': 'Encrypted web traffic - safe'},
        445: {'name': 'SMB', 'risk': 'CRITICAL', 'reason': 'Windows file sharing - vulnerable'},
        3306: {'name': 'MySQL', 'risk': 'CRITICAL', 'reason': 'Exposed database - data breach'},
        3389: {'name': 'RDP', 'risk': 'CRITICAL', 'reason': 'Remote desktop - lateral movement'},
        5432: {'name': 'PostgreSQL', 'risk': 'CRITICAL', 'reason': 'Exposed database - data breach'},
        5900: {'name': 'VNC', 'risk': 'CRITICAL', 'reason': 'Remote access - no encryption'},
        8080: {'name': 'HTTP-ALT', 'risk': 'MEDIUM', 'reason': 'Alternate web service'},
        8443: {'name': 'HTTPS-ALT', 'risk': 'LOW', 'reason': 'Alternate HTTPS service'},
    }

    # Risk recommendations
    RECOMMENDATIONS = {
        'CRITICAL': [
            '🔴 CRITICAL RISK - Immediate action required',
            '• Firewall: Block access to this port immediately',
            '• Network: Isolate the host if not essential',
            '• Authentication: Enforce strong credentials if service required',
            '• Encryption: Enable TLS/SSL for all communications'
        ],
        'HIGH': [
            '🟠 HIGH RISK - Address promptly',
            '• Restrict: Limit access to trusted networks only',
            '• Update: Apply latest security patches',
            '• Monitor: Enable logging and intrusion detection',
            '• Credentials: Use strong passwords/key authentication'
        ],
        'MEDIUM': [
            '🟡 MEDIUM RISK - Monitor and secure',
            '• Baseline: Ensure service is up to date',
            '• Access: Implement access control lists (ACLs)',
            '• Logging: Enable and monitor service logs',
            '• Updates: Subscribe to security advisories'
        ],
        'LOW': [
            '🟢 LOW RISK - Standard practice',
            '• Monitor: Regular vulnerability scanning',
            '• Updates: Keep software current',
            '• Config: Review security configuration',
            '• Testing: Periodic penetration testing'
        ]
    }

    def __init__(self):
        self.results = {}

    def is_valid_ip(self, ip_string: str) -> bool:
        """Validate if string is a valid IP address"""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False

    def is_valid_domain(self, domain: str) -> bool:
        """Validate if string is a valid domain"""
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        return bool(re.match(domain_pattern, domain.lower()))

    def is_private_ip(self, ip_string: str) -> bool:
        """Check if IP is private/internal"""
        try:
            ip = ipaddress.ip_address(ip_string)
            return ip.is_private
        except ValueError:
            return False

    def resolve_dns(self, domain: str) -> Dict:
        """Resolve domain to IP address"""
        result = {
            'success': False,
            'domain': domain,
            'ips': [],
            'error': None
        }

        try:
            answers = dns.resolver.resolve(domain, 'A')
            result['ips'] = [str(rdata) for rdata in answers]
            result['success'] = True
        except dns.resolver.NXDOMAIN:
            result['error'] = 'Domain not found (NXDOMAIN)'
        except dns.resolver.NoAnswer:
            result['error'] = 'No A records found'
        except Exception as e:
            result['error'] = f'DNS resolution failed: {str(e)}'

        return result

    def scan_ports(self, target: str) -> Dict:
        """Scan target for open ports using socket"""
        scan_result = {
            'target': target,
            'ports': [],
            'scan_method': 'Socket-based TCP connection',
            'timestamp': None
        }

        for port, service_info in self.COMMON_PORTS.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)  # 2 second timeout

                result = sock.connect_ex((target, port))
                sock.close()

                if result == 0:  # Port is open
                    scan_result['ports'].append({
                        'port': port,
                        'service': service_info['name'],
                        'status': 'OPEN',
                        'risk_level': service_info['risk'],
                        'reason': service_info['reason']
                    })
            except socket.gaierror:
                return {
                    'target': target,
                    'ports': [],
                    'error': 'Hostname could not be resolved'
                }
            except Exception as e:
                continue

        return scan_result

    def assess_security(self, scan_result: Dict) -> Dict:
        """Assess overall security based on open ports"""
        assessment = {
            'overall_risk': 'LOW',
            'critical_ports': [],
            'high_risk_ports': [],
            'medium_risk_ports': [],
            'recommendations': [],
            'summary': ''
        }

        if not scan_result.get('ports'):
            assessment['summary'] = '✅ No common ports detected as open. Good baseline security.'
            return assessment

        risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for port_info in scan_result['ports']:
            risk = port_info['risk_level']
            risk_levels[risk] += 1

            if risk == 'CRITICAL':
                assessment['critical_ports'].append(port_info)
            elif risk == 'HIGH':
                assessment['high_risk_ports'].append(port_info)
            elif risk == 'MEDIUM':
                assessment['medium_risk_ports'].append(port_info)

        # Determine overall risk
        if risk_levels['CRITICAL'] > 0:
            assessment['overall_risk'] = 'CRITICAL'
        elif risk_levels['HIGH'] > 0:
            assessment['overall_risk'] = 'HIGH'
        elif risk_levels['MEDIUM'] > 0:
            assessment['overall_risk'] = 'MEDIUM'
        else:
            assessment['overall_risk'] = 'LOW'

        # Generate recommendations
        assessment['recommendations'] = self.RECOMMENDATIONS.get(assessment['overall_risk'], [])

        # Generate summary
        total_open = len(scan_result['ports'])
        summary_parts = [f"Scan found {total_open} open port(s)"]
        if risk_levels['CRITICAL'] > 0:
            summary_parts.append(f"{risk_levels['CRITICAL']} CRITICAL")
        if risk_levels['HIGH'] > 0:
            summary_parts.append(f"{risk_levels['HIGH']} HIGH")
        if risk_levels['MEDIUM'] > 0:
            summary_parts.append(f"{risk_levels['MEDIUM']} MEDIUM")

        assessment['summary'] = ', '.join(summary_parts) + '.'

        return assessment

    def full_scan(self, target: str) -> Dict:
        """Perform full security scan on target"""
        final_result = {
            'target': target,
            'is_private': False,
            'dns_info': None,
            'scan_info': None,
            'assessment': None,
            'error': None
        }

        # Input validation
        if not target or len(target.strip()) == 0:
            final_result['error'] = 'Target cannot be empty'
            return final_result

        target = target.strip().lower()

        # Check if input is domain or IP
        if self.is_valid_domain(target):
            # It's a domain - resolve first
            dns_result = self.resolve_dns(target)
            final_result['dns_info'] = dns_result

            if not dns_result['success']:
                final_result['error'] = dns_result['error']
                return final_result

            # Use first resolved IP for scanning
            target_ip = dns_result['ips'][0]
        elif self.is_valid_ip(target):
            target_ip = target
        else:
            final_result['error'] = 'Invalid IP address or domain name'
            return final_result

        # Check if private
        final_result['is_private'] = self.is_private_ip(target_ip)

        # Perform port scan
        scan_info = self.scan_ports(target_ip)
        final_result['scan_info'] = scan_info

        # Assess security
        assessment = self.assess_security(scan_info)
        final_result['assessment'] = assessment

        return final_result
