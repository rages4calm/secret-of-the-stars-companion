using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;

namespace SecretOfTheStars.Companion.Core;

public static class ProfileService
{
    private const string GameName = "SecretOfTheStarsSNESRecomp";
    private const string RomHash = "7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600";
    private static readonly StringComparer Paths = OperatingSystem.IsWindows() ? StringComparer.OrdinalIgnoreCase : StringComparer.Ordinal;

    public static ProfileSnapshot Load(string root, string? profile = null)
    {
        root = Path.GetFullPath(root);
        profile = Path.GetFullPath(string.IsNullOrWhiteSpace(profile) ? PublicSetupService.GetSelectedProfile(root) ?? Path.Combine(root, "local", "player-foundation") :
            Path.IsPathRooted(profile) ? profile : Path.Combine(root, profile));
        RejectReparse(profile);
        var files = new Dictionary<string, FileIdentity>(Paths);
        foreach (var name in new[] { "config.ini", "foundation.ini", "keybinds.ini", "controls-v2.done", "presentation-vsync-v1.done" })
            Track(files, Path.Combine(profile, name));
        Track(files, Path.Combine(root, "local", "evidence", "build-receipt.json"));
        Track(files, Path.Combine(root, "local", "native-proof", GameName, "build", GameName + ".exe"));
        Track(files, Path.Combine(root, "local", "inputs", "clean-usa.sfc"));
        Track(files, Path.Combine(profile, GameName + ".exe"));
        Track(files, Path.Combine(profile, PublicSetupService.ManifestName));
        if (files[Path.Combine(profile, PublicSetupService.ManifestName)].Exists)
        {
            var source = PublicSetupService.ReadProfile(profile);
            var receiptPath = PublicSetupService.RequireInside(source.ReceiptPath, Path.Combine(root, "local", "source-builds"));
            PublicSetupService.RejectLinkedPath(source.RomPath);
            Track(files, receiptPath); Track(files, Path.GetFullPath(source.RomPath));
            Track(files, Path.Combine(Path.GetDirectoryName(receiptPath)!, "build", GameName + ".exe"));
        }
        foreach (var script in new[] { "Start-Foundation.ps1", "Start-LikadoPreview.ps1", "Start-HdMenuPreview.ps1" })
            Track(files, Path.Combine(root, "tools", script));
        var config = new IniDocument(files[Path.Combine(profile, "config.ini")].Bytes);
        var foundation = new IniDocument(files[Path.Combine(profile, "foundation.ini")].Bytes);
        var bindings = new IniDocument(files[Path.Combine(profile, "keybinds.ini")].Bytes);
        var settings = ReadSettings(config, foundation, bindings);
        if (!SupportsQol(profile, files) && config.Get("GamepadMap", "Turbo") is null)
            settings.HotkeyBindings["Turbo"] = settings.HotkeyBindings["Turbo"] with { Controller = "None" };
        var snapshot = new ProfileSnapshot
        {
            RootDirectory = root, ProfileDirectory = profile, Settings = settings,
            OriginalSettings = settings.DeepCopy(), Files = files,
            Readiness = CheckReadiness(root, profile, files), Saves = ReadSaves(profile)
        };
        return snapshot;
    }

    public static bool IsGameRunning(ProfileSnapshot snapshot)
    {
        var installed = Path.Combine(snapshot.ProfileDirectory, GameName + ".exe");
        foreach (var process in Process.GetProcessesByName(GameName))
        {
            using (process)
            {
                try
                {
                    if (!process.HasExited)
                    {
                        var path = process.MainModule?.FileName;
                        if (string.IsNullOrEmpty(path) || Paths.Equals(Path.GetFullPath(path), installed)) return true;
                    }
                }
                catch (InvalidOperationException) { if (!HasExited(process)) return true; }
                catch (Win32Exception) { return true; } // Cannot establish that it belongs to another profile.
                catch (NotSupportedException) { return true; }
            }
        }
        return false;
    }

    public static ApplyResult Apply(ProfileSnapshot snapshot, GameSettings settings) =>
        ApplyCore(snapshot, settings, () => IsGameRunning(snapshot));

