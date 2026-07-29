$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw ".venv가 없습니다. 먼저 .\scripts\setup.ps1을 실행해 주세요."
}

& .\.venv\Scripts\python.exe main.py
