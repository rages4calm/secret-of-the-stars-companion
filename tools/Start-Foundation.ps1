param([switch]$PrepareOnly, [switch]$ResumeFixture, [switch]$OriginalView, [string]$ProfileDirectory, [string]$ResumeCheckpoint, [int]$VerifyFrames = 0)
$ErrorActionPreference = 'Stop'
# A parent PowerShell 7 session can pass its module path to Windows PowerShell
# 5.1 through Python/cmd. Prefer this host's own compatible built-in modules.
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$taskRoot = Split-Path -Parent $PSScriptRoot
$receipt = Get-Content -LiteralPath (Join-Path $taskRoot 'local/evidence/build-receipt.json') -Raw | ConvertFrom-Json
$binary = Join-Path $taskRoot 'local/native-proof/SecretOfTheStarsSNESRecomp/build/SecretOfTheStarsSNESRecomp.exe'
$rom = Join-Path $taskRoot 'local/inputs/clean-usa.sfc'
if ((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.release_executable_sha256) {
    throw 'The binary differs from the verified foundation receipt. Requalify the changed build before using this demo.'
}
if ((Get-FileHash -LiteralPath $rom -Algorithm SHA256).Hash.ToLowerInvariant() -ne '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600') {
    throw 'The local ROM working copy differs from the supported clean USA input.'
}
$preview = if ($ProfileDirectory) { [IO.Path]::GetFullPath($ProfileDirectory) } else { Join-Path $taskRoot 'local/player-foundation' }
$null = New-Item -ItemType Directory -Path $preview -Force
$installed = Join-Path $preview 'SecretOfTheStarsSNESRecomp.exe'
$active = Get-Process -Name SecretOfTheStarsSNESRecomp -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $installed }
if ($active) { Write-Output 'The foundation demo is already running. Alt+Enter or F11 changes fullscreen; Escape closes rewind.'; exit 0 }
$backup = Join-Path $preview ('backups/' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
function Backup-Profile {
    if (!(Test-Path -LiteralPath $backup)) {
        $null = New-Item -ItemType Directory -Path $backup -Force
        Get-ChildItem -LiteralPath $preview -File | Copy-Item -Destination $backup
        if (Test-Path -LiteralPath (Join-Path $preview 'saves')) {
            Copy-Item -LiteralPath (Join-Path $preview 'saves') -Destination $backup -Recurse
        }
    }
}
if (Test-Path -LiteralPath $installed) {
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash) {
        $oldHash = (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($oldHash -notin @($receipt.previous_release_executable_sha256)) {
            throw 'The demo has an unrecognized installed build. Its saves and settings have been preserved.'
        }
        Backup-Profile
        Copy-Item -LiteralPath $binary -Destination $installed
    }
} else { Copy-Item -LiteralPath $binary -Destination $installed }
$foundationSettings = Join-Path $preview 'foundation.ini'
if (!(Test-Path -LiteralPath $foundationSettings)) {
    Backup-Profile
    @'
[Enhancements]
# Optional native improvements. Set a value to 0 for original behavior.
BattleInfo=1
EnhancedPixels=1
FastMenus=1
# Opening-chapter current lead, derived from verified original story state.
Journal=1
# Optional expanded scenery; unsupported scenes/effects retain side bars.
ExperimentalFieldWide=0
ExperimentalFieldActors=0
# Original-cost native clear proof; no guest CPU acceleration. Opt-in only.
NativeClear=0
# Original-cost native column lookup, bounded to the checked town loader.
NativeColumns=0
# Optional finer menu-frame artwork. World art and text retain pixel art.
HdMenuFrames=0
'@ | Set-Content -LiteralPath $foundationSettings -Encoding ascii
}
elseif (!(Select-String -LiteralPath $foundationSettings -Pattern '^\s*FastMenus\s*=' -Quiet)) {
    Backup-Profile
    Add-Content -LiteralPath $foundationSettings -Value "`r`n# Complete field-menu uploads and slides sooner.`r`nFastMenus=1" -Encoding ascii
}
if (!(Select-String -LiteralPath $foundationSettings -Pattern '^\s*Journal\s*=' -Quiet)) {
    Backup-Profile
    Add-Content -LiteralPath $foundationSettings -Value "`r`n# Opening-chapter current lead; J or click left stick to view.`r`nJournal=1" -Encoding ascii
}
$config = Join-Path $preview 'config.ini'
if (!(Test-Path -LiteralPath $config)) {
    @'
[Graphics]
Renderer=direct3d11
WindowScale=4
Fullscreen=0
VSync=1
NewRenderer=0
NoSpriteLimits=0
Widescreen=0
IgnoreAspectRatio=0
[Sound]
EnableAudio=1
Volume=70
AudioFreq=32040
AudioChannels=2
AudioSamples=512
[General]
DisableFrameDelay=0
Autosave=0
RunAhead=0
'@ | Set-Content -LiteralPath $config -Encoding ascii
}
# The former software default never enabled SDL VSync. Migrate only that
# known profile choice, preserving every other setting and all input bindings.
$presentationMarker = Join-Path $preview 'presentation-vsync-v1.done'
if (!(Test-Path -LiteralPath $presentationMarker)) {
    $configText = [IO.File]::ReadAllText($config)
    $graphics = [regex]::Match($configText, '(?ims)^\[Graphics\][^\[]*')
    if ($graphics.Success -and $graphics.Value -match '(?im)^\s*Renderer\s*=\s*software\s*$') {
        Backup-Profile
        $block = $graphics.Value
        foreach ($setting in @(@('Renderer','direct3d11'), @('OutputMethod','SDL'), @('VSync','1'))) {
            $pattern = '(?im)^\s*' + $setting[0] + '\s*=[^\r\n]*'
            if ([regex]::IsMatch($block, $pattern)) { $block = [regex]::Replace($block, $pattern, ($setting[0] + '=' + $setting[1])) }
            else { $block = $block.TrimEnd("`r", "`n") + "`r`n" + $setting[0] + '=' + $setting[1] + "`r`n" }
        }
        $configText = $configText.Substring(0,$graphics.Index) + $block + $configText.Substring($graphics.Index + $graphics.Length)
        [IO.File]::WriteAllText($config, $configText)
        'Migrated former software default to qualified Direct3D 11 with VSync. Previous settings are backed up.' | Set-Content -LiteralPath $presentationMarker -Encoding ascii
    } else {
        'Qualified GPU default or existing custom renderer retained.' | Set-Content -LiteralPath $presentationMarker -Encoding ascii
    }
}
$saveDir = Join-Path $preview 'saves'
$null = New-Item -ItemType Directory -Path $saveDir -Force
$firstStart = Join-Path $preview 'first-start.done'
$slot = Join-Path $saveDir 'save0.sav'
if (!(Test-Path -LiteralPath $firstStart) -and !(Test-Path -LiteralPath $slot)) {
    Copy-Item -LiteralPath (Join-Path $taskRoot 'local/runs/clean-to-outdoors/saves/save0.sav') -Destination $slot
}
# One migration with a backup. Later custom bindings remain editable.
$controlMarker = Join-Path $preview 'controls-v2.done'
if (!(Test-Path -LiteralPath $controlMarker)) {
    Backup-Profile
    function Set-IniValue([string]$section, [string]$key, [string]$value) {
        $lines = [Collections.Generic.List[string]]::new()
        $lines.AddRange([string[]](Get-Content -LiteralPath $config))
        $start = -1; $end = $lines.Count
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Trim() -ieq "[$section]") { $start = $i; continue }
            if ($start -ge 0 -and $lines[$i] -match '^\s*\[') { $end = $i; break }
        }
        if ($start -lt 0) { $lines.Add("[$section]"); $lines.Add("$key=$value") }
        else {
            $found = $false
            for ($i = $start + 1; $i -lt $end; $i++) {
                if ($lines[$i] -match ('^\s*' + [regex]::Escape($key) + '\s*=')) { $lines[$i] = "$key=$value"; $found = $true; break }
            }
            if (!$found) { $lines.Insert($end, "$key=$value") }
        }
        [IO.File]::WriteAllLines($config, $lines)
    }
    Set-IniValue 'GamepadMap' 'EnableGamepad1' '1'
    Set-IniValue 'GamepadMap' 'EnableGamepad2' '0'
    Set-IniValue 'GamepadMap' 'Controls' 'DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,A,B,X,Y,L1,R1'
    Set-IniValue 'KeyMap' 'Load' 'F1,F2,F3,F4,F5,F6,None,None,F9,F10'
    Set-IniValue 'KeyMap' 'Save' 'Shift+F1,Shift+F2,Shift+F3,Shift+F4,Shift+F5,Shift+F6,None,None,Shift+F9,Shift+F10'
    Set-IniValue 'KeyMap' 'Fullscreen' 'Alt+Return,F11,F12'
    Set-IniValue 'KeyMap' 'SaveStateMenu' 'F7'
    Set-IniValue 'KeyMap' 'Rewind' 'F8'
    'Controller south=A/confirm, east=B/field-menu/back. F11/F12/Alt+Enter fullscreen. F8 rewind, Escape/Z/B closes it.' | Set-Content -LiteralPath $controlMarker -Encoding ascii
}
if ($PrepareOnly) { Write-Output "Prepared isolated demo: $preview"; exit 0 }
$arguments = @('--no-launcher', '--rom', ('"' + $rom + '"'))
$resume = Join-Path $preview 'fixture-resume.state'
# Normal launch always follows the game's original boot/title flow. The supplied
# research checkpoint is available via F1 or the separate explicit resume command.
if ($ResumeCheckpoint) {
    $selected = [IO.Path]::GetFullPath($ResumeCheckpoint)
    $saveRoot = [IO.Path]::GetFullPath($saveDir).TrimEnd('\')
    if (![IO.Path]::GetDirectoryName($selected).Equals($saveRoot, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetExtension($selected) -ine '.sav' -or !(Test-Path -LiteralPath $selected -PathType Leaf)) {
        throw 'Resume requires an existing checkpoint from this profile saves folder.'
    }
    if (((Get-Item -LiteralPath $selected).Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        ((Get-Item -LiteralPath $saveRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Resume requires a regular checkpoint and saves directory in this profile.'
    }
    if (Test-Path -LiteralPath $resume) {
        if ((Get-FileHash -LiteralPath $selected -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $resume -Algorithm SHA256).Hash) {
            throw "A different pending checkpoint is preserved. Resolve it before selecting another: $resume"
        }
    } else { Copy-Item -LiteralPath $selected -Destination $resume }
    $arguments += @('--resume-state', ('"' + $resume + '"'))
} elseif ($ResumeFixture) {
    if (!(Test-Path -LiteralPath $resume)) { Copy-Item -LiteralPath $slot -Destination $resume }
    $arguments += @('--resume-state', ('"' + $resume + '"'))
}
$resumeRequested = [bool]$ResumeFixture -or [bool]$ResumeCheckpoint
$logs = Join-Path $preview 'logs'
$null = New-Item -ItemType Directory -Path $logs -Force
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$stdout = Join-Path $logs "$stamp-stdout.log"
$stderr = Join-Path $logs "$stamp-stderr.log"
$oldPath = $env:PATH
$savedEnvironment = @{}
try {
    # This executable imports system DLLs only. Keep unrelated tool paths and
    # diagnostic variables out of a player launch; retain Windows device settings.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    Get-ChildItem Env: | Where-Object { $_.Name -like 'SNESRECOMP_*' } | ForEach-Object {
        $savedEnvironment[$_.Name] = $_.Value
        Remove-Item -LiteralPath ("Env:" + $_.Name)
    }
    if ($VerifyFrames -gt 0) { $env:SNESRECOMP_RUN_FRAMES = "$VerifyFrames" }
    if ($OriginalView) {
        $env:SNESRECOMP_FOUNDATION_BATTLE_INFO = '0'
        $env:SNESRECOMP_FOUNDATION_ENHANCED_PIXELS = '0'
        $env:SNESRECOMP_FOUNDATION_WIDE = '0'
        $env:SNESRECOMP_FOUNDATION_WIDE_ACTORS = '0'
        $env:SNESRECOMP_FOUNDATION_FAST_MENUS = '0'
        $env:SNESRECOMP_FOUNDATION_JOURNAL = '0'
        $env:SNESRECOMP_FOUNDATION_NATIVE_CLEAR = '0'
        $env:SNESRECOMP_FOUNDATION_NATIVE_COLUMNS = '0'
        $env:SNESRECOMP_FOUNDATION_HD_MENU_FRAMES = '0'
        $env:SNESRECOMP_FOUNDATION_XP_PERCENT = '100'
        $env:SNESRECOMP_FOUNDATION_GOLD_PERCENT = '100'
        $env:SNESRECOMP_FOUNDATION_MOVEMENT_PERCENT = '100'
    }
    $process = Start-Process -FilePath $installed -ArgumentList $arguments -WorkingDirectory $preview -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    # Windows PowerShell 5.1 needs a retained handle to read ExitCode reliably.
    $null = $process.Handle
} finally {
    $env:PATH = $oldPath
    Get-ChildItem Env: | Where-Object { $_.Name -like 'SNESRECOMP_*' } | ForEach-Object {
        Remove-Item -LiteralPath ("Env:" + $_.Name)
    }
    foreach ($name in $savedEnvironment.Keys) { Set-Item -LiteralPath ("Env:" + $name) -Value $savedEnvironment[$name] }
}
$started = $false
$deadline = (Get-Date).AddSeconds(12)
do {
    Start-Sleep -Milliseconds 100
    $process.Refresh()
    $errText = ''
    if (Test-Path -LiteralPath $stderr) {
        $stream = [IO.File]::Open($stderr, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        $reader = [IO.StreamReader]::new($stream)
        try { $errText = $reader.ReadToEnd() } finally { $reader.Dispose() }
    }
    if ($errText -match 'entering main loop') { $started = $true; break }
} while (!$process.HasExited -and (Get-Date) -lt $deadline)
if (!$started) {
    $code = if ($process.HasExited) { '0x{0:x8}' -f [uint32]([int64]$process.ExitCode -band 0xffffffffL) } else { 'startup timeout' }
    throw "Game did not reach gameplay startup ($code). Saves are preserved. Diagnostics: $logs"
}
if ($resumeRequested -and (Test-Path -LiteralPath $resume)) {
    throw "The game started but refused the pending checkpoint. It is preserved for diagnosis: $resume"
}
if (!$resumeRequested -or !(Test-Path -LiteralPath $resume)) {
    'Successful demo startup; F1 loads slot 0. Later launches use the normal title screen.' | Set-Content -LiteralPath $firstStart -Encoding ascii
}
if ($VerifyFrames -gt 0) {
    if (!$process.WaitForExit(15000)) { throw "Verification still running; inspect diagnostics: $logs" }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Verification exited with $($process.ExitCode): $logs" }
}
Write-Output 'Game started. Fullscreen: Alt+Enter/F11/F12. Rewind: F8; close with Escape, Z or controller B.'
Write-Output 'Opening journal: J or click left stick. Enemy HP: H or click right stick.'
Write-Output "Launch diagnostics: $logs"
