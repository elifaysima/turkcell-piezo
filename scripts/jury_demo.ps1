<#
JURY DEMO SCRIPT — Windows (PowerShell)

KULLANIM:
  powershell -ExecutionPolicy Bypass -File .\scripts\jury_demo.ps1

SENARYO:
  - Sensör yoksa: fake_publisher otomatik açılır
  - Sensör varsa: $StartFakePublisher = $false yap

#>

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..") # repo root

# ====== AYARLAR ======
$StartFakePublisher = $true # sensör varken $false yap
$Topic = "piyon/v1/steps"
$DashUrl = "http://127.0.0.1:8050"
# =====================

Write-Host "=== PIYON JURY DEMO (Windows) ===" -ForegroundColor Cyan
Write-Host "Repo root: $(Get-Location)"
Write-Host "Topic : $Topic"
Write-Host ""

function Test-Port($port) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $port)
    $c.Close()
    return $true
  } catch { return $false }
}

function Find-Mosquitto {
  $candidates = @(
    "C:\Program Files\mosquitto\mosquitto.exe",
    "C:\Program Files (x86)\mosquitto\mosquitto.exe"
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) { return $p }
  }
  $cmd = Get-Command mosquitto -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$mosq = Find-Mosquitto
if (-not $mosq) {
  Write-Host "[HATA] Mosquitto bulunamadi." -ForegroundColor Red
  Write-Host "Kurulum: https://mosquitto.org/download/ (Windows installer)" -ForegroundColor Yellow
  Write-Host "Winget : winget install -e --id EclipseMosquitto.Mosquitto" -ForegroundColor Yellow
  exit 1
}
Write-Host "[OK] Mosquitto: $mosq" -ForegroundColor Green

if (-not (Test-Port 1883)) {
  Write-Host "[INFO] Broker baslatiliyor (1883)..." -ForegroundColor Cyan
  Start-Process -FilePath $mosq -ArgumentList "-v" -WindowStyle Normal
  Start-Sleep -Seconds 1
  if (-not (Test-Port 1883)) {
    Write-Host "[HATA] Broker 1883 portunda acilmadi (Firewall/izin/port?)." -ForegroundColor Red
    exit 1
  }
} else {
  Write-Host "[OK] Broker zaten calisiyor (1883)." -ForegroundColor Green
}

Write-Host "[INFO] Dashboard baslatiliyor..." -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "src\dashboard.py" -WindowStyle Normal
Start-Sleep -Seconds 1

if ($StartFakePublisher) {
  Write-Host "[INFO] Fake publisher baslatiliyor (sensör yok modu)..." -ForegroundColor Cyan
  Start-Process -FilePath "python" -ArgumentList "src\fake_publisher.py" -WindowStyle Normal
} else {
  Write-Host "[INFO] Fake publisher kapali (sensör var modu)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[OK] DEMO HAZIR." -ForegroundColor Green
Write-Host "Dashboard: $DashUrl"
Write-Host ""
Write-Host "Sensör varken checklist:" -ForegroundColor Yellow
Write-Host " 1) ESP32 TOPIC = $Topic"
Write-Host " 2) ESP32 MQTT_HOST = laptop IPv4 (ipconfig)"
Write-Host " 3) Fake aciksa kapat (Ctrl+C)"
Write-Host ""
Write-Host "Durdurma: powershell -ExecutionPolicy Bypass -File .\scripts\stop_demo.ps1" -ForegroundColor Cyan
