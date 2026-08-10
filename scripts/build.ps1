param(
    [string]$Version = "",
    [string]$BuildDate = ""
)

[Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw ".venv not found. Please run .\scripts\setup.ps1 first."
}

if (-not $Version) {
    $Version = Read-Host "Enter version (e.g. 1.0.0)"
}
if (-not $BuildDate) {
    $BuildDate = Read-Host "Enter build date (e.g. 2026-08-10)"
}

$VersionFile = Join-Path $Root "backend\version.py"
$VersionContent = @"
from __future__ import annotations

APP_VERSION = "$Version"
BUILD_DATE = "$BuildDate"
"@
Set-Content -Path $VersionFile -Value $VersionContent -Encoding UTF8
Write-Host "Version: v$Version (Build date: $BuildDate)" -ForegroundColor Cyan

& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean posid_document_converter_onefile.spec
Write-Host "Build complete: dist\POSID_DocumentConverter.exe" -ForegroundColor Green
