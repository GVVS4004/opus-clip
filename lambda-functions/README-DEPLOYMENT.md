# Opus Clip - AWS Lambda Deployment Guide

Complete guide to deploy your video processing project to AWS Lambda using the AWS Console (no CLI needed).

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Create S3 Bucket](#step-1-create-s3-bucket)
4. [Step 2: Create IAM Roles](#step-2-create-iam-roles)
5. [Step 3: Create Lambda Layers](#step-3-create-lambda-layers)
6. [Step 4: Deploy Lambda Functions](#step-4-deploy-lambda-functions)
7. [Step 5: Create Step Functions](#step-5-create-step-functions)
8. [Step 6: Setup API Gateway](#step-6-setup-api-gateway)
9. [Testing](#testing)
10. [Cost Estimation](#cost-estimation)

---

## Prerequisites

- AWS Account with Free Tier
- Basic understanding of AWS services
- Python 3.11 installed locally (for creating deployment packages)
- 7-Zip or similar tool to create ZIP files

---

## Architecture Overview

```
[Your UI] → [API Gateway] → [Lambda: API Handler] → [Step Functions]
                                                           ↓
    [Lambda: Download] → [Lambda: Transcribe] → [Lambda: Detect]
                                                           ↓
                                [Lambda: Process Clip] (parallel × N)
                                                           ↓
                                    [Lambda: Finalize]
                                                           ↓
                                        [S3 Storage]
```

**Cost for 100 videos/month: ~$6.14**

---

## Step 1: Create S3 Bucket

### 1.1 Create Bucket

1. Go to **S3 Console**: https://s3.console.aws.amazon.com/
2. Click **Create bucket**
3. **Bucket name**: `opus-clip-videos-YOUR_NAME` (must be globally unique)
4. **Region**: Select your preferred region (e.g., `us-east-1`)
5. **Block Public Access**: Keep all boxes checked (default)
6. Click **Create bucket**

### 1.2 Configure Lifecycle Policy (Auto-cleanup)

1. Open your bucket → **Management** tab
2. Click **Create lifecycle rule**
3. **Rule name**: `auto-delete-old-videos`
4. **Rule scope**: Apply to all objects
5. **Lifecycle rule actions**: Check "Expire current versions of objects"
6. **Days after object creation**: 7 (videos deleted after 7 days)
7. Click **Create rule**

### 1.3 Enable CORS (if accessing from browser)

1. Open your bucket → **Permissions** tab
2. Scroll to **Cross-origin resource sharing (CORS)**
3. Click **Edit** and paste:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

---

## Step 2: Create IAM Roles

### 2.1 Lambda Execution Role

1. Go to **IAM Console**: https://console.aws.amazon.com/iam/
2. Click **Roles** → **Create role**
3. **Trusted entity**: AWS service → Lambda
4. Click **Next**
5. **Attach policies**:
   - Search and select: `AWSLambdaBasicExecutionRole`
   - Click **Next**
6. **Role name**: `opus-clip-lambda-role`
7. Click **Create role**

### 2.2 Add S3 Permissions to Lambda Role

1. Open the role you just created: `opus-clip-lambda-role`
2. Click **Add permissions** → **Create inline policy**
3. Click **JSON** tab and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::opus-clip-videos-YOUR_NAME/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::opus-clip-videos-YOUR_NAME"
        }
    ]
}
```

**Replace** `opus-clip-videos-YOUR_NAME` with your bucket name!

4. Click **Next**
5. **Policy name**: `S3AccessPolicy`
6. Click **Create policy**

### 2.3 Step Functions Execution Role

1. **Roles** → **Create role**
2. **Trusted entity**: AWS service → **Step Functions**
3. Click **Next**
4. **Attach policies**: (none needed yet, we'll add inline policy)
5. **Role name**: `opus-clip-stepfunctions-role`
6. Click **Create role**

### 2.4 Add Lambda Invoke Permission to Step Functions Role

1. Open role: `opus-clip-stepfunctions-role`
2. **Add permissions** → **Create inline policy** → **JSON**:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:*:*:function:opus-*"
        }
    ]
}
```

3. **Policy name**: `LambdaInvokePolicy`
4. Click **Create policy**

### 2.5 Add Step Functions Permission to API Lambda Role

1. Go back to `opus-clip-lambda-role`
2. **Add permissions** → **Create inline policy** → **JSON**:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "states:StartExecution",
                "states:DescribeExecution"
            ],
            "Resource": "arn:aws:states:*:*:*"
        }
    ]
}
```

3. **Policy name**: `StepFunctionsPolicy`
4. Click **Create policy**

---

## Step 3: Create Lambda Layers

Lambda layers contain shared dependencies (libraries, FFmpeg binary).

### 3.1 Create FFmpeg Layer

#### Option A: Use Pre-built FFmpeg Layer

1. Go to: https://github.com/serverlesspub/ffmpeg-aws-lambda-layer
2. Download the latest `ffmpeg-layer.zip`
3. Or use this ARN directly (us-east-1):
   ```
   arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4
   ```

#### Option B: Build Your Own (Windows)

1. Download FFmpeg static build: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. Extract and create this structure:
   ```
   layer/
   └── bin/
       ├── ffmpeg.exe
       └── ffprobe.exe
   ```
3. Zip the `layer` folder → `ffmpeg-layer.zip`

#### Upload FFmpeg Layer

1. Go to **Lambda Console**: https://console.aws.amazon.com/lambda/
2. Click **Layers** (left sidebar) → **Create layer**
3. **Name**: `ffmpeg-layer`
4. **Upload**: Select `ffmpeg-layer.zip`
5. **Compatible runtimes**: Python 3.11
6. Click **Create**
7. **Note the Layer ARN** (you'll need it later)

### 3.2 Create Python Dependencies Layer

#### On Windows (with WSL or Git Bash):

```bash
# Create layer directory
mkdir -p python-layer/python

# Install dependencies
pip install -t python-layer/python \
    pytubefix \
    openai-whisper \
    boto3 \
    numpy

# Create ZIP
cd python-layer
zip -r ../python-deps-layer.zip .
cd ..
```

#### Alternative (Using Docker on Windows):

```bash
docker run -v "%CD%":/var/task "public.ecr.aws/sam/build-python3.11" /bin/sh -c "pip install -t python pytubefix openai-whisper boto3 numpy && zip -r python-deps-layer.zip python"
```

**Warning**: The Python dependencies layer will be ~1.5 GB! This exceeds Lambda's 250 MB layer limit.

#### Solution: Include dependencies in each function

We'll include smaller dependencies in each function's deployment package instead.

---

## Step 4: Deploy Lambda Functions

We'll create 6 Lambda functions. For each function:

### 4.1 Lambda 1: opus-download

#### Create Deployment Package:

```bash
# Create deployment directory
mkdir deploy-download
cd deploy-download

# Copy function code
copy ..\1-lambda-download.py lambda_function.py

# Install dependencies
pip install -t . pytubefix

# Create ZIP (exclude unnecessary files)
zip -r opus-download.zip . -x "*.pyc" "*__pycache__*"
```

**Important**: Rename `1-lambda-download.py` to `lambda_function.py` and ensure the handler is `lambda_function.lambda_handler`.

#### Create Function via AWS Console:

1. Go to **Lambda Console** → **Create function**
2. **Function name**: `opus-download`
3. **Runtime**: Python 3.11
4. **Architecture**: x86_64
5. **Permissions**: Use existing role → `opus-clip-lambda-role`
6. Click **Create function**

#### Configure Function:

1. **Code** tab → **Upload from** → **.zip file**
2. Upload `opus-download.zip`
3. **Runtime settings** → **Edit**:
   - **Handler**: `lambda_function.lambda_handler`
4. **Configuration** tab:
   - **General configuration** → **Edit**:
     - **Memory**: 3072 MB (3 GB)
     - **Timeout**: 5 minutes
     - **Ephemeral storage**: 5120 MB (5 GB)
   - **Environment variables** → **Edit** → **Add**:
     - Key: `BUCKET_NAME`, Value: `opus-clip-videos-YOUR_NAME`

#### Add FFmpeg Layer (if needed):

1. **Code** tab → **Layers** section → **Add a layer**
2. **Choose a layer**: Custom layers → `ffmpeg-layer`
3. Click **Add**

---

### 4.2 Lambda 2: opus-transcribe

**Deployment Package**:

```bash
mkdir deploy-transcribe
cd deploy-transcribe
copy ..\2-lambda-transcribe.py lambda_function.py

# Install Whisper (large package!)
pip install -t . openai-whisper

# Create ZIP
zip -r opus-transcribe.zip .
```

**Configuration**:
- **Function name**: `opus-transcribe`
- **Memory**: 10240 MB (10 GB - maximum!)
- **Timeout**: 10 minutes
- **Ephemeral storage**: 10240 MB (10 GB)
- **Environment variables**:
  - `BUCKET_NAME`: Your bucket name
  - `WHISPER_MODEL`: `base` (or `tiny` for faster processing)

**⚠️ WARNING**: Whisper package is ~2.5 GB. Deployment package might exceed Lambda's 50 MB direct upload limit.

**Solution**: Upload to S3 first, then reference:

1. Upload `opus-transcribe.zip` to your S3 bucket
2. In Lambda creation, choose **Upload a file from Amazon S3**
3. Enter S3 URL: `https://opus-clip-videos-YOUR_NAME.s3.amazonaws.com/opus-transcribe.zip`

---

### 4.3 Lambda 3: opus-detect

**Deployment Package**:

```bash
mkdir deploy-detect
cd deploy-detect
copy ..\3-lambda-detect-clips.py lambda_function.py

# No large dependencies needed
zip opus-detect.zip lambda_function.py
```

**Configuration**:
- **Function name**: `opus-detect`
- **Memory**: 2048 MB (2 GB)
- **Timeout**: 1 minute
- **Environment variables**:
  - `BUCKET_NAME`: Your bucket name
  - `MIN_CLIP_DURATION`: `15`
  - `MAX_CLIP_DURATION`: `60`
  - `TARGET_CLIP_DURATION`: `30`
  - `NUM_CLIPS`: `3`

---

### 4.4 Lambda 4: opus-process-clip

**Configuration**:
- **Function name**: `opus-process-clip`
- **Memory**: 4096 MB (4 GB)
- **Timeout**: 5 minutes
- **Ephemeral storage**: 10240 MB (10 GB)
- **Environment variables**:
  - `BUCKET_NAME`: Your bucket name
  - `FFMPEG_PATH`: `/opt/bin/ffmpeg`
- **Layers**: Add `ffmpeg-layer`

---

### 4.5 Lambda 5: opus-finalize

**Configuration**:
- **Function name**: `opus-finalize`
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Environment variables**:
  - `BUCKET_NAME`: Your bucket name

---

### 4.6 Lambda 6: opus-api-gateway

**Configuration**:
- **Function name**: `opus-api-gateway`
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Environment variables**:
  - `BUCKET_NAME`: Your bucket name
  - `STATE_MACHINE_ARN`: (you'll add this after creating Step Functions)

---

## Step 5: Create Step Functions

### 5.1 Create State Machine

1. Go to **Step Functions Console**: https://console.aws.amazon.com/states/
2. Click **Create state machine**
3. **Choose authoring method**: Write your workflow in code
4. **Type**: Standard
5. **Definition**: Paste the content from `step-functions-state-machine.json`

**⚠️ IMPORTANT**: Replace placeholders in the JSON:
- Replace `REGION` with your region (e.g., `us-east-1`)
- Replace `ACCOUNT_ID` with your AWS account ID

To find your account ID:
- Click your name in top-right → Account ID shown

6. Click **Next**
7. **State machine name**: `opus-clip-state-machine`
8. **Permissions**: Choose existing role → `opus-clip-stepfunctions-role`
9. Click **Create state machine**

### 5.2 Copy State Machine ARN

1. Open your state machine
2. Copy the **ARN** (e.g., `arn:aws:states:us-east-1:123456789:stateMachine:opus-clip-state-machine`)

### 5.3 Update API Lambda with State Machine ARN

1. Go back to Lambda → `opus-api-gateway` function
2. **Configuration** → **Environment variables** → **Edit**
3. Add variable:
   - Key: `STATE_MACHINE_ARN`
   - Value: (paste the ARN you copied)
4. Click **Save**

---

## Step 6: Setup API Gateway

### 6.1 Create HTTP API

1. Go to **API Gateway Console**: https://console.aws.amazon.com/apigateway/
2. Click **Create API**
3. Choose **HTTP API** → **Build**
4. **API name**: `opus-clip-api`
5. Click **Next**

### 6.2 Configure Routes

**Route 1: POST /process**

1. Click **Add integration** → **Lambda**
2. **Lambda function**: `opus-api-gateway`
3. **Method**: POST
4. **Resource path**: `/process`
5. Click **Next**

**Route 2: GET /status/{session_id}**

1. **Add route**
2. **Method**: GET
3. **Resource path**: `/status/{session_id}`
4. **Integration**: `opus-api-gateway`
5. Click **Next**

**Route 3: GET /result/{session_id}**

1. **Add route**
2. **Method**: GET
3. **Resource path**: `/result/{session_id}`
4. **Integration**: `opus-api-gateway`

### 6.3 Configure CORS

1. **CORS** section → **Configure**
2. **Access-Control-Allow-Origin**: `*`
3. **Access-Control-Allow-Methods**: GET, POST, OPTIONS
4. **Access-Control-Allow-Headers**: `*`
5. Click **Save**

### 6.4 Deploy API

1. Click **Create** to finish
2. **Note your API endpoint** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com`)

---

## Testing

### Test via cURL:

```bash
# Start processing
curl -X POST https://YOUR_API_ENDPOINT/process \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Response: {"session_id": "uuid-here", "status": "processing"}

# Check status
curl https://YOUR_API_ENDPOINT/status/SESSION_ID_HERE

# Get result (when completed)
curl https://YOUR_API_ENDPOINT/result/SESSION_ID_HERE
```

### Test via AWS Console:

#### Step 1: Test Individual Lambda

1. Go to Lambda → `opus-download`
2. **Test** tab → **Create test event**
3. **Event JSON**:
```json
{
  "session_id": "test-123",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
4. Click **Test**
5. Check **Execution result** for success

#### Step 2: Test Step Functions

1. Go to Step Functions → `opus-clip-state-machine`
2. Click **Start execution**
3. **Input**:
```json
{
  "session_id": "test-456",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
4. Click **Start execution**
5. Watch the visual workflow progress
6. Check S3 bucket for output files

---

## Cost Estimation

### For 100 videos/month (15 min avg, 3 clips each):

| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| Lambda (Download) | 400K GB-sec | 54K GB-sec | **$0** |
| Lambda (Transcribe) | 400K GB-sec | 360K GB-sec | **$0** |
| Lambda (Detect) | Covered | 6K GB-sec | **$0** |
| Lambda (Process) | Partially | 216K GB-sec | **$3.94** |
| Lambda (Finalize) | Covered | 500 GB-sec | **$0** |
| Lambda Invocations | 1M free | 700 | **$0** |
| Step Functions | 4K transitions | 800 | **$0** |
| S3 Storage | 5 GB free | 100 GB | **$2.19** |
| S3 Requests | 20K free | 1.5K | **$0.01** |
| Data Transfer | 100 GB free | 50 GB | **$0** |
| **TOTAL** | | | **~$6.14/month** |

---

## Troubleshooting

### Lambda Timeout Errors

- Increase timeout in Configuration → General configuration
- Check CloudWatch Logs for specific error

### "No module named 'pytube'" Error

- Deployment package missing dependencies
- Recreate ZIP with `pip install -t .`

### FFmpeg Not Found

- Add FFmpeg layer to function
- Check `FFMPEG_PATH` environment variable is `/opt/bin/ffmpeg`

### Step Functions Execution Failed

1. Open execution in Step Functions console
2. Click failed step
3. Check **Cause** and **Error** details
4. Go to CloudWatch Logs for that Lambda function

### Out of Memory Errors

- Increase Lambda memory in Configuration
- Reduce Whisper model size (`tiny` instead of `base`)

---

## Next Steps

1. **Optimize Costs**: Reduce Whisper model to `tiny` for faster/cheaper processing
2. **Add Monitoring**: Set up CloudWatch Alarms for failures
3. **Add Authentication**: Use API Gateway Authorizers
4. **Scale Up**: Increase concurrency limits in Lambda settings

---

## Support

For issues, check:
- CloudWatch Logs for each Lambda function
- Step Functions execution history
- S3 bucket contents

**Estimated Deployment Time**: 2-3 hours for first-time setup

**Congratulations! Your serverless video processing pipeline is ready! 🎉**
