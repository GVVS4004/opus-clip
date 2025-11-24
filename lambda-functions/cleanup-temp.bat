@echo off
echo ========================================
echo Cleaning up temporary deployment folders
echo ========================================
echo.
echo This will delete:
echo   - deploy-download/
echo   - deploy-transcribe/
echo   - deploy-detect/
echo   - deploy-process/
echo   - deploy-finalize/
echo   - deploy-api/
echo.
echo The ZIP files will NOT be deleted.
echo.
pause

rmdir /s /q deploy-download 2>nul
rmdir /s /q deploy-transcribe 2>nul
rmdir /s /q deploy-detect 2>nul
rmdir /s /q deploy-process 2>nul
rmdir /s /q deploy-finalize 2>nul
rmdir /s /q deploy-api 2>nul

echo.
echo ✓ Cleanup complete!
echo.
pause