    internal static ApplyResult ApplyCore(ProfileSnapshot snapshot, GameSettings settings, Func<bool> running)
    {
        string? backup = null;
        var replaced = new List<(FileIdentity Original, string NewHash)>();
        var temporary = new List<string>();
        try
        {
            Validate(settings, snapshot.OriginalSettings);
            if (!SupportsQol(snapshot) && QolChanged(settings, snapshot.OriginalSettings))
                throw new InvalidOperationException("These reward, movement and configurable overlay options require native foundation 0.2.0 or newer. Build and select the current source in Setup first. Existing settings and saves are preserved.");
            if (!SupportsJournalPossession(snapshot) && settings.JournalPossession != snapshot.OriginalSettings.JournalPossession)
                throw new InvalidOperationException("Journal item-summary choices require native foundation 0.2.3 or newer. Update the selected source build in Setup first. Existing settings and saves are preserved.");
            EnsureUnchanged(snapshot);
            if (running()) throw new InvalidOperationException("Close this profile's game before applying settings.");
            RejectReparse(snapshot.ProfileDirectory);
            var before = Values(snapshot.OriginalSettings);
            var after = Values(settings);
            var documents = new Dictionary<string, IniDocument>(Paths);
            foreach (var item in after)
            {
                if (before[item.Key] == item.Value) continue;
                var (file, section, key) = item.Key;
                var path = Path.Combine(snapshot.ProfileDirectory, file);
                if (!documents.TryGetValue(path, out var document))
                { document = new IniDocument(snapshot.Files[path].Bytes); documents[path] = document; }
                document.Set(section, key, item.Value, file == "foundation.ini");
            }
            // A previous in-game launcher can explicitly select gamepad-only
            // input. Disabling that pad must restore keyboard input for player1;
            // leave unchanged device assignments and unrelated edits byte exact.
            var configPath = Path.Combine(snapshot.ProfileDirectory, "config.ini");
            var originalConfig = new IniDocument(snapshot.Files[configPath].Bytes);
            foreach (var (oldEnabled, enabled, source, replacement) in new[]
            {
                (snapshot.OriginalSettings.EnableGamepad, settings.EnableGamepad, "SourceP1", "1"),
                (snapshot.OriginalSettings.EnableGamepad2, settings.EnableGamepad2, "SourceP2", "0")
            })
            {
                if (oldEnabled == enabled || enabled || originalConfig.Get("Controller", source) != "2") continue;
                if (!documents.TryGetValue(configPath, out var configDocument))
                { configDocument = new IniDocument(snapshot.Files[configPath].Bytes); documents[configPath] = configDocument; }
                configDocument.Set("Controller", source, replacement);
            }
            var changes = documents.Select(d => (Original: snapshot.Files[d.Key], Bytes: d.Value.ToBytes()))
                .Where(d => !d.Original.Bytes.AsSpan().SequenceEqual(d.Bytes)).ToArray();
            if (changes.Length == 0) return new(true, "No settings changed.", Load(snapshot.RootDirectory, snapshot.ProfileDirectory));
            Directory.CreateDirectory(snapshot.ProfileDirectory);
            backup = Path.Combine(snapshot.ProfileDirectory, "backups", "settings-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fffffff", CultureInfo.InvariantCulture) + "-" + Guid.NewGuid().ToString("N")[..8]);
            RejectReparse(Path.Combine(snapshot.ProfileDirectory, "backups"));
            Directory.CreateDirectory(backup);
            var manifest = new List<object>();
            foreach (var change in changes)
            {
                RejectReparse(change.Original.Path);
                if (change.Original.Exists)
                {
                    var destination = Path.Combine(backup, Path.GetFileName(change.Original.Path));
                    File.Copy(change.Original.Path, destination, false);
                    if (Hash(File.ReadAllBytes(destination)) != change.Original.Sha256)
                        throw new IOException("Settings backup verification failed; no config was replaced.");
                }
                manifest.Add(new { file = Path.GetFileName(change.Original.Path), existed = change.Original.Exists,
                    original_sha256 = change.Original.Sha256, edited_sha256 = Hash(change.Bytes) });
            }
            WriteDurable(Path.Combine(backup, "settings-backup.json"), JsonSerializer.SerializeToUtf8Bytes(manifest, new JsonSerializerOptions { WriteIndented = true }));
            var prepared = new List<(FileIdentity Original, string Temp, string Hash)>();
            foreach (var change in changes)
            {
                var temp = Path.Combine(snapshot.ProfileDirectory, ".companion-" + Guid.NewGuid().ToString("N") + ".tmp");
                temporary.Add(temp); WriteDurable(temp, change.Bytes);
                var hash = Hash(change.Bytes);
                if (Hash(File.ReadAllBytes(temp)) != hash) throw new IOException("Prepared config verification failed.");
                prepared.Add((change.Original, temp, hash));
            }
            EnsureUnchanged(snapshot); // Backups and durable temporary writes are finished before any replacement.
            foreach (var item in prepared)
            {
                if (running()) throw new InvalidOperationException("The game started while settings were being prepared. Close it and reload settings.");
                EnsureIdentity(item.Original);
                Replace(item.Temp, item.Original.Path, item.Original.Exists);
                replaced.Add((item.Original, item.Hash));
                if (Hash(File.ReadAllBytes(item.Original.Path)) != item.Hash) throw new IOException("Written config verification failed.");
            }
            return new(true, "Settings applied. Verified backup: " + backup, Load(snapshot.RootDirectory, snapshot.ProfileDirectory), backup);
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or InvalidOperationException or ArgumentException or System.Text.DecoderFallbackException)
        {
            var rollbackErrors = new List<string>();
            foreach (var item in replaced.AsEnumerable().Reverse())
            {
                try
                {
                    // Do not overwrite a concurrent editor's newer work during recovery.
                    if (!File.Exists(item.Original.Path) || Hash(File.ReadAllBytes(item.Original.Path)) != item.NewHash)
                        throw new IOException("Config changed during recovery: " + Path.GetFileName(item.Original.Path));
                    if (item.Original.Exists)
                    {
                        var temp = Path.Combine(snapshot.ProfileDirectory, ".companion-restore-" + Guid.NewGuid().ToString("N") + ".tmp");
                        temporary.Add(temp); WriteDurable(temp, item.Original.Bytes); Replace(temp, item.Original.Path, true);
                    }
                    else File.Delete(item.Original.Path);
                }
                catch (Exception recovery) when (recovery is IOException or UnauthorizedAccessException) { rollbackErrors.Add(recovery.Message); }
            }
            var message = error.Message;
            if (replaced.Count > 0 && rollbackErrors.Count == 0) message += " Applied configs were restored to their original bytes.";
            if (rollbackErrors.Count > 0) message += " Recovery needs attention; retain backup " + backup + ": " + string.Join("; ", rollbackErrors);
            return new(false, message, null, backup);
        }
        finally
        {
            foreach (var temp in temporary)
                try { if (File.Exists(temp)) File.Delete(temp); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
    }

    public static ProcessStartInfo BuildLaunch(ProfileSnapshot snapshot, LaunchRequest request)
    {
        EnsureUnchanged(snapshot);
        if (IsGameRunning(snapshot)) throw new InvalidOperationException("This profile's game is already running.");
        var refreshed = Load(snapshot.RootDirectory, snapshot.ProfileDirectory);
        if (!refreshed.Readiness.Ready) throw new InvalidOperationException(refreshed.Readiness.Message);
        if (snapshot.Files[Path.Combine(snapshot.ProfileDirectory, PublicSetupService.ManifestName)].Exists)
            return BuildSourceLaunch(snapshot, request);
        var script = request.Mode switch
        {
            LaunchMode.WidescreenPreview => "Start-LikadoPreview.ps1",
            LaunchMode.HdMenuPreview => "Start-HdMenuPreview.ps1",
            _ => "Start-Foundation.ps1"
        };
        if (!snapshot.Files[Path.Combine(snapshot.RootDirectory, "tools", script)].Exists)
            throw new InvalidOperationException("The selected launch helper is missing.");
        if (!Enum.IsDefined(request.Mode)) throw new ArgumentException("Unknown launch mode.");
        if (request.Mode != LaunchMode.Resume && request.SavePath is not null)
            throw new ArgumentException("A checkpoint is accepted only for explicit Resume.");
        if (request.Mode is LaunchMode.WidescreenPreview or LaunchMode.HdMenuPreview)
        {
            using var receipt = JsonDocument.Parse(snapshot.Files[ReceiptPath(snapshot.RootDirectory)].Bytes);
            var key = request.Mode == LaunchMode.WidescreenPreview ? "likado_terrain_preview_qualified" : "hd_menu_frames_qualified";
            if (!receipt.RootElement.TryGetProperty(key, out var qualified) || qualified.ValueKind != JsonValueKind.True)
                throw new InvalidOperationException("This preview has no qualified receipt.");
        }
        var powershell = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "WindowsPowerShell", "v1.0", "powershell.exe");
        var start = new ProcessStartInfo(powershell)
        {
            UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = snapshot.RootDirectory,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        foreach (var arg in new[] { "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", Path.Combine(snapshot.RootDirectory, "tools", script) }) start.ArgumentList.Add(arg);
        if (request.Mode is LaunchMode.WidescreenPreview or LaunchMode.HdMenuPreview)
        { start.ArgumentList.Add("-SourceProfileDirectory"); start.ArgumentList.Add(snapshot.ProfileDirectory); }
        else
        {
            start.ArgumentList.Add("-ProfileDirectory"); start.ArgumentList.Add(snapshot.ProfileDirectory);
            if (request.Mode == LaunchMode.OriginalView) start.ArgumentList.Add("-OriginalView");
            if (request.Mode == LaunchMode.Resume)
            {
                var save = RequireSave(snapshot, request.SavePath);
                if (File.Exists(Path.Combine(snapshot.ProfileDirectory, "fixture-resume.state")))
                    throw new InvalidOperationException("A pending resume copy already exists. It has been preserved; resolve it before choosing another checkpoint.");
                start.ArgumentList.Add("-ResumeCheckpoint"); start.ArgumentList.Add(save.Path);
            }
        }
        // The existing helper also sanitizes the child game immediately before launching.
        foreach (var key in start.Environment.Keys.Where(k => k.StartsWith("SNESRECOMP_", StringComparison.OrdinalIgnoreCase)).ToArray()) start.Environment.Remove(key);
        var windows = Environment.GetEnvironmentVariable("SystemRoot") ?? Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        start.Environment["PATH"] = Path.Combine(windows, "System32") + ";" + windows;
        return start; // ArgumentList, never a shell command assembled from profile/save paths.
    }

    public static bool SupportsQol(ProfileSnapshot snapshot) => SupportsQol(snapshot.ProfileDirectory, snapshot.Files);
    public static bool SupportsJournalPossession(ProfileSnapshot snapshot) => SupportsFoundationVersion(snapshot.ProfileDirectory, snapshot.Files, new Version(0, 2, 3));

    private static bool SupportsQol(string profile, IReadOnlyDictionary<string, FileIdentity> files) => SupportsFoundationVersion(profile, files, new Version(0, 2, 0));

    private static bool SupportsFoundationVersion(string profile, IReadOnlyDictionary<string, FileIdentity> files, Version minimum)
    {
        try
        {
            string? version;
            if (files.TryGetValue(Path.Combine(profile, PublicSetupService.ManifestName), out var manifest) && manifest.Exists)
            {
                var source = JsonSerializer.Deserialize<SourceProfile>(manifest.Bytes) ?? throw new InvalidOperationException("Source manifest is invalid.");
                using var receipt = JsonDocument.Parse(files[source.ReceiptPath].Bytes);
                version = receipt.RootElement.GetProperty("version").GetString();
            }
            else
            {
                var receipt = files.Values.FirstOrDefault(f => f.Path.EndsWith(Path.Combine("local", "evidence", "build-receipt.json"), StringComparison.OrdinalIgnoreCase));
                if (receipt?.Exists != true) return false;
                using var json = JsonDocument.Parse(receipt.Bytes); version = json.RootElement.TryGetProperty("release_version", out var release) ? release.GetString() : null;
            }
            return Version.TryParse(version, out var parsed) && parsed >= minimum;
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or KeyNotFoundException) { return false; }
    }

    private static bool QolChanged(GameSettings value, GameSettings original) =>
        value.XpMultiplierPercent != original.XpMultiplierPercent || value.GoldMultiplierPercent != original.GoldMultiplierPercent ||
        value.MovementSpeedPercent != original.MovementSpeedPercent || value.FastForwardToggle != original.FastForwardToggle ||
        value.LegacyControllerGestures != original.LegacyControllerGestures ||
        new[] { "BattleInfo", "Journal", "MovementBoost" }.Any(name => value.HotkeyBindings.GetValueOrDefault(name) != original.HotkeyBindings.GetValueOrDefault(name));

    private static ProcessStartInfo BuildSourceLaunch(ProfileSnapshot snapshot, LaunchRequest request)
    {
        if (!Enum.IsDefined(request.Mode)) throw new ArgumentException("Unknown launch mode.");
        if (request.Mode != LaunchMode.Resume && request.SavePath is not null) throw new ArgumentException("A checkpoint is accepted only for explicit Resume.");
        if (request.Mode is LaunchMode.HdMenuPreview or LaunchMode.WidescreenPreview)
            throw new InvalidOperationException("Private scene previews are not part of public setup. Set the optional presentation choices in Display, then start at the title.");
        var source = PublicSetupService.ReadProfile(snapshot.ProfileDirectory);
        var start = new ProcessStartInfo(Path.Combine(snapshot.ProfileDirectory, GameName + ".exe"))
        {
            WorkingDirectory = snapshot.ProfileDirectory, UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        foreach (var argument in new[] { "--no-launcher", "--rom", source.RomPath }) start.ArgumentList.Add(argument);
        foreach (var key in start.Environment.Keys.Where(k => k.StartsWith("SNESRECOMP_", StringComparison.OrdinalIgnoreCase)).ToArray()) start.Environment.Remove(key);
        var windows = Environment.GetEnvironmentVariable("SystemRoot") ?? Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        start.Environment["PATH"] = Path.Combine(windows, "System32") + ";" + windows;
        if (request.Mode == LaunchMode.OriginalView)
        {
            foreach (var enhancement in new[] { "BATTLE_INFO", "ENHANCED_PIXELS", "WIDE", "WIDE_ACTORS", "FAST_MENUS", "JOURNAL", "NATIVE_CLEAR", "NATIVE_COLUMNS", "HD_MENU_FRAMES" })
                start.Environment["SNESRECOMP_FOUNDATION_" + enhancement] = "0";
            foreach (var modifier in new[] { "XP_PERCENT", "GOLD_PERCENT", "MOVEMENT_PERCENT" }) start.Environment["SNESRECOMP_FOUNDATION_" + modifier] = "100";
        }
        if (request.Mode == LaunchMode.Resume)
        {
            var save = RequireSave(snapshot, request.SavePath);
            var pending = Path.Combine(snapshot.ProfileDirectory, "companion-resume.state"); RejectReparse(pending);
            if (File.Exists(pending)) throw new InvalidOperationException("A pending resume copy is preserved. Resolve it before selecting another checkpoint.");
            File.Copy(save.Path, pending, false);
            if (Hash(File.ReadAllBytes(pending)) != save.Sha256 || Hash(File.ReadAllBytes(save.Path)) != save.Sha256)
                throw new IOException("Checkpoint changed while preparing Resume. Its source and the pending copy are preserved.");
            start.ArgumentList.Add("--resume-state"); start.ArgumentList.Add(pending);
        }
        return start;
    }

    private static SaveEntry RequireSave(ProfileSnapshot snapshot, string? path)
    {
        if (string.IsNullOrWhiteSpace(path)) throw new ArgumentException("Choose a saved checkpoint for Resume.");
        path = Path.GetFullPath(path);
        var saveDirectory = Path.Combine(snapshot.ProfileDirectory, "saves");
        if (!Paths.Equals(Path.GetDirectoryName(path), saveDirectory) || !Path.GetExtension(path).Equals(".sav", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Resume accepts only saved .sav checkpoints directly inside this profile's saves folder.");
        RejectReparse(saveDirectory); RejectReparse(path);
        var found = snapshot.Saves.FirstOrDefault(s => Paths.Equals(s.Path, path)) ?? throw new InvalidOperationException("Checkpoint was not in the loaded list. Reload first.");
        if (!File.Exists(path) || Hash(File.ReadAllBytes(path)) != found.Sha256) throw new InvalidOperationException("Checkpoint changed since it was listed. Reload first.");
        return found;
    }

    private static IReadOnlyList<SaveEntry> ReadSaves(string profile)
    {
        var directory = Path.Combine(profile, "saves");
        if (!Directory.Exists(directory)) return Array.Empty<SaveEntry>();
        RejectReparse(directory);
        return Directory.EnumerateFiles(directory, "*", SearchOption.TopDirectoryOnly)
            .Where(p => Path.GetExtension(p).Equals(".sav", StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(File.GetLastWriteTimeUtc).ThenBy(p => p, Paths)
            .Select(p => { RejectReparse(p); var bytes = File.ReadAllBytes(p); return new SaveEntry(Path.GetFileName(p), Path.GetFullPath(p), File.GetLastWriteTimeUtc(p), bytes.Length) { Sha256 = Hash(bytes) }; }).ToArray();
    }

    private static ReadinessInfo CheckReadiness(string root, string profile, IReadOnlyDictionary<string, FileIdentity> files)
    {
        try
        {
            var sourceManifest = files[Path.Combine(profile, PublicSetupService.ManifestName)];
            if (sourceManifest.Exists)
            {
                var source = PublicSetupService.ReadProfile(profile);
                var build = PublicSetupService.CheckBuild(root, source.ReceiptPath);
                if (files[build.ReceiptPath].Sha256 != source.ReceiptSha256 || build.ExecutableSha256 != source.ExecutableSha256)
                    return new(false, "Source build receipt changed. Existing profile and saves are preserved; adopt a new build through Setup.");
                var installedSource = files[Path.Combine(profile, GameName + ".exe")];
                if (!installedSource.Exists || installedSource.Sha256 != source.ExecutableSha256)
                    return new(false, "Source profile executable differs from its recorded compilation.");
                var ownedRom = files[Path.GetFullPath(source.RomPath)];
                if (!ownedRom.Exists || ownedRom.Bytes.LongLength != 1572864 || ownedRom.Sha256 != RomHash)
                    return new(false, "Selected owned ROM is missing or changed. Re-select the exact clean USA ROM through Setup.");
                return new(true, "Source build ready: compilation verified; gameplay unqualified. Play starts at the title and Resume uses a selected copied checkpoint.");
            }
            var receipt = files[ReceiptPath(root)];
            if (!receipt.Exists) return new(false, "Foundation build receipt is missing.");
            using var document = JsonDocument.Parse(receipt.Bytes);
            var expected = document.RootElement.GetProperty("release_executable_sha256").GetString();
            var binary = files[Path.Combine(root, "local", "native-proof", GameName, "build", GameName + ".exe")];
            if (!binary.Exists || !binary.Sha256.Equals(expected, StringComparison.OrdinalIgnoreCase)) return new(false, "Foundation binary differs from the qualified receipt.");
            var rom = files[Path.Combine(root, "local", "inputs", "clean-usa.sfc")];
            if (!rom.Exists || rom.Sha256 != RomHash) return new(false, "Supported local clean USA ROM is missing or differs from its verified hash.");
            if (!files[Path.Combine(root, "tools", "Start-Foundation.ps1")].Exists) return new(false, "Foundation launch helper is missing.");
            var installed = files[Path.Combine(profile, GameName + ".exe")];
            if (installed.Exists && !installed.Sha256.Equals(expected, StringComparison.OrdinalIgnoreCase))
            {
                var known = document.RootElement.TryGetProperty("previous_release_executable_sha256", out var previous) &&
                    previous.EnumerateArray().Any(v => installed.Sha256.Equals(v.GetString(), StringComparison.OrdinalIgnoreCase));
                if (!known) return new(false, "Installed profile binary is unrecognized. Its saves and settings are preserved.");
                return new(true, "Qualified foundation ready. The helper will back up and update this recognized older profile build.");
            }
            return new(true, "Qualified foundation ready. Play starts at the title; Resume uses only the selected copied checkpoint.");
        }
        catch (Exception error) when (error is JsonException or InvalidOperationException or KeyNotFoundException or IOException or UnauthorizedAccessException)
        { return new(false, "Build receipt is invalid: " + error.Message); }
    }

    private static GameSettings ReadSettings(IniDocument config, IniDocument foundation, IniDocument bindings)
    {
        var settings = new GameSettings
        {
        Fullscreen = Bool(config.Get("Graphics", "Fullscreen"), false), WindowScale = Number(config.Get("Graphics", "WindowScale"), 4),
        VSync = Bool(config.Get("Graphics", "VSync"), true), Renderer = config.Get("Graphics", "Renderer") ?? "direct3d11",
        NoSpriteLimits = Bool(config.Get("Graphics", "NoSpriteLimits"), false), EnableAudio = Bool(config.Get("Sound", "EnableAudio"), true),
        Volume = Number(config.Get("Sound", "Volume"), 70), EnableGamepad = Bool(config.Get("GamepadMap", "EnableGamepad1"), true),
        EnableGamepad2 = Bool(config.Get("GamepadMap", "EnableGamepad2"), false), Deadzone = Number(config.Get("GamepadMap", "GamepadDeadzone"), 3277),
        BattleInfo = Bool(foundation.Get("Enhancements", "BattleInfo", true), true), EnhancedPixels = Bool(foundation.Get("Enhancements", "EnhancedPixels", true), true),
        FastMenus = Bool(foundation.Get("Enhancements", "FastMenus", true), true), Journal = Bool(foundation.Get("Enhancements", "Journal", true), true),
        JournalPossession = Bool(foundation.Get("Enhancements", "JournalPossession", true), true),
        HdMenuFrames = Bool(foundation.Get("Enhancements", "HdMenuFrames", true), false),
        ExperimentalFieldWide = Bool(foundation.Get("Enhancements", "ExperimentalFieldWide", true), false),
        ExperimentalFieldActors = Bool(foundation.Get("Enhancements", "ExperimentalFieldActors", true), false),
        XpMultiplierPercent = Number(foundation.Get("Enhancements", "XpMultiplierPercent", true), 100),
        GoldMultiplierPercent = Number(foundation.Get("Enhancements", "GoldMultiplierPercent", true), 100),
        MovementSpeedPercent = Number(foundation.Get("Enhancements", "MovementSpeedPercent", true), 200),
        FastForwardToggle = Bool(foundation.Get("Enhancements", "FastForwardToggle", true), false),
        LegacyControllerGestures = Bool(foundation.Get("Enhancements", "LegacyControllerGestures", true), true),
        HotkeyBindings = HotkeyCatalog.CreateBindings(), GameplayKeys = HotkeyCatalog.CreateGameplayKeys()
        };
        foreach (var name in settings.HotkeyBindings.Keys.ToArray())
        {
            var fallback = settings.HotkeyBindings[name];
            settings.HotkeyBindings[name] = new HotkeyBinding(config.Get("KeyMap", name) ?? fallback.Keyboard,
                config.Get("GamepadMap", name) ?? fallback.Controller);
        }
        foreach (var name in settings.GameplayKeys.Keys.ToArray())
        {
            var parts = name.Split(':'); settings.GameplayKeys[name] = bindings.Get(parts[0], parts[1]) ?? settings.GameplayKeys[name];
        }
        return settings;
    }

    private static Dictionary<(string File, string Section, string Key), string> Values(GameSettings settings)
    {
        string B(bool value) => value ? "1" : "0";
        string N(int value) => value.ToString(CultureInfo.InvariantCulture);
        var result = new Dictionary<(string File, string Section, string Key), string>
        {
            [("config.ini", "Graphics", "Fullscreen")] = B(settings.Fullscreen), [("config.ini", "Graphics", "WindowScale")] = N(settings.WindowScale),
            [("config.ini", "Graphics", "VSync")] = B(settings.VSync), [("config.ini", "Graphics", "Renderer")] = settings.Renderer,
            [("config.ini", "Graphics", "NoSpriteLimits")] = B(settings.NoSpriteLimits), [("config.ini", "Sound", "EnableAudio")] = B(settings.EnableAudio),
            [("config.ini", "Sound", "Volume")] = N(settings.Volume), [("config.ini", "GamepadMap", "EnableGamepad1")] = B(settings.EnableGamepad),
            [("config.ini", "GamepadMap", "EnableGamepad2")] = B(settings.EnableGamepad2), [("config.ini", "GamepadMap", "GamepadDeadzone")] = N(settings.Deadzone),
            [("foundation.ini", "Enhancements", "BattleInfo")] = B(settings.BattleInfo), [("foundation.ini", "Enhancements", "EnhancedPixels")] = B(settings.EnhancedPixels),
            [("foundation.ini", "Enhancements", "FastMenus")] = B(settings.FastMenus), [("foundation.ini", "Enhancements", "Journal")] = B(settings.Journal),
            [("foundation.ini", "Enhancements", "JournalPossession")] = B(settings.JournalPossession),
            [("foundation.ini", "Enhancements", "HdMenuFrames")] = B(settings.HdMenuFrames),
            [("foundation.ini", "Enhancements", "ExperimentalFieldWide")] = B(settings.ExperimentalFieldWide),
            [("foundation.ini", "Enhancements", "ExperimentalFieldActors")] = B(settings.ExperimentalFieldActors),
            [("foundation.ini", "Enhancements", "XpMultiplierPercent")] = N(settings.XpMultiplierPercent),
            [("foundation.ini", "Enhancements", "GoldMultiplierPercent")] = N(settings.GoldMultiplierPercent),
            [("foundation.ini", "Enhancements", "MovementSpeedPercent")] = N(settings.MovementSpeedPercent),
            [("foundation.ini", "Enhancements", "FastForwardToggle")] = B(settings.FastForwardToggle),
            [("foundation.ini", "Enhancements", "LegacyControllerGestures")] = B(settings.LegacyControllerGestures)
        };
        foreach (var binding in settings.HotkeyBindings)
        {
            if (binding.Key is not ("Controls" or "ControlsP2")) result[("config.ini", "KeyMap", binding.Key)] = binding.Value.Keyboard;
            result[("config.ini", "GamepadMap", binding.Key)] = binding.Value.Controller;
        }
        foreach (var binding in settings.GameplayKeys)
        {
            var parts = binding.Key.Split(':'); result[("keybinds.ini", parts[0], parts[1])] = binding.Value;
        }
        return result;
    }
    private static bool Bool(string? value, bool fallback) => value?.ToLowerInvariant() switch
    { "1" or "true" or "yes" or "on" or "2" => true, "0" or "false" or "no" or "off" => false, _ => fallback };
    private static int Number(string? value, int fallback) => int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var result) ? result : fallback;
    private static void Validate(GameSettings value, GameSettings old)
    {
        // Preserve existing custom/legacy values when another setting changes.
        // In particular WindowScale=0 is the runtime's existing automatic mode.
        if (value.WindowScale != old.WindowScale && value.WindowScale is < 1 or > 8) throw new ArgumentException("Window scale must be 1 to 8.");
        if (value.Volume != old.Volume && value.Volume is < 0 or > 100) throw new ArgumentException("Volume must be 0 to 100.");
        if (value.Deadzone != old.Deadzone && value.Deadzone is < 0 or > 32767) throw new ArgumentException("Controller deadzone must be 0 to 32767 raw units.");
        if (value.Renderer != old.Renderer && value.Renderer is not ("direct3d11" or "opengl" or "software"))
            throw new ArgumentException("Choose Direct3D 11, OpenGL or software rendering.");
        if (value.Renderer is null || value.Renderer.IndexOfAny(new[] { '\r', '\n', '\0' }) >= 0) throw new ArgumentException("Renderer must be a single setting value.");
        if (value.XpMultiplierPercent != old.XpMultiplierPercent && value.XpMultiplierPercent is < 100 or > 1000) throw new ArgumentException("XP rate must be 100 to 1000 percent.");
        if (value.GoldMultiplierPercent != old.GoldMultiplierPercent && value.GoldMultiplierPercent is < 100 or > 1000) throw new ArgumentException("Gold rate must be 100 to 1000 percent.");
        if (value.MovementSpeedPercent != old.MovementSpeedPercent && value.MovementSpeedPercent is < 100 or > 300) throw new ArgumentException("Movement boost must be 100 to 300 percent.");
        HotkeyCatalog.Validate(value, old);
    }
    private static string ReceiptPath(string root) => Path.Combine(root, "local", "evidence", "build-receipt.json");
    private static bool HasExited(Process process) { try { return process.HasExited; } catch (InvalidOperationException) { return true; } }
    private static string Hash(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    private static void Track(IDictionary<string, FileIdentity> files, string path)
    {
        RejectReparse(path);
        var exists = File.Exists(path); var bytes = exists ? File.ReadAllBytes(path) : Array.Empty<byte>();
        files[path] = new(path, exists, exists ? Hash(bytes) : "", bytes);
    }
    private static void EnsureUnchanged(ProfileSnapshot snapshot)
    { foreach (var identity in snapshot.Files.Values) EnsureIdentity(identity); }
    private static void EnsureIdentity(FileIdentity identity)
    {
        RejectReparse(identity.Path);
        if (File.Exists(identity.Path) != identity.Exists || (identity.Exists && Hash(File.ReadAllBytes(identity.Path)) != identity.Sha256))
            throw new InvalidOperationException(Path.GetFileName(identity.Path) + " changed since settings were loaded. Reload before continuing.");
    }
    private static void RejectReparse(string path)
    {
        if ((File.Exists(path) || Directory.Exists(path)) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new InvalidOperationException("Linked config/profile/checkpoint paths are not supported: " + path);
    }
    private static void WriteDurable(string path, byte[] bytes)
    { using var file = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough); file.Write(bytes); file.Flush(true); }
    private static void Replace(string temp, string path, bool exists)
    { if (exists) File.Replace(temp, path, null); else File.Move(temp, path); }
}
