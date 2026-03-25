# Build Windows desktop executable (requires Python 3.x on PATH)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm MemoryReader.spec

Write-Host "Done: dist\MemoryReader.exe" -ForegroundColor Green
