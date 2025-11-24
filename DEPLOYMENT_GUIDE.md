# Complete Deployment Guide - Oracle Cloud

Step-by-step guide to deploy Opus Clip Cloud on Oracle Cloud Free Tier.

## Part 1: Oracle Cloud Account Setup

### Step 1.1: Create Oracle Cloud Account

1. Go to: https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in your information:
   - Email address
   - Country
   - Name and company info
4. Enter credit card (for verification only - **NO CHARGES**)
5. Complete phone verification
6. Wait for account approval (usually instant)

### Step 1.2: Choose Your Region

Select a region with Ampere (ARM) availability:
- **US East (Ashburn)** - Recommended
- **US West (Phoenix)**
- **Germany Central (Frankfurt)**
- **UK South (London)**

## Part 2: Create VM Instance

### Step 2.1: Navigate to Instance Creation

1. Login to Oracle Cloud Console
2. Click hamburger menu (☰) → **Compute** → **Instances**
3. Click **"Create Instance"**

### Step 2.2: Configure Instance

**Name:**
```
opus-clip-server
```

**Placement:**
- Keep default Availability Domain

**Image and Shape:**

1. Click **"Change Image"**
   - Select: **Canonical Ubuntu** 22.04
   - Click **"Select Image"**

2. Click **"Change Shape"**
   - Shape Series: **Ampere**
   - Shape: **VM.Standard.A1.Flex**
   - OCPUs: **4** (use the slider)
   - Memory (GB): **24** (use the slider)
   - Click **"Select Shape"**

**Networking:**
- Keep defaults (creates new VCN automatically)
- Make sure **"Assign a public IPv4 address"** is CHECKED ✅

**Add SSH Keys:**

Choose one option:

**Option A - Generate new key pair (easiest):**
- Select **"Generate a key pair for me"**
- Click **"Save Private Key"** - IMPORTANT: Save this file!
- Click **"Save Public Key"** (optional)

**Option B - Use your own SSH key:**
- Select **"Upload public key files"**
- Upload your `id_rsa.pub` or similar

**Boot Volume:**
- Size: **200 GB** (maximum for free tier)

### Step 2.3: Create the Instance

1. Click **"Create"** button at the bottom
2. Wait 2-3 minutes for provisioning
3. Status will change to: **RUNNING** (green)
4. **Copy the Public IP address** - you'll need this!

## Part 3: Configure Network Security

### Step 3.1: Open Port 5000

1. On your instance page, find **"Subnet"** link
2. Click on the subnet name (e.g., "subnet-20250123...")
3. Click **"Default Security List for..."**
4. Click **"Add Ingress Rules"**

**Add this rule:**
```
Stateless: Unchecked
Source Type: CIDR
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Source Port Range: (leave empty)
Destination Port Range: 5000
Description: Opus Clip Web Interface
```

5. Click **"Add Ingress Rules"**

## Part 4: Connect to Your VM

### Step 4.1: Connect via SSH

**From Windows (PowerShell):**
```powershell
ssh -i C:\path\to\your-private-key ubuntu@YOUR_PUBLIC_IP
```

**From Mac/Linux:**
```bash
chmod 400 ~/path/to/your-private-key
ssh -i ~/path/to/your-private-key ubuntu@YOUR_PUBLIC_IP
```

**First time connection:**
- Type `yes` when asked about host authenticity

You should see:
```
Welcome to Ubuntu 22.04...
```

## Part 5: Upload Project Files

### Option A: Upload via SCP (From Your Local Computer)

**From Windows:**
```powershell
scp -i C:\path\to\key -r C:\Projects\opus-clip-cloud ubuntu@YOUR_IP:~/
```

**From Mac/Linux:**
```bash
scp -i ~/path/to/key -r /path/to/opus-clip-cloud ubuntu@YOUR_IP:~/
```

### Option B: Clone from Git

**On the VM:**
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/opus-clip-cloud.git
cd opus-clip-cloud
```

### Option C: Upload via SFTP

Use FileZilla or WinSCP to upload files using your SSH key.

## Part 6: Install and Setup

### Step 6.1: Run Setup Script

```bash
cd ~/opus-clip-cloud
chmod +x setup_cloud.sh run_cloud.sh
./setup_cloud.sh
```

This will take about 5-10 minutes and install:
- Python 3 and pip
- FFmpeg for video processing
- Python virtual environment
- All required Python packages
- Whisper AI model (downloads on first use)

### Step 6.2: Configure Firewall on VM

```bash
sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
sudo apt install -y iptables-persistent
# Press YES to save current rules when asked
sudo netfilter-persistent save
```

## Part 7: Test the Application

### Step 7.1: Start in Development Mode

```bash
cd ~/opus-clip-cloud
./run_cloud.sh
```

You should see:
```
Starting Opus Clip Cloud...
VIRAL CLIP EXTRACTOR - Web Interface (Cloud Edition)
Listening on: http://0.0.0.0:5000
```

### Step 7.2: Access from Your Browser

Open your browser and go to:
```
http://YOUR_PUBLIC_IP:5000
```

You should see the Opus Clip interface!

### Step 7.3: Test Video Processing

1. Paste a YouTube URL
2. Click "Extract Viral Clips"
3. Wait for processing to complete
4. Download your clip!

**To stop the test:**
Press `Ctrl+C` in the terminal

## Part 8: Production Deployment

### Step 8.1: Install as System Service

```bash
cd ~/opus-clip-cloud

