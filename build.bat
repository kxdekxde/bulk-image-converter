@echo off
setlocal enabledelayedexpansion

:: Configuration
set SCRIPT_NAME=script.py
set OUTPUT_NAME=BulkImageConverter
set ICON_NAME=icon.ico

:: Colors for better visibility
set "RED="
set "GREEN="
set "YELLOW="
set "RESET="

:: Check if PyInstaller is installed
echo [1/5] Checking PyInstaller installation...
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INSTALL] Installing PyInstaller...
    pip install pyinstaller
)

:: Initialize build
echo [2/5] Starting PyInstaller build process...
echo    Input script: %SCRIPT_NAME%
echo    Output name: %OUTPUT_NAME%
echo    Icon file: %ICON_NAME%
echo.

:: Run PyInstaller with visible output
echo [3/5] Analyzing dependencies and building executable...
echo -----------------------------------------------
pyinstaller ^
    --name="%OUTPUT_NAME%" ^
    --onefile ^
    --icon="%ICON_NAME%" ^
    --add-data="%ICON_NAME%;." ^
    --log-level=INFO ^
    "%SCRIPT_NAME%"
echo -----------------------------------------------

:: Check build status
if %ERRORLEVEL% equ 0 (
    echo [4/5] Build completed successfully!
    echo.
    echo [5/5] Finalizing...
    echo    Executable created at: %cd%\dist\%OUTPUT_NAME%.exe
    echo    Size: %~z0
    echo.
    echo BUILD SUCCESSFUL
) else (
    echo [ERROR] Build failed at stage 3 with error %ERRORLEVEL%
    echo Check the PyInstaller output above for details
)

:: Cleanup
del /Q build\%OUTPUT_NAME%.spec >nul 2>&1
endlocal
pause