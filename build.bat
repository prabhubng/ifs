@echo off
REM Build script for Windows

echo ===================================
echo Intelligent File Search - Builder
echo ===================================
echo.

:menu
echo Select build option:
echo 1) Install dependencies
echo 2) Build Windows executable
echo 3) Build installer (requires Inno Setup)
echo 4) Build portable version
echo 0) Exit
echo.
set /p option="Enter option: "

if "%option%"=="1" goto install_deps
if "%option%"=="2" goto build_exe
if "%option%"=="3" goto build_installer
if "%option%"=="4" goto build_portable
if "%option%"=="0" goto exit
goto menu

:install_deps
echo Installing dependencies...
pip install -r requirements.txt
echo Dependencies installed.
pause
goto menu

:build_exe
echo Building Windows executable...
pip install pyinstaller
pyinstaller --clean --onefile --windowed --name "FileSearch" main.py
echo.
echo Executable created in dist\FileSearch.exe
pause
goto menu

:build_installer
echo Building Windows installer...
pip install pyinstaller
pyinstaller --clean --onefile --windowed --name "FileSearch" main.py

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo Installer created in installer\FileSearch-Setup-Windows.exe
) else (
    echo ERROR: Inno Setup not found.
    echo Download from: https://jrsoftware.org/isdl.php
)
pause
goto menu

:build_portable
echo Building portable version...
pip install pyinstaller
pyinstaller --clean --onedir --windowed --name "FileSearch" main.py
echo.
echo Portable version created in dist\FileSearch\
echo Copy the entire folder to any location to use.
pause
goto menu

:exit
echo Exiting...
exit /b 0
