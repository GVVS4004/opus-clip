@echo off
echo ========================================
echo Packaging opus-api-gateway only
echo ========================================
echo.

REM Clean up
rmdir /s /q deploy-api 2>nul
del opus-api-gateway.zip 2>nul

REM Create directory
mkdir deploy-api
cd deploy-api

echo Copying source file...
copy ..\6-lambda-api-gateway.py lambda_function.py
if errorlevel 1 (
    echo ERROR: Failed to copy source file!
    cd ..
    pause
    exit /b 1
)

echo Installing dependencies (boto3)...
python -m pip install --target . boto3
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    cd ..
    pause
    exit /b 1
)

echo Creating ZIP...
python -c "import shutil; shutil.make_archive('../opus-api-gateway', 'zip', '.')"
if errorlevel 1 (
    echo ERROR: Failed to create ZIP!
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo ✓ opus-api-gateway.zip created successfully!
dir opus-api-gateway.zip
echo.
pause
