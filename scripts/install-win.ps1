# GrblWheel Windows install script for development/testing.
# Run from repo root: .\scripts\install-win.ps1
# Or from anywhere: & "D:\path\to\GrblWheel\scripts\install-win.ps1"
# Creates .venv, installs package (no GPIO), copies config if missing, builds frontend if npm is available.

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

Write-Host "=== GrblWheel install (Windows) ==="
Write-Host "Repo: $RepoRoot"
Write-Host ""

# Python venv and package
Write-Host "--- Python ---"
$venvPath = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $venvPath)) {
    py -m venv $venvPath
    Write-Host "Created .venv"
}
$pip = Join-Path $venvPath "Scripts\pip.exe"
& $pip install -q --upgrade pip
& $pip install -e .
Write-Host "Python deps installed."
Write-Host ""

# Config
Write-Host "--- Config ---"
$configPath = Join-Path $RepoRoot "config\config.yaml"
$configExample = Join-Path $RepoRoot "config\config.example.yaml"
if (-not (Test-Path $configPath)) {
    Copy-Item $configExample $configPath
    Write-Host "Created config\config.yaml (edit as needed)."
} else {
    Write-Host "config\config.yaml already exists."
}
Write-Host ""

# Frontend (optional if npm available)
Write-Host "--- Frontend ---"
$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm) {
    Push-Location (Join-Path $RepoRoot "frontend")
    npm install --silent
    npm run build
    Pop-Location
    Write-Host "Frontend built."
} else {
    Write-Host "npm not found; skipping frontend build. Install Node.js or copy frontend\dist from another machine."
}
Write-Host ""

Write-Host "=== Install done ==="
Write-Host "  Run:  py -m grblwheel.main"
Write-Host "  Or:   .\.venv\Scripts\python.exe -m grblwheel.main"
Write-Host "  Then open http://localhost:8765"
Write-Host "  Config: $RepoRoot\config\config.yaml"
Write-Host "  Update: $RepoRoot\scripts\update-win.ps1"
