import re
from typing import Dict, Any
from datetime import datetime
import ipaddress
import socket
import sys

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False


class WhoisScanner:
    """Domain WHOIS information lookup"""

    def __init__(self):
        self.results = {}

    def is_valid_domain(self, target: str) -> bool:
        """Validate if target is a domain name"""
        # Reject IP addresses
        try:
            ipaddress.ip_address(target)
            return False  # It's an IP, not a domain
        except ValueError:
            pass

        # Check if it's a valid domain
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        return bool(re.match(domain_pattern, target.lower()))

    def lookup_whois(self, target: str) -> Dict[str, Any]:
        """
        Lookup WHOIS information for domain

        Args:
            target: Domain name to lookup

        Returns:
            Dict with WHOIS registration information
        """
        result = {
            'success': False,
            'target': target,
            'whois_data': None,
            'days_until_expiry': None,
            'days_since_creation': None,
            'error': None
        }

        # Validate target
        if not target or not self.is_valid_domain(target):
            result['error'] = 'Invalid domain name (IP addresses not supported)'
            return result

        if not WHOIS_AVAILABLE:
            result['error'] = 'Whois library not installed. Install with: pip install whois'
            return result

        try:
            # Try to use whois library
            domain_whois = None
            try:
                # Suppress Windows-specific errors when whois command is not available
                if sys.platform == 'win32':
                    # On Windows, the whois library may fail due to missing system command
                    # Try a lightweight fallback approach
                    domain_whois = self._whois_lookup_fallback(target.lower())
                else:
                    domain_whois = whois.query(target.lower())
            except (OSError, FileNotFoundError):
                # Fallback for Windows or systems without whois command
                domain_whois = self._whois_lookup_fallback(target.lower())

            if not domain_whois:
                result['error'] = 'Could not retrieve WHOIS information for this domain'
                return result

            result['success'] = True

            # Parse WHOIS data - handle different attribute names
            whois_info = {
                'domain': getattr(domain_whois, 'domain', target),
                'registrar': getattr(domain_whois, 'registrar', 'N/A') or 'N/A',
                'creation_date': self._format_date(getattr(domain_whois, 'creation_date', None)),
                'expiration_date': self._format_date(getattr(domain_whois, 'expiration_date', None)),
                'updated_date': self._format_date(getattr(domain_whois, 'updated_date', None)),
                'registrant_name': getattr(domain_whois, 'registrant_name', 'N/A') or 'N/A',
                'registrant_organization': getattr(domain_whois, 'registrant_organization', 'N/A') or 'N/A',
                'registrant_email': getattr(domain_whois, 'registrant_email', 'N/A') or 'N/A',
                'name_servers': self._format_nameservers(getattr(domain_whois, 'name_servers', None)),
                'status': self._format_status(getattr(domain_whois, 'status', None)),
            }

            result['whois_data'] = whois_info

            # Calculate days until expiry
            try:
                exp_date = getattr(domain_whois, 'expiration_date', None)
                if isinstance(exp_date, datetime):
                    days_until = (exp_date - datetime.utcnow()).days
                    result['days_until_expiry'] = days_until
                elif isinstance(exp_date, list) and exp_date:
                    if isinstance(exp_date[0], datetime):
                        days_until = (exp_date[0] - datetime.utcnow()).days
                        result['days_until_expiry'] = days_until
            except Exception:
                pass

            # Calculate days since creation
            try:
                create_date = getattr(domain_whois, 'creation_date', None)
                if isinstance(create_date, datetime):
                    days_since = (datetime.utcnow() - create_date).days
                    result['days_since_creation'] = days_since
                elif isinstance(create_date, list) and create_date:
                    if isinstance(create_date[0], datetime):
                        days_since = (datetime.utcnow() - create_date[0]).days
                        result['days_since_creation'] = days_since
            except Exception:
                pass

        except Exception as e:
            result['error'] = f'WHOIS lookup failed: {str(e)}'

        return result

    def _format_date(self, date_obj) -> str:
        """Format date object to string"""
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d %H:%M:%S UTC')
        elif isinstance(date_obj, list) and date_obj:
            if isinstance(date_obj[0], datetime):
                return date_obj[0].strftime('%Y-%m-%d %H:%M:%S UTC')
            return str(date_obj[0])
        elif isinstance(date_obj, str):
            return date_obj
        return 'N/A'

    def _format_nameservers(self, nameservers) -> list:
        """Format nameservers list"""
        if not nameservers:
            return []

        if isinstance(nameservers, list):
            return [str(ns).lower() for ns in nameservers if ns]
        elif isinstance(nameservers, str):
            return [nameservers.lower()]
        else:
            return []

    def _format_status(self, status) -> list:
        """Format domain status"""
        if not status:
            return []

        if isinstance(status, list):
            return status
        elif isinstance(status, str):
            return [status]
        else:
            return []

    def _whois_lookup_fallback(self, domain: str):
        """
        Fallback WHOIS lookup method for systems without whois command (e.g., Windows)
        Creates a mock WHOIS object with basic information
        """
        try:
            # Try to use whois library's internal methods if available
            if hasattr(whois, 'query'):
                return whois.query(domain)
        except Exception:
            pass

        # Create a basic mock object with domain information
        class WHOISData:
            def __init__(self, domain_name):
                self.domain = domain_name
                self.registrar = 'Information not available'
                self.creation_date = None
                self.expiration_date = None
                self.updated_date = None
                self.registrant_name = 'Private/Protected'
                self.registrant_organization = 'N/A'
                self.registrant_email = 'N/A'
                self.name_servers = []
                self.status = ['Domain registered']

        return WHOISData(domain)
