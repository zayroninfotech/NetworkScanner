# Network Scanner - Project Structure Overview

## 📁 Directory Layout

```
NetworkScanner/
│
├── 📄 manage.py                          # Django command-line utility
├── 📄 db.sqlite3                         # SQLite database (created after migration)
├── 📄 requirements.txt                   # Python dependencies
│
├── 📚 Documentation Files
│   ├── README.md                         # Full documentation and setup guide
│   ├── QUICKSTART.md                     # Quick start guide for first-time users
│   └── PROJECT_STRUCTURE.md              # This file
│
├── 🔧 Setup Scripts
│   ├── setup.bat                         # Setup script for Windows
│   └── setup.sh                          # Setup script for Linux/Mac
│
├── 📋 Configuration Files
│   ├── .gitignore                        # Git ignore rules
│   └── requirements.txt                  # Python package dependencies
│
├── 🖥️ scanner_config/                    # Django Project Configuration
│   ├── __init__.py
│   ├── settings.py                       # Django settings (DB, apps, middleware)
│   ├── urls.py                           # Project-level URL routing
│   ├── asgi.py                           # ASGI application
│   └── wsgi.py                           # WSGI application
│
└── 🛡️ scanner/                            # Main Scanner Application
    ├── __init__.py
    ├── apps.py                           # App configuration
    ├── admin.py                          # Django admin interface setup
    ├── models.py                         # Database models
    │   ├── ScanResult                    # Stores scan results
    │   └── ScanHistory                   # Tracks scan activity
    ├── views.py                          # View handlers
    │   ├── index()                       # Home page
    │   ├── scan_target()                 # API: Perform scan
    │   ├── scan_history()                # API: Get scan history
    │   ├── scan_detail()                 # API: Get scan details
    │   └── dashboard_stats()             # API: Get statistics
    ├── urls.py                           # App-level URL routing
    ├── scanner_utils.py                  # Core scanning logic
    │   └── NetworkScanner                # Main scanner class
    ├── tests.py                          # Unit tests
    │
    ├── migrations/                       # Database migrations
    │   ├── 0001_initial.py               # Initial models migration
    │   └── __init__.py
    │
    └── templates/                        # HTML templates
        └── scanner/
            └── index.html                # Main dashboard interface
```

## 🔑 Key Files Explained

### Core Files

#### `scanner/scanner_utils.py`
The heart of the application. Contains the `NetworkScanner` class with:
- **Input Validation**: Validates IP addresses and domains
- **DNS Resolution**: Resolves domains to IPs using `dns.resolver`
- **Port Scanning**: Connects to ports using Python sockets
- **Service Detection**: Maps ports to service names
- **Risk Assessment**: Evaluates security risk of open ports
- **Recommendations**: Provides contextual security advice

Key Methods:
```python
is_valid_ip(ip_string)           # Validate IP address
is_valid_domain(domain)           # Validate domain name
is_private_ip(ip_string)          # Check if IP is private
resolve_dns(domain)               # Resolve domain to IP
scan_ports(target)                # Scan common ports
assess_security(scan_result)      # Evaluate security risk
full_scan(target)                 # Complete scan workflow
```

#### `scanner/views.py`
Handles HTTP requests and responses:
- `index()` - Renders main dashboard
- `scan_target()` - POST endpoint for new scans
- `scan_history()` - GET endpoint for scan list
- `scan_detail()` - GET endpoint for individual scan details
- `dashboard_stats()` - GET endpoint for statistics

#### `scanner/models.py`
Defines database schema:

**ScanResult Model**
```
- target: CharField (IP or domain scanned)
- target_ip: CharField (resolved IP address)
- is_private: Boolean (private/public IP)
- dns_success: Boolean (DNS resolution status)
- dns_resolved_ips: JSONField (list of resolved IPs)
- open_ports: JSONField (list of open ports with details)
- overall_risk: CharField (CRITICAL/HIGH/MEDIUM/LOW)
- critical/high/medium_ports_count: IntegerField (risk counts)
- full_result: JSONField (complete scan data)
- created_at/updated_at: DateTimeField (timestamps)
```

**ScanHistory Model**
```
- ip_address: GenericIPAddressField (user IP)
- target_scanned: CharField (scan target)
- scan_result: ForeignKey (reference to ScanResult)
- created_at: DateTimeField (scan timestamp)
```

#### `scanner/templates/scanner/index.html`
Single-page application dashboard with:
- **Input Form**: Target entry field
- **Loading State**: Visual feedback during scanning
- **Results Display**: Open ports, risk assessment, recommendations
- **Statistics**: Dashboard metrics
- **Scan History**: Table of previous scans
- **Responsive Design**: Mobile-friendly layout

### Configuration Files

#### `scanner_config/settings.py`
Django configuration:
- `INSTALLED_APPS`: Registers the scanner app
- `MIDDLEWARE`: Security middleware stack
- `TEMPLATES`: Django template engine setup
- `DATABASES`: SQLite3 configuration
- `LOGGING`: Console logging setup
- `SECURITY`: XSS and CSP headers

#### `scanner_config/urls.py`
URL routing:
```python
path('admin/', admin.site.urls)      # Django admin
path('', include('scanner.urls'))    # Scanner app routes
```

#### `scanner/urls.py`
App-level routes:
```python
path('', views.index)                # GET  /
path('api/scan/', views.scan_target) # POST /api/scan/
path('api/stats/', views.dashboard_stats) # GET /api/stats/
path('history/', views.scan_history) # GET /history/
path('detail/<int:scan_id>/', views.scan_detail) # GET /detail/<id>/
```

