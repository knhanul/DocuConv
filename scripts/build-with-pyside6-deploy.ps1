$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\pyside6-deploy.exe")) {
    throw "pyside6-deploy를 찾을 수 없습니다. 먼저 .\scripts\setup.ps1을 실행해 주세요."
}

# 첫 실행 시 pysidedeploy.spec 파일이 자동 생성됩니다.
& .\.venv\Scripts\pyside6-deploy.exe main.py
