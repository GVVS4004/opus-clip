# Quick Start Guide - Deploy in 30 Minutes

This is a simplified guide to get you up and running quickly.

## ⚡ Fast Track Deployment

### Step 1: Package Lambda Functions (5 minutes)

**On Windows:**
```cmd
cd lambda-functions
package-lambda.bat
```

This creates 6 ZIP files ready for upload.

### Step 2: AWS Setup (25 minutes)

#### 2.1 Create S3 Bucket (2 min)
1. Go to S3: https://s3.console.aws.amazon.com/
2. Create bucket: `opus-clip-videos-YOURNAME`
3. Keep all defaults
4. Upload `opus-transcribe.zip` to this bucket

#### 2.2 Create IAM Role (3 min)
1. Go to IAM: https://console.aws.amazon.com/iam/
2. Create role → Lambda → Name: `opus-clip-lambda-role`
3. Attach policy: `AWSLambdaBasicExecutionRole`
4. Add inline policy (JSON):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": "arn:aws:s3:::opus-clip-videos-YOURNAME/*"
        },
        {
            "Effect": "Allow",
            "Action": ["states:*", "lambda:*"],
            "Resource": "*"
        }
    ]
}
```

#### 2.3 Create Lambda Functions (10 min)

**For each function (1-6):**

1. Lambda Console → Create function
2. Runtime: Python 3.11
3. Role: `opus-clip-lambda-role`
4. Upload ZIP (or S3 URL for transcribe)
5. Set environment variable: `BUCKET_NAME` = your bucket name

**Function Settings:**

| Function | Name | Memory | Timeout | Handler |
|----------|------|--------|---------|---------|
| 1 | opus-download | 3 GB | 5 min | lambda_function.lambda_handler |
| 2 | opus-transcribe | 10 GB | 10 min | lambda_function.lambda_handler |
| 3 | opus-detect | 2 GB | 1 min | lambda_function.lambda_handler |
| 4 | opus-process-clip | 4 GB | 5 min | lambda_function.lambda_handler |
| 5 | opus-finalize | 512 MB | 30 sec | lambda_function.lambda_handler |
| 6 | opus-api-gateway | 512 MB | 30 sec | lambda_function.lambda_handler |

**Additional env vars for specific functions:**
- opus-transcribe: `WHISPER_MODEL=base`
- opus-detect: `NUM_CLIPS=3`
- opus-process-clip: `FFMPEG_PATH=/opt/bin/ffmpeg`

#### 2.4 Create Step Functions (5 min)

1. Step Functions Console: https://console.aws.amazon.com/states/
2. Create state machine → Standard
3. Paste content from `step-functions-state-machine.json`
4. **Replace** `REGION` and `ACCOUNT_ID` in the JSON
5. Name: `opus-clip-state-machine`
6. Use existing role: `opus-clip-lambda-role`
7. Copy the State Machine ARN

#### 2.5 Update API Lambda (1 min)

1. Go to `opus-api-gateway` Lambda
2. Add environment variable:
   - `STATE_MACHINE_ARN` = (paste ARN from step 2.4)

#### 2.6 Create API Gateway (4 min)

1. API Gateway: https://console.aws.amazon.com/apigateway/
2. Create HTTP API → Name: `opus-clip-api`
3. Add routes:
   - POST `/process` → Integration: opus-api-gateway
   - GET `/status/{session_id}` → Integration: opus-api-gateway
   - GET `/result/{session_id}` → Integration: opus-api-gateway
4. Enable CORS: Allow Origin = `*`
5. Copy API endpoint URL

---

## 🧪 Test Your Deployment

### Test 1: API Endpoint (cURL)

```bash
# Replace YOUR_API_URL with your API Gateway endpoint
curl -X POST https://YOUR_API_URL/process \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# You'll get: {"session_id":"abc-123","status":"processing"}

# Check status
curl https://YOUR_API_URL/status/abc-123

# Get result (after 10-15 min)
curl https://YOUR_API_URL/result/abc-123
```

### Test 2: Step Functions Console

1. Go to your state machine
2. Click "Start execution"
3. Input:
```json
{
  "session_id": "test-123",
  "youtube_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"
}
```
4. Watch the workflow execute
5. Check S3 bucket for output videos in `test-123/clips/`

---

## 💰 Expected Costs

**For 100 videos/month (15 min avg):**
- Lambda: ~$4
- S3: ~$2
- Step Functions: Free
- **Total: ~$6/month**

**First 12 months with AWS Free Tier:**
- Lambda: FREE (1M requests, 400K GB-sec)
- S3: FREE (5 GB storage, 20K requests)
- **Total: $0-2/month**

---

## 🐛 Troubleshooting

### "Internal Server Error"
- Check CloudWatch Logs for the failing Lambda
- Most common: Missing environment variables

### "Timeout"
- Increase Lambda timeout in Configuration
- For transcribe: Use `WHISPER_MODEL=tiny` instead of `base`

### "No module named 'pytubefix'"
- Deployment package missing dependencies
- Run `package-lambda.bat` again

### Videos not appearing in S3
- Check Step Functions execution status
- Look for failed steps
- Check Lambda CloudWatch logs

---

## 📱 Connect Your UI

Your API endpoints:

```
POST https://YOUR_API_URL/process
Body: {"youtube_url": "..."}
Returns: {"session_id": "..."}

GET https://YOUR_API_URL/status/{session_id}
Returns: {"status": "processing|completed|failed"}

GET https://YOUR_API_URL/result/{session_id}
Returns: {"clips": [{"download_url": "..."}]}
```

### Example JavaScript Integration:

```javascript
// Start processing
const response = await fetch('https://YOUR_API_URL/process', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({youtube_url: 'https://...'})
});
const {session_id} = await response.json();

// Poll for status
const checkStatus = async () => {
  const status = await fetch(`https://YOUR_API_URL/status/${session_id}`);
  const data = await status.json();

  if (data.status === 'completed') {
    const result = await fetch(`https://YOUR_API_URL/result/${session_id}`);
    const clips = await result.json();

    // Download URLs are in clips.clips[].download_url
    console.log(clips);
  } else {
    setTimeout(checkStatus, 5000); // Check every 5 seconds
  }
};

checkStatus();
```

---

## 🎉 You're Done!

Your serverless video processing pipeline is live!

- Processing time: ~10-15 minutes per 15-minute video
- Parallel clip processing: 3-5x faster than sequential
- Auto-scales to handle traffic spikes
- Costs only when processing (scale-to-zero)

**Next Steps:**
- Add authentication to API Gateway
- Set up CloudWatch alarms
- Optimize Whisper model size for your needs

Need help? Check the full guide in `README-DEPLOYMENT.md`
