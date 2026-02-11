# UnifiedAi – Windows Installer

## Building the installer

1. **Prerequisites**
   - [Node.js](https://nodejs.org/) 18+ (LTS recommended)
   - This repo (UnifiedAi) on your machine

2. **Build**
   - Double‑click **`BUILD_INSTALLER.bat`**, or  
   - From a terminal in the UnifiedAi folder:
     ```bat
     BUILD_INSTALLER.bat
     ```
   - First run will `npm install` in `electron/`, then run `electron-builder --win`.

3. **Output**
   - Installer is created under **`electron\dist\`**
   - File name is typically **`UnifiedAi Setup 1.0.0.exe`** (or the current version in `electron/package.json`)

**Note:** The build disables code signing (`CSC_IDENTITY_AUTO_DISCOVERY=false` and `signAndEditExecutable: false`) so the Windows installer builds without needing the winCodeSign tool (which can fail on some systems with "Cannot create symbolic link" unless you run as Administrator or enable Developer Mode). The installer is still valid; it just isn’t signed.

## What the installer does

- Installs the **UnifiedAi** desktop app (Electron).
- Option to choose install directory (not one‑click).
- Creates **Start Menu** and **Desktop** shortcuts.
- Bundles the **backend** (Python app) and **frontend** (static files) inside the app.

## User requirement: Python

The app starts the **Python backend** when you launch UnifiedAi. So **Python 3.11+** must be installed and available as `py` or `python` on the machine where the installer is run.

- **Windows:** Install from [python.org](https://www.python.org/downloads/) and ensure “Add Python to PATH” is checked, or use the `py` launcher.
- The Electron app looks for `py` (Windows) or `python3` (Mac/Linux) to run `backend/run.py`.

If Python is missing, the app window will show a connection error. Install Python and run UnifiedAi again.

## Optional: custom app icon

To use your own icon in the installer and app:

1. Add **`electron/icon.png`** (256×256 recommended for Windows).
2. In **`electron/package.json`**, under `"build"`, add back:
   - `"files": ["main.js", "preload.js", "loading.html", "icon.png"]`
   - `"win": { "target": "nsis", "icon": "icon.png" }`
3. Run **`BUILD_INSTALLER.bat`** again.

## Quick test without building

- **Backend only:** run **`START.bat`** (needs Python).
- **Full app:** run **`UnifiedAi.bat`** (needs Node.js + Python).  
Then build the installer when you’re ready to distribute.
