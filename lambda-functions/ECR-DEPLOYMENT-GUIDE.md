# ECR Deployment Guide for opus-transcribe Lambda Function

## 📋 Overview

This guide explains how to deploy the `opus-transcribe` Lambda function as a **Docker container** to **Amazon ECR** (Elastic Container Registry) instead of using a ZIP file.

### Why Use ECR Instead of ZIP?

| Feature | ZIP Deployment | ECR Container |
|---------|---------------|---------------|
| Max Size | 250 MB (S3) / 50 MB (console) | 10 GB |
| opus-transcribe Size | ~1.8 GB ❌ Too large! | ~2-3 GB ✅ Works! |
| Cold Start | 5-10 seconds | 10-20 seconds |
| Deployment Speed | Fast | Slower (Docker build) |
| Flexibility | Limited | Full control |
| Best For | Small functions | Large ML models |

**Verdict:** For `opus-transcribe` with Whisper model, ECR is the **only viable option**.

---

## 🎯 Architecture Overview

```
Your Computer
    │
    ├─ Dockerfile.transcribe       (Container definition)
    ├─ 2-lambda-transcribe.py      (Lambda function code)
    └─ requirements-transcribe.txt (Python dependencies)
    │
    ↓ docker build
    │
Docker Image (~2-3 GB)
    ├─ Python 3.11 Runtime
    ├─ OpenAI Whisper + Models
    ├─ FFmpeg (for audio processing)
    ├─ Lambda function code
    └─ All dependencies
    │
    ↓ docker push
    │
Amazon ECR Repository
    └─ opus-transcribe:latest
        │
        ↓ Lambda pulls image
        │
AWS Lambda Function
    └─ Runs containerized function
```

---

## ⚡ Quick Start (15 Minutes)

### Prerequisites

1. **Docker Desktop** installed and running
   - Windows: https://www.docker.com/products/docker-desktop/
   - Mac: https://www.docker.com/products/docker-desktop/
   - Linux: `sudo apt-get install docker.io`

2. **AWS CLI** installed and configured
   ```bash
   # Install AWS CLI
   # Windows: Download from https://aws.amazon.com/cli/
   # Mac: brew install awscli
   # Linux: sudo apt-get install awscli

   # Configure AWS credentials
   aws configure
   # Enter:
   # - AWS Access Key ID
   # - AWS Secret Access Key
   # - Default region (e.g., us-east-1)
   # - Default output format: json
   ```

3. **AWS Account ID**
   ```bash
   # Get your AWS Account ID
   aws sts get-caller-identity --query Account --output text
   ```

---

## 🚀 Step-by-Step Deployment

### Step 1: Set Environment Variables

**Windows (Command Prompt):**
```cmd
set AWS_REGION=us-east-1
set AWS_ACCOUNT_ID=123456789012
```

**Windows (PowerShell):**
```powershell
$env:AWS_REGION="us-east-1"
$env:AWS_ACCOUNT_ID="123456789012"
```

**Mac/Linux:**
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
```

**Replace:**
- `us-east-1` with your AWS region
- `123456789012` with your AWS Account ID

---

### Step 2: Run Build and Push Script

**Navigate to lambda-functions directory:**
```bash
cd C:\Projects\opus-clip-cloud\lambda-functions
```

**Windows:**
```cmd
build-and-push-transcribe-ecr.bat
```

**Mac/Linux:**
```bash
chmod +x build-and-push-transcribe-ecr.sh
./build-and-push-transcribe-ecr.sh
```

**What this does:**
1. ✅ Creates ECR repository `opus-transcribe` (if not exists)
2. ✅ Authenticates Docker with ECR
3. ✅ Builds Docker image (~10-15 minutes)
   - Downloads Whisper model
   - Installs dependencies
   - Packages everything
4. ✅ Tags image for ECR
5. ✅ Pushes to ECR (~5-10 minutes, ~2-3 GB upload)

**Expected Output:**
```
============================================================================
SUCCESS! Image pushed to ECR
============================================================================

