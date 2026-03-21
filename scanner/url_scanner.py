import dns.resolver
import dns.reversename
import socket
import whois
from typing import Dict, List
import re

class URLScanner:
    """URL/Domain scanner for DNS and security analysis"""

    DNS_SECURITY_ISSUES = {
        'dns_spoofing': {
            'name': 'DNS Spoofing Risk',
            'severity': 'HIGH',
            'description': 'DNS responses should be validated',
            'solution': 'Enable DNSSEC validation'
        },
        'no_dnssec': {
            'name': 'DNSSEC Not Enabled',
            'severity': 'MEDIUM',
            'description': 'Domain does not have DNSSEC enabled',
            'solution': 'Enable DNSSEC for domain'
        },
        'open_resolver': {
            'name': 'Open DNS Resolver',
            'severity': 'MEDIUM',
            'description': 'DNS resolver accepts queries from anywhere',
            'solution': 'Restrict DNS resolver access'
        },
        'dns_amplification': {
            'name': 'DNS Amplification Risk',
            'severity': 'MEDIUM',
            'description': 'Large DNS responses can be amplified in attacks',
            'solution': 'Implement rate limiting'
        },
        'subdomain_takeover': {
            'name': 'Subdomain Takeover Risk',
            'severity': 'HIGH',
            'description': 'Unresolved subdomains can be taken over',
            'solution': 'Monitor and remove unused subdomains'
        }
    }

    def __init__(self):
        self.results = {}

    def is_valid_url(self, url: str) -> bool:
        """Validate if string is a valid URL or domain"""
        # Remove protocol if present
        url_clean = url.replace('http://', '').replace('https://', '')

        # Basic domain validation
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        return bool(re.match(domain_pattern, url_clean.lower()))

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        url = url.strip().lower()
        # Remove protocol
        url = url.replace('http://', '').replace('https://', '')
        # Remove path
        url = url.split('/')[0]
        # Remove port
        url = url.split(':')[0]
        return url

    def resolve_dns(self, domain: str) -> Dict:
        """Resolve domain to IP addresses"""
        result = {
            'success': False,
            'a_records': [],
            'aaaa_records': [],
            'mx_records': [],
            'ns_records': [],
            'cname_record': None,
            'txt_records': [],
            'error': None
        }

        try:
            # A Records (IPv4)
            try:
                a_answers = dns.resolver.resolve(domain, 'A')
                result['a_records'] = [str(rdata) for rdata in a_answers]
            except:
                pass

            # AAAA Records (IPv6)
            try:
                aaaa_answers = dns.resolver.resolve(domain, 'AAAA')
                result['aaaa_records'] = [str(rdata) for rdata in aaaa_answers]
            except:
                pass

            # MX Records
            try:
                mx_answers = dns.resolver.resolve(domain, 'MX')
                result['mx_records'] = [(int(rdata.preference), str(rdata.exchange)) for rdata in mx_answers]
            except:
                pass

            # NS Records
            try:
                ns_answers = dns.resolver.resolve(domain, 'NS')
                result['ns_records'] = [str(rdata) for rdata in ns_answers]
            except:
                pass

            # CNAME Record
            try:
                cname_answers = dns.resolver.resolve(domain, 'CNAME')
                result['cname_record'] = str(cname_answers[0])
            except:
                pass

            # TXT Records
            try:
                txt_answers = dns.resolver.resolve(domain, 'TXT')
                result['txt_records'] = [str(rdata) for rdata in txt_answers]
            except:
                pass

            result['success'] = True

        except dns.resolver.NXDOMAIN:
            result['error'] = '❌ Domain not found (NXDOMAIN) - This domain does not exist'
        except dns.resolver.NoNameservers:
            result['error'] = '❌ No nameservers found for this domain'
        except dns.name.InvalidName:
            result['error'] = '❌ Invalid domain name format'
        except Exception as e:
            result['error'] = f'❌ DNS resolution failed: {str(e)}'

        return result

    def get_reverse_dns(self, ip_address: str) -> str:
        """Get reverse DNS for IP address"""
        try:
            reversed_ip = dns.reversename.from_address(ip_address)
            result = dns.resolver.resolve(reversed_ip, 'PTR')
            return str(result[0]).rstrip('.')
        except:
            return None

    def detect_dns_security_issues(self, dns_data: Dict, domain: str) -> List[Dict]:
        """Detect potential DNS security issues"""
        issues = []

        # Check if DNS resolves
        if not dns_data['success']:
            issues.append({
                'type': 'no_dns',
                'severity': 'CRITICAL',
                'title': '⚠️ DNS Resolution Failed',
                'description': 'Domain does not resolve to any IP address',
                'recommendation': 'Verify domain name is correct and DNS is properly configured'
            })
            return issues

        # Check for multiple A records (load balancing - good)
        if len(dns_data['a_records']) > 1:
            issues.append({
                'type': 'load_balancing',
                'severity': 'INFO',
                'title': '✅ Load Balancing Detected',
                'description': f'Domain has {len(dns_data["a_records"])} IP addresses (load balancing)',
                'recommendation': 'Good practice for redundancy and load distribution'
            })

        # Check for IPv6
        if len(dns_data['aaaa_records']) == 0:
            issues.append({
                'type': 'no_ipv6',
                'severity': 'LOW',
                'title': '📝 No IPv6 Support',
                'description': 'Domain does not have IPv6 AAAA records',
                'recommendation': 'Consider adding IPv6 support for modern networks'
            })

        # Check for MX records
        if len(dns_data['mx_records']) == 0:
            issues.append({
                'type': 'no_mx',
                'severity': 'MEDIUM',
                'title': '📧 No Mail Server Configured',
                'description': 'No MX records found - email delivery will fail',
                'recommendation': 'Configure MX records if you need email service'
            })

        # Check for DNS spoofing risk
        issues.append({
            'type': 'dns_spoofing',
            'severity': 'MEDIUM',
            'title': '🔓 DNS Spoofing Risk',
            'description': 'DNS responses should be validated and signed',
            'recommendation': 'Enable DNSSEC for enhanced security'
        })

        # Check for DNS amplification risk (if many TXT records)
        if len(dns_data['txt_records']) > 5:
            issues.append({
                'type': 'dns_amplification',
                'severity': 'MEDIUM',
                'title': '⚡ DNS Amplification Risk',
                'description': f'Domain has {len(dns_data["txt_records"])} TXT records - could be used in amplification attacks',
                'recommendation': 'Monitor and limit unnecessary TXT records'
            })

        # Check for subdomain takeover risk
        if dns_data['cname_record']:
            issues.append({
                'type': 'cname_chain',
                'severity': 'LOW',
                'title': '🔗 CNAME Chain Detected',
                'description': 'Domain uses CNAME alias for redirection',
                'recommendation': 'Monitor CNAME targets for availability'
            })

        return issues

    def scan_url(self, url: str) -> Dict:
        """Complete URL/Domain scanning"""
        result = {
            'url': url,
            'domain': None,
            'dns_info': None,
            'security_issues': [],
            'primary_ip': None,
            'all_ips': [],
            'reverse_dns': None,
            'error': None
        }

        # Validate URL
        if not url or len(url.strip()) == 0:
            result['error'] = 'URL/Domain cannot be empty'
            return result

        # Extract domain
        try:
            domain = self.extract_domain(url)
            if not self.is_valid_url(domain):
                result['error'] = 'Invalid URL or domain format'
                return result
            result['domain'] = domain
        except Exception as e:
            result['error'] = f'Invalid URL format: {str(e)}'
            return result

        # Resolve DNS
        dns_info = self.resolve_dns(domain)
        result['dns_info'] = dns_info

        if dns_info['success']:
            # Get primary IP
            if dns_info['a_records']:
                result['primary_ip'] = dns_info['a_records'][0]
                result['all_ips'] = dns_info['a_records']

                # Get reverse DNS
                result['reverse_dns'] = self.get_reverse_dns(result['primary_ip'])

            # Detect security issues
            result['security_issues'] = self.detect_dns_security_issues(dns_info, domain)
        else:
            result['security_issues'] = self.detect_dns_security_issues(dns_info, domain)

        return result
