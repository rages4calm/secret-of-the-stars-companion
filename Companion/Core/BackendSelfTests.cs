using System.Security.Cryptography;
using System.Text;

namespace SecretOfTheStars.Companion.Core;

/// <summary>Focused backend tests. They create only one unique disposable
/// directory and never read or modify an owner profile, ROM, or installation.</summary>
public static class BackendSelfTests
{
    public static IReadOnlyList<string> Run()
    {
        var passed = new List<string>();
        void Check(string name, bool value) { if (!value) throw new InvalidOperationException("Backend self-test failed: " + name); passed.Add(name); }
        var utf8 = new UTF8Encoding(false);
        var source = Encoding.UTF8.GetPreamble().Concat(utf8.GetBytes(
            "# keep café 🎮\r\n[Graphics]\r\nFullscreen = 0 ; retain comment\nfullscreen=0\r\n[Sound]\nVolume  = 70\n[Sound]\r\nvolume = 70  # old duplicate\r\n[Custom]\nOpaque=零\n")).ToArray();
        var ini = new IniDocument(source);
        Check("UTF8 BOM and mixed line endings no-op byte parity", ini.ToBytes().AsSpan().SequenceEqual(source));
        Check("last duplicate value read", ini.Get("Sound", "Volume") == "70");
        ini.Set("Sound", "Volume", "90");
        var expected = Encoding.UTF8.GetPreamble().Concat(utf8.GetBytes(
            "# keep café 🎮\r\n[Graphics]\r\nFullscreen = 0 ; retain comment\nfullscreen=0\r\n[Sound]\nVolume  = 90\n[Sound]\r\nvolume = 90  # old duplicate\r\n[Custom]\nOpaque=零\n")).ToArray();
        Check("known duplicates updated with unknown bytes/spacing/comments retained", ini.ToBytes().AsSpan().SequenceEqual(expected));
        ini.Set("Graphics", "Fullscreen", "1");
        Check("case-insensitive config duplicates coherent", ini.Get("Graphics", "Fullscreen") == "1" &&
            Encoding.UTF8.GetString(ini.ToBytes()).Contains("Fullscreen = 1 ; retain comment\nfullscreen=1"));
        var original16 = Encoding.Unicode.GetPreamble().Concat(Encoding.Unicode.GetBytes("[Sound]\r\nVolume = 70\r\nUnknown=Ω\r\n")).ToArray();
        var unicode = new IniDocument(original16);
        Check("UTF16 BOM no-op byte parity", unicode.ToBytes().AsSpan().SequenceEqual(original16));
        unicode.Set("Sound", "Volume", "71");
        Check("UTF16 precise edit", unicode.ToBytes().AsSpan().SequenceEqual(Encoding.Unicode.GetPreamble().Concat(
            Encoding.Unicode.GetBytes("[Sound]\r\nVolume = 71\r\nUnknown=Ω\r\n")).ToArray()));
        var native = new IniDocument(Encoding.ASCII.GetBytes("[Enhancements]\nJournal=1\n[Other]\nJournal=0\nUnknown=7"));
        Check("title settings parser observes last canonical key across sections", native.Get("Enhancements", "Journal", true) == "0");
        native.Set("Enhancements", "Journal", "1", true);
        Check("title duplicate assignment coherence", Encoding.ASCII.GetString(native.ToBytes()) == "[Enhancements]\nJournal=1\n[Other]\nJournal=1\nUnknown=7");
        var missing = new IniDocument(Encoding.ASCII.GetBytes("[Graphics]\r\nUnknown=7"));
        missing.Set("Graphics", "VSync", "1");
        Check("missing key appended to correct section", Encoding.ASCII.GetString(missing.ToBytes()) == "[Graphics]\r\nUnknown=7\r\nVSync=1\r\n");

        var temporaryRoot = Path.GetFullPath(Path.Combine(Path.GetTempPath(), "sots-companion-core-" + Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(temporaryRoot);
        try
        {
            var profile = Path.Combine(temporaryRoot, "profile with space $tick` ; café");
            Directory.CreateDirectory(profile);
            var config = Path.Combine(profile, "config.ini");
            File.WriteAllBytes(config, source);
            var bindings = Path.Combine(profile, "keybinds.ini");
            var bindingBytes = Encoding.UTF8.GetBytes("[KeyMap]\nCustom = Alt+Q\n[GamepadMap]\nControls = Owner,Custom,Buttons\n");
            File.WriteAllBytes(bindings, bindingBytes);
            var saves = Path.Combine(profile, "saves"); Directory.CreateDirectory(saves);
            var checkpoint = Path.Combine(saves, "save0.sav"); var saveBytes = new byte[] { 9, 8, 7, 0, 6 };
            File.WriteAllBytes(checkpoint, saveBytes);
            var snapshot = ProfileService.Load(temporaryRoot, profile);
            Check("profile load does not manufacture config/save files", !File.Exists(Path.Combine(profile, "foundation.ini")) && snapshot.Saves.Count == 1);
            var noOp = ProfileService.ApplyCore(snapshot, snapshot.Settings with { }, () => false);
            Check("service no-op has no backup or rewritten bytes", noOp.Success && noOp.BackupDirectory is null && File.ReadAllBytes(config).AsSpan().SequenceEqual(source));
            var edited = snapshot.Settings with { Volume = 90, HdMenuFrames = true };
            var applied = ProfileService.ApplyCore(snapshot, edited, () => false);
            Check("config and missing foundation setting apply", applied.Success && applied.Snapshot?.Settings.Volume == 90 && applied.Snapshot.Settings.HdMenuFrames);
            Check("hash-verified original config backup", applied.BackupDirectory is not null &&
                File.ReadAllBytes(Path.Combine(applied.BackupDirectory, "config.ini")).AsSpan().SequenceEqual(source));
            Check("custom bindings preserved byte-for-byte", File.ReadAllBytes(bindings).AsSpan().SequenceEqual(bindingBytes));
            Check("checkpoint preserved byte-for-byte", File.ReadAllBytes(checkpoint).AsSpan().SequenceEqual(saveBytes));
            var beforeRefusal = File.ReadAllBytes(config);
            var refusedRunning = ProfileService.ApplyCore(applied.Snapshot!, applied.Snapshot!.Settings with { Volume = 85 }, () => true);
            Check("running-game refusal before writes", !refusedRunning.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(beforeRefusal));
            var invalid = ProfileService.ApplyCore(applied.Snapshot, applied.Snapshot.Settings with { Deadzone = -1 }, () => false);
            Check("range validation before writes", !invalid.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(beforeRefusal));
            var injected = ProfileService.ApplyCore(applied.Snapshot, applied.Snapshot.Settings with { Renderer = "software\nAutosave=1" }, () => false);
            Check("multiline setting rejected", !injected.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(beforeRefusal));
            File.AppendAllText(bindings, "# external binding edit\n");
            var staleBindings = ProfileService.ApplyCore(applied.Snapshot, applied.Snapshot.Settings with { Volume = 80 }, () => false);
            Check("external custom-bindings change refuses stale apply", !staleBindings.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(beforeRefusal));
            var fresh = ProfileService.Load(temporaryRoot, profile);
            File.AppendAllText(config, "# external config edit\n");
            var changedBytes = File.ReadAllBytes(config);
            var stale = ProfileService.ApplyCore(fresh, fresh.Settings with { Volume = 80 }, () => false);
            Check("external config change refuses stale apply", !stale.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(changedBytes));
            var after = ProfileService.Load(temporaryRoot, profile);
            Check("missing receipt/ROM marks launch unready", !after.Readiness.Ready);
            var launchRefused = false;
            try { ProfileService.BuildLaunch(after, new(LaunchMode.Play)); } catch (InvalidOperationException) { launchRefused = true; }
            Check("unqualified launch rejected without writing saves", launchRefused && File.ReadAllBytes(checkpoint).AsSpan().SequenceEqual(saveBytes));

            // Simulate the game becoming active after the first file replacement.
            // The backend must restore those original bytes; no incomplete setting pair.
            var calls = 0;
            var rollback = ProfileService.ApplyCore(after, after.Settings with { Volume = 55, HdMenuFrames = false }, () => ++calls >= 3);
            Check("partial apply rolls back to original bytes", !rollback.Success &&
                File.ReadAllBytes(config).AsSpan().SequenceEqual(changedBytes) && ProfileService.Load(temporaryRoot, profile).Settings.HdMenuFrames);
            Check("all refusal/recovery paths preserve checkpoint", File.ReadAllBytes(checkpoint).AsSpan().SequenceEqual(saveBytes));
            var beforeConflict = ProfileService.Load(temporaryRoot, profile);
            var foundationPath = Path.Combine(profile, "foundation.ini");
            var foundationBefore = File.ReadAllBytes(foundationPath);
            var probes = 0;
            var conflict = ProfileService.ApplyCore(beforeConflict, beforeConflict.Settings with { Volume = 54, HdMenuFrames = false }, () =>
            {
                if (++probes == 2) File.AppendAllText(foundationPath, "# concurrent editor\n");
                return false;
            });
            Check("source change during staged apply preserves concurrent edit and rolls back other config", !conflict.Success &&
                File.ReadAllBytes(config).AsSpan().SequenceEqual(changedBytes) &&
                File.ReadAllBytes(foundationPath).AsSpan().SequenceEqual(foundationBefore.Concat(Encoding.UTF8.GetBytes("# concurrent editor\n")).ToArray()));
            File.AppendAllText(foundationPath, "ExperimentalFieldWide = 1 ; custom mixed setting\nExperimentalFieldActors=0\n");
            var mixed = ProfileService.Load(temporaryRoot, profile);
            var mixedBytes = File.ReadAllBytes(foundationPath);
            Check("mixed existing wide/actor flags load independently", mixed.Settings.ExperimentalFieldWide && !mixed.Settings.ExperimentalFieldActors);
            var unrelated = ProfileService.ApplyCore(mixed, mixed.Settings with { Volume = 57 }, () => false);
            Check("unrelated settings retain mixed wide/actor config bytes", unrelated.Success && File.ReadAllBytes(foundationPath).AsSpan().SequenceEqual(mixedBytes));
            var paired = ProfileService.ApplyCore(unrelated.Snapshot!, unrelated.Snapshot!.Settings with { ExperimentalFieldWide = true, ExperimentalFieldActors = true }, () => false);
            Check("paired wide/actor settings reach their independent native keys", paired.Success && paired.Snapshot!.Settings.ExperimentalFieldWide && paired.Snapshot.Settings.ExperimentalFieldActors);
            Check("paired edit retains untouched custom terrain flag line", Encoding.UTF8.GetString(File.ReadAllBytes(foundationPath)).Contains("ExperimentalFieldWide = 1 ; custom mixed setting\nExperimentalFieldActors=1\n"));
            File.AppendAllText(config, "\n[Controller]\nSourceP1=2\nSourceP2=1\n[GamepadMap]\nEnableGamepad1=1\nEnableGamepad2=0\n");
            var deviceSource = ProfileService.Load(temporaryRoot, profile);
            var deviceBytes = File.ReadAllBytes(config);
            var deviceNoOp = ProfileService.ApplyCore(deviceSource, deviceSource.Settings.DeepCopy(), () => false);
            Check("Device source selection remains byte exact on no-op", deviceNoOp.Success && File.ReadAllBytes(config).AsSpan().SequenceEqual(deviceBytes));
            var keyboardFallback = ProfileService.ApplyCore(deviceSource, deviceSource.Settings.DeepCopy() with { EnableGamepad = false }, () => false);
            var fallbackConfig = new IniDocument(File.ReadAllBytes(config));
            Check("Disabling gamepad-only player1 restores keyboard source", keyboardFallback.Success && fallbackConfig.Get("Controller", "SourceP1") == "1" && fallbackConfig.Get("GamepadMap", "EnableGamepad1") == "0");
            Check("Player2 custom keyboard source survives unrelated pad disable", fallbackConfig.Get("Controller", "SourceP2") == "1");

            // Settings-only capability fixtures declare a version, never native
            // qualification. Actual source receipt adoption is tested separately.
            var encounterProfile = Path.Combine(temporaryRoot, "encounter settings");
            Directory.CreateDirectory(encounterProfile);
            var encounterConfig = Path.Combine(encounterProfile, "config.ini");
            var encounterFoundation = Path.Combine(encounterProfile, "foundation.ini");
            var encounterBindings = Path.Combine(encounterProfile, "keybinds.ini");
            var encounterSave = Path.Combine(encounterProfile, "saves", "save0.sav");
            Directory.CreateDirectory(Path.GetDirectoryName(encounterSave)!);
            File.WriteAllBytes(encounterConfig, Encoding.UTF8.GetBytes("[Sound]\nVolume = 70\n[Owner]\nOpaque=café\n"));
            File.WriteAllBytes(encounterBindings, bindingBytes);
            File.WriteAllBytes(encounterSave, saveBytes);
            var settingsReceipt = Path.Combine(temporaryRoot, "local", "evidence", "build-receipt.json");
            Directory.CreateDirectory(Path.GetDirectoryName(settingsReceipt)!);
            void EncounterVersion(string version) => File.WriteAllText(settingsReceipt,
                System.Text.Json.JsonSerializer.Serialize(new { release_version = version, fixture_scope = "settings capability only; not a qualified build" }));
            Dictionary<string, string> EncounterHashes() => Directory.EnumerateFiles(encounterProfile, "*", SearchOption.AllDirectories)
                .Where(p => !Path.GetRelativePath(encounterProfile, p).StartsWith("backups" + Path.DirectorySeparatorChar))
                .ToDictionary(p => Path.GetRelativePath(encounterProfile, p), p => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(p))));
            bool SameEncounterHashes(Dictionary<string, string> before) => before.OrderBy(p => p.Key).SequenceEqual(EncounterHashes().OrderBy(p => p.Key));
            var defaultEncounter = ProfileService.Load(temporaryRoot, encounterProfile);
            Check("Encounter model and missing key default to original100 without writing", new GameSettings().RandomEncounterPercent == 100 && defaultEncounter.Settings.RandomEncounterPercent == 100 && !File.Exists(encounterFoundation));
            var missingNoOp = ProfileService.ApplyCore(defaultEncounter, defaultEncounter.Settings.DeepCopy(), () => false);
            Check("Missing encounter key no-op does not manufacture foundation setting", missingNoOp.Success && missingNoOp.BackupDirectory is null && !File.Exists(encounterFoundation));
            var missingBefore = EncounterHashes();
            Check("Missing native version refuses changed encounter setting without writes", !ProfileService.ApplyCore(defaultEncounter, defaultEncounter.Settings with { RandomEncounterPercent = 50 }, () => false).Success && SameEncounterHashes(missingBefore));
            EncounterVersion("0.3.5");
            var oldEncounter = ProfileService.Load(temporaryRoot, encounterProfile);
            Check("Pre036 capability excludes encounter changes", !ProfileService.SupportsEncounterRate(oldEncounter));
            var olderBefore = EncounterHashes();
            Check("Pre036 encounter Apply refuses before changing any profile bytes", !ProfileService.ApplyCore(oldEncounter, oldEncounter.Settings with { RandomEncounterPercent = 0 }, () => false).Success && SameEncounterHashes(olderBefore));
            var oldUnrelated = ProfileService.ApplyCore(oldEncounter, oldEncounter.Settings with { Volume = 69 }, () => false);
            Check("Older native unrelated settings Apply keeps missing encounter key absent", oldUnrelated.Success && !File.Exists(encounterFoundation));
            EncounterVersion("0.3.6");
            var currentEncounter = ProfileService.Load(temporaryRoot, encounterProfile);
            Check("036 capability admits encounter settings", ProfileService.SupportsEncounterRate(currentEncounter));
            var unknownEncounterBytes = Encoding.UTF8.GetPreamble().Concat(utf8.GetBytes("# café 🎮\r\n[Enhancements]\nRandomEncounterPercent = 100 ; keep\r\n[Other]\nrandomencounterpercent=100\r\nOpaque=零\n")).ToArray();
            File.WriteAllBytes(encounterFoundation, unknownEncounterBytes);
            currentEncounter = ProfileService.Load(temporaryRoot, encounterProfile);
            var unchangedConfig = File.ReadAllBytes(encounterConfig);
            foreach (var percent in new[] { 0, 50, 100 })
            {
                var appliedEncounter = ProfileService.ApplyCore(currentEncounter, currentEncounter.Settings with { RandomEncounterPercent = percent }, () => false);
                Check("Encounter rate applies and reloads " + percent, appliedEncounter.Success && appliedEncounter.Snapshot!.Settings.RandomEncounterPercent == percent);
                currentEncounter = appliedEncounter.Snapshot!;
                var expectedEncounter = new IniDocument(unknownEncounterBytes);
                expectedEncounter.Set("Enhancements", "RandomEncounterPercent", percent.ToString(System.Globalization.CultureInfo.InvariantCulture), true);
                Check("Encounter edit preserves BOM/unknown/comment/duplicate bytes " + percent, File.ReadAllBytes(encounterFoundation).AsSpan().SequenceEqual(expectedEncounter.ToBytes()));
                Check("Encounter edit preserves config/custom bindings/save " + percent, File.ReadAllBytes(encounterConfig).AsSpan().SequenceEqual(unchangedConfig) && File.ReadAllBytes(encounterBindings).AsSpan().SequenceEqual(bindingBytes) && File.ReadAllBytes(encounterSave).AsSpan().SequenceEqual(saveBytes));
            }
            foreach (var badPercent in new[] { -1, 101, int.MinValue, int.MaxValue })
            {
                var beforeBad = EncounterHashes();
                Check("Invalid encounter rate refuses with no writes " + badPercent, !ProfileService.ApplyCore(currentEncounter, currentEncounter.Settings with { RandomEncounterPercent = badPercent }, () => false).Success && SameEncounterHashes(beforeBad));
            }
            var beforeRunning = EncounterHashes();
            Check("Running-game encounter edit refuses before writes", !ProfileService.ApplyCore(currentEncounter, currentEncounter.Settings with { RandomEncounterPercent = 50 }, () => true).Success && SameEncounterHashes(beforeRunning));
            var noOpEncounter = ProfileService.ApplyCore(currentEncounter, currentEncounter.Settings.DeepCopy(), () => false);
            Check("Explicit100 encounter no-op is byte exact and makes no backup", noOpEncounter.Success && noOpEncounter.BackupDirectory is null && SameEncounterHashes(beforeRunning));
            File.WriteAllBytes(encounterFoundation, utf8.GetBytes("[Enhancements]\nRandomEncounterPercent=150\nUnknown=café\n"));
            var legacyInvalidEncounter = ProfileService.Load(temporaryRoot, encounterProfile);
            var invalidStoredBytes = File.ReadAllBytes(encounterFoundation);
            var preservedInvalid = ProfileService.ApplyCore(legacyInvalidEncounter, legacyInvalidEncounter.Settings with { Volume = 68 }, () => false);
            Check("Unchanged preexisting out-of-range encounter value survives unrelated Apply", preservedInvalid.Success && File.ReadAllBytes(encounterFoundation).AsSpan().SequenceEqual(invalidStoredBytes));
            var correctedEncounter = ProfileService.ApplyCore(preservedInvalid.Snapshot!, preservedInvalid.Snapshot!.Settings with { RandomEncounterPercent = 100 }, () => false);
            Check("Explicit user correction restores original100 from out-of-range setting", correctedEncounter.Success && correctedEncounter.Snapshot!.Settings.RandomEncounterPercent == 100);
            var staleEncounter = correctedEncounter.Snapshot!;
            File.AppendAllText(encounterFoundation, "# outside edit\n");
            var staleBefore = EncounterHashes();
            Check("Stale encounter Apply refuses and preserves external edit", !ProfileService.ApplyCore(staleEncounter, staleEncounter.Settings with { RandomEncounterPercent = 50 }, () => false).Success && SameEncounterHashes(staleBefore));
        }
        finally
        {
            // Only this exact GUID directory created above is removed.
            if (Path.GetDirectoryName(temporaryRoot) == Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar) &&
                Path.GetFileName(temporaryRoot).StartsWith("sots-companion-core-", StringComparison.Ordinal))
                Directory.Delete(temporaryRoot, true);
        }
        return passed;
    }
}
