param([int]$VerifyFrames = 0, [string]$SourceProfileDirectory)
$ErrorActionPreference = 'Stop'
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$receipt = Get-Content -LiteralPath (Join-Path $taskRoot 'local/evidence/build-receipt.json') -Raw | ConvertFrom-Json
if (!$receipt.likado_terrain_preview_qualified) { throw 'The Likado terrain preview has not passed its focused qualification.' }
$fixture = Join-Path $taskRoot 'local/runs/likado-east-a/saves/save0.sav'
if ((Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'aabd365c8b4a64dd17cfec34476c8864c9a538a73e44b97c19aeab4bd9c0fa51') {
    throw 'The isolated Likado fixture differs from its checked identity.'
}
# Each preview gets a fresh profile. The owner's active SRAM/checkpoints are
# never launched, copied into the fixture, reset, or overwritten by this proof.
$preview = Join-Path $taskRoot ('local/preview-likado/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$null = New-Item -ItemType Directory -Path (Join-Path $preview 'saves') -Force
$owner = if ($SourceProfileDirectory) { [IO.Path]::GetFullPath($SourceProfileDirectory) } else { Join-Path $taskRoot 'local/player-foundation' }
foreach ($name in @('config.ini','keybinds.ini','controls-v2.done','presentation-vsync-v1.done','foundation.ini')) {
    $source = Join-Path $owner $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $preview $name) }
}
Copy-Item -LiteralPath $fixture -Destination (Join-Path $preview 'saves/save0.sav')
& (Join-Path $PSScriptRoot 'Start-Foundation.ps1') -ProfileDirectory $preview -PrepareOnly
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw 'The isolated profile could not be prepared.' }
$settings = Join-Path $preview 'foundation.ini'
$text = [IO.File]::ReadAllText($settings)
if ($text -match '(?m)^\s*ExperimentalFieldWide\s*=') {
    $text = [regex]::Replace($text, '(?m)^\s*ExperimentalFieldWide\s*=.*$', 'ExperimentalFieldWide=1')
} else { $text += "`r`nExperimentalFieldWide=1`r`n" }
[IO.File]::WriteAllText($settings, $text)
if ($receipt.likado_actor_preview_qualified) {
    $text = [IO.File]::ReadAllText($settings)
    if ($text -match '(?m)^\s*ExperimentalFieldActors\s*=') {
        $text = [regex]::Replace($text, '(?m)^\s*ExperimentalFieldActors\s*=.*$', 'ExperimentalFieldActors=1')
    } else { $text += "`r`nExperimentalFieldActors=1`r`n" }
    [IO.File]::WriteAllText($settings, $text)
}
Write-Output 'Likado widescreen preview: original center and gameplay with expanded town scenery.'
if ($receipt.likado_actor_preview_qualified) {
    Write-Output 'Checked regular actors also appear in the side margins. Other supported scenes expand when widescreen is enabled.'
} else { Write-Output 'Actors beyond the original viewport are not expanded in this fixture.' }
Write-Output "Separate preview saves and diagnostics: $preview"
& (Join-Path $PSScriptRoot 'Start-Foundation.ps1') -ProfileDirectory $preview -ResumeFixture -VerifyFrames $VerifyFrames
