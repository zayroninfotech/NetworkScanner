# 🛡️ Network Scanner & Security Analyzer

An entry-level Web-Based Network Scanner Dashboard built with Django. Perfect for CEH (Certified Ethical Hacker) students and security professionals learning about network reconnaissance and basic security assessment.

## Features

### 🔍 Core Scanning Capabilities
- **IP Address Input**: Scan individual IP addresses or domains
- **DNS Resolution**: Resolve domain names to IP addresses
- **TCP Port Scanning**: Scan 15 common ports with service identification
- **Open Service Detection**: Identify services running on open ports
- **Risk Assessment**: Categorize ports as CRITICAL, HIGH, MEDIUM, or LOW risk

### 📊 Security Analysis
- **Risk Level Classification**: CRITICAL, HIGH, MEDIUM, LOW
- **Private/Public IP Detection**: Identify if IP is private or public
- **Service-Based Risk Scoring**: Built-in database of risky services
- **Security Recommendations**: Contextual security advice for each risk level

### 📈 Dashboard Features
- **Scan History**: View all previous scans
- **Risk Statistics**: Track critical, high, medium, and low-risk scans
- **Detailed Results**: Full assessment including port details and recommendations
- **Admin Panel**: Django admin interface for managing scan data

## ⚠️ Legal & Ethical Notice

**WARNING**: This tool is intended ONLY for:
- ✅ Authorized penetration testing
- ✅ Educational purposes (CEH courses, cybersecurity training)
- ✅ Scanning systems you own
- ✅ Systems where you have explicit written permission

**NEVER** use this tool to:
- ❌ Scan systems you don't own or lack permission to test
- ❌ Launch denial-of-service attacks
- ❌ Gain unauthorized access
- ❌ For malicious purposes

Users are responsible for all actions performed with this tool.

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Windows/Linux/Mac

### Setup Steps

1. **Clone or navigate to project directory**
```bash
cd C:\CEH\projects\NetworkScanner
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create superuser (optional, for admin access)**
```bash
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Access the application**
- Open browser and go to: `http://localhost:8000/`
- Admin panel: `http://localhost:8000/admin/`

## Usage

### Quick Scan
1. Enter an IP address (e.g., `192.168.1.1`) or domain (e.g., `example.com`)
2. Click "🔍 Scan" button
3. Wait for results (scan timeout: 30 seconds)
4. Review:
   - Target information
   - Open ports
   - Risk assessment
   - Security recommendations

### Understanding Results

#### Risk Levels
- **🔴 CRITICAL**: Immediate action required (e.g., Telnet, RDP, MySQL open)
- **🟠 HIGH**: Address promptly (e.g., FTP, POP3, SMB)
- **🟡 MEDIUM**: Monitor and secure (e.g., DNS, HTTP)
- **🟢 LOW**: Standard practice (e.g., SSH, HTTPS)

#### Scanned Ports
- **21**: FTP (File Transfer Protocol) - Unencrypted
- **22**: SSH (Secure Shell) - Secure remote access
- **23**: Telnet - Dangerous! Unencrypted remote access
- **25**: SMTP (Email) - Relay abuse risk
- **53**: DNS - Information disclosure risk
- **80**: HTTP - Unencrypted web traffic
- **110/143**: POP3/IMAP - Unencrypted email
- **443**: HTTPS - Encrypted web traffic (safe)
- **445**: SMB - Windows file sharing (vulnerable)
- **3306**: MySQL - Exposed database (critical)
- **3389**: RDP - Remote Desktop (critical)
- **5432**: PostgreSQL - Exposed database (critical)
- **5900**: VNC - Unencrypted remote access
- **8080/8443**: Alternative HTTP/HTTPS ports

## Project Structure

```
NetworkScanner/
├── scanner/                    # Main Django app
│   ├── models.py              # Database models
│   ├── views.py               # View logic
│   ├── urls.py                # URL routing
│   ├── admin.py               # Admin configuration
│   ├── scanner_utils.py       # Core scanning logic
│   └── templates/
│       └── scanner/
│           └── index.html     # Main dashboard template
├── scanner_config/            # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── db.sqlite3                 # SQLite database
└── README.md                  # This file
```

## Technical Details

### Scanning Method
- **TCP Connection Scan**: Uses Python's socket library
- **Timeout**: 2 seconds per port
- **Ports Scanned**: 15 common ports
- **DNS Resolution**: Using dnspython library

### Database Models
- **ScanResult**: Stores scan results with risk assessment
- **ScanHistory**: Logs all scan activities

### Security Features
- CSRF protection on all forms
- Input validation for IP/domain
- SQLi prevention (Django ORM)
- XSS protection
- Secure headers configuration

## Customization

### Add More Ports
Edit `scanner/scanner_utils.py` and modify the `COMMON_PORTS` dictionary:

```python
COMMON_PORTS = {
    21: {'name': 'FTP', 'risk': 'HIGH', 'reason': 'Unencrypted file transfer'},
    # Add more ports here...
}
```

### Change Risk Recommendations
Modify the `RECOMMENDATIONS` dictionary in `scanner_utils.py`

### Update UI
Edit `scanner/templates/scanner/index.html` to customize the dashboard

## Troubleshooting

### "Permission denied" scanning ports
- Windows: Run as Administrator
- Linux/Mac: Some ports require elevated privileges

### "Database locked" error
- Delete `db.sqlite3` and run migrations again
- Ensure no other processes are accessing the database

### DNS resolution fails
- Check internet connection
- Verify domain name is spelled correctly
- Use IP address instead of domain

### Port scan timeout
- Network latency issues
- Firewall blocking connections
- Try different target

## Performance Notes

- First scan may take 20-30 seconds (setting up scanner)
- Subsequent scans: 5-15 seconds depending on network
- Each port check has 2-second timeout
- Total timeout per target: ~30 seconds

## Future Enhancements

Potential features for advanced versions:
- UDP scanning
- Service version detection
- HTTP/HTTPS header analysis
- SSL/TLS certificate inspection
- Vulnerability database lookup
- Rate limiting for scan frequency
- Multi-threaded scanning for speed
- Export results (PDF/CSV)
- API endpoints
- Docker containerization
- Email alerts

## Dependencies

- **Django 4.2.0**: Web framework
- **python-nmap 0.7.1**: Nmap integration (optional)
- **dnspython 2.3.0**: DNS resolution
- **requests 2.31.0**: HTTP library

## License

Educational use only. See LICENSE file for details.

## Contributing

This is an educational project. Improvements and suggestions welcome!

## Support

For issues or questions:
1. Check this README
2. Review Django documentation: https://docs.djangoproject.com/
3. Check DNS resolution: `nslookup example.com`
4. Verify network connectivity: `ping example.com`

## Disclaimer

This tool is provided AS-IS for educational purposes. Users are solely responsible for complying with all applicable laws and regulations. Unauthorized network scanning is illegal in many jurisdictions. Always obtain written permission before scanning any network or system you do not own.

---

**Happy learning! 🔐**
