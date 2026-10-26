# Start/Restart NEUROEXPLORER (formerly "Model Steering Studio") cleanly.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\start_studio.ps1
#
# Why this exists: stale uvicorn instances kept sharing port 8321 on Windows
# (SO_REUSEADDR) and answered requests with different stored state.

$ErrorActionPreference = "SilentlyContinue"

# kill any uvicorn serving our app
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*server.app*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# kill any stray engines (optional; you can skip this to keep one loaded)
Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'" |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Start-Sleep -Seconds 2

Set-Location (Split-Path $PSScriptRoot -Parent)
python -m uvicorn server.app:app --port 8321
