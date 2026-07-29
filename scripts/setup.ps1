$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        & py -3.12 --version | Out-Null
        $Python = @("py", "-3.12")
    } catch {
        $Python = @("py", "-3")
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = @("python")
} else {
    throw "Python을 찾을 수 없습니다. Python 3.12 x64를 먼저 설치해 주세요."
}

if (-not (Test-Path ".venv")) {
    if ($Python.Count -eq 2) { & $Python[0] $Python[1] -m venv .venv }
    else { & $Python[0] -m venv .venv }
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Write-Host "개발 환경 구성이 완료되었습니다." -ForegroundColor Green
