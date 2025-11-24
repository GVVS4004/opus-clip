@echo off
REM =====================================================
REM AWS Lambda Packaging Script v2 - Improved
REM Creates deployment packages for all Lambda functions
REM =====================================================

echo ========================================
echo Opus Clip Lambda Packaging Script v2
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
python --version
echo.

REM Clean up old deployment directories and ZIPs
echo Cleaning up old files...
rmdir /s /q deploy-download 2>nul
rmdir /s /q deploy-transcribe 2>nul
rmdir /s /q deploy-detect 2>nul
rmdir /s /q deploy-process 2>nul
rmdir /s /q deploy-finalize 2>nul
rmdir /s /q deploy-api 2>nul
del opus-download.zip 2>nul
del opus-transcribe.zip 2>nul
del opus-detect.zip 2>nul
del opus-process-clip.zip 2>nul
del opus-finalize.zip 2>nul
del opus-api-gateway.zip 2>nul
echo Done!
echo.

REM =====================================================
REM Lambda 1: opus-download
REM =====================================================
echo ========================================
echo [1/6] Packaging opus-download...
echo ========================================
mkdir deploy-download
cd deploy-download

echo Copying source file...
copy ..\1-lambda-download.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies (pytubefix, boto3)...
python -m pip install --quiet --target . pytubefix boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP file...
python -c "import shutil; shutil.make_archive('../opus-download', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-download.zip created successfully!
dir opus-download.zip
echo.

REM =====================================================
REM Lambda 2: opus-transcribe
REM =====================================================
echo ========================================
echo [2/6] Packaging opus-transcribe...
echo ========================================
echo WARNING: This package is very large (~1.5-2 GB)
echo This will take 10-15 minutes...
echo.
mkdir deploy-transcribe
cd deploy-transcribe

echo Copying source file...
copy ..\2-lambda-transcribe.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing Whisper (this will take a while)...
echo Please wait...
python -m pip install --target . openai-whisper==20231117 boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running: pip install --upgrade pip
    cd ..
    pause
    exit /b 1
)

echo Removing unnecessary files to reduce size...
del /s /q *.pyc 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r %%d in (*.dist-info) do @if exist "%%d" rd /s /q "%%d"
for /d /r %%d in (tests) do @if exist "%%d" rd /s /q "%%d"

echo Creating ZIP file (this will take a few minutes)...
echo Please be patient...
python -c "import shutil; shutil.make_archive('../opus-transcribe', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-transcribe.zip created successfully!
echo NOTE: This file is too large for direct Lambda upload
echo You must upload it to S3 first!
dir opus-transcribe.zip
echo.

REM =====================================================
REM Lambda 3: opus-detect
REM =====================================================
echo ========================================
echo [3/6] Packaging opus-detect...
echo ========================================
mkdir deploy-detect
cd deploy-detect

echo Copying source file...
copy ..\3-lambda-detect-clips.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --quiet --target . boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP file...
python -c "import shutil; shutil.make_archive('../opus-detect', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-detect.zip created successfully!
dir opus-detect.zip
echo.

REM =====================================================
REM Lambda 4: opus-process-clip
REM =====================================================
echo ========================================
echo [4/6] Packaging opus-process-clip...
echo ========================================
mkdir deploy-process
cd deploy-process

echo Copying source file...
copy ..\4-lambda-process-clip.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --quiet --target . boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP file...
python -c "import shutil; shutil.make_archive('../opus-process-clip', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-process-clip.zip created successfully!
dir opus-process-clip.zip
echo.

REM =====================================================
REM Lambda 5: opus-finalize
REM =====================================================
echo ========================================
echo [5/6] Packaging opus-finalize...
echo ========================================
mkdir deploy-finalize
cd deploy-finalize

echo Copying source file...
copy ..\5-lambda-finalize.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --quiet --target . boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP file...
python -c "import shutil; shutil.make_archive('../opus-finalize', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-finalize.zip created successfully!
dir opus-finalize.zip
echo.

REM =====================================================
REM Lambda 6: opus-api-gateway
REM =====================================================
echo ========================================
echo [6/6] Packaging opus-api-gateway...
echo ========================================
mkdir deploy-api
cd deploy-api

echo Copying source file...
copy ..\6-lambda-api-gateway.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --quiet --target . boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP file...
python -c "import shutil; shutil.make_archive('../opus-api-gateway', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP
    cd ..
    pause
    exit /b 1
)

cd ..
echo ✓ opus-api-gateway.zip created successfully!
dir opus-api-gateway.zip
echo.

REM =====================================================
REM Summary
REM =====================================================
echo ========================================
echo Packaging Complete!
echo ========================================
echo.
echo Created deployment packages:
dir opus-*.zip
echo.
echo IMPORTANT NOTES:
echo ================
echo 1. opus-transcribe.zip is too large for direct Lambda upload
echo    - Upload it to your S3 bucket first
echo    - Then reference the S3 URL when creating the Lambda function
echo.
echo 2. All other ZIPs can be uploaded directly via Lambda console
echo.
echo 3. Next steps:
echo    - Follow QUICK-START.md or README-DEPLOYMENT.md
echo    - Upload opus-transcribe.zip to S3
echo    - Upload other ZIPs directly to Lambda
echo.
echo 4. If you want to clean up temporary folders:
echo    - Run: cleanup-temp.bat
echo.
pause
