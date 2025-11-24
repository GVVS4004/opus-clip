# Lambda Packaging Help Guide

## Problem: Some ZIP files not created

If you ran `package-lambda.bat` and only got 3 ZIP files (detect, process, finalize) but missing the others (download, transcribe, api-gateway), use these solutions:

---

## Solution 1: Use the Improved Script (Recommended)

Run the improved version with better error handling:

```cmd
package-lambda-v2.bat
```

This version:
- ✅ Shows detailed error messages
- ✅ Stops on errors instead of continuing
- ✅ Uses Python's shutil instead of PowerShell
- ✅ Cleans up old files first

---

## Solution 2: Package Functions Individually

If the all-in-one script still has issues, package each function separately:

### Package opus-download:
```cmd
package-download.bat
```

### Package opus-transcribe:
```cmd
package-transcribe.bat
```
**Note**: This takes 10-15 minutes and downloads ~1.5 GB!

### Package opus-api-gateway:
```cmd
package-api-gateway.bat
```

### The others should already work:
- `opus-detect.zip` ✓
- `opus-process-clip.zip` ✓
- `opus-finalize.zip` ✓

---

## Solution 3: Manual Packaging (If Scripts Fail)

### For opus-download:

```cmd
mkdir deploy-download
cd deploy-download
copy ..\1-lambda-download.py lambda_function.py
python -m pip install --target . pytubefix boto3
python -c "import shutil; shutil.make_archive('../opus-download', 'zip', '.')"
cd ..
```

### For opus-api-gateway:

```cmd
mkdir deploy-api
cd deploy-api
copy ..\6-lambda-api-gateway.py lambda_function.py
python -m pip install --target . boto3
python -c "import shutil; shutil.make_archive('../opus-api-gateway', 'zip', '.')"
cd ..
```

### For opus-transcribe:

```cmd
mkdir deploy-transcribe
cd deploy-transcribe
copy ..\2-lambda-transcribe.py lambda_function.py
python -m pip install --target . openai-whisper==20231117 boto3
python -c "import shutil; shutil.make_archive('../opus-transcribe', 'zip', '.')"
cd ..
```

---

## Common Issues & Fixes

### Issue 1: "Python is not recognized"

**Fix:** Add Python to PATH or use full path:
```cmd
C:\Python311\python.exe -m pip install ...
```

### Issue 2: "pip is not recognized"

**Fix:** Install/upgrade pip:
```cmd
python -m ensurepip
python -m pip install --upgrade pip
```

### Issue 3: PowerShell Compress-Archive fails silently

**Fix:** Use Python's shutil (already done in v2 script):
```cmd
python -c "import shutil; shutil.make_archive('opus-download', 'zip', '.')"
```

### Issue 4: "Permission denied" or "Access denied"

**Fix:** Run Command Prompt as Administrator
- Right-click Command Prompt
- Select "Run as administrator"
- Navigate to lambda-functions folder
- Run the script again

### Issue 5: pip install fails with SSL errors

**Fix:** Try with trusted host:
```cmd
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --target . pytubefix boto3
```

### Issue 6: opus-transcribe.zip is too large (>2 GB)

This is expected! The Whisper package is huge.

**Solutions:**

**Option A:** Use a smaller Whisper model
- Edit `2-lambda-transcribe.py`
- Change `MODEL_SIZE = os.environ.get('WHISPER_MODEL', 'base')`
- Set environment variable: `WHISPER_MODEL=tiny`

**Option B:** Upload to S3 (required for Lambda anyway)
1. Create your S3 bucket first
2. Upload the ZIP file to S3
3. When creating Lambda function, reference S3 URL

**Option C:** Use Lambda Container Images (advanced)
- Package as Docker container instead of ZIP
- Deploy as container image to Lambda

---

## Verify All ZIPs Created

After running the script, check for all 6 files:

```cmd
dir opus-*.zip
```

You should see:
```
opus-api-gateway.zip   (~15 MB)
opus-detect.zip        (~15 MB)
opus-download.zip      (~20 MB)
opus-finalize.zip      (~15 MB)
opus-process-clip.zip  (~15 MB)
opus-transcribe.zip    (~1.5-2 GB)  ⚠️ LARGE FILE
```

---

## Clean Up Temporary Folders

After successful packaging, clean up:

```cmd
cleanup-temp.bat
```

This deletes the `deploy-*` folders but keeps your ZIP files.

---

## Alternative: Use Linux/WSL

If Windows scripts keep failing, use WSL (Windows Subsystem for Linux):

```bash
# Open WSL/Ubuntu terminal
cd /mnt/c/Projects/opus-clip-cloud/lambda-functions

# Package each function
for func in download transcribe detect process finalize api; do
    mkdir -p deploy-$func
    cd deploy-$func

    # Copy appropriate source file
    cp ../[number]-lambda-*.py lambda_function.py

    # Install deps
    pip install -t . [dependencies]

    # Create ZIP
    zip -r ../opus-$func.zip .

    cd ..
done
```

---

## Still Having Issues?

### Check Your Environment:

```cmd
python --version
python -m pip --version
python -c "import shutil; print('shutil OK')"
```

All should work without errors.

### Test a Simple ZIP:

```cmd
mkdir test-zip
cd test-zip
echo test > test.txt
python -c "import shutil; shutil.make_archive('../test', 'zip', '.')"
cd ..
```

If `test.zip` is created, your environment is working.

### Get Detailed Errors:

Remove the `2>nul` and `>nul` redirects to see error messages:

Edit the batch file and remove all instances of:
- `>nul`
- `2>nul`
- `-q` flag from pip

Then run again to see full error output.

---

## Summary of Available Scripts

| Script | Purpose |
|--------|---------|
| `package-lambda.bat` | Original script (may have issues) |
| `package-lambda-v2.bat` | ✅ **Improved script - USE THIS** |
| `package-download.bat` | Package only opus-download |
| `package-transcribe.bat` | Package only opus-transcribe |
| `package-api-gateway.bat` | Package only opus-api-gateway |
| `cleanup-temp.bat` | Remove temporary folders |

---

## Next Steps After Packaging

1. ✅ Verify all 6 ZIP files exist
2. 📤 Upload `opus-transcribe.zip` to S3 bucket
3. 📋 Follow QUICK-START.md for deployment
4. 🧹 Run `cleanup-temp.bat` to clean up

---

Need more help? Check the error messages and match them to the "Common Issues" section above.
