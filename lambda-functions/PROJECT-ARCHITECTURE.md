# Opus Clip Cloud - Complete Architecture Analysis

## 📊 Project Overview

**Opus Clip Cloud** is a serverless video processing system that automatically extracts viral short-form clips from long-form YouTube videos using AI-powered transcription and content analysis.

### Key Features
- 🎥 YouTube video downloading
- 🎤 AI transcription with OpenAI Whisper (word-level timestamps)
- 🎯 Viral clip detection using keyword analysis and scoring
- ✂️ Automated video processing with FFmpeg
- 📝 Karaoke-style subtitles (word-by-word highlighting)
- 📱 Multiple aspect ratios (9:16, 16:9, 1:1, 4:5)
- ☁️ Fully serverless on AWS Lambda
- 💰 Pay-per-use pricing (~$4-6/month for 100 videos)

---

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                  (Flask Web Application)                        │
│                                                                 │
│  Components:                                                    │
│  • Modern glassmorphic UI                                      │
│  • Aspect ratio selector (9:16, 16:9, 1:1, 4:5)              │
│  • Real-time progress tracking                                │
│  • Download management                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓ POST /process
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (AWS)                          │
│                                                                 │
│  Endpoints:                                                     │
│  • POST   /process              → Start video processing       │
│  • GET    /status/{session_id}  → Check processing status     │
│  • GET    /result/{session_id}  → Get final results           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              LAMBDA: API Gateway Handler                        │
│              (opus-api-gateway)                                 │
│                                                                 │
│  • Validates requests                                          │
│  • Starts Step Functions execution                            │
│  • Returns session_id to client                               │
│  • Queries execution status                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS STEP FUNCTIONS                           │
│              (State Machine Orchestrator)                       │
│                                                                 │
│  Workflow:                                                      │
│  1. Download Video                                             │
│  2. Transcribe Audio                                           │
│  3. Detect Viral Clips                                         │
│  4. Process Clips (Parallel)                                   │
│  5. Finalize Results                                           │
└───┬──────────┬──────────┬──────────┬──────────┬────────────────┘
    │          │          │          │          │
    ↓          ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Step 1 │ │ Step 2 │ │ Step 3 │ │ Step 4 │ │ Step 5 │
│Download│ │Transcri│ │ Detect │ │Process │ │Finalize│
│        │ │  be    │ │ Clips  │ │(x3)    │ │        │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                     AMAZON S3 BUCKET                            │
│                  (File Storage)                                 │
│                                                                 │
│  Structure:                                                     │
│  /{session_id}/                                                │
│    ├── original_video.mp4      (downloaded YouTube video)     │
│    ├── transcript.json         (Whisper transcription)        │
│    ├── result.json             (final metadata)               │
│    └── clips/                                                  │
│        ├── clip_0.mp4          (processed clip 1)             │
│        ├── clip_1.mp4          (processed clip 2)             │
│        └── clip_2.mp4          (processed clip 3)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Processing Flow (Detailed)

### 1. Download Phase (Lambda 1)
**Function:** `opus-download`
**Runtime:** Python 3.11
**Memory:** 3 GB
**Timeout:** 5 minutes

**What it does:**
```python
1. Receives YouTube URL from user
2. Uses pytubefix library to download video
3. Selects best quality stream (720p progressive)
4. Uploads to S3: s3://bucket/{session_id}/original_video.mp4
5. Extracts metadata: title, duration, views, etc.
6. Returns S3 key and video info
```

**Key Files:**
- `1-lambda-download.py`
- `requirements-download.txt`: pytubefix, boto3

**Potential Issues:**
- ❌ Video too long (>1 hour) → Timeout
- ❌ YouTube blocking → Use alternative downloader
- ❌ Insufficient storage → Increase ephemeral storage

---

### 2. Transcription Phase (Lambda 2) 🎯 **ECR Container**
**Function:** `opus-transcribe`
**Runtime:** Container (Python 3.11 + Whisper)
**Memory:** 10 GB
**Timeout:** 10 minutes
**Container Size:** ~2-3 GB

