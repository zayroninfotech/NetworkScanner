import ssl
import socket
import ipaddress
from typing import Dict, Any
from datetime import datetime
import re


class SSLScanner:
    """SSL/TLS certificate analyzer"""

    def __init__(self):
        self.results = {}

    def is_valid_target(self, target: str) -> bool:
        """Validate if target is valid IP or domain"""
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            # Check if it's a valid domain
            domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
            return bool(re.match(domain_pattern, target.lower()))

    def scan_certificate(self, target: str, port: int = 443) -> Dict[str, Any]:
        """
        Scan SSL/TLS certificate of target

        Args:
            target: IP address or domain name
            port: HTTPS port (default 443)

        Returns:
            Dict with certificate information and validity status
        """
        result = {
            'success': False,
            'target': target,
            'port': port,
            'certificate': None,
            'chain_valid': False,
            'security_issues': [],
            'error': None
        }

        # Validate inputs
        if not target or not self.is_valid_target(target):
            result['error'] = 'Invalid IP address or domain name'
            return result

        if not isinstance(port, int) or port < 1 or port > 65535:
            result['error'] = 'Invalid port number (1-65535)'
            return result

        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Retrieve certificate
            with socket.create_connection((target, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)

            # Parse certificate
            result['success'] = True
            result['chain_valid'] = True
            cert_info = ssl.cert_time_to_seconds

            # Get certificate details
            try:
                # Get peer certificate in DER format
                with socket.create_connection((target, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=target) as ssock:
                        cert_dict = ssock.getpeercert()
            except ssl.SSLError as ssl_err:
                # Certificate validation error
                result['chain_valid'] = False
                result['security_issues'].append({
                    'severity': 'HIGH',
                    'title': 'Certificate Validation Failed',
                    'description': str(ssl_err),
                    'recommendation': 'Verify certificate is properly signed and not expired'
                })
                cert_dict = self._get_cert_without_validation(target, port)

            if cert_dict:
                cert_info = {
                    'subject': self._parse_subject(cert_dict.get('subject', [])),
                    'issuer': self._parse_issuer(cert_dict.get('issuer', [])),
                    'valid_from': self._parse_date(cert_dict.get('notBefore')),
                    'valid_until': self._parse_date(cert_dict.get('notAfter')),
                    'serial_number': cert_dict.get('serialNumber', 'N/A'),
                    'version': cert_dict.get('version', 'N/A'),
                    'subject_alt_names': self._extract_san(cert_dict)
                }

                # Calculate days remaining
                try:
                    expiry = datetime.strptime(cert_dict.get('notAfter', ''), '%b %d %H:%M:%S %Y %Z')
                    days_remaining = (expiry - datetime.utcnow()).days
                    cert_info['days_remaining'] = days_remaining

                    # Check expiry status
                    if days_remaining < 0:
                        result['security_issues'].append({
                            'severity': 'CRITICAL',
                            'title': 'Certificate Expired',
                            'description': f'Certificate expired {abs(days_remaining)} days ago',
                            'recommendation': 'Renew certificate immediately'
                        })
                    elif days_remaining < 30:
                        result['security_issues'].append({
                            'severity': 'HIGH',
                            'title': 'Certificate Expiring Soon',
                            'description': f'Certificate expires in {days_remaining} days',
                            'recommendation': 'Renew certificate before expiry'
                        })

                except Exception:
                    cert_info['days_remaining'] = None

                result['certificate'] = cert_info

                # Check for weak protocols
                try:
                    context_tls12 = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                    context_tls12.check_hostname = False
                    context_tls12.verify_mode = ssl.CERT_NONE

                    with socket.create_connection((target, port), timeout=10) as sock:
                        try:
                            with context_tls12.wrap_socket(sock, server_hostname=target) as ssock:
                                protocol = ssock.version()
                                if 'TLSv1' in protocol or 'SSLv' in protocol:
                                    result['security_issues'].append({
                                        'severity': 'MEDIUM',
                                        'title': f'Weak Protocol Detected: {protocol}',
                                        'description': f'Server supports {protocol} which is deprecated',
                                        'recommendation': 'Upgrade to TLS 1.3 or higher'
                                    })
                        except (ssl.SSLError, OSError):
                            pass

                except Exception:
                    pass

        except socket.timeout:
            result['error'] = f'Connection timeout to {target}:{port}'

        except socket.gaierror:
            result['error'] = f'Could not resolve hostname: {target}'

        except ConnectionRefusedError:
            result['error'] = f'Connection refused on {target}:{port}'

        except ssl.SSLError as e:
            result['success'] = True
            result['chain_valid'] = False
            result['security_issues'].append({
                'severity': 'HIGH',
                'title': 'SSL/TLS Error',
                'description': str(e),
                'recommendation': 'Check certificate configuration and validity'
            })

        except Exception as e:
            result['success'] = False
            result['error'] = f'Certificate scan failed: {str(e)}'

        return result

    def _get_cert_without_validation(self, target: str, port: int) -> Dict:
        """Get certificate without validation for error cases"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((target, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    return ssock.getpeercert()

        except Exception:
            return None

    def _parse_subject(self, subject: tuple) -> str:
        """Parse certificate subject"""
        try:
            if subject and isinstance(subject[0], tuple):
                return ', '.join([f"{k[0][0]}={k[0][1]}" for k in subject if k])
            return 'N/A'
        except Exception:
            return 'N/A'

    def _parse_issuer(self, issuer: tuple) -> str:
        """Parse certificate issuer"""
        try:
            if issuer and isinstance(issuer[0], tuple):
                return ', '.join([f"{k[0][0]}={k[0][1]}" for k in issuer if k])
            return 'N/A'
        except Exception:
            return 'N/A'

    def _parse_date(self, date_str: str) -> str:
        """Parse certificate date"""
        if not date_str:
            return 'N/A'
        return date_str

    def _extract_san(self, cert_dict: Dict) -> list:
        """Extract Subject Alternative Names"""
        san = []
        try:
            for ext_tuple in cert_dict.get('subjectAltName', []):
                san.append(ext_tuple[1])
        except Exception:
            pass
        return san if san else ['N/A']
