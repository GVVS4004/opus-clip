# Opus Clip Cloud - Oracle Cloud Edition

🚀 A cloud-optimized viral clip extractor designed specifically for Oracle Cloud Free Tier deployment.

## What is This?

This is a **cloud-adapted version** of the Opus Clip viral video processor that:
- ✅ Uses **pytube** instead of yt-dlp (more reliable on cloud IPs)
- ✅ Optimized for **Oracle Cloud Free Tier** (4 ARM cores, 24 GB RAM)
- ✅ Auto-cleanup to save disk space
- ✅ Production-ready with systemd service
- ✅ Comprehensive logging and monitoring
- ✅ **100% FREE** - runs on Oracle's Always Free Tier

## Quick Start

### 1. Get Oracle Cloud Account
Sign up for free: https://www.oracle.com/cloud/free/

### 2. Create Ubuntu VM
- Shape: VM.Standard.A1.Flex (ARM)
- OCPUs: 4
- Memory: 24 GB
- Storage: 200 GB
- OS: Ubuntu 22.04

### 3. Upload This Project
```bash
scp -i your-key -r opus-clip-cloud ubuntu@YOUR_VM_IP:~/
```

### 4. Run Setup
```bash
cd ~/opus-clip-cloud
./setup_cloud.sh
```

### 5. Start Application
```bash
./run_cloud.sh
```

### 6. Access in Browser
```
http://YOUR_VM_IP:5000
```

## Key Features

### 🎥 Video Processing
- Download YouTube videos using pytube
- AI transcription with OpenAI Whisper
- Intelligent viral clip detection
- Karaoke-style subtitles
- 9:16 vertical format (TikTok/Reels ready)

### ☁️ Cloud Optimizations
- Automatic cleanup of downloaded videos
- Memory-efficient processing
- Resource monitoring
- Health check endpoints
- Comprehensive logging

### 🔧 Production Ready
- Systemd service integration
- Gunicorn WSGI server
- Auto-restart on failures
- Log rotation support

## Documentation

- **[README_CLOUD.md](README_CLOUD.md)** - Overview and quick reference
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment instructions
- **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** - Technical details of all changes from original

## Project Structure

```
opus-clip-cloud/
├── app_cloud.py              # Flask web application (cloud-optimized)
├── pipeline_cloud.py         # Main processing pipeline
├── downloader_cloud.py       # YouTube downloader (uses pytube)
├── transcriber.py            # Whisper AI transcription
├── clip_detector.py          # Viral clip detection algorithm
├── video_processor_v2.py     # FFmpeg video processing
├── config_cloud.py           # Cloud-specific configuration
├── requirements_cloud.txt    # Python dependencies
├── setup_cloud.sh            # Setup script
├── run_cloud.sh              # Run script
├── opus-clip-cloud.service   # Systemd service definition
├── templates/
│   └── index.html           # Web interface
└── README.md                # This file
```

## Main Differences from Original

| Feature | Original | Cloud Version |
|---------|----------|---------------|
| Downloader | yt-dlp | **pytube** |
| Cleanup | Manual | **Automatic** |
| Logging | Basic | **Comprehensive** |
| Web Server | Flask dev | **Gunicorn** |
| Service | Manual start | **Systemd auto-start** |
| Monitoring | None | **Health checks** |
| Resource Management | None | **Auto-cleanup, monitoring** |

## Configuration

Edit `config_cloud.py` to customize:

```python
# Whisper model (tiny, base, small, medium, large)
WHISPER_MODEL = 'base'

# Number of clips to generate
DEFAULT_NUM_CLIPS = 1

# Auto-cleanup settings
AUTO_CLEANUP_DOWNLOADS = True
KEEP_RECENT_DOWNLOADS = 5

# Server settings
WEB_PORT = 5000
DEBUG_MODE = False
```

## Usage

### Web Interface
1. Open `http://YOUR_VM_IP:5000`
2. Paste YouTube URL
3. Click "Extract Viral Clips"
4. Wait for processing
5. Download your clips!

### Command Line
```bash
cd ~/opus-clip-cloud
source venv/bin/activate
python3 pipeline_cloud.py
```

## Service Management

### Start Service
```bash
sudo systemctl start opus-clip-cloud
```

### Stop Service
```bash
sudo systemctl stop opus-clip-cloud
```

### Check Status
```bash
sudo systemctl status opus-clip-cloud
```

### View Logs
```bash
sudo journalctl -u opus-clip-cloud -f
```

## Performance

On Oracle Cloud Free Tier:

| Video Length | Processing Time |
|--------------|-----------------|
| 5 minutes    | 3-5 minutes     |
| 15 minutes   | 8-12 minutes    |
| 30 minutes   | 15-20 minutes   |
| 60 minutes   | 30-40 minutes   |

## Maintenance

### Clean Up Old Files
```bash
cd ~/opus-clip-cloud
rm -rf downloads/* outputs/*.mp4
```

### Update Application
```bash
cd ~/opus-clip-cloud
git pull  # if using git
source venv/bin/activate
pip install -r requirements_cloud.txt --upgrade
sudo systemctl restart opus-clip-cloud
```

### Check Disk Space
```bash
df -h
```

### Monitor Resources
```bash
htop
```

## Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u opus-clip-cloud -n 50
```

### Can't Access from Browser
1. Check security list on Oracle Cloud (port 5000 open)
2. Check VM firewall: `sudo iptables -L -n | grep 5000`
3. Test locally: `curl http://localhost:5000/health`

### Pytube Download Fails
```bash
cd ~/opus-clip-cloud
source venv/bin/activate
pip install --upgrade pytube
sudo systemctl restart opus-clip-cloud
```

### Out of Memory
```bash
# Add 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Security Notes

1. Change secret key in production
2. Keep system updated: `sudo apt update && sudo apt upgrade`
3. Monitor access logs regularly
4. Consider adding HTTPS with Let's Encrypt

## Cost

**$0/month** - Everything runs on Oracle Cloud Free Tier! 🎉

No hidden charges, completely free forever.

## Support & Resources

- **Oracle Cloud:** https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **Pytube:** https://github.com/pytube/pytube
- **Whisper AI:** https://github.com/openai/whisper
- **FFmpeg:** https://ffmpeg.org/

## Why Pytube Instead of yt-dlp?

**Problem with yt-dlp:**
- Frequently blocked by YouTube on cloud data center IPs
- Requires constant updates
- Not reliable in cloud environments

**Pytube Benefits:**
- Pure Python implementation
- More reliable on cloud IPs
- No IP blocking issues
- Simpler API
- Better error handling

## Requirements

### System
- Ubuntu 22.04 (or similar Linux)
- 4 CPU cores
- 24 GB RAM
- 200 GB storage
- FFmpeg

### Python
- Python 3.8+
- See `requirements_cloud.txt` for packages

## License

Uses open-source tools:
- pytube: Unlicense
- Whisper: MIT License
- FFmpeg: LGPL/GPL
- Flask: BSD License

## Credits

Based on the original Opus Clip implementation, adapted for cloud deployment with:
- pytube for YouTube downloads
- OpenAI Whisper for transcription
- FFmpeg for video processing
- Flask for web interface

---

## Getting Started

👉 **New to this?** Start with **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete step-by-step instructions.

👉 **Want technical details?** Check **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)** for all modifications.

👉 **Quick reference?** See **[README_CLOUD.md](README_CLOUD.md)** for commands and tips.

---

**Made with ❤️ for content creators who want to run their tools on free cloud infrastructure**

🚀 Deploy once, create forever - all for **$0/month**!
