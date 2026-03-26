Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1) Build desktop executable.
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm MemoryReader.spec

# 2) Locate Inno Setup compiler.
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    $iscc = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $iscc)) {
    throw "Inno Setup 6 not found. Install it from https://jrsoftware.org/isinfo.php"
}

# 3) Build installer GUI executable.
& $iscc "installer.iss"

Write-Host "Done: installer-output\MemoryAnalyzerSetup.exe" -ForegroundColor Green
