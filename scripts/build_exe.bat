@echo off
echo Building Route Manager executable...

cd /d "%~dp0.."
rem Change to project root directory (parent of scripts folder)

echo Attempting to close any running instances...
taskkill /F /IM RouteManager.exe >nul 2>&1
timeout /T 2 >nul

echo Cleaning previous builds...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1

echo Building executable with PyInstaller...
pyinstaller --onefile --windowed --name "RouteManager" --icon="icon/route_manager.ico" route_manager.py

if exist "dist\RouteManager.exe" (
    echo.
    echo Build successful!
    echo Executable created: dist\RouteManager.exe
    echo Size:
    dir "dist\RouteManager.exe" | find "RouteManager.exe"

    echo.
    echo Cleaning up build artifacts...
    rmdir /s /q build >nul 2>&1
    if exist *.spec del *.spec >nul 2>&1

    echo.
    echo Build complete! You can find the executable in the dist/ folder.
    echo.
    echo Testing the executable...
    start "" "dist\RouteManager.exe"
) else (
    echo.
    echo Build failed! Please check the error messages above.
)

echo.
pause