## 🗄️ Database Schema

### ScanResult Table
```sql
CREATE TABLE scanner_scanresult (
    id BIGAUTO PRIMARY KEY,
    target VARCHAR(255),
    target_ip VARCHAR(255),
    is_private BOOLEAN,
    dns_success BOOLEAN,
    dns_resolved_ips JSON,
    open_ports JSON,
    overall_risk VARCHAR(20),
    critical_ports_count INTEGER,
    high_ports_count INTEGER,
    medium_ports_count INTEGER,
    full_result JSON,
    created_at DATETIME,
    updated_at DATETIME
)
```

### ScanHistory Table
```sql
CREATE TABLE scanner_scanhistory (
    id BIGAUTO PRIMARY KEY,
    ip_address GENERICIPADDRESS,
    target_scanned VARCHAR(255),
    scan_result_id BIGAUTO FOREIGN KEY,
    created_at DATETIME
)
```

## 📊 Data Flow

### Complete Scan Workflow

```
1. User Input
   └─> IP address or domain

2. Input Validation (scanner_utils.py)
   ├─> Check if valid IP or domain
   └─> Sanitize input

3. DNS Resolution (if domain)
   ├─> dns.resolver.resolve(domain, 'A')
   └─> Extract IP address(es)

4. Port Scanning (socket-based)
   ├─> For each common port:
   │   ├─> Create socket
   │   ├─> Attempt connection (2s timeout)
   │   ├─> If successful: record as OPEN
   │   └─> Close socket
   │
   └─> Return list of open ports

5. Service Detection
   ├─> Match port number to service name
   ├─> Look up service risk level
   └─> Retrieve risk description

6. Risk Assessment
   ├─> Evaluate each open port
   ├─> Count CRITICAL/HIGH/MEDIUM/LOW
   ├─> Assign overall risk level
   └─> Generate recommendations

7. Database Storage (models.py)
   ├─> Create ScanResult record
   ├─> Log ScanHistory entry
   └─> Commit to database

8. API Response (views.py)
   └─> Return JSON with all results

9. Frontend Display (index.html)
   ├─> Parse JSON response
   ├─> Render results in UI
   └─> Display risk recommendations
```

## 🔐 Security Architecture

### Input Security
- CSRF token validation on POST requests
- Input length validation (max 255 chars)
- Regular expression validation for domains
- IP address validation using ipaddress module

### Output Security
- JSON responses properly encoded
- Template auto-escaping enabled
- No user input reflected in HTML
- CORS/CSP headers configured

### Network Security
- Local socket connections only
- 2-second timeout per port (prevents hanging)
- No raw network packets sent
- Standard TCP connection handshake

### Data Security
- SQLite database (file-based)
- No sensitive credentials stored
- Timestamps for audit trail
- Scan history preserved

## 📦 Dependencies

### Core Django
- **Django 4.2.0**: Web framework

### Network & DNS
- **dnspython 2.3.0**: DNS resolution
- **requests 2.31.0**: HTTP client (future use)

### Environment
- **python-dotenv 1.0.0**: Environment variable management

### Built-in Python
- **socket**: TCP port scanning
- **ipaddress**: IP validation
- **re**: Regular expressions for domain validation
- **json**: JSON handling
- **logging**: Application logging

## 🚀 Deployment Readiness

### Development Ready
✅ Database configured
✅ Admin interface set up
✅ URL routing complete
✅ Views and templates created
✅ Models defined
✅ Security headers configured

### Production Checklist (Before Deploying)
- [ ] Set `DEBUG = False` in settings.py
- [ ] Change `SECRET_KEY` to random string
- [ ] Update `ALLOWED_HOSTS` for your domain
- [ ] Configure static files collection
- [ ] Set up PostgreSQL/MySQL database
- [ ] Configure proper logging
- [ ] Enable HTTPS/SSL
- [ ] Add rate limiting middleware
- [ ] Set up monitoring/alerts
- [ ] Create backup strategy

## 📈 Scalability Notes

### Current Limitations
- Single-threaded scanning (one scan at a time)
- 15 common ports only
- Synchronous socket scanning
- SQLite database (suitable for testing only)

### For Production Scaling
- Use Celery for asynchronous scanning
- Implement database connection pooling
- Use PostgreSQL/MySQL
- Add Redis for caching
- Implement request queueing
- Multi-process scanning
- Load balancing with Nginx

## 🧪 Testing Strategy

### Unit Tests (tests.py)
```python
class NetworkScannerTests(TestCase):
    def test_valid_ip()
    def test_invalid_ip()
    def test_dns_resolution()
    def test_port_scanning()
    def test_risk_assessment()
```

### Manual Testing Checklist
- [ ] Scan localhost (127.0.0.1)
- [ ] Scan private IP (192.168.x.x)
- [ ] Scan domain name (example.com)
- [ ] Test invalid input
- [ ] Check admin interface
- [ ] Verify database storage
- [ ] Test history retrieval
- [ ] Check responsive design

## 📚 Learning Resources

### Django
- [Django Documentation](https://docs.djangoproject.com/)
- [Django Models Guide](https://docs.djangoproject.com/en/4.2/topics/db/models/)
- [Django Views Guide](https://docs.djangoproject.com/en/4.2/topics/http/views/)

### Network Programming
- [Python Socket Documentation](https://docs.python.org/3/library/socket.html)
- [DNS Resolution Guide](https://dnspython.readthedocs.io/)
- [Network Security Basics](https://owasp.org/)

### CEH Related
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Port Reference](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers)

---

Generated: 2026-03-02
Version: 1.0
