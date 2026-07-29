$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Source = Join-Path $Root "dist\POSID_DocumentConverter"
if (-not (Test-Path $Source)) {
    & "$PSScriptRoot\build.ps1"
}

$ArtifactDir = Join-Path $Root "artifacts"
New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null
$Zip = Join-Path $ArtifactDir "POSID_DocumentConverter_v1.0.0_win-x64.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path "$Source\*" -DestinationPath $Zip -CompressionLevel Optimal
Write-Host "배포 ZIP 생성 완료: $Zip" -ForegroundColor Green
