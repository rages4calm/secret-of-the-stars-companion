using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class PublicSetupTests
{
    public static int Run(string root, string output, string? romPath)
    {
        output = Path.GetFullPath(output);
        if (Directory.Exists(output)) throw new IOException("Public self-test output must be a new directory.");
        Directory.CreateDirectory(output);
        var checks = new List<string>(BackendSelfTests.Run());
        void Check(string name, bool condition) { if (!condition) throw new InvalidOperationException(name); checks.Add(name); }
        void Refused(string name, Action action)
        {
            bool failed = false;
            try { action(); } catch (Exception error) when (error is InvalidOperationException or ArgumentException or IOException) { failed = true; }
            Check(name, failed);
        }
        var isolated = Path.Combine(output, "fresh clone $tick` ; café"); Directory.CreateDirectory(isolated);
        var missing = ProfileService.Load(isolated);
        Check("Fresh clone has no fabricated installation/readiness", !missing.Readiness.Ready && PublicSetupService.DiscoverBuilds(isolated).Count == 0);
        Check("Fresh clone load creates no profile or save files", !Directory.Exists(missing.ProfileDirectory));
        var invalid = Path.Combine(output, "unsupported.sfc"); File.WriteAllBytes(invalid, [1, 2, 3]);
        Refused("Unsupported ROM rejected before setup", () => PublicSetupService.ValidateRom(invalid));
        Refused("Build receipt outside isolated source-build folder rejected", () => PublicSetupService.CheckBuild(isolated, Path.Combine(root, "local", "evidence", "build-receipt.json")));
        Check("Missing setup selection is harmless", PublicSetupService.GetSelectedProfile(isolated) is null);
        var staleSetupFolder = Path.Combine(isolated, "local", "companion-public"); Directory.CreateDirectory(staleSetupFolder);
        var staleSetup = Path.Combine(staleSetupFolder, "setup.json"); File.WriteAllText(staleSetup, "{invalid retained selection");
        var staleBytes = File.ReadAllBytes(staleSetup);
        Check("Malformed prior selection recovers to Setup without replacing bytes", PublicSetupService.GetSelectedProfile(isolated) is null && PublicSetupService.GetSelectionProblem(isolated) is not null && File.ReadAllBytes(staleSetup).AsSpan().SequenceEqual(staleBytes));
        bool compilationCase = false;
        string? adoptedProfile = null;
        if (romPath is not null)
        {
            romPath = PublicSetupService.ValidateRom(romPath); var romBefore = PublicSetupService.HashFile(romPath);
            var build = PublicSetupService.DiscoverBuilds(root).FirstOrDefault() ?? throw new InvalidOperationException("Valid-case public tests require an actual prior source compilation.");
            var fixture = Path.Combine(isolated, "local", "source-builds", "actual-compilation");
            Directory.CreateDirectory(Path.Combine(fixture, "build")); Directory.CreateDirectory(Path.Combine(fixture, "profile"));
            var actual = Path.GetDirectoryName(build.ReceiptPath)!;
            File.Copy(build.ReceiptPath, Path.Combine(fixture, "source-build-receipt.json"));
            File.Copy(Path.Combine(actual, "build", PublicSetupService.GameName + ".exe"), Path.Combine(fixture, "build", PublicSetupService.GameName + ".exe"));
            foreach (var name in new[] { "config.ini", "foundation.ini", "keybinds.ini" })
                if (File.Exists(Path.Combine(actual, "profile", name))) File.Copy(Path.Combine(actual, "profile", name), Path.Combine(fixture, "profile", name));
            var sourceFiles = Directory.EnumerateFiles(fixture, "*", SearchOption.AllDirectories).ToDictionary(p => p, PublicSetupService.HashFile);
            var sourceReceipt = Path.Combine(fixture, "source-build-receipt.json");
            var profile = PublicSetupService.AdoptBuild(isolated, sourceReceipt, romPath);
            adoptedProfile = profile; File.WriteAllText(Path.Combine(profile, ".ui-test-disposable"), "Explicit disposable source-first GUI test profile.");
            var snapshot = ProfileService.Load(isolated, profile);
            Check("Actual source compilation adoption is ready without private fixtures", snapshot.Readiness.Ready && snapshot.Readiness.Message.Contains("gameplay unqualified"));
            Check("Selection persists to isolated profile only", PublicSetupService.GetSelectedProfile(isolated) == profile);
            Check("Adoption preserves original source-build files", sourceFiles.All(f => PublicSetupService.HashFile(f.Key) == f.Value));
            Check("No ROM copied into source profile", !Directory.EnumerateFiles(profile, "*", SearchOption.AllDirectories).Any(f => Path.GetExtension(f) is ".sfc" or ".smc"));
            var original = snapshot.Settings.DeepCopy(); var changed = original.DeepCopy(); changed.XpMultiplierPercent = 250; changed.GoldMultiplierPercent = 300;
            changed.MovementSpeedPercent = 225; changed.FastForwardToggle = true; changed.LegacyControllerGestures = false;
            changed.HotkeyBindings["Turbo"] = new("Tab", "Back+R2"); changed.HotkeyBindings["MovementBoost"] = new("Left Shift", "L2");
            changed.GameplayKeys["player1:a"] = "X";
            Check("Deep settings copy does not mutate loaded bindings", snapshot.Settings.HotkeyBindings["Turbo"] != changed.HotkeyBindings["Turbo"]);
            var applied = ProfileService.ApplyCore(snapshot, changed, () => false);
            if (ProfileService.SupportsQol(snapshot))
            {
                Check("Reward movement toggle and both-device hotkeys apply with backup", applied.Success && applied.BackupDirectory is not null);
                snapshot = applied.Snapshot!;
                Check("QoL and bindings reload exactly", snapshot.Settings.XpMultiplierPercent == 250 && snapshot.Settings.GoldMultiplierPercent == 300 &&
                    snapshot.Settings.MovementSpeedPercent == 225 && snapshot.Settings.FastForwardToggle && !snapshot.Settings.LegacyControllerGestures && snapshot.Settings.HotkeyBindings["Turbo"].Controller == "Back+R2" && snapshot.Settings.GameplayKeys["player1:a"] == "X");
                var duplicateKeyboard = snapshot.Settings.DeepCopy(); duplicateKeyboard.GameplayKeys["player1:a"] = duplicateKeyboard.GameplayKeys["player1:b"];
                Check("Changed duplicate keyboard game button refuses before writing", !ProfileService.ApplyCore(snapshot, duplicateKeyboard, () => false).Success);
                var gamepadHostConflict = snapshot.Settings.DeepCopy(); gamepadHostConflict.HotkeyBindings["Controls"] = gamepadHostConflict.HotkeyBindings["Controls"] with
                { Controller = HotkeyCatalog.SetSlot(gamepadHostConflict.HotkeyBindings["Controls"].Controller, 6, 12, gamepadHostConflict.HotkeyBindings["Turbo"].Controller) };
                Check("Changed controller game button conflicting with host action refuses before writing", !ProfileService.ApplyCore(snapshot, gamepadHostConflict, () => false).Success);
            }
            else Check("Older native compilation rejects unsupported QoL edits before writes", !applied.Success && applied.BackupDirectory is null && applied.Message.Contains("0.2.0"));
            var noOp = ProfileService.ApplyCore(snapshot, snapshot.Settings.DeepCopy(), () => false);
            Check("Expanded settings no-op leaves bytes and backups untouched", noOp.Success && noOp.BackupDirectory is null);
            var badSettings = snapshot.Settings.DeepCopy(); badSettings.XpMultiplierPercent = 1001;
            Check("QoL out-of-range settings refuse before writing", !ProfileService.ApplyCore(snapshot, badSettings, () => false).Success);
            var start = ProfileService.BuildLaunch(snapshot, new(LaunchMode.Play));
            Check("Title-first source launch uses direct executable and structured ROM path", start.FileName == Path.Combine(profile, PublicSetupService.GameName + ".exe") && start.WorkingDirectory == profile &&
                start.ArgumentList.Contains(romPath) && !start.ArgumentList.Contains("--resume-state") && start.Arguments == "");
            Check("Source launch strips inherited guest diagnostics", !start.Environment.Keys.Any(k => k.StartsWith("SNESRECOMP_", StringComparison.OrdinalIgnoreCase)));
            var save = Path.Combine(profile, "saves", "save7.sav"); var bytes = Encoding.ASCII.GetBytes("synthetic checkpoint copy test; not executed"); File.WriteAllBytes(save, bytes);
            snapshot = ProfileService.Load(isolated, profile);
            var resume = ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, save)); var pending = Path.Combine(profile, "companion-resume.state");
            Check("Resume prepares selected copy and keeps source bytes", resume.ArgumentList.Contains("--resume-state") && resume.ArgumentList.Contains(pending) &&
                File.ReadAllBytes(save).AsSpan().SequenceEqual(bytes) && File.ReadAllBytes(pending).AsSpan().SequenceEqual(bytes));
            Refused("Pending resume conflict is preserved", () => ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, save)));
            Check("Pending refusal preserves both checkpoint copies", File.ReadAllBytes(pending).AsSpan().SequenceEqual(bytes) && File.ReadAllBytes(save).AsSpan().SequenceEqual(bytes));
            File.Delete(pending); File.AppendAllText(save, " changed");
            Refused("Stale selected checkpoint refuses resume", () => ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, save)));
            // Exercise async failure/cancellation using an authored disposable
            // failure helper; never fabricate a successful build or receipt.
            var tools = Path.Combine(isolated, "tools"); Directory.CreateDirectory(tools);
            var helper = Path.Combine(tools, "build_public_foundation.py");
            File.WriteAllText(helper, "import sys\nfor i in range(3000):\n print('stdout diagnostic '+str(i)+' x'*20)\n print('stderr diagnostic '+str(i)+' y'*20,file=sys.stderr)\nraise SystemExit(1)\n");
            var selectionPath = Path.Combine(isolated, "local", "companion-public", "setup.json"); var selectionBefore = File.ReadAllBytes(selectionPath);
            var progressLines = 0;
            Refused("Async build drains full stdout/stderr pipes and reports failure", () => PublicSetupService.BuildAsync(isolated, romPath,
                new InlineProgress(_ => Interlocked.Increment(ref progressLines))).GetAwaiter().GetResult());
            Check("Build failure preserves selected profile and existing compilation", progressLines >= 6000 && File.ReadAllBytes(selectionPath).AsSpan().SequenceEqual(selectionBefore) && ProfileService.Load(isolated, profile).Readiness.Ready);
            File.WriteAllText(helper, "import time\nprint('cancellable diagnostic helper',flush=True)\ntime.sleep(120)\n");
            using (var cancellation = new CancellationTokenSource(TimeSpan.FromMilliseconds(250)))
            {
                bool cancelled = false;
                try { PublicSetupService.BuildAsync(isolated, romPath, cancellation: cancellation.Token).GetAwaiter().GetResult(); }
                catch (OperationCanceledException) { cancelled = true; }
                Check("Cancelled source build stops only its diagnostic child and preserves selection", cancelled && File.ReadAllBytes(selectionPath).AsSpan().SequenceEqual(selectionBefore));
            }
            File.AppendAllText(sourceReceipt, "\n");
            Check("Receipt mutation refuses readiness without rewriting profile", !ProfileService.Load(isolated, profile).Readiness.Ready);
            File.Copy(build.ReceiptPath, sourceReceipt, true); // Restore this disposable compilation receipt for subsequent GUI checks.
            Check("Owned ROM remains byte-identical", PublicSetupService.HashFile(romPath) == romBefore);
            compilationCase = true;
        }
        File.WriteAllText(Path.Combine(output, "report.json"), JsonSerializer.Serialize(new { passed = true, checks = checks.Count,
            actual_compilation_case = compilationCase, gameplay_executed = false, test_root = isolated, adopted_profile = adoptedProfile, cases = checks }, new JsonSerializerOptions { WriteIndented = true }));
        return 0;
    }

    sealed class InlineProgress(Action<string> action) : IProgress<string>
    { public void Report(string value) => action(value); }
}