**What it does:**
```python
1. Downloads video from S3 to /tmp
2. Loads Whisper model (base by default)
3. Transcribes audio with word-level timestamps
4. Extracts segments with start/end times
5. Saves transcript to S3: {session_id}/transcript.json
6. Cleans up /tmp to free space
```

**Why ECR Container?**
| Reason | Explanation |
|--------|-------------|
| Model Size | Whisper model is 140 MB (base) to 2.9 GB (large) |
| ZIP Limit | Lambda ZIP max = 250 MB, Transcribe = 1.8 GB |
| Cold Start | Pre-loading model in container = faster warm starts |
| Flexibility | Easy to update model without repackaging |

**Whisper Models:**
```
tiny   (39 MB)   → 3 min/15-min video   → Lower accuracy
base   (139 MB)  → 6 min/15-min video   → Balanced ✅
small  (461 MB)  → 10 min/15-min video  → Better accuracy
medium (1.5 GB)  → 20 min/15-min video  → High accuracy
large  (2.9 GB)  → 40 min/15-min video  → Maximum accuracy
```

**Key Files:**
- `2-lambda-transcribe.py`
- `Dockerfile.transcribe` ← **NEW!**
- `build-and-push-transcribe-ecr.bat/sh` ← **NEW!**
- `requirements-transcribe.txt`: openai-whisper, boto3, numpy

**ECR Deployment:**
```bash
# Build and push to ECR
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
./build-and-push-transcribe-ecr.sh

# Creates:
# - ECR repository: opus-transcribe
# - Docker image: {account}.dkr.ecr.{region}.amazonaws.com/opus-transcribe:latest
# - Lambda pulls from ECR when invoked
```

---

### 3. Clip Detection Phase (Lambda 3)
**Function:** `opus-detect`
**Runtime:** Python 3.11
**Memory:** 2 GB
**Timeout:** 1 minute

**What it does:**
```python
1. Downloads transcript from S3
2. Analyzes segments for viral potential
3. Scores based on:
   - Keyword matching (secret, hack, amazing, etc.)
   - Duration (15-60 seconds, prefer 30s)
   - Speaking pace (2-4 words/second)
   - Sentence completeness
   - Question marks and exclamation marks
4. Ranks clips by score
5. Returns top N clips (default: 3)
```

**Scoring Algorithm:**
```python
score = 0
score += keyword_match * 10        # Viral keywords
score += question_mark * 5          # Engagement hooks
score += exclamation_mark * 3       # Emotional appeal
score += duration_match * 20        # Ideal length
score += completeness * 10          # Full sentences
score += speaking_pace * 10         # Natural flow
score += action_words * 5           # Active verbs
```

**Key Files:**
- `3-lambda-detect-clips.py`
- Viral keywords list (60+ keywords)

---

### 4. Video Processing Phase (Lambda 4)
**Function:** `opus-process-clip`
**Runtime:** Python 3.11 + FFmpeg Layer
**Memory:** 4 GB
**Timeout:** 5 minutes
**Runs:** In parallel (3 instances for 3 clips)

**What it does:**
```python
1. Receives clip info (start, end, aspect_ratio)
2. Downloads original video from S3
3. Extracts clip segment using FFmpeg
4. Converts to target aspect ratio:
   - 9:16 (1080x1920) - TikTok/Reels
   - 16:9 (1920x1080) - YouTube
   - 1:1 (1080x1080)  - Instagram Post
   - 4:5 (1080x1350)  - Instagram Feed
5. Adds karaoke-style subtitles (ASS format)
   - Word-by-word highlighting
   - Green highlight on active word
6. Uploads processed clip to S3
```

