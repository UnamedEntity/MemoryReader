# 📊 Memory Analyzer (Tkinter Disk Usage Tool)

A Python-based desktop application that analyzes disk usage, visualizes file sizes, and helps users identify and manage large files and folders. Built with **Tkinter**, it provides an interactive UI, treemap visualization, caching, and safe deletion features.

---

## 🚀 Features

- 📂 **Directory Scanning**
  - Browse through folders and view their contents
  - Displays file and folder sizes in real time

- ⚡ **Multithreaded Performance**
  - Uses `ThreadPoolExecutor` to speed up folder size calculations

- 🧠 **Caching System**
  - Stores previously computed folder sizes
  - Optional background caching for faster future access

- 📊 **Treemap Visualization**
  - Visual representation of largest files
  - Interactive (hover for details, click to navigate)

- 📋 **Largest Files & Folders Panel**
  - Quickly identify storage-heavy items

- 🗑 **Delete Functionality**
  - Delete files or folders directly from the UI
  - Confirmation prompt to prevent accidental deletion
  - System folders are protected

- 🔐 **Admin Privileges**
  - Automatically relaunches with admin rights for full disk access

---

## 🖥️ UI Overview

- **Left Panel:** File and folder list with sizes  
- **Right Panel:**  
  - Treemap visualization  
  - Largest folders list  
- **Top Bar:** Navigation, delete, and caching controls  
- **Bottom Bar:** Status updates  

---

## 📦 Requirements

- Python 3.8+
- Windows OS (uses `ctypes` for admin privileges)
- (For installer creation) [Inno Setup 6](https://jrsoftware.org/isinfo.php)

### Running from source (no pip packages)

The app uses only the Python standard library:

- `tkinter`
- `os`
- `shutil`
- `threading`
- `concurrent.futures`
- `ctypes`
- `sys`

To ship a standalone **desktop `.exe`**, use **PyInstaller** from `requirements.txt` and follow [Building the desktop app](#building-the-desktop-app-windows) below.
To ship a **GUI installer (`Setup.exe`)**, follow [Building the Windows installer](#building-the-windows-installer-gui-setup).

---

## ▶️ How to Run

### From source

```bash
python main.py
```

Windows will prompt for administrator approval (or the app will relaunch elevated) so it can scan protected locations.

### Desktop app (built executable)

After [building](#building-the-desktop-app-windows), run:

```text
dist\MemoryReader.exe
```

The packaged executable is a single file, runs without a console window, and requests admin rights via its application manifest (UAC).

---

## 🏗️ Building the desktop app (Windows)

1. Install Python with Tkinter (the default **python.org** Windows installer includes it).
2. From the project folder:

   ```powershell
   .\build.ps1
   ```

   Or manually:

   ```powershell
   python -m pip install -r requirements.txt
   python -m PyInstaller --noconfirm MemoryReader.spec
   ```

3. Output: **`dist\MemoryReader.exe`** — share or ship this file (or zip it). PyInstaller also writes a `build\` folder; you can ignore or delete it after a successful build.

Configuration lives in **`MemoryReader.spec`** (one-file bundle, no console, `uac_admin` enabled).

---

## Building the Windows installer (GUI Setup)

The project now includes an Inno Setup script (`installer.iss`) that creates a standard Windows installer wizard GUI.

### Option A: one command

```powershell
.\build-installer.ps1
```

This will:

1. Build `dist\MemoryReader.exe` with PyInstaller
2. Compile `installer.iss` with Inno Setup (`ISCC.exe`)
3. Produce `installer-output\MemoryAnalyzerSetup.exe`

### Option B: manual installer build

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

If Inno Setup is installed in `C:\Program Files\Inno Setup 6`, use that path instead.

### What the installer includes

- Installs `MemoryReader.exe` to `Program Files\Memory Analyzer`
- Adds a Start Menu shortcut
- Optional desktop shortcut
- Uninstaller entry in Windows Apps list
