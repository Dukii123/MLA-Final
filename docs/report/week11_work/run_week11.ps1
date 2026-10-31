$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
try {
    $raw = $host.UI.RawUI
    $raw.BufferSize = New-Object System.Management.Automation.Host.Size(120, 3000)
    $raw.WindowSize = New-Object System.Management.Automation.Host.Size(120, 60)
} catch {
    Write-Host "could not resize console: $($_.Exception.Message)"
}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$py = 'C:\Users\DucAnh\AppData\Local\Programs\Python\Python314\python.exe'
$done = Join-Path $PSScriptRoot 'official_run.done'
if (Test-Path $done) { Remove-Item $done -Force }

Write-Host "=== WEEK 11 OFFICIAL RUN $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Windows CPU only ==="
& $py week11_analysis.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ANALYSIS FAILED exit=$LASTEXITCODE"
    Set-Content -Path $done -Value 'FAILED' -Encoding ASCII
    Read-Host 'press enter to close'
    exit 1
}
& $py make_figure_week11.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "FIGURES FAILED exit=$LASTEXITCODE"
    Set-Content -Path $done -Value 'FAILED' -Encoding ASCII
    Read-Host 'press enter to close'
    exit 1
}
Write-Host "ALL DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Set-Content -Path $done -Value 'OK' -Encoding ASCII
Read-Host 'press enter to close'
