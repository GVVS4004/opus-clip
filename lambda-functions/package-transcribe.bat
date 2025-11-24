@echo off
echo ========================================
echo Packaging opus-transcribe only
echo ========================================
echo WARNING: Large download (~1.5 GB)
echo This will take 10-15 minutes!
echo.
pause
echo.

REM Clean up
rmdir /s /q deploy-transcribe 2>nul
del opus-transcribe.zip 2>nul

REM Create directory
mkdir deploy-transcribe
cd deploy-transcribe

echo Copying source file...
copy ..\2-lambda-transcribe.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file!
    cd ..
    pause
    exit /b 1
)

echo Installing Whisper (this will take several minutes)...
python -m pip install --target . openai-whisper==20231117 boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    echo Try: python -m pip install --upgrade pip
    cd ..
    pause
    exit /b 1
)

echo Cleaning up unnecessary files...
del /s /q *.pyc 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Creating ZIP (this will take a few minutes)...
python -c "import shutil; print('Compressing...'); shutil.make_archive('../opus-transcribe', 'zip', '.'); print('Done!')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP!
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ✓ opus-transcribe.zip created successfully!
echo NOTE: This file is too large for direct Lambda upload.
echo You MUST upload it to S3 first!
dir opus-transcribe.zip
echo.
pause
