#!/bin/bash
# Build script for creating platform-specific executables

echo "==================================="
echo "Intelligent File Search - Builder"
echo "==================================="

# Detect OS
OS=$(uname -s)

# Function to build Windows executable
build_windows() {
    echo "Building Windows executable..."
    pip install pyinstaller
    pyinstaller --clean --onefile --windowed \
        --name "FileSearch" \
        --icon=icon.ico \
        --add-data "README.md:." \
        main.py
    
    echo "Windows executable created in dist/FileSearch.exe"
    
    # Optional: Create installer with Inno Setup (Windows only)
    if command -v iscc &> /dev/null; then
        echo "Creating Windows installer..."
        iscc installer.iss
        echo "Installer created in installer/FileSearch-Setup-Windows.exe"
    else
        echo "Inno Setup not found. Skipping installer creation."
        echo "Download from: https://jrsoftware.org/isdl.php"
    fi
}

# Function to build macOS app
build_macos() {
    echo "Building macOS application..."
    pip install pyinstaller
    pyinstaller --clean --onefile --windowed \
        --name "FileSearch" \
        --icon=icon.icns \
        --add-data "README.md:." \
        --osx-bundle-identifier "com.filesearch.app" \
        main.py
    
    echo "macOS app created in dist/FileSearch.app"
    
    # Create DMG (requires create-dmg)
    if command -v create-dmg &> /dev/null; then
        echo "Creating DMG..."
        create-dmg \
            --volname "Intelligent File Search" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --app-drop-link 450 150 \
            "FileSearch-Installer.dmg" \
            "dist/FileSearch.app"
        echo "DMG created: FileSearch-Installer.dmg"
    else
        echo "create-dmg not found. Skipping DMG creation."
        echo "Install with: brew install create-dmg"
    fi
}

# Function to build Linux executable
build_linux() {
    echo "Building Linux executable..."
    pip install pyinstaller
    pyinstaller --clean --onefile \
        --name "file-search" \
        --add-data "README.md:." \
        main.py
    
    echo "Linux executable created in dist/file-search"
    
    # Make it executable
    chmod +x dist/file-search
    
    # Optional: Create AppImage (requires appimagetool)
    if command -v appimagetool &> /dev/null; then
        echo "Creating AppImage..."
        mkdir -p AppDir/usr/bin
        mkdir -p AppDir/usr/share/applications
        mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
        
        cp dist/file-search AppDir/usr/bin/
        
        cat > AppDir/usr/share/applications/file-search.desktop <<EOF
[Desktop Entry]
Name=Intelligent File Search
Exec=file-search
Icon=file-search
Type=Application
Categories=Utility;FileTools;
EOF
        
        # Copy icon if available
        if [ -f "icon.png" ]; then
            cp icon.png AppDir/usr/share/icons/hicolor/256x256/apps/file-search.png
        fi
        
        appimagetool AppDir FileSearch-x86_64.AppImage
        echo "AppImage created: FileSearch-x86_64.AppImage"
    else
        echo "appimagetool not found. Skipping AppImage creation."
    fi
}

# Function to install dependencies
install_deps() {
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed."
}

# Main menu
echo ""
echo "Select build option:"
echo "1) Install dependencies"
echo "2) Build for current platform"
echo "3) Build for Windows"
echo "4) Build for macOS"
echo "5) Build for Linux"
echo "6) Build all platforms (if possible)"
echo "0) Exit"
echo ""
read -p "Enter option: " option

case $option in
    1)
        install_deps
        ;;
    2)
        case $OS in
            Linux*)
                build_linux
                ;;
            Darwin*)
                build_macos
                ;;
            MINGW*|MSYS*|CYGWIN*)
                build_windows
                ;;
            *)
                echo "Unknown OS: $OS"
                ;;
        esac
        ;;
    3)
        build_windows
        ;;
    4)
        build_macos
        ;;
    5)
        build_linux
        ;;
    6)
        echo "Building for all platforms..."
        build_windows
        build_macos
        build_linux
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Build complete!"
