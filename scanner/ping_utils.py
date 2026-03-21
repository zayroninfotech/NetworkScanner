import subprocess
import platform
import re
from typing import Dict, Any
import ipaddress


class PingScanner:
    """Host reachability scanner using ICMP ping"""

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

    def ping(self, target: str, count: int = 4, timeout: int = 5) -> Dict[str, Any]:
        """
        Perform ICMP ping to target

        Args:
            target: IP address or domain name
            count: Number of ping packets to send
            timeout: Timeout in seconds

        Returns:
            Dict with ping results including success, reachable, response time, etc.
        """
        result = {
            'success': False,
            'target': target,
            'reachable': False,
            'response_time_ms': None,
            'packets_sent': count,
            'packets_received': 0,
            'packet_loss': 100.0,
            'min_time': None,
            'max_time': None,
            'avg_time': None,
            'error': None
        }

        # Validate target
        if not target or not self.is_valid_target(target):
            result['error'] = 'Invalid IP address or domain name'
            return result

        try:
            # Platform-specific ping command
            if self.os_type == 'Windows':
                # Windows: ping -n 4 -w 2000 target
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), target]
            else:
                # Linux/Mac: ping -c 4 -W 2 target
                cmd = ['ping', '-c', str(count), '-W', str(timeout), target]

            # Execute ping
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * (count + 1)
            )

            output = proc.stdout + proc.stderr

            # Parse results
            if proc.returncode == 0:
                result['success'] = True
                result['reachable'] = True

                # Parse packet statistics
                if self.os_type == 'Windows':
                    # Windows output format
                    loss_match = re.search(r'(\d+)% loss', output)
                    if loss_match:
                        result['packet_loss'] = float(loss_match.group(1))
                        result['packets_received'] = count - int(count * int(loss_match.group(1)) / 100)

                    # Extract min/max/avg times
                    time_match = re.search(r'Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms', output)
                    if time_match:
                        result['min_time'] = int(time_match.group(1))
                        result['max_time'] = int(time_match.group(2))
                        result['avg_time'] = int(time_match.group(3))
                        result['response_time_ms'] = int(time_match.group(3))

                else:
                    # Linux/Mac output format
                    loss_match = re.search(r'(\d+\.?\d*)% packet loss', output)
                    if loss_match:
                        result['packet_loss'] = float(loss_match.group(1))
                        result['packets_received'] = count - int(count * float(loss_match.group(1)) / 100)

                    # Extract min/avg/max/stddev times
                    time_match = re.search(r'min/avg/max/stddev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
                    if time_match:
                        result['min_time'] = float(time_match.group(1))
                        result['avg_time'] = float(time_match.group(2))
                        result['max_time'] = float(time_match.group(3))
                        result['response_time_ms'] = float(time_match.group(2))

            else:
                # Host unreachable or no response
                result['success'] = True
                result['reachable'] = False
                result['packet_loss'] = 100.0
                result['packets_received'] = 0
                result['error'] = None

        except subprocess.TimeoutExpired:
            result['success'] = False
            result['reachable'] = False
            result['packet_loss'] = 100.0
            result['error'] = f'Ping timeout after {timeout} seconds'

        except FileNotFoundError:
            result['success'] = False
            result['error'] = 'Ping command not found on this system'

        except Exception as e:
            result['success'] = False
            result['error'] = f'Ping failed: {str(e)}'

        return result
