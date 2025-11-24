# Quick Start Guide - 5 Minutes to Deploy

Get your viral clip extractor running on Oracle Cloud in just 5 minutes!

## Prerequisites

✅ Oracle Cloud account (free tier)
✅ Ubuntu 22.04 VM created with:
   - 4 ARM CPUs
   - 24 GB RAM
   - 200 GB storage
   - Port 5000 open in security list

## Step 1: Upload Files (1 minute)

From your local computer:

```bash
scp -i your-key.pem -r opus-clip-cloud ubuntu@YOUR_VM_IP:~/
```

## Step 2: Connect to VM (30 seconds)

```bash
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

## Step 3: Run Setup (3 minutes)

```bash
cd ~/opus-clip-cloud
chmod +x setup_cloud.sh run_cloud.sh
./setup_cloud.sh
```

Wait for installation to complete...

## Step 4: Start Application (30 seconds)

**For testing:**
```bash
./run_cloud.sh
```

**For production:**
```bash
sudo cp opus-clip-cloud.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable opus-clip-cloud
sudo systemctl start opus-clip-cloud
```

## Step 5: Access & Test (30 seconds)

Open browser:
```
http://YOUR_VM_IP:5000
```

Test with any YouTube URL!

## Done! 🎉

Your viral clip extractor is now running 24/7 on Oracle Cloud - completely FREE!

---

## Common Commands

### Check Status
```bash
sudo systemctl status opus-clip-cloud
```

### View Logs
```bash
sudo journalctl -u opus-clip-cloud -f
```

### Restart
```bash
sudo systemctl restart opus-clip-cloud
```

### Stop
```bash
sudo systemctl stop opus-clip-cloud
```

---

## Troubleshooting

### Can't access from browser?

1. **Check Oracle Cloud security list:**
   - Instance → Subnet → Security List
   - Add ingress rule for port 5000

2. **Check VM firewall:**
   ```bash
   sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
   sudo netfilter-persistent save
   ```

3. **Test locally:**
   ```bash
   curl http://localhost:5000/health
   ```

### Service not starting?

```bash
# Check logs
sudo journalctl -u opus-clip-cloud -n 50

# Verify virtual environment
cd ~/opus-clip-cloud
source venv/bin/activate
python3 -c "import flask; print('OK')"
```

### Pytube error?

```bash
cd ~/opus-clip-cloud
source venv/bin/activate
pip install --upgrade pytube
sudo systemctl restart opus-clip-cloud
```

---

## Next Steps

1. ✅ Process your first video
2. ✅ Configure settings in `config_cloud.py`
3. ✅ Set up monitoring
4. ✅ Add a domain name (optional)
5. ✅ Enable HTTPS (optional)

---

For detailed instructions, see **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**
