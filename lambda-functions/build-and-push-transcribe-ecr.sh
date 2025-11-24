#!/bin/bash
# ============================================================================
# Build and Push opus-transcribe to Amazon ECR
# This script builds a Docker container and pushes it to ECR for Lambda
# ============================================================================

set -e  # Exit on error

echo ""
echo "============================================================================"
echo "Building and Pushing opus-transcribe to Amazon ECR"
echo "============================================================================"
echo ""

# Check if required environment variables are set
if [ -z "$AWS_REGION" ]; then
    echo "ERROR: AWS_REGION environment variable is not set"
    echo "Please set it: export AWS_REGION=us-east-1"
    exit 1
fi

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "ERROR: AWS_ACCOUNT_ID environment variable is not set"
    echo "Please set it: export AWS_ACCOUNT_ID=123456789012"
    exit 1
fi

# Configuration
IMAGE_NAME="opus-transcribe"
WHISPER_MODEL="${WHISPER_MODEL:-base}"  # Default to 'base' if not set
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPO="${ECR_REGISTRY}/${IMAGE_NAME}"

echo "AWS Region: $AWS_REGION"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR Registry: $ECR_REGISTRY"
echo "Image Name: $IMAGE_NAME"
echo "Whisper Model: $WHISPER_MODEL"
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo "[1/5] Creating ECR repository (if not exists)..."
if ! aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo "Creating new ECR repository: $IMAGE_NAME"
    aws ecr create-repository --repository-name "$IMAGE_NAME" --region "$AWS_REGION"
else
    echo "Repository already exists: $IMAGE_NAME"
fi
echo ""

# Step 2: Authenticate Docker to ECR
echo "[2/5] Authenticating Docker with ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
echo ""

# Step 3: Build Docker image
echo "[3/5] Building Docker image..."
echo "This may take 10-15 minutes (downloads Whisper model)..."
docker build -f Dockerfile.transcribe -t "$IMAGE_NAME:latest" --build-arg WHISPER_MODEL="$WHISPER_MODEL" .
echo ""

# Step 4: Tag image for ECR
echo "[4/5] Tagging image for ECR..."
docker tag "$IMAGE_NAME:latest" "$ECR_REPO:latest"
echo ""

# Step 5: Push to ECR
echo "[5/5] Pushing image to ECR..."
echo "This may take 5-10 minutes (uploading ~2-3 GB)..."
docker push "$ECR_REPO:latest"
echo ""

# Display success message
cat << EOF
============================================================================
SUCCESS! Image pushed to ECR
============================================================================

ECR Image URI: $ECR_REPO:latest

NEXT STEPS:
1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/
2. Create new function "opus-transcribe" or update existing
3. Select "Container image" as package type
4. Use image URI: $ECR_REPO:latest
5. Set memory to 10 GB and timeout to 10 minutes
6. Add environment variable:
   - BUCKET_NAME = your-s3-bucket-name
   - WHISPER_MODEL = $WHISPER_MODEL

Image size: ~2-3 GB (includes Whisper model)
Cold start: ~10-20 seconds
Warm start: ~1-2 seconds

============================================================================
EOF
