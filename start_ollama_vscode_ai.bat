@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo.
echo ------------------------------------------------------------
echo   VS Code + Continue + Ollama AI
echo ------------------------------------------------------------
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 2 | Out-Null; Write-Host 'Ollama API: OK' } catch { Write-Host 'Starting Ollama server...'; Start-Process -FilePath ollama -ArgumentList 'serve' -WindowStyle Hidden; Start-Sleep -Seconds 3 }"

echo.
echo Opening VS Code...
code "%~dp0"

echo.
echo Continue is configured to use local Ollama models.
echo Open the Continue sidebar in VS Code when ready.
echo.

endlocal
