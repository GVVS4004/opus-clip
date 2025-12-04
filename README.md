# Opus Clip - AWS Lambda Video Processing Pipeline

A serverless video processing system built on AWS Lambda that automatically downloads YouTube videos, transcribes them using OpenAI Whisper, and generates viral-worthy clips.

## Features

- **Serverless Architecture**: Built entirely on AWS Lambda for automatic scaling
- **AI-Powered Transcription**: Uses OpenAI Whisper for accurate transcription
- **Intelligent Clip Detection**: Analyzes transcript to identify the best viral moments
- **Parallel Processing**: Processes multiple clips simultaneously for faster output
- **Cost-Effective Storage**: Supports both AWS S3 and Cloudflare R2 (10GB free forever)
- **Automated Workflow**: Step Functions orchestrate the entire pipeline

## Architecture

```
User Request → API Gateway → Step Functions
                                  ↓
                      ┌───────────┴───────────┐
                      ↓                       ↓
              Download Lambda           S3/R2 Storage
                      ↓                       ↑
              Transcribe Lambda ──────────────┤
                      ↓                       │
           Detect Clips Lambda                │
                      ↓                       │
          Process Clip Lambda ────────────────┤
          (parallel × N clips)                │
                      ↓                       │
             Finalize Lambda ─────────────────┘
                      ↓
              Result with URLs
```

## Project Structure

```
opus-clip/
├── README.md                    # This file
├── .gitignore                   # Git ignore patterns
├── backup/                      # Backup files
│   └── opus-node-download/      # Node.js implementation backup
├── docs/                        # Documentation
│   ├── lambda-deployment.md     # Lambda deployment guide
│   ├── cloudflare-setup.md      # Cloudflare R2 setup
│   ├── cookie-setup.md          # YouTube cookie setup
│   └── ytdlp-deployment.md      # yt-dlp layer deployment
├── src/                         # Source code
│   ├── download/                # Lambda: Download YouTube videos
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── transcribe/              # Lambda: Transcribe audio with Whisper
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── detect-clips/            # Lambda: Detect viral clips
│   │   └── lambda_function.py
│   ├── process-clip/            # Lambda: Extract & process clips
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── finalize/                # Lambda: Generate download URLs
│   │   └── lambda_function.py
│   └── api-gateway/             # Lambda: API Gateway handler
│       └── lambda_function.py
└── deployment/                  # Deployment scripts & configs
    ├── dockerfiles/             # Docker build files
    ├── *.bat                    # Windows deployment scripts
    ├── *.sh                     # Linux deployment scripts
    └── requirements-*.txt       # Additional requirements files
```

## Quick Start

### Prerequisites

- AWS Account with Lambda access
- AWS CLI configured
- Python 3.11
- Docker (for building Lambda layers)

### 1. Deploy Lambda Functions

```bash
# Build deployment packages
cd deployment
./build-all.sh  # Linux/Mac
# or
build-all.bat   # Windows

# Deploy to AWS Lambda using AWS CLI
aws lambda create-function \
  --function-name opus-download \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --zip-file fileb://opus-download.zip \
  --memory-size 3072 \
  --timeout 300
```

### 2. Configure Storage

**Option A: AWS S3**
```bash
aws s3 mb s3://your-opus-clips-bucket
```

**Option B: Cloudflare R2 (Recommended - 10GB Free)**

See [docs/cloudflare-setup.md](docs/cloudflare-setup.md) for detailed setup instructions.

### 3. Set Environment Variables

For each Lambda function, configure:
```
BUCKET_NAME=your-bucket-name
R2_ENDPOINT=https://[account-id].r2.cloudflarestorage.com  # If using R2
R2_ACCESS_KEY=your-r2-access-key                            # If using R2
R2_SECRET_KEY=your-r2-secret-key                            # If using R2
```

### 4. Create Step Functions State Machine

Import the state machine definition from `deployment/step-functions-state-machine.json` into AWS Step Functions.

### 5. Test the Pipeline

```bash
curl -X POST https://your-api-gateway-url/process \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }'
```

## Lambda Functions Overview

| Function | Purpose | Memory | Timeout | Dependencies |
|----------|---------|--------|---------|--------------|
| **download** | Downloads YouTube videos to S3/R2 | 3 GB | 5 min | pytubefix, boto3 |
| **transcribe** | Transcribes audio using Whisper | 10 GB | 10 min | openai-whisper, boto3 |
| **detect-clips** | Analyzes transcript for viral moments | 2 GB | 1 min | boto3 |
| **process-clip** | Extracts clips & adds subtitles | 4 GB | 5 min | boto3, FFmpeg |
| **finalize** | Generates presigned URLs | 512 MB | 30 sec | boto3 |
| **api-gateway** | Handles API requests | 512 MB | 30 sec | boto3 |

## Configuration

### Whisper Model Selection

Configure in `transcribe` Lambda:
- `WHISPER_MODEL=tiny` - Fast, less accurate (~3 min for 15-min video)
- `WHISPER_MODEL=base` - Balanced (default) (~6 min)
- `WHISPER_MODEL=small` - More accurate (~10 min)
- `WHISPER_MODEL=large` - Best accuracy (~40 min)

### Clip Detection Parameters

Configure in `detect-clips` Lambda:
- `NUM_CLIPS=3` - Number of clips to generate
- `MIN_CLIP_DURATION=15` - Minimum clip length (seconds)
- `MAX_CLIP_DURATION=60` - Maximum clip length (seconds)
- `TARGET_CLIP_DURATION=30` - Preferred clip length (seconds)

## Cost Estimation

### For 100 videos/month (15 min avg, 3 clips each):

**Using AWS S3:**
- Lambda Compute: ~$3.94/month
- S3 Storage: ~$2.19/month
- **Total: ~$6.14/month**

**Using Cloudflare R2:**
- Lambda Compute: ~$3.94/month
- R2 Storage: **$0/month (free)**
- **Total: ~$3.94/month**

## Documentation

- [Lambda Deployment Guide](docs/lambda-deployment.md) - Complete deployment instructions
- [Cloudflare R2 Setup](docs/cloudflare-setup.md) - Free storage setup (10GB)
- [Cookie Setup](docs/cookie-setup.md) - YouTube authentication
- [yt-dlp Deployment](docs/ytdlp-deployment.md) - Lambda layer setup

## Monitoring

### CloudWatch Logs

Each function logs to: `/aws/lambda/opus-{function-name}`

### Step Functions

Monitor workflow execution in the AWS Step Functions console.

### S3/R2 Structure

```
your-bucket/
└── {session-id}/
    ├── original_video.mp4
    ├── transcript.json
    ├── result.json
    └── clips/
        ├── clip_0.mp4
        ├── clip_1.mp4
        └── clip_2.mp4
```

## Troubleshooting

**Lambda Timeout:**
- Increase timeout in Lambda configuration
- Consider using smaller Whisper model for transcription

**Out of Memory:**
- Increase Lambda memory allocation
- For transcribe: Use `tiny` or `base` model

**FFmpeg Not Found:**
- Ensure FFmpeg Lambda Layer is attached to `process-clip` function
- Use public layer: `arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4`

## License

This project uses:
- OpenAI Whisper (MIT License)
- PyTubeFix (MIT License)
- FFmpeg (GPL License - use static binaries)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions:
- Check the [documentation](docs/)
- Review CloudWatch Logs
- Open a GitHub issue
