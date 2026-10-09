param([int]$VerifyFrames = 0, [string]$SourceProfileDirectory)
$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$receipt = Get-Content -LiteralPath (Join-Path $taskRoot 'local/evidence/build-receipt.json') -Raw | ConvertFrom-Json
if (!$receipt.hd_menu_frames_qualified) { throw 'The menu-frame preview has not passed its focused qualification.' }
$fixture = Join-Path $taskRoot 'local/runs/likado-inside-a/saves/save0.sav'
if ((Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.hd_menu_fixture_sha256) {
    throw 'The menu preview checkpoint differs from its checked identity.'
}
$preview = Join-Path $taskRoot ('local/preview-hd-menu/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$null = New-Item -ItemType Directory -Path (Join-Path $preview 'saves') -Force
$owner = if ($SourceProfileDirectory) { [IO.Path]::GetFullPath($SourceProfileDirectory) } else { Join-Path $taskRoot 'local/player-foundation' }
foreach ($name in @('config.ini','keybinds.ini','controls-v2.done','presentation-vsync-v1.done','foundation.ini')) {
    $source = Join-Path $owner $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $preview $name) }
}
Copy-Item -LiteralPath $fixture -Destination (Join-Path $preview 'saves/save0.sav')
& (Join-Path $PSScriptRoot 'Start-Foundation.ps1') -ProfileDirectory $preview -PrepareOnly
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw 'The menu preview profile could not be prepared.' }
$settings = Join-Path $preview 'foundation.ini'
$text = [IO.File]::ReadAllText($settings)
foreach ($setting in @(@('HdMenuFrames','1'),@('ExperimentalFieldWide','0'),@('NativeClear','0'),@('NativeColumns','0'))) {
    $pattern = '(?m)^\s*' + $setting[0] + '\s*=.*$'
    if ($text -match $pattern) { $text = [regex]::Replace($text, $pattern, $setting[0] + '=' + $setting[1]) }
    else { $text += "`r`n" + $setting[0] + '=' + $setting[1] + "`r`n" }
}
[IO.File]::WriteAllText($settings, $text)
Write-Output 'Menu-frame preview: press the field-menu button (controller east/B) to view finer frame artwork.'
Write-Output 'This replaces eight border tiles only. World art, portraits and text remain pixel art.'
Write-Output "Separate preview saves and diagnostics: $preview"
& (Join-Path $PSScriptRoot 'Start-Foundation.ps1') -ProfileDirectory $preview -ResumeFixture -VerifyFrames $VerifyFrames