**FFmpeg Commands:**
```bash
# Extract and convert to 9:16
ffmpeg -i video.mp4 -ss 12.5 -t 30 \
  -vf "scale=-2:1920,crop=1080:1920:(iw-1080)/2:0" \
  -c:v libx264 -preset fast -crf 23 \
  output.mp4

# Add subtitles
ffmpeg -i video.mp4 -vf "ass=subtitles.ass" \
  -c:v libx264 -c:a copy output_with_subs.mp4
```

**Subtitle Format (ASS):**
```
[Events]
Dialogue: 0,0:00:00.00,0:00:01.50,Default,,0,0,0,,{\fs95\b1\c&H00FF00&}This{\r} is highlighted
```

**Key Files:**
- `4-lambda-process-clip.py`
- FFmpeg Lambda Layer (required)
- `video_processor_v2.py` (logic)

---

### 5. Finalization Phase (Lambda 5)
**Function:** `opus-finalize`
**Runtime:** Python 3.11
**Memory:** 512 MB
**Timeout:** 30 seconds

**What it does:**
```python
1. Collects all processed clip S3 keys
2. Generates pre-signed download URLs (7-day expiry)
3. Creates result JSON with:
   - Video info (title, duration)
   - Clip metadata (start, end, score, text)
   - Download URLs for each clip
4. Saves to S3: {session_id}/result.json
5. Returns complete result object
```

**Result JSON Structure:**
```json
{
  "session_id": "abc-123",
  "youtube_url": "https://...",
  "video_title": "How to...",
  "processed_at": "2025-01-24T12:00:00Z",
  "clips": [
    {
      "number": 1,
      "start": 12.5,
      "end": 42.3,
      "duration": 29.8,
      "score": 87.5,
      "text": "This is the clip transcript...",
      "s3_key": "abc-123/clips/clip_0.mp4",
      "download_url": "https://s3.amazonaws.com/..."
    }
  ]
}
```

**Key Files:**
- `5-lambda-finalize.py`

---

## 💾 Data Flow

### Input
```
User submits:
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "aspect_ratio": "9:16",
  "num_clips": 3,
  "add_subtitles": true
}
```

### Step Functions State Machine
```json
{
  "StartAt": "DownloadVideo",
  "States": {
    "DownloadVideo": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:opus-download",
      "Next": "TranscribeVideo"
    },
    "TranscribeVideo": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:opus-transcribe",
      "Next": "DetectClips"
    },
    "DetectClips": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:opus-detect",
      "Next": "ProcessClips"
    },
    "ProcessClips": {
      "Type": "Map",
      "ItemsPath": "$.clips",
      "Iterator": {
        "StartAt": "ProcessSingleClip",
        "States": {
          "ProcessSingleClip": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:opus-process-clip",
            "End": true
          }
        }
      },
      "Next": "FinalizeResults"
    },
    "FinalizeResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:opus-finalize",
      "End": true
    }
  }
}
```

### Output
```json
{
  "statusCode": 200,
  "clips": [
    {
      "download_url": "https://...",
      "text": "...",
      "score": 87.5
    }
  ]
}
```

---

## 📊 Performance Metrics

### Processing Time (15-minute video)

| Phase | Time | Bottleneck |
|-------|------|------------|
| Download | 1-2 min | Internet speed |
| Transcribe (base) | 6-8 min | Whisper model |
| Detect Clips | 5-10 sec | CPU analysis |
| Process Clips (x3) | 2-3 min | FFmpeg encoding |
| Finalize | 2-5 sec | S3 API calls |
| **Total** | **10-15 min** | Transcription |

### Optimization Strategies

1. **Faster Transcription:**
   - Use `WHISPER_MODEL=tiny` → 3 min instead of 6 min
   - Trade-off: Lower accuracy

2. **Parallel Processing:**
   - Step Functions processes 3 clips simultaneously
   - Saves 4-6 minutes vs sequential

3. **Warm Lambda Containers:**
   - First invocation: 10-20 sec cold start
   - Subsequent: <1 sec warm start
   - Keep functions warm with CloudWatch Events

---

## 💰 Cost Breakdown

### Per 100 Videos (15 min avg, 3 clips each)

