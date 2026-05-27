$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cloudflared = Join-Path $root "bin\cloudflared.exe"
$port = $env:CHAMSOSIK_AI_TUNNEL_PORT
$hostName = "127.0.0.1"
$healthPath = $env:CHAMSOSIK_AI_TUNNEL_HEALTH_PATH
$serverDataDir = Join-Path $root "data"
$serverTunnelFile = Join-Path $serverDataDir "ai-tunnel-url.json"
$remoteUser = $env:CHAMSOSIK_REMOTE_USER
$remoteHost = $env:CHAMSOSIK_REMOTE_HOST
$remoteTunnelFile = $env:CHAMSOSIK_REMOTE_TUNNEL_FILE

if (!$port) { $port = "11434" }
if (!$healthPath) {
  if ($port -eq "11434") {
    $healthPath = "/api/tags"
  } else {
    $healthPath = "/health"
  }
}
if (!$remoteUser) { $remoteUser = "root" }
if (!$remoteHost) { $remoteHost = "211.45.162.155" }
if (!$remoteTunnelFile) { $remoteTunnelFile = "web/data/ai-tunnel-url.json" }

if (!(Test-Path -LiteralPath $cloudflared)) {
  $cloudflared = "cloudflared"
}

Write-Host ""
Write-Host "================================================"
Write-Host " Chamsosik AI - Cloudflare Quick Tunnel"
Write-Host "================================================"
Write-Host ""

try {
  $health = Invoke-WebRequest -Uri "http://$hostName`:$port$healthPath" -UseBasicParsing -TimeoutSec 5
  Write-Host "[OK] Local AI target is running."
  Write-Host $health.Content
} catch {
  Write-Host "[ERROR] Ollama is not responding on http://$hostName`:$port"
  Write-Host "Start the local AI target first, then run this file again."
  pause
  exit 1
}

New-Item -ItemType Directory -Force -Path $serverDataDir | Out-Null

Write-Host ""
Write-Host "[INFO] Starting Cloudflare Quick Tunnel..."
Write-Host "[INFO] Local target: http://$hostName`:$port"
Write-Host "[INFO] The trycloudflare.com URL will be saved automatically."
Write-Host ""

$argsList = @(
  "tunnel",
  "--url", "http://$hostName`:$port",
  "--http-host-header", "localhost:$port"
)

$env:CLOUDFLARED_LOGLEVEL = "info"
cmd /c "`"$cloudflared`" tunnel --url http://$hostName`:$port --http-host-header localhost:$port 2>&1" | ForEach-Object {
  $line = $_.ToString()
  Write-Host $line

  $match = [regex]::Match($line, "https://[a-z0-9-]+\.trycloudflare\.com")
  if ($match.Success) {
    $url = $match.Value.TrimEnd("/")
$payload = [ordered]@{
      url = $url
      updatedAt = (Get-Date).ToString("o")
      target = "http://$hostName`:$port"
      healthPath = $healthPath
    } | ConvertTo-Json -Depth 3

    Set-Content -LiteralPath $serverTunnelFile -Value $payload -Encoding UTF8
    $remoteDir = Split-Path -Parent $remoteTunnelFile
    $remotePayloadBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($payload))

    try {
      ssh "$remoteUser@$remoteHost" "mkdir -p '$remoteDir' && printf '%s' '$remotePayloadBase64' | base64 -d > '$remoteTunnelFile'" | Out-Host
      Write-Host "[OK] Remote tunnel URL updated: $remoteUser@$remoteHost`:$remoteTunnelFile"
    } catch {
      Write-Host "[WARN] Remote tunnel URL update failed: $($_.Exception.Message)"
      Write-Host "[WARN] Update manually on server: $remoteTunnelFile"
    }

    Write-Host ""
    Write-Host "[OK] Tunnel URL saved:"
    Write-Host "  $serverTunnelFile"
    Write-Host ""
  }
}
