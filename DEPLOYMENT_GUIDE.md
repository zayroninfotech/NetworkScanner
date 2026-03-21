# NetworkScanner - GitHub & Hostinger Deployment Guide

## Part 1: Push Code to GitHub

### Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `NetworkScanner`
3. Description: `Network Security Scanner & Analyzer`
4. Choose Public/Private
5. Click "Create repository"

### Step 2: Initialize Git Locally
```bash
cd C:\CEH\projects\NetworkScanner

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Network Security Scanner application"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/NetworkScanner.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Update Requirements
Ensure your `requirements.txt` has:
```
Django==4.2.0
requests==2.31.0
whois==0.9.7
```

---

## Part 2: Deploy on Hostinger VPS

### Prerequisites:
- SSH access to your Hostinger VPS (IP: 187.127.131.93)
- Root or sudo access
- Port 3000 is open

### Step 1: SSH into Your VPS
```bash
ssh root@187.127.131.93
# Enter your password when prompted
```

### Step 2: Install Required Software
```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install -y python3 python3-pip python3-venv

# Install Git
apt install -y git

# Install other dependencies
apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### Step 3: Clone Repository from GitHub
```bash
# Create application directory
mkdir -p /var/www/networkscanner
cd /var/www/networkscanner

# Clone your repository
git clone https://github.com/YOUR_USERNAME/NetworkScanner.git .
```

### Step 4: Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 5: Configure Django for Production
Edit `scanner_config/settings.py`:

```python
# Change DEBUG to False
DEBUG = False

# Add your VPS IP to ALLOWED_HOSTS
ALLOWED_HOSTS = ['187.127.131.93', 'localhost', '127.0.0.1', 'srv1499287.hstgr.cloud']

# Add static files configuration
STATIC_ROOT = '/var/www/networkscanner/staticfiles/'
STATIC_URL = '/static/'
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7: Install Gunicorn (Production Server)
```bash
pip install gunicorn
```

### Step 8: Test Application
```bash
# Test with Gunicorn on port 3000
gunicorn --bind 0.0.0.0:3000 scanner_config.wsgi:application
```

If successful, you should see:
```
[INFO] Listening at: http://0.0.0.0:3000 (PID: XXXX)
```

Access it at: `http://187.127.131.93:3000`

### Step 9: Create Systemd Service (Auto-start)
```bash
sudo nano /etc/systemd/system/networkscanner.service
```

Paste this content:
```ini
[Unit]
Description=NetworkScanner Django Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/var/www/networkscanner
Environment="PATH=/var/www/networkscanner/venv/bin"
ExecStart=/var/www/networkscanner/venv/bin/gunicorn --bind 0.0.0.0:3000 --workers 3 scanner_config.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Step 10: Enable and Start Service
```bash
# Enable service to start on boot
sudo systemctl enable networkscanner

# Start the service
sudo systemctl start networkscanner

# Check status
sudo systemctl status networkscanner
```

### Step 11: Configure Nginx (Optional - Reverse Proxy)
```bash
apt install -y nginx

sudo nano /etc/nginx/sites-available/networkscanner
```

Paste this:
```nginx
server {
    listen 80;
    server_name 187.127.131.93 srv1499287.hstgr.cloud;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/networkscanner/staticfiles/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/networkscanner /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## Part 3: Useful Commands

### Check if running:
```bash
curl http://187.127.131.93:3000
```

### View logs:
```bash
sudo systemctl logs networkscanner -f
```

### Restart application:
```bash
sudo systemctl restart networkscanner
```

### Stop application:
```bash
sudo systemctl stop networkscanner
```

### Update code from GitHub:
```bash
cd /var/www/networkscanner
git pull origin main
python manage.py migrate
sudo systemctl restart networkscanner
```

---

## Quick Start Commands Summary

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/NetworkScanner.git
cd NetworkScanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run on port 3000
gunicorn --bind 0.0.0.0:3000 scanner_config.wsgi:application
```

---

## Access Your Application

Once deployed:
- **Direct Access**: http://187.127.131.93:3000
- **With Nginx**: http://187.127.131.93 (port 80)

---

## Troubleshooting

### Port 3000 already in use:
```bash
sudo lsof -i :3000
sudo kill -9 PID
```

### Permission denied:
```bash
sudo chown -R root:root /var/www/networkscanner
```

### Module not found:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

For questions or issues, check logs:
```bash
sudo journalctl -u networkscanner -n 50
```
