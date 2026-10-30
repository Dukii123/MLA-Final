$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$done = Join-Path $PSScriptRoot 'official_run.done'
if (Test-Path $done) { Remove-Item $done -Force }

$proc = Start-Process powershell -ArgumentList '-NoLogo', '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'run_week11.ps1') -PassThru
Write-Host "started visible PowerShell pid=$($proc.Id)"

for ($i = 0; $i -lt 1800; $i++) {
    if (Test-Path $done) { break }
    Start-Sleep -Seconds 2
}
if (-not (Test-Path $done)) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    throw 'Timeout waiting for official run'
}
$status = (Get-Content $done -Raw).Trim()
Write-Host "run status: $status"
if ($status -ne 'OK') {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    throw "Official run failed: $status"
}
Start-Sleep -Seconds 2
& (Join-Path $PSScriptRoot 'capture_terminal.ps1') -TargetPid $proc.Id -OutPath (Join-Path $PSScriptRoot 'terminal_week11_run_win.png')
Start-Sleep -Milliseconds 500
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host 'official run captured and window closed'
