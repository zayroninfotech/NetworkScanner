# Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Windows Users
```bash
# 1. Navigate to project
cd C:\CEH\projects\NetworkScanner

# 2. Run setup script
setup.bat

# 3. Start server
python manage.py runserver

# 4. Open browser
# Visit: http://localhost:8000/
```

### Linux/Mac Users
```bash
# 1. Navigate to project
cd ~/CEH/projects/NetworkScanner

# 2. Make setup script executable and run
chmod +x setup.sh
./setup.sh

# 3. Start server
python manage.py runserver

# 4. Open browser
# Visit: http://localhost:8000/
```

## 📝 Your First Scan

1. **Open the dashboard**: http://localhost:8000/
2. **Enter a test target**:
   - Your own IP: `127.0.0.1` or `localhost`
   - Your router: `192.168.1.1` (typical)
   - A domain: `example.com`
3. **Click "🔍 Scan"**
4. **Wait** for results (20-30 seconds)
5. **Review** the risk assessment

## 🔐 Understanding the Dashboard

### Input Section
- **Target Field**: Enter IP address or domain name
- **Scan Button**: Starts the network scan
- **Warning**: Only scan systems you own!

### Results Section
Shows after scanning completes:
- **Target Info**: IP address and type (public/private)
- **Risk Badge**: Overall security risk level
- **Open Ports**: List of vulnerable services
- **Recommendations**: Security best practices

### Statistics Dashboard
- **Total Scans**: How many scans you've performed
- **Risk Breakdown**: Critical, High, Medium, Low counts

### Scan History
- **Recent Scans Table**: All previous scans
- **Sortable**: By risk level or target

## 🎓 Learning Path

### Beginner Tasks
1. ✅ Scan your localhost (127.0.0.1)
2. ✅ Scan your router (192.168.1.1 or 192.168.0.1)
3. ✅ Identify which services are "CRITICAL"
4. ✅ Read the recommendations for each risk level

### Intermediate Tasks
1. 📚 Learn what each port does
2. 🔐 Understand why certain ports are risky
3. 🛡️ Research how to secure each service
4. 📊 Compare risks across multiple scans

### Advanced Tasks
1. 🔍 Add more ports to scan
2. 📈 Create scan trending reports
3. 🔒 Integrate with security tools
4. 📱 Deploy to cloud server

## 🆘 Common Issues

### "Address already in use" error
```bash
# The port 8000 is already in use. Use a different port:
python manage.py runserver 8001
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Permission denied" scanning ports
- **Windows**: Run Command Prompt as Administrator
- **Linux**: Use `sudo` if needed (not recommended for prod)

### Slow scans
- Network latency with target
- Firewall blocking connections
- Multiple scans running simultaneously

## 📊 Example Results

### Safe System (Low Risk)
```
Target: example.com (93.184.216.34)
Type: Public IP
Open Ports: 2 (80 - HTTP, 443 - HTTPS)
Risk Level: 🟢 LOW
Recommendation: Standard monitoring recommended
```

### Insecure System (Critical Risk)
```
Target: 192.168.1.1 (Router)
Type: Private IP
Open Ports: 4 (23 - Telnet, 445 - SMB, 3389 - RDP)
Risk Level: 🔴 CRITICAL
Recommendation: Immediate action required! Disable Telnet/SMB/RDP
```

## 🔑 Key Concepts

### Port Scanning
- Trying to connect to common ports on a target
- Determines if service is running and listening
- Helps identify potential vulnerabilities

### Risk Assessment
- Each open port gets a risk level based on service
- Services like Telnet are inherently insecure
- Multiple risky ports increase overall risk

### Security Recommendations
- Contextual advice based on open services
- Suggests firewall rules
- Recommends encryption/authentication
- Advises on monitoring and updates

## 📚 Resources

### Learn More
- [OWASP Port Numbers](https://owasp.org/www-community/attacks/Port_scanning)
- [Common Port Reference](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers)
- [Security Best Practices](https://cheatsheetseries.owasp.org/)

### CEH Study Materials
- Network reconnaissance techniques
- Port scanning methodology
- Service identification
- Risk assessment frameworks

## ⚠️ Remember

> **Only scan systems you own or have explicit permission to test!**

Unauthorized network scanning is:
- 🚫 Illegal in many jurisdictions
- 🚫 Unethical
- 🚫 Violation of computer abuse laws
- 🚫 Grounds for legal action

Always get written permission before scanning any system.

---

**Happy learning and stay ethical!** 🛡️
