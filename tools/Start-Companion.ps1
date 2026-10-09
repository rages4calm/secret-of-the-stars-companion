param([string]$ProfileDirectory, [string]$VerifyCaptureDirectory, [string]$VerifyVisibleReport)
$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$receiptPath = Join-Path $taskRoot 'local/evidence/companion-receipt.json'
$publicSource = $false
if (Test-Path -LiteralPath $receiptPath) {
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    $binary = Join-Path $taskRoot 'local/companion/Secret of the Stars Companion.exe'
    if (!$receipt.qualified -or !(Test-Path -LiteralPath $binary) -or (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.executable_sha256) {
        throw 'Companion differs from its qualified receipt. Retain settings and requalify the changed artifact.'
    }
} else {
    $receiptPath = Join-Path $taskRoot 'local/public-companion/source-companion-receipt.json'
    if (!(Test-Path -LiteralPath $receiptPath)) {
        $builder = Join-Path $taskRoot 'tools/build_public_companion.py'
        if (!(Test-Path -LiteralPath $builder)) { throw 'Public Companion build helper is missing. Restore the source checkout; profiles are preserved.' }
        & python -u $builder
        if ($LASTEXITCODE -ne 0) { throw 'Public Companion build failed. Install the .NET 8 SDK and inspect the builder diagnostics; profiles are preserved.' }
    }
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    $binary = [IO.Path]::GetFullPath([string]$receipt.executable)
    $allowed = [IO.Path]::GetFullPath((Join-Path $taskRoot 'local/public-companion')).TrimEnd('\') + '\'
    if (!$binary.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Public Companion receipt points outside its isolated build folder.' }
    if ($receipt.status -ne 'compiled_unqualified' -or !$receipt.public_build -or $receipt.component -ne 'Companion' -or
        !(Test-Path -LiteralPath $binary -PathType Leaf) -or (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.executable_sha256) {
        throw 'Public Companion differs from its source compilation receipt. Build a fresh candidate; existing profiles are preserved.'
    }
    $manifest = Join-Path $taskRoot 'Companion/authored-files.json'
    if (!(Test-Path -LiteralPath $manifest)) { throw 'Companion authored source manifest is missing. Existing builds and profiles are preserved.' }
    if ($receipt.source_manifest_sha256 -ne (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()) {
        Write-Output 'Companion source snapshot changed. Building a new isolated GUI; the previous executable and profiles are preserved.'
        & python -u (Join-Path $taskRoot 'tools/build_public_companion.py')
        if ($LASTEXITCODE -ne 0) { throw 'Updated Companion source did not build. Inspect diagnostics; previous builds and profiles are preserved.' }
        $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        $binary = [IO.Path]::GetFullPath([string]$receipt.executable)
        if (!$binary.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase) -or $receipt.status -ne 'compiled_unqualified' -or
            !(Test-Path -LiteralPath $binary -PathType Leaf) -or (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.executable_sha256 -or
            $receipt.source_manifest_sha256 -ne (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()) {
            throw 'Updated Companion source receipt could not be verified. Existing profiles are preserved.'
        }
    }
    $publicSource = $true
}
$arguments = @('--root', ('"' + $taskRoot + '"'))
if ($publicSource) { $arguments += '--setup' }
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
