@echo off
REM ============================================================================
REM Build and Push opus-transcribe to Amazon ECR
REM This script builds a Docker container and pushes it to ECR for Lambda
REM ============================================================================

echo.
echo ============================================================================
echo Building and Pushing opus-transcribe to Amazon ECR
echo ============================================================================
echo.

REM Check if required environment variables are set
if "%AWS_REGION%"=="" (
    echo ERROR: AWS_REGION environment variable is not set
    echo Please set it: set AWS_REGION=us-east-1
    exit /b 1
)

if "%AWS_ACCOUNT_ID%"=="" (
    echo ERROR: AWS_ACCOUNT_ID environment variable is not set
    echo Please set it: set AWS_ACCOUNT_ID=123456789012
    exit /b 1
)

REM Configuration
set IMAGE_NAME=opus-transcribe
set WHISPER_MODEL=base
set ECR_REGISTRY=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
set ECR_REPO=%ECR_REGISTRY%/%IMAGE_NAME%

echo AWS Region: %AWS_REGION%
echo AWS Account ID: %AWS_ACCOUNT_ID%
echo ECR Registry: %ECR_REGISTRY%
echo Image Name: %IMAGE_NAME%
echo Whisper Model: %WHISPER_MODEL%
echo.

REM Step 1: Create ECR repository if it doesn't exist
echo [1/5] Creating ECR repository (if not exists)...
aws ecr describe-repositories --repository-names %IMAGE_NAME% --region %AWS_REGION% >nul 2>&1
if errorlevel 1 (
    echo Creating new ECR repository: %IMAGE_NAME%
    aws ecr create-repository --repository-name %IMAGE_NAME% --region %AWS_REGION%
    if errorlevel 1 (
        echo ERROR: Failed to create ECR repository
        exit /b 1
    )
) else (
    echo Repository already exists: %IMAGE_NAME%
)
echo.

REM Step 2: Authenticate Docker to ECR
echo [2/5] Authenticating Docker with ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_REGISTRY%
if errorlevel 1 (
    echo ERROR: Failed to authenticate with ECR
    echo Make sure AWS CLI is configured: aws configure
    exit /b 1
)
echo.

REM Step 3: Build Docker image
echo [3/5] Building Docker image...
echo This may take 10-15 minutes (downloads Whisper model)...
docker build -f Dockerfile.transcribe -t %IMAGE_NAME%:latest --build-arg WHISPER_MODEL=%WHISPER_MODEL% .
if errorlevel 1 (
    echo ERROR: Docker build failed
    exit /b 1
)
echo.

REM Step 4: Tag image for ECR
echo [4/5] Tagging image for ECR...
docker tag %IMAGE_NAME%:latest %ECR_REPO%:latest
if errorlevel 1 (
    echo ERROR: Failed to tag image
    exit /b 1
)
echo.

REM Step 5: Push to ECR
echo [5/5] Pushing image to ECR...
echo This may take 5-10 minutes (uploading ~2-3 GB)...
docker push %ECR_REPO%:latest
if errorlevel 1 (
    echo ERROR: Failed to push image to ECR
    exit /b 1
)
echo.

REM Display success message
echo ============================================================================
echo SUCCESS! Image pushed to ECR
echo ============================================================================
echo.
echo ECR Image URI: %ECR_REPO%:latest
echo.
echo NEXT STEPS:
echo 1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/
echo 2. Create new function "opus-transcribe" or update existing
echo 3. Select "Container image" as package type
echo 4. Use image URI: %ECR_REPO%:latest
echo 5. Set memory to 10 GB and timeout to 10 minutes
echo 6. Add environment variable:
echo    - BUCKET_NAME = your-s3-bucket-name
echo    - WHISPER_MODEL = %WHISPER_MODEL%
echo.
echo Image size: ~2-3 GB (includes Whisper model)
echo Cold start: ~10-20 seconds
echo Warm start: ~1-2 seconds
echo.
echo ============================================================================
