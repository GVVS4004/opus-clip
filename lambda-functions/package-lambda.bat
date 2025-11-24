@echo off
REM =====================================================
REM AWS Lambda Packaging Script for Windows
REM Creates deployment packages for all Lambda functions
REM =====================================================

echo ========================================
echo Opus Clip Lambda Packaging Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 and try again
    pause
    exit /b 1
)

echo Python found!
echo.

REM Create deployment directories
echo Creating deployment directories...
mkdir deploy-download 2>nul
mkdir deploy-transcribe 2>nul
mkdir deploy-detect 2>nul
mkdir deploy-process 2>nul
mkdir deploy-finalize 2>nul
mkdir deploy-api 2>nul
echo Done!
echo.

REM =====================================================
REM Lambda 1: opus-download
REM =====================================================
echo [1/6] Packaging opus-download...
cd deploy-download
copy ..\1-lambda-download.py lambda_function.py >nul
echo Installing dependencies...
pip install -q -t . pytubefix boto3
echo Creating ZIP...
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-download.zip -Force"
cd ..
echo ✓ opus-download.zip created
echo.

REM =====================================================
REM Lambda 2: opus-transcribe
REM =====================================================
echo [2/6] Packaging opus-transcribe...
echo WARNING: This will download ~2.5 GB of dependencies!
echo This may take 10-15 minutes...
cd deploy-transcribe
copy ..\2-lambda-transcribe.py lambda_function.py >nul
echo Installing Whisper and dependencies...
pip install -q -t . openai-whisper boto3 numpy
echo Creating ZIP (this will be large, ~1.5-2 GB)...
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-transcribe.zip -Force"
cd ..
echo ✓ opus-transcribe.zip created (NOTE: Upload to S3 first!)
echo.

REM =====================================================
REM Lambda 3: opus-detect
REM =====================================================
echo [3/6] Packaging opus-detect...
cd deploy-detect
copy ..\3-lambda-detect-clips.py lambda_function.py >nul
pip install -q -t . boto3
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-detect.zip -Force"
cd ..
echo ✓ opus-detect.zip created
echo.

REM =====================================================
REM Lambda 4: opus-process-clip
REM =====================================================
echo [4/6] Packaging opus-process-clip...
cd deploy-process
copy ..\4-lambda-process-clip.py lambda_function.py >nul
pip install -q -t . boto3
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-process-clip.zip -Force"
cd ..
echo ✓ opus-process-clip.zip created
echo.

REM =====================================================
REM Lambda 5: opus-finalize
REM =====================================================
echo [5/6] Packaging opus-finalize...
cd deploy-finalize
copy ..\5-lambda-finalize.py lambda_function.py >nul
pip install -q -t . boto3
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-finalize.zip -Force"
cd ..
echo ✓ opus-finalize.zip created
echo.

REM =====================================================
REM Lambda 6: opus-api-gateway
REM =====================================================
echo [6/6] Packaging opus-api-gateway...
cd deploy-api
copy ..\6-lambda-api-gateway.py lambda_function.py >nul
pip install -q -t . boto3
powershell -command "Compress-Archive -Path * -DestinationPath ..\opus-api-gateway.zip -Force"
cd ..
echo ✓ opus-api-gateway.zip created
echo.

echo ========================================
echo Packaging Complete!
echo ========================================
echo.
echo Created deployment packages:
echo   1. opus-download.zip        (~20 MB)
echo   2. opus-transcribe.zip      (~1.8 GB) - UPLOAD TO S3 FIRST!
echo   3. opus-detect.zip          (~15 MB)
echo   4. opus-process-clip.zip    (~15 MB)
echo   5. opus-finalize.zip        (~15 MB)
echo   6. opus-api-gateway.zip     (~15 MB)
echo.
echo IMPORTANT:
echo   - opus-transcribe.zip is too large for direct Lambda upload
echo   - Upload it to S3 first, then reference the S3 URL in Lambda
echo.
echo Next steps:
echo   1. Follow README-DEPLOYMENT.md
echo   2. Upload opus-transcribe.zip to your S3 bucket
echo   3. Upload other ZIPs directly via Lambda console
echo.
pause