| Service | Resource | Usage | Cost |
|---------|----------|-------|------|
| **Lambda Download** | 3 GB × 2 min | 600 GB-min | $0.50 |
| **Lambda Transcribe** | 10 GB × 6 min | 6,000 GB-min | $3.00 |
| **Lambda Detect** | 2 GB × 10 sec | 33 GB-min | $0.03 |
| **Lambda Process** | 4 GB × 2 min × 3 | 2,400 GB-min | $1.20 |
| **Lambda Finalize** | 512 MB × 5 sec | 4 GB-min | $0.00 |
| **Step Functions** | 800 transitions | Free tier | $0.00 |
| **S3 Storage** | 100 GB | $0.023/GB | $2.30 |
| **S3 Requests** | 1,500 | Free tier | $0.00 |
| **ECR Storage** | 2.5 GB | $0.10/GB | $0.25 |
| **Data Transfer** | 50 GB | Free (same region) | $0.00 |
| **Total** | | | **$7.28/month** |

### Free Tier Benefits (First 12 months)
- Lambda: 400K GB-seconds/month → Covers ~60 videos FREE
- S3: 5 GB storage → Covers first 5 videos FREE
- Step Functions: 4K transitions → Covers 500 videos FREE

**Actual Cost with Free Tier:** ~$3-4/month for first year

---

## 🔐 Security Architecture

### IAM Roles & Permissions

```
opus-clip-lambda-role
├── AWSLambdaBasicExecutionRole (CloudWatch Logs)
├── S3 Permissions
│   ├── s3:GetObject (read videos/transcripts)
│   ├── s3:PutObject (write clips/results)
│   └── s3:DeleteObject (cleanup)
├── Step Functions Permissions
│   ├── states:StartExecution
│   └── states:DescribeExecution
└── Lambda Permissions
    └── lambda:InvokeFunction (for testing)
```

### Network Security
- All Lambda functions run in AWS managed VPC
- S3 bucket has "Block Public Access" enabled
- Pre-signed URLs for downloads (7-day expiry)
- API Gateway with CORS enabled
- Optional: VPC endpoints for S3 (enhanced security)

---

## 🚀 Deployment Options

### Option 1: ZIP Deployment (Most Functions)
```bash
cd lambda-functions
package-lambda.bat  # Creates 6 ZIP files
```

Upload to Lambda:
- opus-download.zip (62 MB)
- opus-detect.zip (16 MB)
- opus-process-clip.zip (16 MB)
- opus-finalize.zip (16 MB)
- opus-api-gateway.zip (16 MB)

### Option 2: ECR Container (Transcribe Only) ✅
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
./build-and-push-transcribe-ecr.sh
```

Creates:
- ECR image: opus-transcribe:latest (2-3 GB)
- Includes: Whisper model + dependencies
- Faster warm starts (model pre-loaded)

**Why ECR for Transcribe?**
- ZIP size limit: 250 MB (via S3) / 50 MB (console)
- Whisper package: 1.8 GB (too large!)
- Container limit: 10 GB (plenty of space)
- Pre-loaded model: Faster cold starts

---

## 📈 Scalability

### Concurrent Execution
- **Default:** 1000 concurrent Lambda executions
- **Transcribe:** 10 GB memory = ~10 concurrent videos
- **Total capacity:** Process 10 videos simultaneously
- **Queue handling:** API Gateway + Step Functions queue excess

### Handling Spikes
```
100 users submit videos simultaneously:
├─ API Gateway: Accepts all 100 requests instantly
├─ Step Functions: Starts 100 executions
├─ Lambda Download: Processes 10 at a time (limited by memory)
├─ Lambda Transcribe: Processes 10 at a time
└─ Results: All 100 complete in ~30-40 minutes

