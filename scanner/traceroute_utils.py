import subprocess
import platform
import re
from typing import Dict, Any, List
import ipaddress
import shutil
import os


class TracerouteScanner:
    """Network path analysis using traceroute/tracert"""

    def __init__(self):
        self.results = {}
        self.os_type = platform.system()

    def is_valid_target(self, target: str) -> bool:
        """Validate if target is valid IP or domain"""
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            # Check if it's a valid domain
            domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
            return bool(re.match(domain_pattern, target.lower()))

    def traceroute(self, target: str, max_hops: int = 30, timeout: int = 5) -> Dict[str, Any]:
        """
        Perform traceroute to target

        Args:
            target: IP address or domain name
            max_hops: Maximum number of hops to trace
            timeout: Timeout per hop in seconds

        Returns:
            Dict with traceroute results including hops and latencies
        """
        result = {
            'success': False,
            'target': target,
            'hops': [],
            'total_hops': 0,
            'reached': False,
            'error': None
        }

        # Validate target
        if not target or not self.is_valid_target(target):
            result['error'] = 'Invalid IP address or domain name'
            return result

        try:
            # Platform-specific traceroute command
            if self.os_type == 'Windows':
                # Windows: tracert -h 30 -w 2000 target
                cmd = ['tracert', '-h', str(max_hops), '-w', str(timeout * 1000), target]
            else:
                # Linux: traceroute -m 30 -w 2 target
                # Find traceroute command with fallback paths
                traceroute_cmd = shutil.which('traceroute')
                if not traceroute_cmd and os.path.exists('/usr/bin/traceroute'):
                    traceroute_cmd = '/usr/bin/traceroute'
                if not traceroute_cmd and os.path.exists('/usr/sbin/traceroute'):
                    traceroute_cmd = '/usr/sbin/traceroute'
                if not traceroute_cmd:
                    result['success'] = False
                    result['error'] = 'Traceroute command not found on this system'
                    return result

                cmd = [traceroute_cmd, '-m', str(max_hops), '-w', str(timeout), target]

            # Execute traceroute
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max_hops * timeout + 10
            )

            output = proc.stdout + proc.stderr
            result['success'] = True

            # Parse output
            hops = self._parse_traceroute_output(output, self.os_type)
            result['hops'] = hops
            result['total_hops'] = len(hops)

            # Check if destination was reached
            if hops and hops[-1].get('status') == 'reached':
                result['reached'] = True

        except subprocess.TimeoutExpired:
            result['success'] = False
            result['error'] = f'Traceroute timeout after {max_hops * timeout} seconds'

        except FileNotFoundError:
            result['success'] = False
            result['error'] = f'Traceroute command not found. Try "tracert" on Windows or "traceroute" on Linux/Mac'

        except Exception as e:
            result['success'] = False
            result['error'] = f'Traceroute failed: {str(e)}'

        return result

    def _parse_traceroute_output(self, output: str, os_type: str) -> List[Dict[str, Any]]:
        """Parse traceroute output and extract hop information"""
        hops = []

        lines = output.split('\n')

        if os_type == 'Windows':
            # Windows tracert output format:
            # 1    <1 ms    <1 ms    <1 ms  192.168.1.1
            # 2    * * * Request timed out.
            for line in lines:
                line = line.strip()
                if not line or not line[0].isdigit():
                    continue

                parts = line.split()
                if len(parts) < 4:
                    continue

                try:
                    hop_num = int(parts[0])

                    # Check for timeout
                    if '*' in line and 'Request timed out' in output[output.index(line):output.index(line) + 100]:
                        hops.append({
                            'hop_number': hop_num,
                            'ip': None,
                            'hostname': 'No response',
                            'latency_ms': None,
                            'status': 'timeout'
                        })
                    else:
                        # Extract times and IP
                        times = []
                        ip = None
                        for i in range(1, len(parts)):
                            if parts[i] == '*':
                                times.append(None)
                            elif 'ms' in parts[i]:
                                try:
                                    times.append(float(parts[i].replace('ms', '')))
                                except ValueError:
                                    pass
                            elif self._is_ip(parts[i]):
                                ip = parts[i]

                        avg_latency = None
                        if times:
                            valid_times = [t for t in times if t is not None]
                            if valid_times:
                                avg_latency = sum(valid_times) / len(valid_times)

                        hops.append({
                            'hop_number': hop_num,
                            'ip': ip,
                            'hostname': self._reverse_dns_lookup(ip) if ip else 'Unknown',
                            'latency_ms': avg_latency,
                            'status': 'reached' if ip else 'timeout'
                        })

                except (ValueError, IndexError):
                    continue

        else:
            # Linux/Mac traceroute output format:
            # 1  192.168.1.1 (192.168.1.1)  0.123 ms  0.456 ms  0.789 ms
            # 2  * * * Request timed out
            for line in lines:
                line = line.strip()
                if not line or not line[0].isdigit():
                    continue

                match = re.match(r'(\d+)\s+([\w\.\-]+)\s+\(([\d\.]+)\)', line)
                if match:
                    hop_num = int(match.group(1))
                    hostname = match.group(2)
                    ip = match.group(3)

                    # Extract latencies
                    latencies = re.findall(r'([\d.]+)\s+ms', line)
                    avg_latency = None
                    if latencies:
                        avg_latency = sum(float(l) for l in latencies) / len(latencies)

                    hops.append({
                        'hop_number': hop_num,
                        'ip': ip,
                        'hostname': hostname,
                        'latency_ms': avg_latency,
                        'status': 'reached'
                    })

                elif '*' in line:
                    # Timeout hop
                    match = re.match(r'(\d+)\s+\*', line)
                    if match:
                        hop_num = int(match.group(1))
                        hops.append({
                            'hop_number': hop_num,
                            'ip': None,
                            'hostname': 'No response',
                            'latency_ms': None,
                            'status': 'timeout'
                        })

        return hops

    def _is_ip(self, ip_string: str) -> bool:
        """Check if string is valid IP address"""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False

    def _reverse_dns_lookup(self, ip: str) -> str:
        """Attempt reverse DNS lookup for IP"""
        try:
            import socket
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return ip
