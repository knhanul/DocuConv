$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Parent = Split-Path -Parent $Root
$Zip = Join-Path $Parent "POSID_DocumentConverter_QML_Source_v1.0.0.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }

$Exclude = @(".venv", "build", "dist", "artifacts", "__pycache__", ".pytest_cache", ".ruff_cache")
$Staging = Join-Path $env:TEMP "POSID_DocumentConverter_Source_Staging"
if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Staging | Out-Null
robocopy $Root $Staging /E /XD $Exclude | Out-Null
Compress-Archive -Path "$Staging\*" -DestinationPath $Zip -CompressionLevel Optimal
Remove-Item $Staging -Recurse -Force
Write-Host "소스 ZIP 생성 완료: $Zip" -ForegroundColor Green
