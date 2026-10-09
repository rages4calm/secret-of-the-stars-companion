using System.Text.Json.Nodes;
using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class ProfileUpdateTests
{
    public static int Run(string root, string output, string romPath, string? checkpoint)
    {
        output = Path.GetFullPath(output);
        if (Directory.Exists(output)) throw new IOException("Update test output must be a new directory.");
        Directory.CreateDirectory(output);
        var isolated = Path.Combine(output, "isolated source checkout"); Directory.CreateDirectory(isolated);
        var cases = new List<string>();
        void Check(string name, bool condition) { if (!condition) throw new InvalidOperationException(name); cases.Add(name); }
        void Refused(string name, Action action)
        {
            bool refused = false;
            try { action(); } catch (Exception error) when (error is IOException or InvalidOperationException or JsonException or ArgumentException or KeyNotFoundException) { refused = true; }
            Check(name, refused);
        }
        var actual = PublicSetupService.DiscoverBuilds(root).FirstOrDefault() ?? throw new InvalidOperationException("An actual source compilation is required.");
        romPath = PublicSetupService.ValidateRom(romPath); var romHash = PublicSetupService.HashFile(romPath);
        var fixture = Path.Combine(isolated, "local", "source-builds", "actual-native");
        Directory.CreateDirectory(Path.Combine(fixture, "build")); Directory.CreateDirectory(Path.Combine(fixture, "profile"));
        var originalBuild = Path.GetDirectoryName(actual.ReceiptPath)!;
        var receipt = Path.Combine(fixture, "source-build-receipt.json");
        File.Copy(actual.ReceiptPath, receipt);
        File.Copy(Path.Combine(originalBuild, "build", PublicSetupService.GameName + ".exe"), Path.Combine(fixture, "build", PublicSetupService.GameName + ".exe"));
        foreach (var name in new[] { "config.ini", "foundation.ini", "keybinds.ini" })
            if (File.Exists(Path.Combine(originalBuild, "profile", name))) File.Copy(Path.Combine(originalBuild, "profile", name), Path.Combine(fixture, "profile", name));
        var profile = PublicSetupService.AdoptBuild(isolated, receipt, romPath);
        File.WriteAllText(Path.Combine(profile, ".ui-test-disposable"), "Disposable update test profile.");
        File.WriteAllBytes(Path.Combine(profile, "saves", "save.srm"), Enumerable.Range(0, 8192).Select(i => (byte)(i * 17)).ToArray());
        if (checkpoint is not null)
        {
            PublicSetupService.RejectLinkedPath(checkpoint); File.Copy(checkpoint, Path.Combine(profile, "saves", "save7.sav"));
            Check("Explicit real checkpoint fixture copied without modification", PublicSetupService.HashFile(checkpoint) == PublicSetupService.HashFile(Path.Combine(profile, "saves", "save7.sav")));
        }
        var config = Path.Combine(profile, "config.ini"); File.AppendAllText(config, "\r\n; retained custom byte comment\r\n");
        Directory.CreateDirectory(Path.Combine(profile, "backups", "retained")); File.WriteAllBytes(Path.Combine(profile, "backups", "retained", "unknown-note.bin"), [7, 8, 9, 10]);
        var source = ProfileService.Load(isolated, profile);
        var initial = ProfileUpdateService.Inventory(profile);
        var selector = Path.Combine(isolated, "local", "companion-public", "setup.json");
        var originalSelection = File.ReadAllBytes(selector);
        bool Same(string folder, Dictionary<string, string> hashes) => hashes.Count == ProfileUpdateService.Inventory(folder).Count && hashes.All(f => PublicSetupService.HashFile(Path.Combine(folder, f.Key)) == f.Value);
        void ResumeCopiedCheckpoint(string selectedProfile, string label)
        {
            var before = ProfileUpdateService.Inventory(selectedProfile);
            var runs = Path.Combine(isolated, "local", "runs");
            var priorRuns = Directory.Exists(runs) ? Directory.EnumerateDirectories(runs).ToHashSet(StringComparer.OrdinalIgnoreCase) : [];
            var report = Path.Combine(output, label + "-native-resume.json");
            var start = new ProcessStartInfo(Environment.ProcessPath!) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            foreach (var argument in new[] { "--root", isolated, "--profile", selectedProfile, "--launch-test", "Resume", "--save", Path.Combine(selectedProfile, "saves", "save7.sav"), "--verify-frames", "180", "--report", report }) start.ArgumentList.Add(argument);
            using var process = Process.Start(start) ?? throw new IOException("Diagnostic child did not start.");
            var stdout = process.StandardOutput.ReadToEndAsync(); var stderr = process.StandardError.ReadToEndAsync();
            if (!process.WaitForExit(60000)) { process.Kill(entireProcessTree: true); throw new TimeoutException("Finite copied-checkpoint resume timed out."); }
            _ = stdout.GetAwaiter().GetResult(); _ = stderr.GetAwaiter().GetResult();
            using var launchReport = JsonDocument.Parse(File.ReadAllBytes(report));
            Check(label + " actual native copied-checkpoint launch exits successfully", process.ExitCode == 0 && launchReport.RootElement.GetProperty("exit_code").GetInt32() == 0);
            var diagnostic = Directory.EnumerateDirectories(runs).Single(p => !priorRuns.Contains(p));
            Check(label + " native restore accepted and consumed only prepared diagnostic checkpoint", !File.Exists(Path.Combine(diagnostic, "companion-resume.state")) &&
                PublicSetupService.HashFile(Path.Combine(diagnostic, "saves", "save7.sav")) == before[Path.Combine("saves", "save7.sav")]);
            Check(label + " finite native launch leaves selected settings and saves byte-identical", Same(selectedProfile, before));
        }
        Refused("Busy game refuses update", () => ProfileUpdateService.UpdateCore(source, receipt, () => true));
        Check("Busy refusal preserves selection and profile", File.ReadAllBytes(selector).AsSpan().SequenceEqual(originalSelection) && Same(profile, initial));
        using (var buildLock = new FileStream(Path.Combine(Path.GetDirectoryName(selector)!, "build.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
            Refused("Concurrent build refuses update", () => ProfileUpdateService.UpdateCore(source, receipt, () => false));
        using (var selectLock = PublicSetupService.AcquireSelectionLock(isolated))
            Refused("Concurrent profile selection refuses update", () => ProfileUpdateService.UpdateCore(source, receipt, () => false));
        var pending = Path.Combine(profile, "companion-resume.state"); File.WriteAllBytes(pending, [1, 2, 3]);
        Refused("Prepared Resume checkpoint refuses update without consuming it", () => ProfileUpdateService.UpdateCore(ProfileService.Load(isolated, profile), receipt, () => false));
        Check("Pending Resume bytes preserved", File.ReadAllBytes(pending).AsSpan().SequenceEqual(new byte[] { 1, 2, 3 })); File.Delete(pending);
        File.AppendAllText(config, "changed after load");
        Refused("Stale settings refuse update", () => ProfileUpdateService.UpdateCore(source, receipt, () => false));
        File.WriteAllBytes(config, source.Files[config].Bytes);
        var native = Path.Combine(fixture, "build", PublicSetupService.GameName + ".exe");
        using (var file = new FileStream(native, FileMode.Open, FileAccess.Write)) { file.Position = file.Length; file.WriteByte(0); }
        Refused("Modified target binary refuses before profile copy", () => ProfileUpdateService.UpdateCore(source, receipt, () => false));
        File.Copy(Path.Combine(originalBuild, "build", PublicSetupService.GameName + ".exe"), native, true);
        File.AppendAllText(receipt, "\n");
        Refused("Modified source receipt refuses update", () => ProfileUpdateService.UpdateCore(source, receipt, () => false)); File.Copy(actual.ReceiptPath, receipt, true);
        var junctionTarget = Path.Combine(output, "junction target"); Directory.CreateDirectory(junctionTarget);
        var junction = Path.Combine(profile, "linked-save-folder");
        var junctionScript = Path.Combine(output, "create-test-junction.ps1");
        File.WriteAllText(junctionScript, "param([string]$Link,[string]$Target)\n$ErrorActionPreference='Stop'\nNew-Item -ItemType Junction -Path $Link -Target $Target | Out-Null\n");
        var junctionStart = new ProcessStartInfo("powershell.exe") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (var argument in new[] { "-NoProfile", "-NonInteractive", "-File", junctionScript, junction, junctionTarget }) junctionStart.ArgumentList.Add(argument);
        using (var process = Process.Start(junctionStart) ?? throw new IOException("Junction fixture helper did not start."))
        {
            var stdout = process.StandardOutput.ReadToEndAsync(); var stderr = process.StandardError.ReadToEndAsync();
            if (!process.WaitForExit(15000)) { process.Kill(entireProcessTree: true); throw new TimeoutException("Junction fixture helper timed out."); }
            if (process.ExitCode != 0) throw new IOException("Junction fixture creation failed: " + stderr.GetAwaiter().GetResult());
            _ = stdout.GetAwaiter().GetResult();
        }
        Refused("Nested junction refuses source profile traversal before copy", () => ProfileUpdateService.UpdateCore(source, receipt, () => false));
        Directory.Delete(junction); // Remove only the junction itself, never its target.
        Check("Linked-path refusal preserves target selection and source data", Directory.Exists(junctionTarget) && File.ReadAllBytes(selector).AsSpan().SequenceEqual(originalSelection) && Same(profile, initial));
        var parent = Path.GetDirectoryName(profile)!;
        var beforePartial = Directory.EnumerateDirectories(parent).Count();
        Refused("Interrupted copy transaction refuses selection", () => ProfileUpdateService.UpdateCore(source, receipt, () => false, step => { if (step == "copied") throw new IOException("Injected copy-phase interruption."); }));
        Check("Partial output retained separately and old data unchanged", Directory.EnumerateDirectories(parent).Count() == beforePartial + 1 && Same(profile, initial) && File.ReadAllBytes(selector).AsSpan().SequenceEqual(originalSelection));
        Refused("Selection conflict at commit is preserved", () => ProfileUpdateService.UpdateCore(source, receipt, () => false, step => { if (step == "ready") File.WriteAllText(selector, "{\"profile\":\"external selection\"}"); }));
        Check("Conflict never overwrites an external selector", File.ReadAllText(selector).Contains("external selection")); File.WriteAllBytes(selector, originalSelection);
        var next = ProfileUpdateService.UpdateCore(source, receipt, () => false);
        Check("Same-native-SHA update selects a newly isolated ready profile", next != profile && ProfileService.Load(isolated, next).Readiness.Ready && PublicSetupService.GetSelectedProfile(isolated) == next);
        Check("Original profile settings saves backups and native identity unchanged", Same(profile, initial));
        Check("All settings and save bytes copied exactly including nested backups", initial.Where(f => f.Key != PublicSetupService.ManifestName).All(f => PublicSetupService.HashFile(Path.Combine(next, f.Key)) == f.Value));
        Check("Update adds verified history and leaves old selector in history", ProfileUpdateService.GetRollback(isolated, next)?.PreviousProfile == profile);
        var nextInventory = ProfileUpdateService.Inventory(next);
        var nextSnapshot = ProfileService.Load(isolated, next);
        Refused("Busy game refuses rollback", () => ProfileUpdateService.RollbackCore(nextSnapshot, () => true));
        var nextPending = Path.Combine(next, "companion-resume.state"); File.WriteAllBytes(nextPending, [4, 5, 6]);
        Refused("Prepared Resume checkpoint refuses rollback without consuming it", () => ProfileUpdateService.RollbackCore(nextSnapshot, () => false));
        Check("Rollback pending checkpoint refusal preserves bytes", File.ReadAllBytes(nextPending).AsSpan().SequenceEqual(new byte[] { 4, 5, 6 })); File.Delete(nextPending);
        var historyPath = Path.Combine(next, "update-history.json"); var historyBytes = File.ReadAllBytes(historyPath); File.AppendAllText(historyPath, "\n");
        Refused("Modified transaction history refuses rollback", () => ProfileUpdateService.RollbackCore(nextSnapshot, () => false)); File.WriteAllBytes(historyPath, historyBytes);
        var previousManifest = Path.Combine(profile, PublicSetupService.ManifestName); var manifestBytes = File.ReadAllBytes(previousManifest); File.AppendAllText(previousManifest, "\n");
        Refused("Modified previous identity refuses rollback", () => ProfileUpdateService.RollbackCore(nextSnapshot, () => false)); File.WriteAllBytes(previousManifest, manifestBytes);
        var rolledBack = ProfileUpdateService.RollbackCore(nextSnapshot, () => false);
        Check("Rollback restores the exact previous selector bytes", rolledBack == profile && File.ReadAllBytes(selector).AsSpan().SequenceEqual(originalSelection));
        Check("Rollback modifies neither old nor newer profile progress", Same(profile, initial) && Same(next, nextInventory));
        Refused("An unselected stale profile refuses another update", () => ProfileUpdateService.UpdateCore(ProfileService.Load(isolated, next), receipt, () => false));
        Check("Owned ROM and original actual compilation remain unchanged", PublicSetupService.HashFile(romPath) == romHash && PublicSetupService.HashFile(Path.Combine(originalBuild, "build", PublicSetupService.GameName + ".exe")) == actual.ExecutableSha256);
        // Exercise the real Setup action wiring with a disposable selected source
        // profile, rather than calling only its backend methods.
        using (var form = new MainForm(isolated, profile))
        {
            form.StartPosition = FormStartPosition.Manual; form.Location = new(-30000, -30000); form.ShowInTaskbar = false;
            form.Show(); form.ShowPage("setup"); Application.DoEvents();
            static IEnumerable<Control> Walk(Control control) { foreach (Control child in control.Controls) { yield return child; foreach (var nested in Walk(child)) yield return nested; } }
            var update = Walk(form).OfType<Button>().Single(c => c.Text == "Update selected profile");
            var rollback = Walk(form).OfType<Button>().Single(c => c.Text == "Use previous profile");
            Check("Setup distinguishes fresh adoption and profile update", Walk(form).OfType<Button>().Any(c => c.Text == "Use selected build") && update.Enabled && !rollback.Enabled);
            void Guard(string field, bool value)
            {
                typeof(MainForm).GetField(field, BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(form, value);
                typeof(MainForm).GetMethod("UpdateEnabled", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(form, null);
            }
            Guard("dirty", true); Check("Unapplied settings disable profile update in Setup", !update.Enabled); Guard("dirty", false);
            Guard("helperRunning", true); Check("Running launch/build helper disables source profile actions", !update.Enabled && !rollback.Enabled); Guard("helperRunning", false);
            update.PerformClick(); Application.DoEvents();
            var uiSelected = PublicSetupService.GetSelectedProfile(isolated)!;
            Check("Setup update button performs actual clone and exposes rollback", uiSelected != profile && rollback.Enabled && Same(profile, initial));
            var originalSize = form.Size;
            var view = update.Parent;
            while (view is not null && view is not Panel { AutoScroll: true }) view = view.Parent;
            var scroll = (Panel)(view ?? throw new InvalidOperationException("Setup scroll container missing."));
            foreach (var (label, size) in new[] { ("normal", originalSize), ("minimum", new Size(950, 650)) })
            {
                form.Size = size; form.PerformLayout(); Application.DoEvents();
                scroll.AutoScrollPosition = new Point(0, Math.Max(0, update.Top - 240)); form.Refresh(); Application.DoEvents();
                var rightEdge = scroll.PointToClient(update.PointToScreen(new Point(update.Width, 0))).X;
                Check("Setup history " + label + " layout has no horizontal overflow", !scroll.HorizontalScroll.Visible && rightEdge <= scroll.ClientSize.Width);
                var lower = scroll.PointToClient(rollback.PointToScreen(new Point(0, rollback.Height))).Y;
                Check("Setup history " + label + " update and rollback actions visible together", lower < scroll.ClientSize.Height && lower > 0);
                using var bitmap = new Bitmap(form.Width, form.Height); form.DrawToBitmap(bitmap, new Rectangle(Point.Empty, bitmap.Size));
                bitmap.Save(Path.Combine(output, "setup-history-" + label + ".png"));
            }
            form.Size = originalSize;
            rollback.PerformClick(); Application.DoEvents();
            Check("Setup rollback button selects the preserved original profile", PublicSetupService.GetSelectedProfile(isolated) == profile && !rollback.Enabled);
            form.Close();
        }
        bool changedExecutableChecked = false;
        var compatible = PublicSetupService.DiscoverBuilds(root).FirstOrDefault(b => b.ExecutableSha256 != actual.ExecutableSha256 &&
            JsonNode.Parse(File.ReadAllBytes(b.ReceiptPath))?["execution_state_abi_sha256"]?.GetValue<string>() ==
            JsonNode.Parse(File.ReadAllBytes(actual.ReceiptPath))?["execution_state_abi_sha256"]?.GetValue<string>());
        string? changedProfile = null;
        if (compatible is not null)
        {
            var targetFolder = Path.Combine(isolated, "local", "source-builds", "actual-compatible-native"); Directory.CreateDirectory(Path.Combine(targetFolder, "build"));
            var targetReceipt = Path.Combine(targetFolder, "source-build-receipt.json"); var targetReceiptBytes = File.ReadAllBytes(compatible.ReceiptPath);
            File.WriteAllBytes(targetReceipt, targetReceiptBytes);
            File.Copy(Path.Combine(Path.GetDirectoryName(compatible.ReceiptPath)!, "build", PublicSetupService.GameName + ".exe"), Path.Combine(targetFolder, "build", PublicSetupService.GameName + ".exe"));
            source = ProfileService.Load(isolated, profile);
            void ReceiptFault(string field, JsonNode? value)
            {
                var node = JsonNode.Parse(targetReceiptBytes)!; node[field] = value;
                File.WriteAllText(targetReceipt, node.ToJsonString());
            }
            ReceiptFault("execution_state_abi_sha256", new string('0', 64));
            Refused("Different native SHA with incompatible execution ABI refuses copied progress", () => ProfileUpdateService.UpdateCore(source, targetReceipt, () => false));
            ReceiptFault("save_compatibility", "foreign-title-sram");
            Refused("Different SRAM compatibility refuses copied progress", () => ProfileUpdateService.UpdateCore(source, targetReceipt, () => false));
            ReceiptFault("checkpoint_schema", new JsonObject { ["identity"] = "sots-clean-foundation-v1", ["writes"] = 3, ["reads"] = new JsonArray(1, 2) });
            Refused("Target not reading source-written checkpoint schema refuses update", () => ProfileUpdateService.UpdateCore(source, targetReceipt, () => false));
            if (checkpoint is not null)
            {
                ReceiptFault("checkpoint_schema", new JsonObject { ["identity"] = "sots-clean-foundation-v1", ["writes"] = 3, ["reads"] = new JsonArray(3) });
                var saved = Path.Combine(profile, "saves", "save7.sav"); var savedBytes = File.ReadAllBytes(saved);
                // This fixture normally uses v2. Explicit unknown-header fault
                // avoids assuming its original schema when exercising rejection.
                var modified = savedBytes.ToArray();
                var header = modified.AsSpan().IndexOf(new byte[] { 0x53, 0x4f, 0x54, 0x53 });
                if (header < 0) throw new InvalidOperationException("Explicit checkpoint lacks the native title schema.");
                modified[header + 4] = 99; File.WriteAllBytes(saved, modified);
                Refused("Unknown schema in an existing checkpoint refuses changed-executable update", () => ProfileUpdateService.UpdateCore(source, targetReceipt, () => false));
                File.WriteAllBytes(saved, savedBytes);
            }
            File.WriteAllBytes(targetReceipt, targetReceiptBytes);
            Check("Compatibility refusals retain original selection and all original data", File.ReadAllBytes(selector).AsSpan().SequenceEqual(originalSelection) && Same(profile, initial));
            changedProfile = ProfileUpdateService.UpdateCore(source, targetReceipt, () => false);
            Check("Actual distinct executable with matching declared ABI updates copied profile", PublicSetupService.GetSelectedProfile(isolated) == changedProfile &&
                PublicSetupService.HashFile(Path.Combine(changedProfile, PublicSetupService.GameName + ".exe")) == compatible.ExecutableSha256 && ProfileService.Load(isolated, changedProfile).Readiness.Ready);
            Check("Compatible changed-executable update preserves original checkpoint and settings bytes", initial.Where(f => f.Key != PublicSetupService.ManifestName && f.Key != PublicSetupService.GameName + ".exe")
                .All(f => PublicSetupService.HashFile(Path.Combine(changedProfile, f.Key)) == f.Value) && Same(profile, initial));
            if (checkpoint is not null) ResumeCopiedCheckpoint(changedProfile, "post-update");
            File.AppendAllText(Path.Combine(changedProfile, "config.ini"), "; progress after upgrade\r\n");
            File.WriteAllBytes(Path.Combine(changedProfile, "saves", "save.srm"), [9, 8, 7, 6]);
            var changedInventory = ProfileUpdateService.Inventory(changedProfile);
            Check("Rollback after newer progress selects original without merging or discarding", ProfileUpdateService.RollbackCore(ProfileService.Load(isolated, changedProfile), () => false) == profile &&
                Same(changedProfile, changedInventory) && Same(profile, initial));
            if (checkpoint is not null) ResumeCopiedCheckpoint(profile, "post-rollback");
            changedExecutableChecked = true;
        }
        File.WriteAllText(Path.Combine(output, "report.json"), JsonSerializer.Serialize(new { passed = true, checks = cases.Count, actual_native_sha256 = actual.ExecutableSha256,
            actual_checkpoint_copied = checkpoint is not null, checkpoint_gameplay_executed = checkpoint is not null && changedExecutableChecked, changed_executable_compatibility_case = changedExecutableChecked,
            test_root = isolated, original_profile = profile, updated_profile = next, compatible_changed_profile = changedProfile, cases }, new JsonSerializerOptions { WriteIndented = true }));
        return 0;
    }
}