# Copy service file
sudo cp opus-clip-cloud.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable opus-clip-cloud

# Start the service
sudo systemctl start opus-clip-cloud
```

### Step 8.2: Verify Service is Running

```bash
sudo systemctl status opus-clip-cloud
```

Should show: **active (running)** in green

### Step 8.3: View Logs

```bash
# Real-time logs
sudo journalctl -u opus-clip-cloud -f

# Last 50 lines
sudo journalctl -u opus-clip-cloud -n 50
```

## Part 9: Usage

### Access Your Application

```
http://YOUR_PUBLIC_IP:5000
```

### Process a Video

1. Copy any YouTube video URL
2. Paste it in the input box
3. Configure options (optional):
   - Number of clips: 1-5 recommended
   - Clip duration: 15-60 seconds
4. Click "Extract Viral Clips"
5. Wait for processing (usually 5-15 minutes)
6. Download your viral clips!

### Monitor Processing

The web interface shows:
- Download progress
- Transcription status
- Clip detection progress
- Final clip generation

## Part 10: Maintenance

### Check Service Status
```bash
sudo systemctl status opus-clip-cloud
```

### Restart Service
```bash
sudo systemctl restart opus-clip-cloud
```

### View Recent Logs
```bash
sudo journalctl -u opus-clip-cloud -n 100
```

### Clean Up Old Files
```bash
cd ~/opus-clip-cloud

# Remove old downloads
rm -rf downloads/*

# Remove old clips (keep result JSON files)
rm -f outputs/clip_*.mp4
```

### Check Disk Space
```bash
df -h
```

### Check Memory Usage
```bash
free -h
```

### Monitor Resources
```bash
# Install htop
sudo apt install htop

# Run htop
htop
```

Press `q` to quit htop

## Troubleshooting

### Can't Connect to VM
- Check security list has port 5000 open
- Verify VM firewall: `sudo iptables -L -n | grep 5000`
- Check public IP is correct
- Test locally on VM: `curl http://localhost:5000/health`

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u opus-clip-cloud -n 100 --no-pager

# Check Python virtual environment
cd ~/opus-clip-cloud
source venv/bin/activate
python3 -c "import flask; print('OK')"
```

### Pytube Download Fails
```bash
# Update pytube
cd ~/opus-clip-cloud
source venv/bin/activate
pip install --upgrade pytube

# Restart service
sudo systemctl restart opus-clip-cloud
```

### Out of Memory
```bash
# Add 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Out of Disk Space
```bash
# Check usage
df -h

# Clean up
cd ~/opus-clip-cloud
rm -rf downloads/* outputs/*.mp4

# Clean system cache
sudo apt clean
```

## Security Best Practices

### 1. Change Secret Key

```bash
cd ~/opus-clip-cloud
nano app_cloud.py
```

Find line with `SECRET_KEY` and change it to a random string.

### 2. Update System Regularly

```bash
sudo apt update && sudo apt upgrade -y
sudo systemctl restart opus-clip-cloud
```

### 3. Monitor Access Logs

```bash
sudo journalctl -u opus-clip-cloud | grep "Started processing"
```

### 4. Backup Configuration

```bash
cp config_cloud.py config_cloud.py.backup
```

## Cost Summary

**Monthly Cost: $0** 🎉

Everything runs on Oracle Cloud Free Tier:
- Compute: Free (4 ARM CPUs, 24 GB RAM)
- Storage: Free (200 GB)
- Bandwidth: Free (10 TB/month)
- Public IP: Free

No credit card charges, completely free forever!

## What's Next?

### Optional Enhancements

1. **Add Domain Name**
   - Get free domain from Freenom or No-IP
   - Point A record to your VM IP
   - Access via: `http://your-domain.com:5000`

2. **Add HTTPS/SSL**
   - Install Nginx
   - Get free SSL from Let's Encrypt
   - Secure access: `https://your-domain.com`

3. **Email Notifications**
   - Get notified when clips are ready
   - Use SendGrid or similar service

4. **Queue System**
   - Process multiple videos
   - Use Celery + Redis

## Support

- **Oracle Cloud Docs:** https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **Pytube Issues:** https://github.com/pytube/pytube/issues
- **FFmpeg Docs:** https://ffmpeg.org/documentation.html
- **Whisper AI:** https://github.com/openai/whisper

---

**Congratulations! You now have a fully functional viral clip extractor running on Oracle Cloud for FREE! 🎉**

Enjoy creating viral content! 🚀
