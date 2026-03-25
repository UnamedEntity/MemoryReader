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

### Standard Library Only (No external dependencies)

- `tkinter`
- `os`
- `shutil`
- `threading`
- `concurrent.futures`
- `ctypes`
- `sys`

---

## ▶️ How to Run

```bash
python memory_analyzer.py
