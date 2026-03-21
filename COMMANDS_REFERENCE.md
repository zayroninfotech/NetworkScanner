# Command Reference Guide

Quick reference for all commands used with the Network Scanner.

## 📋 Django Management Commands

### Project Setup & Configuration

```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Create a superuser (admin account)
python manage.py createsuperuser

# Check project configuration
python manage.py check
```

### Running the Server

```bash
# Start development server (default: port 8000)
python manage.py runserver

# Start on specific port
python manage.py runserver 8001

# Start on specific host and port
python manage.py runserver 0.0.0.0:8000

# Run with verbose output
python manage.py runserver --verbosity=2
```

### Database Commands

```bash
# Show database migrations status
python manage.py showmigrations

# Show all database migrations for an app
python manage.py showmigrations scanner

# Migrate to specific migration
python manage.py migrate scanner 0001

# Create empty migration
python manage.py makemigrations --empty scanner --name my_migration

# Squash migrations
python manage.py squashmigrations scanner 0001 0003
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test scanner

# Run specific test class
python manage.py test scanner.tests.NetworkScannerTests

# Run specific test method
python manage.py test scanner.tests.NetworkScannerTests.test_valid_ip

# Run with verbose output
python manage.py test --verbosity=2

# Keep test database (for debugging)
python manage.py test --keepdb
```

### Administrative Commands

```bash
# Run Python shell with Django context
python manage.py shell

# Create backup of database
python manage.py dumpdata > backup.json

# Restore from backup
python manage.py loaddata backup.json

# Flush database (delete all data)
python manage.py flush

# Create static files directory
python manage.py collectstatic

# Clear sessions
python manage.py clearsessions
```

## 🔍 Using Django Shell

Access interactive Django shell:
```bash
python manage.py shell
```

### Common Shell Commands

```python
# Import models
from scanner.models import ScanResult, ScanHistory

# Create a scan result
scan = ScanResult.objects.create(
    target='example.com',
    target_ip='93.184.216.34',
    is_private=False,
    overall_risk='LOW'
)

# Query all scans
all_scans = ScanResult.objects.all()

# Get specific scan
scan = ScanResult.objects.get(id=1)

# Filter scans by risk
critical_scans = ScanResult.objects.filter(overall_risk='CRITICAL')

# Delete a scan
scan.delete()

# Update a scan
scan.overall_risk = 'MEDIUM'
scan.save()

# Count scans
total = ScanResult.objects.count()

# Order by date
recent = ScanResult.objects.order_by('-created_at')[:10]

# Get statistics
from django.db.models import Count
stats = ScanResult.objects.values('overall_risk').annotate(count=Count('id'))
```

## 🌐 API Endpoints

### Manual Testing with curl

```bash
# Get dashboard
curl http://localhost:8000/

# Get statistics
curl http://localhost:8000/api/stats/

# Get scan history
curl http://localhost:8000/api/history/

# Perform scan (requires CSRF token)
curl -X POST http://localhost:8000/api/scan/ \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'

# Get scan details
curl http://localhost:8000/detail/1/
```

### Using Python Requests

```python
import requests
import json

# Get statistics
response = requests.get('http://localhost:8000/api/stats/')
stats = response.json()
print(stats)

# Perform scan
scan_data = {'target': '127.0.0.1'}
response = requests.post(
    'http://localhost:8000/api/scan/',
    json=scan_data
)
result = response.json()
print(json.dumps(result, indent=2))
```

## 🐚 Useful Shell Commands

### Windows (Command Prompt)

```batch
# Activate virtual environment
venv\Scripts\activate

# Deactivate virtual environment
deactivate

# Install requirements
pip install -r requirements.txt

# Check Python version
python --version

# List installed packages
pip list

# Create new virtual environment
python -m venv venv
```

### Linux/Mac (Bash)

```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Install requirements
pip install -r requirements.txt

# Check Python version
python3 --version

# List installed packages
pip list

# Create new virtual environment
python3 -m venv venv

# Run with sudo (if needed)
sudo python manage.py runserver
```

## 🔧 Development Utilities

### Using Python Interpreter

```python
# Test IP validation
from scanner.scanner_utils import NetworkScanner

scanner = NetworkScanner()

# Test valid IP
print(scanner.is_valid_ip('192.168.1.1'))  # True
print(scanner.is_valid_ip('999.999.999.999'))  # False

# Test domain validation
print(scanner.is_valid_domain('example.com'))  # True
print(scanner.is_valid_domain('not a domain'))  # False

# Test DNS resolution
result = scanner.resolve_dns('example.com')
print(result)

# Perform full scan
result = scanner.full_scan('127.0.0.1')
print(result)
```

### Logging Configuration

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('scanner')
logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
```

## 📊 Database Inspection

### Using SQLite CLI

```bash
# Enter SQLite shell
sqlite3 db.sqlite3

# List tables
.tables

# Show schema
.schema scanner_scanresult

# Query data
SELECT * FROM scanner_scanresult;

# Count records
SELECT COUNT(*) FROM scanner_scanresult;

# Export to CSV
.mode csv
.output results.csv
SELECT * FROM scanner_scanresult;

# Exit SQLite
.exit
```

## 🔐 Security Commands

### Generate Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Check Security Settings

```bash
# Verify HTTPS readiness
python manage.py check --deploy

# List insecure settings
python manage.py check --list
```

## 🚀 Deployment Commands

### Prepare for Production

```bash
# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Backup database
python manage.py dumpdata > production_backup.json

# Compress static files
python manage.py compress
```

### Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn scanner_config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Run with specific configuration
gunicorn scanner_config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60 \
  --log-level info
```

## 📈 Performance Monitoring

### Check Query Performance

```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

# Count queries
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    from django.db import connection

    # Your code here
    ScanResult.objects.all()

    # Check number of queries
    print(f"Queries executed: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])
```

## 🐛 Debugging Commands

### Enable Debug Mode

```python
# In scanner_config/settings.py
DEBUG = True  # Development only!

# Log all SQL queries
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Browser Developer Tools

```javascript
// In browser console (F12)

// Check API response
fetch('/api/stats/')
  .then(r => r.json())
  .then(d => console.log(d))

// Test scan
fetch('/api/scan/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({target: '127.0.0.1'})
})
.then(r => r.json())
.then(d => console.log(d))
```

## 📚 Additional Resources

### Help Commands

```bash
# Get help for specific command
python manage.py help runserver

# List all available commands
python manage.py help

# Show SQL for a command (development)
python manage.py <command> --sqlprint
```

### Version Information

```bash
# Django version
python -m django --version

# Python version
python --version

# Installed packages
pip list --format=json
```

## 🎯 Quick Command Aliases

Create shortcuts for frequent commands:

### Windows (In Command Prompt)

```batch
# Add to batch script or set as alias
DOSKEY runserver=python manage.py runserver
DOSKEY migrate=python manage.py migrate
DOSKEY test=python manage.py test
DOSKEY shell=python manage.py shell
```

### Linux/Mac (In ~/.bashrc or ~/.zshrc)

```bash
alias runserver='python manage.py runserver'
alias migrate='python manage.py migrate'
alias test='python manage.py test'
alias shell='python manage.py shell'
alias check='python manage.py check'
```

---

**Last Updated**: March 2, 2026
**Django Version**: 4.2.0
**Python Version**: 3.8+
