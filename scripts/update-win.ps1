# Pull latest GrblWheel from GitHub and run the Windows install script.
# Run from repo root: .\scripts\update-win.ps1
# Exits with error if the current directory is not a git repository.

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Error "Not a git repo. Clone GrblWheel first, then run this script."
    exit 1
}

Write-Host "=== GrblWheel update ==="
Write-Host "Repo: $RepoRoot"
git pull
Write-Host ""
Write-Host "Running install script..."
& (Join-Path $RepoRoot "scripts\install-win.ps1")
