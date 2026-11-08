# Builds dist\roadgram.exe (single file, no Python needed on the target machine).
# Needs Python 3.10+ and internet once (to install PyInstaller). Run:  powershell -File build_exe.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install --quiet --upgrade pyinstaller
python -m unittest discover -s tests -t .
if ($LASTEXITCODE -ne 0) { throw "tests failed; not building" }

python -m PyInstaller --onefile --clean --noconfirm --name roadgram --console run_roadgram.py
if ($LASTEXITCODE -ne 0) { throw "build failed" }

Write-Host "Built: $PSScriptRoot\dist\roadgram.exe"
& "$PSScriptRoot\dist\roadgram.exe" --version