Sequential would take: 100 × 15 min = 25 hours
Parallel (10x): 10 × 15 min = 2.5 hours
```

---

## 🛠️ Customization Examples

### Change Clip Count
```python
# In opus-detect Lambda environment variables
NUM_CLIPS = 5  # Generate 5 clips instead of 3
```

### Change Whisper Model
```bash
# Rebuild container with different model
export WHISPER_MODEL=small
./build-and-push-transcribe-ecr.sh

# Update Lambda environment variable
WHISPER_MODEL = small
```

### Add Custom Keywords
```python
# In clip_detector.py
VIRAL_KEYWORDS = [
    'secret', 'hack', 'tip',
    'YOUR_CUSTOM_KEYWORD',  # Add here
]
```

### Change Aspect Ratio
```python
# Already supported in UI
aspect_ratios = ['9:16', '16:9', '1:1', '4:5']
```

---

## 📚 File Reference

### Core Application Files
```
opus-clip-cloud/
├── app_cloud.py                    # Flask web server
├── pipeline_cloud.py               # Main processing logic
├── downloader_cloud.py             # YouTube downloader
├── transcriber.py                  # Whisper integration
├── clip_detector.py                # Viral clip detection
├── video_processor_v2.py           # FFmpeg processing
├── config_cloud.py                 # Configuration
└── templates/
    └── index.html                  # Modern UI (1150 lines)
```

### Lambda Function Files
```
lambda-functions/
├── 1-lambda-download.py            # Download function
├── 2-lambda-transcribe.py          # Transcribe function
├── 3-lambda-detect-clips.py        # Detection function
├── 4-lambda-process-clip.py        # Processing function
├── 5-lambda-finalize.py            # Finalization function
├── 6-lambda-api-gateway.py         # API handler
├── Dockerfile.transcribe           # Container definition ← NEW!
├── build-and-push-transcribe-ecr.bat  # Build script ← NEW!
├── build-and-push-transcribe-ecr.sh   # Build script ← NEW!
├── ECR-DEPLOYMENT-GUIDE.md         # Full ECR guide ← NEW!
└── ECR-QUICK-REFERENCE.md          # Quick reference ← NEW!
```

### Documentation Files
```
lambda-functions/
├── 00-README.md                    # Lambda overview
├── QUICK-START.md                  # 30-minute deploy
├── README-DEPLOYMENT.md            # Full deployment
├── PACKAGING-HELP.md               # ZIP packaging
├── ECR-DEPLOYMENT-GUIDE.md         # ECR guide ← NEW!
├── ECR-QUICK-REFERENCE.md          # ECR quick ref ← NEW!
└── PROJECT-ARCHITECTURE.md         # This file ← NEW!
```

---

## 🎯 Next Steps

1. **Deploy Transcribe to ECR:**
   ```bash
   cd lambda-functions
   ./build-and-push-transcribe-ecr.sh
   ```

2. **Deploy Other Functions:**
   ```bash
   package-lambda.bat
   # Upload ZIPs to Lambda
   ```

3. **Configure Step Functions:**
   - Use `step-functions-state-machine.json`
   - Update ARNs for your Lambda functions

4. **Set Up API Gateway:**
   - Create HTTP API
   - Configure routes: /process, /status, /result

5. **Connect Web UI:**
   - Update API endpoint in `index.html`
   - Deploy Flask app to Oracle Cloud or EC2

6. **Monitor & Optimize:**
   - CloudWatch Logs for debugging
   - Cost Explorer for spending
   - X-Ray for performance tracing

---

## ✅ Success Criteria

Your deployment is successful when:

- [ ] All 6 Lambda functions deployed
- [ ] opus-transcribe running from ECR container
- [ ] Step Functions state machine created
- [ ] API Gateway endpoints working
- [ ] S3 bucket configured with lifecycle rules
- [ ] Test video processed successfully
- [ ] Clips generated with subtitles
- [ ] Download URLs working
- [ ] Total cost under $10/month
- [ ] Processing time under 15 minutes

---

**🎉 You now understand the complete architecture! Ready to deploy? Start with `ECR-DEPLOYMENT-GUIDE.md`**
