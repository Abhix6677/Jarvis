# PowerShell installer for a simple 'ai' CLI shim
# Usage (run from project root once):
#   powershell -ExecutionPolicy Bypass -File .\install-cli.ps1

$repo = (Get-Location).Path
$target = Join-Path $env:USERPROFILE 'bin'

if (-not (Test-Path $target)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Write-Host "Created directory: $target"
}

$cmdPath = Join-Path $target 'ai.cmd'
$cmdContent = "@echo off`r`npython \"$repo\\jarvis.py\" %*"

Set-Content -Path $cmdPath -Value $cmdContent -Encoding UTF8
Write-Host "Created shim: $cmdPath"

# Ensure the user has the bin folder on PATH (advisory only)
$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
if ($currentPath -notlike "*$target*") {
    Write-Host "Note: $target is not on your User PATH." -ForegroundColor Yellow
    Write-Host "To add it permanently (PowerShell), run:" -ForegroundColor Yellow
    Write-Host "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';$target', 'User')" -ForegroundColor Cyan
    Write-Host "After adding, open a new terminal to use the 'ai' command." -ForegroundColor Yellow
} else {
    Write-Host "$target is already on your User PATH. You can now run 'ai' from any folder." -ForegroundColor Green
}
