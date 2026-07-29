$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw ".venv가 없습니다. 먼저 .\scripts\setup.ps1을 실행해 주세요."
}

& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean posid_document_converter.spec
Write-Host "빌드 완료: dist\POSID_DocumentConverter" -ForegroundColor Green
