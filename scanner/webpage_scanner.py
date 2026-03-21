import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List
import re


class WebpageScanner:
    """Web page analyzer for security and content analysis"""

    def __init__(self):
        self.results = {}

    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def scan_webpage(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive webpage scanning and analysis

        Args:
            url: URL to scan

        Returns:
            Dict with webpage analysis results
        """
        result = {
            'success': False,
            'url': url,
            'page_info': None,
            'security_issues': [],
            'links_analysis': None,
            'forms_analysis': None,
            'headers_analysis': None,
            'error': None
        }

        # Validate URL
        if not url:
            result['error'] = 'URL is required'
            return result

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            result['url'] = url

        if not self.is_valid_url(url):
            result['error'] = 'Invalid URL format'
            return result

        try:
            # Fetch webpage
            response = requests.get(
                url,
                timeout=10,
                headers={'User-Agent': 'NetSentinel/1.0 WebpageScanner'},
                allow_redirects=True,
                verify=False
            )

            result['success'] = True
            final_url = response.url

            # Page info
            result['page_info'] = {
                'original_url': url,
                'final_url': final_url,
                'status_code': response.status_code,
                'page_title': self._extract_title(response.text),
                'page_size_bytes': len(response.content),
                'redirect_chain': url != final_url,
                'content_type': response.headers.get('Content-Type', 'Unknown'),
            }

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Security headers analysis
            result['headers_analysis'] = self._analyze_headers(response.headers)

            # Links analysis
            result['links_analysis'] = self._analyze_links(soup, final_url)

            # Forms analysis
            result['forms_analysis'] = self._analyze_forms(soup)

            # Security issues detection
            result['security_issues'] = self._detect_security_issues(
                response.headers, soup, response.text
            )

        except requests.exceptions.SSLError:
            result['success'] = True
            result['error'] = 'SSL Certificate Error'
            result['security_issues'].append({
                'severity': 'HIGH',
                'title': 'SSL Certificate Error',
                'description': 'Unable to verify SSL certificate',
                'recommendation': 'Check if certificate is valid and trusted'
            })

        except requests.exceptions.ConnectionError:
            result['error'] = 'Cannot connect to URL'

        except requests.exceptions.Timeout:
            result['error'] = 'Request timeout (10 seconds)'

        except Exception as e:
            result['error'] = f'Webpage scan failed: {str(e)}'

        return result

    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.find('title')
            return title.string if title else 'No title found'
        except Exception:
            return 'Unable to extract title'

    def _analyze_headers(self, headers: dict) -> Dict[str, Any]:
        """Analyze HTTP response headers"""
        return {
            'server': headers.get('Server', 'Not disclosed'),
            'powered_by': headers.get('X-Powered-By', 'Not disclosed'),
            'cache_control': headers.get('Cache-Control', 'Not set'),
            'content_security_policy': headers.get('Content-Security-Policy', 'Not set'),
            'x_frame_options': headers.get('X-Frame-Options', 'Not set'),
            'total_headers': len(headers)
        }

    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Analyze all links on the page"""
        links = {
            'internal_links': [],
            'external_links': [],
            'total_links': 0,
            'broken_links': []
        }

        try:
            domain = urlparse(base_url).netloc

            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)[:50]  # First 50 chars

                if href.startswith('http'):
                    url_domain = urlparse(href).netloc
                    if url_domain == domain:
                        links['internal_links'].append({
                            'url': href,
                            'text': text or 'No text'
                        })
                    else:
                        links['external_links'].append({
                            'url': href,
                            'text': text or 'No text'
                        })
                elif href.startswith('#'):
                    # Anchor link
                    links['internal_links'].append({
                        'url': href,
                        'text': text or 'Anchor'
                    })

            links['total_links'] = len(links['internal_links']) + len(links['external_links'])

        except Exception as e:
            links['error'] = str(e)

        return links

    def _analyze_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze forms on the page"""
        forms = {
            'total_forms': 0,
            'forms': []
        }

        try:
            form_elements = soup.find_all('form')
            forms['total_forms'] = len(form_elements)

            for idx, form in enumerate(form_elements):
                form_info = {
                    'id': idx + 1,
                    'method': form.get('method', 'GET').upper(),
                    'action': form.get('action', 'Not specified'),
                    'has_csrf': bool(form.find('input', {'name': 'csrf_token'})),
                    'input_fields': []
                }

                # Find input fields
                for inp in form.find_all('input'):
                    field_type = inp.get('type', 'text').lower()
                    field_name = inp.get('name', 'unnamed')
                    form_info['input_fields'].append({
                        'name': field_name,
                        'type': field_type,
                        'required': inp.has_attr('required')
                    })

                forms['forms'].append(form_info)

        except Exception as e:
            forms['error'] = str(e)

        return forms

    def _detect_security_issues(self, headers: dict, soup: BeautifulSoup, html: str) -> List[Dict]:
        """Detect potential security issues"""
        issues = []

        # Check for missing security headers
        security_headers = {
            'Strict-Transport-Security': 'HSTS',
            'Content-Security-Policy': 'CSP',
            'X-Frame-Options': 'Clickjacking Protection',
            'X-Content-Type-Options': 'MIME Sniffing Protection'
        }

        for header, label in security_headers.items():
            if header not in headers:
                issues.append({
                    'severity': 'MEDIUM',
                    'title': f'Missing {label} Header',
                    'description': f'{header} header not found',
                    'recommendation': f'Add {header} header to response'
                })

        # Check for deprecated HTML
        if 'target="_blank"' in html and 'rel="noopener"' not in html:
            issues.append({
                'severity': 'LOW',
                'title': 'Potential Security Issue: target="_blank"',
                'description': 'Links opening in new tab without rel="noopener"',
                'recommendation': 'Add rel="noopener noreferrer" to links'
            })

        # Check for inline scripts
        inline_scripts = soup.find_all('script', text=True)
        if len(inline_scripts) > 0:
            issues.append({
                'severity': 'LOW',
                'title': 'Inline JavaScript Detected',
                'description': f'Found {len(inline_scripts)} inline script tags',
                'recommendation': 'Consider moving scripts to external files'
            })

        # Check for deprecated tags
        deprecated = ['<marquee>', '<font>', '<center>']
        for tag in deprecated:
            if tag in html.lower():
                issues.append({
                    'severity': 'LOW',
                    'title': f'Deprecated HTML: {tag}',
                    'description': f'{tag} is deprecated',
                    'recommendation': 'Use modern CSS instead'
                })

        # Server disclosure
        if 'Server' in headers:
            issues.append({
                'severity': 'LOW',
                'title': 'Server Information Disclosed',
                'description': f'Server: {headers.get("Server")}',
                'recommendation': 'Consider hiding server version information'
            })

        return issues
