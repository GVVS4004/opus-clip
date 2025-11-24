# Opus Clip Cloud - Oracle Cloud Edition

A **cloud-optimized** version of the Viral Clip Extractor designed specifically for Oracle Cloud Free Tier deployment. This version uses **pytube** instead of yt-dlp for better compatibility with cloud environments.

## Key Differences from Local Version

### ✅ Cloud Optimizations

1. **Alternative YouTube Downloader**
   - Uses **pytube** instead of yt-dlp
   - More reliable on cloud server IP addresses
   - No IP blocking issues typical with yt-dlp

2. **Memory Management**
   - Automatic cleanup of downloaded videos
   - Smart resource monitoring
   - Keeps only 5 most recent downloads

3. **Better Logging**
   - Comprehensive logging system
   - Easier debugging on remote servers
   - Health check endpoints

4. **Production-Ready**
   - Gunicorn WSGI server
   - Systemd service integration
   - Auto-restart on failures

5. **Resource Limits**
   - Configurable processing limits
   - Disk space monitoring
   - Memory usage tracking

## Oracle Cloud Free Tier Specs

- **4 ARM CPU cores** (Ampere A1)
- **24 GB RAM**
- **200 GB storage**
- **10 TB bandwidth/month**
- **FOREVER FREE** ✨

Perfect for running this application!

## Quick Start

### 1. Prerequisites

Sign up for Oracle Cloud Free Tier:
- https://www.oracle.com/cloud/free/

Create an Ubuntu 22.04 VM with:
- Shape: VM.Standard.A1.Flex
- OCPUs: 4
- Memory: 24 GB
- Boot Volume: 200 GB

### 2. Initial Setup

Connect to your VM:
```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

Clone or upload this project:
```bash
cd ~
# Option 1: Upload via SCP
# Option 2: Clone from git
git clone <your-repo-url> opus-clip-cloud
cd opus-clip-cloud
```

### 3. Run Setup Script

```bash
chmod +x setup_cloud.sh
./setup_cloud.sh
```

This will:
- Install system dependencies (Python, FFmpeg, etc.)
- Create Python virtual environment
- Install all Python packages
- Create necessary directories
- Set up permissions

### 4. Configure Firewall

**On Oracle Cloud Console:**
1. Navigate to your instance
2. Go to Subnet → Security List
3. Add Ingress Rule:
   - Source: 0.0.0.0/0
   - Protocol: TCP
   - Port: 5000

**On the VM:**
```bash
sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

### 5. Test the Application

Development mode (for testing):
```bash
./run_cloud.sh
```

Production mode (with Gunicorn):
```bash
./run_cloud.sh production
```

Access the app:
```
http://YOUR_VM_IP:5000
```

### 6. Production Deployment

Install as a systemd service (runs automatically on boot):

```bash
# Copy service file
sudo cp opus-clip-cloud.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable opus-clip-cloud

# Start service
sudo systemctl start opus-clip-cloud

# Check status
sudo systemctl status opus-clip-cloud
```

## Managing the Service

### Check Status
```bash
sudo systemctl status opus-clip-cloud
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u opus-clip-cloud -f

# Last 100 lines
sudo journalctl -u opus-clip-cloud -n 100
```

### Restart Service
```bash
sudo systemctl restart opus-clip-cloud
```

### Stop Service
```bash
sudo systemctl stop opus-clip-cloud
```

### Disable Auto-Start
```bash
sudo systemctl disable opus-clip-cloud
```

## Configuration

Edit `config_cloud.py` to customize:

```python
# Whisper model size (tiny, base, small, medium, large)
WHISPER_MODEL = 'base'  # Use 'tiny' for faster processing

# Number of clips to generate
DEFAULT_NUM_CLIPS = 1

# Auto-cleanup settings
AUTO_CLEANUP_DOWNLOADS = True
KEEP_RECENT_DOWNLOADS = 5

# Server settings
WEB_PORT = 5000
GUNICORN_WORKERS = 2
```

## Monitoring

### Health Check
```bash
curl http://YOUR_VM_IP:5000/health
```

### Resource Usage
```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
htop
```

### Clean Up Old Files
```bash
cd ~/opus-clip-cloud

# Remove old downloads
rm -rf downloads/*

# Remove old clips (keep results JSON)
rm -f outputs/clip_*.mp4
```

## Performance on Oracle Cloud

### Processing Times (Whisper Base Model)

| Video Length | Processing Time |
|--------------|-----------------|
| 5 minutes    | ~3-5 minutes    |
| 15 minutes   | ~8-12 minutes   |
| 30 minutes   | ~15-20 minutes  |
| 60 minutes   | ~30-40 minutes  |

### Recommendations

1. **For faster processing:** Use `WHISPER_MODEL = 'tiny'`
2. **For better accuracy:** Use `WHISPER_MODEL = 'base'` (default)
3. **For best quality:** Use `WHISPER_MODEL = 'small'` (slower)

## Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u opus-clip-cloud -n 50

# Check if port is already in use
sudo netstat -tlnp | grep 5000

# Verify virtual environment
cd ~/opus-clip-cloud
source venv/bin/activate
python3 -c "import flask; print('Flask OK')"
```

### Cannot Access from Browser
```bash
# Verify service is running
sudo systemctl status opus-clip-cloud

# Check firewall rules
sudo iptables -L -n | grep 5000

# Test locally
curl http://localhost:5000/health
```

### Out of Memory
```bash
# Check memory usage
free -h

# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Pytube Errors

If pytube fails to download videos:

```bash
# Update pytube to latest version
source venv/bin/activate
pip install --upgrade pytube

# If issues persist, pytube may need a patch for recent YouTube changes
# Check: https://github.com/pytube/pytube/issues
```

## Updating the Application

```bash
cd ~/opus-clip-cloud

# Pull latest changes (if using git)
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements_cloud.txt --upgrade

# Restart service
sudo systemctl restart opus-clip-cloud
```

## Security Notes

1. **Change the secret key** in production:
   ```bash
   export SECRET_KEY='your-random-secret-key-here'
   ```

2. **Consider adding HTTPS** with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   # Follow certbot instructions
   ```

3. **Enable rate limiting** to prevent abuse:
   - Edit `config_cloud.py`
   - Set `ENABLE_RATE_LIMITING = True`

## Optional: Domain Name Setup

1. Get a domain name (or use a free one from Freenom)
2. Point A record to your VM's public IP
3. Install Nginx as reverse proxy:

```bash
sudo apt install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/opus-clip
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 1800;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/opus-clip /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Cost

**$0/month** - Runs completely on Oracle Cloud Free Tier! 🎉

## Support

For issues specific to:
- **Pytube**: https://github.com/pytube/pytube/issues
- **Oracle Cloud**: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **This Project**: Check logs and troubleshooting section above

## License

Same as parent project - uses open-source tools:
- pytube: Unlicense
- Whisper: MIT License
- FFmpeg: LGPL/GPL
- Flask: BSD License

---

**Happy cloud hosting! 🚀☁️**