ECR Image URI: 123456789012.dkr.ecr.us-east-1.amazonaws.com/opus-transcribe:latest
```

**Copy this URI** - you'll need it in the next step!

---

### Step 3: Create Lambda Function from Container

#### Option A: AWS Console (Easier)

1. **Go to Lambda Console:**
   https://console.aws.amazon.com/lambda/

2. **Create Function:**
   - Click **"Create function"**
   - Select **"Container image"**
   - Function name: `opus-transcribe`
   - Container image URI: **Paste the URI from Step 2**
   - Architecture: **x86_64**
   - Click **"Create function"**

3. **Configure Function:**
   - **Memory:** 10240 MB (10 GB)
   - **Timeout:** 10 minutes (600 seconds)
   - **Ephemeral storage:** 10240 MB (10 GB)

4. **Add Environment Variables:**
   - Key: `BUCKET_NAME`, Value: `your-s3-bucket-name`
   - Key: `WHISPER_MODEL`, Value: `base`

5. **Add IAM Role Permissions:**
   - Attach policy: `AmazonS3FullAccess` (or custom S3 policy)

#### Option B: AWS CLI (Faster for Automation)

```bash
# Create Lambda function from ECR image
aws lambda create-function \
  --function-name opus-transcribe \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/opus-transcribe:latest \
  --role arn:aws:iam::123456789012:role/opus-clip-lambda-role \
  --memory-size 10240 \
  --timeout 600 \
  --ephemeral-storage Size=10240 \
  --environment "Variables={BUCKET_NAME=your-s3-bucket-name,WHISPER_MODEL=base}" \
  --region us-east-1
```

**Replace:**
- `123456789012` with your Account ID
- `your-s3-bucket-name` with your S3 bucket
- `arn:aws:iam::...` with your IAM role ARN

---

### Step 4: Test the Function

1. **Go to Lambda Console** → Find `opus-transcribe`

2. **Create Test Event:**
   ```json
   {
     "session_id": "test-123",
     "s3_video_key": "test-123/original_video.mp4",
     "video_info": {
       "title": "Test Video",
       "duration": 300
     }
   }
   ```

3. **Upload a test video to S3:**
   ```bash
   # Upload a sample video
   aws s3 cp test-video.mp4 s3://your-bucket/test-123/original_video.mp4
   ```

4. **Invoke Lambda:**
   - Click **"Test"**
   - Watch execution logs
   - Check S3 for `test-123/transcript.json`

**Expected Result:**
```json
{
  "statusCode": 200,
  "session_id": "test-123",
  "s3_transcript_key": "test-123/transcript.json"
}
```

---

## 📦 Customizing the Whisper Model

You can use different Whisper models by changing the `WHISPER_MODEL` build argument:

### Available Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | ~40 MB | Fastest | Lower | Testing/Development |
| `base` | ~140 MB | Fast | Good | **Recommended** (default) |
| `small` | ~460 MB | Medium | Better | Higher accuracy needed |
| `medium` | ~1.5 GB | Slow | Best | Professional use |
| `large` | ~2.9 GB | Slowest | Excellent | Maximum accuracy |

### Build with Different Model

**Windows:**
```cmd
set WHISPER_MODEL=small
build-and-push-transcribe-ecr.bat
```

**Mac/Linux:**
```bash
export WHISPER_MODEL=small
./build-and-push-transcribe-ecr.sh
```

### Update Lambda Environment Variable

After deploying:
```bash
aws lambda update-function-configuration \
  --function-name opus-transcribe \
  --environment "Variables={BUCKET_NAME=your-bucket,WHISPER_MODEL=small}"
```

---

## 🔄 Updating the Container

When you make changes to the code:

### Step 1: Update Code
Edit `2-lambda-transcribe.py` with your changes

### Step 2: Rebuild and Push
```bash
# Windows
build-and-push-transcribe-ecr.bat

# Mac/Linux
./build-and-push-transcribe-ecr.sh
```

### Step 3: Update Lambda
Lambda automatically pulls the `:latest` tag, but you need to trigger an update:

```bash
aws lambda update-function-code \
  --function-name opus-transcribe \
  --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/opus-transcribe:latest
```

Or in Console:
1. Go to Lambda function
2. Click **"Deploy new image"**
3. Lambda will pull latest from ECR

---

## 💰 Cost Analysis

### ECR Storage Costs

| Component | Size | Monthly Cost (us-east-1) |
|-----------|------|--------------------------|
| Container Image | ~2.5 GB | **$0.25/month** |
| Data Transfer | Out to Lambda | Free (same region) |

### Lambda Costs (per 100 videos, 15 min avg)

| Resource | Usage per Video | 100 Videos | Free Tier | Cost |
|----------|----------------|------------|-----------|------|
| Memory (10 GB) | 6 min @ 10 GB | 10,000 GB-min | 400K GB-sec | **$3.50** |
| Requests | 1 invocation | 100 | 1M free | **$0.00** |
| **Total** | | | | **$3.75/month** |

**Total with ECR:** ~$4/month for 100 videos

---

## 🐛 Troubleshooting

### Issue: "Docker daemon not running"

**Solution:**
```bash
# Windows: Start Docker Desktop
# Mac: Open Docker Desktop application
# Linux: sudo systemctl start docker
```

### Issue: "unauthorized: authentication required"

**Solution:** Re-authenticate with ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Issue: "Docker build fails downloading Whisper model"

**Solution:** Check internet connection or use pre-downloaded model
```dockerfile
# In Dockerfile.transcribe, comment out this line:
# RUN python -c "import whisper; whisper.load_model('base')"

