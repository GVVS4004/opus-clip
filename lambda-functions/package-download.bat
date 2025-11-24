@echo off
echo ========================================
echo Packaging opus-download only
echo ========================================
echo.

REM Clean up
rmdir /s /q deploy-download 2>nul
del opus-download.zip 2>nul

REM Create directory
mkdir deploy-download
cd deploy-download

echo Copying source file...
copy ..\1-lambda-download.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file!
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies (pytubefix, boto3)...
python -m pip install --target . pytubefix boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP...
python -c "import shutil; shutil.make_archive('../opus-download', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP!
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ✓ opus-download.zip created successfully!
dir opus-download.zip
echo.
pause
