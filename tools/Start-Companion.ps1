param([string]$ProfileDirectory, [string]$VerifyCaptureDirectory, [string]$VerifyVisibleReport)
$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$receiptPath = Join-Path $taskRoot 'local/evidence/companion-receipt.json'
if (!(Test-Path -LiteralPath $receiptPath)) { throw 'Companion has not been qualified and installed yet.' }
$receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
$binary = Join-Path $taskRoot 'local/companion/Secret of the Stars Companion.exe'
if (!$receipt.qualified -or (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.executable_sha256) {
    throw 'Companion differs from its qualified receipt. Retain settings and requalify the changed artifact.'
}
$arguments = @('--root', ('"' + $taskRoot + '"'))
if ($ProfileDirectory) { $arguments += @('--profile', ('"' + [IO.Path]::GetFullPath($ProfileDirectory) + '"')) }
if ($VerifyCaptureDirectory) {
    $arguments += @('--capture', ('"' + [IO.Path]::GetFullPath($VerifyCaptureDirectory) + '"'))
    $arguments += @('--report', ('"' + (Join-Path ([IO.Path]::GetFullPath($VerifyCaptureDirectory)) 'error.json') + '"'))
}
if ($VerifyVisibleReport) {
    if ($VerifyCaptureDirectory) { throw 'Choose either offscreen capture or real visible-window verification.' }
    $arguments += @('--visible-test', ('"' + [IO.Path]::GetFullPath($VerifyVisibleReport) + '"'))
    $arguments += @('--report', ('"' + ([IO.Path]::GetFullPath($VerifyVisibleReport) + '.error.json') + '"'))
}
# Companion is the visible app requested here. SW_HIDE previously left the
# owner with a live process and no visible top-level window.
$windowStyle = if ($VerifyCaptureDirectory) { 'Hidden' } else { 'Normal' }
$process = Start-Process -FilePath $binary -ArgumentList $arguments -WorkingDirectory $taskRoot -WindowStyle $windowStyle -PassThru
$null = $process.Handle
if ($VerifyCaptureDirectory) {
    if (!$process.WaitForExit(15000)) { throw 'Companion capture did not finish within 15 seconds.' }
    if ($process.ExitCode -ne 0) { throw "Companion capture failed ($($process.ExitCode)). Inspect the capture report." }
}
elseif ($VerifyVisibleReport) {
    if (!$process.WaitForExit(20000)) { throw 'Companion visible-window verification did not finish within 20 seconds.' }
    if ($process.ExitCode -ne 0) { throw "Companion visible-window verification failed ($($process.ExitCode)). Inspect $VerifyVisibleReport" }
    $visible = Get-Content -LiteralPath $VerifyVisibleReport -Raw | ConvertFrom-Json
    if (!$visible.passed -or !$visible.native_visible -or !$visible.intersects_display_work_area) { throw 'Companion did not report a real visible on-screen window.' }
}
else {
    $deadline = (Get-Date).AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 100
        $process.Refresh()
        if ($process.HasExited) { throw "Companion exited before its window was ready ($($process.ExitCode))." }
    } while ($process.MainWindowHandle -eq 0 -and (Get-Date) -lt $deadline)
    if ($process.MainWindowHandle -eq 0) { throw 'Companion is running but its interactive window did not become visible. Inspect local/companion/logs.' }
    Write-Output "Companion window ready (PID $($process.Id))."
}
