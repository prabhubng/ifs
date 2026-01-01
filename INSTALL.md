# Platform-Specific Installation Guide

## Quick Start

Choose your operating system below for detailed installation instructions.

---

## Windows Installation

### Method 1: Using Pre-built Executable (Recommended)

1. **Download** the latest release from the releases page
2. **Run** `FileSearch-Setup-Windows.exe`
3. **Follow** the installation wizard
4. **Launch** from Start Menu or Desktop shortcut

### Method 2: From Source

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Download Source Code**
   ```cmd
   git clone https://github.com/yourusername/intelligent-file-search.git
   cd intelligent-file-search
   ```

3. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run Application**
   ```cmd
   python main.py
   ```

### Method 3: Build Executable Yourself

```cmd
# Install PyInstaller
pip install pyinstaller

# Build executable
build.bat
# Choose option 2 for executable or option 3 for installer
```

---

## macOS Installation

### Method 1: Using DMG (Recommended)

1. **Download** `FileSearch-Installer.dmg` from releases
2. **Open** the DMG file
3. **Drag** FileSearch.app to Applications folder
4. **Launch** from Applications or Spotlight

**First Launch Note**: macOS may show "FileSearch cannot be opened because it is from an unidentified developer"
- **Solution**: Right-click the app → Open → Click "Open" in the dialog

### Method 2: From Source

1. **Install Python 3.8+**
   ```bash
   # Using Homebrew
   brew install python@3.11
   
   # Or download from python.org
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/intelligent-file-search.git
   cd intelligent-file-search
   ```

3. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Run Application**
   ```bash
   python3 main.py
   ```

### Method 3: Build App Bundle

```bash
# Install build tools
pip3 install pyinstaller

# Run build script
chmod +x build.sh
./build.sh
# Choose option 4 for macOS build
```

---

## Linux Installation

### Method 1: Using AppImage (Ubuntu, Debian, Fedora, Arch)

1. **Download** `FileSearch-x86_64.AppImage` from releases

2. **Make Executable**
   ```bash
   chmod +x FileSearch-x86_64.AppImage
   ```

3. **Run**
   ```bash
   ./FileSearch-x86_64.AppImage
   ```

4. **Optional: Desktop Integration**
   ```bash
   # Copy to applications
   cp FileSearch-x86_64.AppImage ~/.local/bin/file-search
   
   # Install desktop entry
   cp file-search.desktop ~/.local/share/applications/
   ```

### Method 2: From Source (All Distributions)

#### Ubuntu/Debian
```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-tk git

# Clone repository
git clone https://github.com/yourusername/intelligent-file-search.git
cd intelligent-file-search

# Install Python packages
pip3 install -r requirements.txt

# Run application
python3 main.py
```

#### Fedora
```bash
# Install dependencies
sudo dnf install python3 python3-pip python3-tkinter git

# Clone and run
git clone https://github.com/yourusername/intelligent-file-search.git
cd intelligent-file-search
pip3 install -r requirements.txt
python3 main.py
```

#### Arch Linux
```bash
# Install dependencies
sudo pacman -S python python-pip tk git

# Clone and run
git clone https://github.com/yourusername/intelligent-file-search.git
cd intelligent-file-search
pip3 install -r requirements.txt
python3 main.py
```

### Method 3: System-wide Installation

```bash
# Clone repository
git clone https://github.com/yourusername/intelligent-file-search.git
cd intelligent-file-search

# Install system-wide
sudo pip3 install -e .

# Install desktop entry
sudo cp file-search.desktop /usr/share/applications/

# Run from anywhere
file-search
```

---

## Verification

After installation, verify the application works:

1. **Launch** the application
2. **Click** "Browse" and select a test directory
3. **Click** "Index" and wait for completion
4. **Try** searching for a known file
5. **Double-click** a result to open the file

If you see the file list populate, installation was successful!

---

## Troubleshooting

### Windows

**"Python not found"**
- Reinstall Python and check "Add to PATH"
- Or use pre-built executable (Method 1)

**"Module not found"**
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### macOS

**"tkinter not found"**
```bash
brew install python-tk@3.11
```

**"Permission denied"**
- Grant terminal access in System Preferences → Security & Privacy

### Linux

**"tkinter not found"**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

**"sentence-transformers fails to install"**
```bash
# Install build dependencies first
sudo apt install build-essential python3-dev
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements.txt
```

---

## Uninstallation

### Windows
- Use "Add or Remove Programs" in Settings
- Or run the uninstaller from Start Menu

### macOS
- Drag FileSearch.app to Trash
- Remove application data (optional):
  ```bash
  rm -rf ~/Library/Application\ Support/FileSearch
  ```

### Linux
```bash
# If installed with pip
pip3 uninstall intelligent-file-search

# Remove AppImage
rm ~/.local/bin/file-search
rm ~/.local/share/applications/file-search.desktop
```

---

## Getting Help

- 📖 Read the [README.md](README.md) for usage guide
- 🐛 Report issues on GitHub
- 💬 Check existing issues for solutions

---

## Next Steps

After installation:
1. Read the [Usage Guide](README.md#usage-guide)
2. Index your first directory
3. Try different search modes
4. Configure preferences in `config.json`