# Model will be downloaded on first Lambda invocation (slower cold start)
```

### Issue: "Lambda timeout during transcription"

**Solutions:**
1. Increase timeout to 15 minutes
2. Use smaller Whisper model (`tiny` or `base`)
3. Increase memory to 10 GB (more CPU allocated)

### Issue: "Out of memory error"

**Solutions:**
1. Increase ephemeral storage to 10 GB
2. Use smaller Whisper model
3. Process shorter videos only

### Issue: "Image too large for Lambda"

**Current Limit:** 10 GB (you're safe with ~2.5 GB)

If you hit limits:
1. Remove unused dependencies
2. Use smaller Whisper model
3. Use multi-stage Docker build (advanced)

---

## 📊 Performance Benchmarks

### Cold Start Times (First Invocation)

| Whisper Model | Container Size | Cold Start | First Transcript |
|---------------|----------------|------------|------------------|
| `tiny` | 1.8 GB | 8-12 sec | 15-20 sec total |
| `base` | 2.2 GB | 10-15 sec | 20-30 sec total |
| `small` | 3.0 GB | 15-20 sec | 30-40 sec total |
| `medium` | 5.5 GB | 25-35 sec | 60-90 sec total |

### Warm Start Times (Subsequent Invocations)

| Whisper Model | Warm Start | 15-min Video |
|---------------|------------|--------------|
| `tiny` | <1 sec | ~3 min |
| `base` | <1 sec | ~6 min |
| `small` | <1 sec | ~10 min |
| `medium` | 1-2 sec | ~20 min |

**Recommendation:** Use `base` model for best balance of speed and accuracy.

---

## 🎯 Advanced Configuration

### Environment Variables

Add these to Lambda configuration:

```bash
BUCKET_NAME=your-s3-bucket        # Required
WHISPER_MODEL=base                # Optional (default: base)
PYTHONUNBUFFERED=1                # Optional (better logging)
```

### Reserved Concurrency

Limit parallel executions to control costs:
```bash
aws lambda put-function-concurrency \
  --function-name opus-transcribe \
  --reserved-concurrent-executions 5
```

### CloudWatch Alarms

Monitor for failures:
```bash
# Create alarm for errors
aws cloudwatch put-metric-alarm \
  --alarm-name opus-transcribe-errors \
  --alarm-description "Alert on transcribe errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 3 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=opus-transcribe
```

---

## 🔐 Security Best Practices

### 1. Use Least Privilege IAM Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 2. Enable ECR Image Scanning

```bash
aws ecr put-image-scanning-configuration \
  --repository-name opus-transcribe \
  --image-scanning-configuration scanOnPush=true
```

### 3. Use VPC Endpoints (Optional)

For enhanced security, run Lambda in VPC with S3 VPC endpoint.

---

## 📚 Additional Resources

### Official Documentation
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [OpenAI Whisper GitHub](https://github.com/openai/whisper)

### Useful Commands

```bash
# List ECR repositories
aws ecr describe-repositories

# List images in repository
aws ecr list-images --repository-name opus-transcribe

# Delete old images
aws ecr batch-delete-image \
  --repository-name opus-transcribe \
  --image-ids imageTag=old-tag

# Get Lambda logs
aws logs tail /aws/lambda/opus-transcribe --follow

# Invoke Lambda
aws lambda invoke \
  --function-name opus-transcribe \
  --payload '{"session_id":"test"}' \
  response.json
```

---

## ✅ Checklist

- [ ] Docker Desktop installed and running
- [ ] AWS CLI installed and configured
- [ ] AWS Account ID obtained
- [ ] Environment variables set (AWS_REGION, AWS_ACCOUNT_ID)
- [ ] Docker image built successfully
- [ ] Image pushed to ECR
- [ ] Lambda function created from container
- [ ] Memory set to 10 GB
- [ ] Timeout set to 10 minutes
- [ ] Environment variables configured
- [ ] IAM role has S3 permissions
- [ ] Test invocation successful
- [ ] Transcript generated in S3

---

## 🎉 You're Done!

Your `opus-transcribe` Lambda function is now deployed as a container!

**Key Benefits:**
- ✅ No ZIP size limits
- ✅ Whisper model pre-loaded (faster warm starts)
- ✅ Full control over environment
- ✅ Easy to update and iterate
- ✅ Professional production setup

**Next Steps:**
1. Integrate with Step Functions workflow
2. Connect other Lambda functions
3. Deploy your API Gateway
4. Monitor performance in CloudWatch
5. Optimize costs based on usage

---

**Need Help?** Check the main `QUICK-START.md` for full deployment guide!
