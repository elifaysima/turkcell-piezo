<#
DEMO STOP SCRIPT
KULLANIM:
  powershell -ExecutionPolicy Bypass -File .\scripts\stop_demo.ps1
#>

$ErrorActionPreference = "SilentlyContinue"

Write-Host "[INFO] python prosesleri kapatiliyor (dashboard/fake)..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "[INFO] mosquitto kapatiliyor..." -ForegroundColor Cyan
Get-Process mosquitto -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "[OK] Durduruldu." -ForegroundColor Green
