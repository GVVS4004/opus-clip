# ECR Deployment - Quick Reference Card

## 🚀 One-Command Deploy

### Prerequisites
```bash
# Install Docker: https://www.docker.com/products/docker-desktop/
# Install AWS CLI: aws configure

# Get your AWS Account ID
aws sts get-caller-identity --query Account --output text
```

### Windows
```cmd
cd lambda-functions
set AWS_REGION=us-east-1
set AWS_ACCOUNT_ID=123456789012
build-and-push-transcribe-ecr.bat
```

### Mac/Linux
```bash
cd lambda-functions
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
./build-and-push-transcribe-ecr.sh
```

---

## 📋 Create Lambda Function

### Console
1. Open https://console.aws.amazon.com/lambda/
2. Create function → **Container image**
3. Name: `opus-transcribe`
4. Image URI: `{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/opus-transcribe:latest`
5. Memory: **10 GB**, Timeout: **10 min**
6. Environment variables:
   - `BUCKET_NAME` = your-s3-bucket
   - `WHISPER_MODEL` = base

### CLI
```bash
aws lambda create-function \
  --function-name opus-transcribe \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/opus-transcribe:latest \
  --role arn:aws:iam::123456789012:role/opus-clip-lambda-role \
  --memory-size 10240 \
  --timeout 600 \
  --environment "Variables={BUCKET_NAME=your-bucket,WHISPER_MODEL=base}"
```

---

## 🔄 Update Deployed Function

```bash
# Rebuild and push
./build-and-push-transcribe-ecr.sh

# Update Lambda
aws lambda update-function-code \
  --function-name opus-transcribe \
  --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/opus-transcribe:latest
```

---

## 🎯 Whisper Models

| Model | Image Size | Accuracy | Speed | Best For |
|-------|------------|----------|-------|----------|
| `tiny` | 1.8 GB | ⭐⭐ | ⚡⚡⚡ | Testing |
| **`base`** | 2.2 GB | ⭐⭐⭐ | ⚡⚡ | **Production** |
| `small` | 3.0 GB | ⭐⭐⭐⭐ | ⚡ | High accuracy |
| `medium` | 5.5 GB | ⭐⭐⭐⭐⭐ | 🐌 | Professional |

Change model:
```bash
export WHISPER_MODEL=small
./build-and-push-transcribe-ecr.sh
```

---

## 🐛 Troubleshooting

### Docker not running
```bash
# Windows: Start Docker Desktop
# Mac: Open Docker.app
# Linux: sudo systemctl start docker
```

### Authentication failed
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Lambda timeout
1. Increase timeout to 15 minutes
2. Use `WHISPER_MODEL=tiny`
3. Increase memory to 10 GB

---

## 💰 Cost

- **ECR Storage:** $0.25/month (~2.5 GB)
- **Lambda (100 videos):** $3.50/month
- **Total:** ~$4/month

---

## 📚 Full Documentation

See `ECR-DEPLOYMENT-GUIDE.md` for complete guide.

---

## ✅ Quick Test

```bash
# Upload test video
aws s3 cp test.mp4 s3://your-bucket/test-123/original_video.mp4

# Invoke Lambda
aws lambda invoke \
  --function-name opus-transcribe \
  --payload '{"session_id":"test-123","s3_video_key":"test-123/original_video.mp4"}' \
  response.json

# Check result
cat response.json

# Download transcript
aws s3 cp s3://your-bucket/test-123/transcript.json .
```

---

**Ready to deploy? Run the script above! ⚡**
