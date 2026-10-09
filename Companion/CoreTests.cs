using System.Security.Cryptography;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class CoreTests
{
    static Dictionary<string, string> Hashes(string directory) => Directory.EnumerateFiles(directory, "*", SearchOption.AllDirectories)
        .Where(path => !Path.GetRelativePath(directory, path).StartsWith("backups" + Path.DirectorySeparatorChar))
        .ToDictionary(path => Path.GetRelativePath(directory, path), path => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant());

    public static int Run(string root, string output)
    {
        if (Directory.Exists(output)) throw new IOException("Self-test output must be a new directory.");
        Directory.CreateDirectory(output);
        var checks = new List<string>(BackendSelfTests.Run());
        void Check(bool passed, string description)
        { if (!passed) throw new InvalidOperationException(description); checks.Add(description); }
        string owner = Path.Combine(root, "local", "player-foundation");
        var ownerBefore = Hashes(owner);
        var snapshot = ProfileService.Load(root, owner);
        Check(snapshot.Readiness.Ready, "Installed owner profile and qualified game/ROM are ready.");
        Check(ownerBefore.OrderBy(x => x.Key).SequenceEqual(Hashes(owner).OrderBy(x => x.Key)), "Loading owner profile is read-only.");
        string copy = Path.Combine(output, "profile with spaces");
        Directory.CreateDirectory(copy);
        foreach (string source in Directory.EnumerateFiles(owner)) File.Copy(source, Path.Combine(copy, Path.GetFileName(source)));
        string saves = Path.Combine(copy, "saves"); Directory.CreateDirectory(saves);
        foreach (string source in Directory.EnumerateFiles(Path.Combine(owner, "saves"))) File.Copy(source, Path.Combine(saves, Path.GetFileName(source)));
        string extra = Path.Combine(saves, "save4.sav");
        File.Copy(Path.Combine(saves, "save0.sav"), extra);
        snapshot = ProfileService.Load(root, copy);
        var copyBefore = Hashes(copy);
        var changed = snapshot.Settings with { Fullscreen = false, Volume = 61, EnhancedPixels = !snapshot.Settings.EnhancedPixels, NoSpriteLimits = true };
        var applied = ProfileService.Apply(snapshot, changed);
        Check(applied.Success && applied.BackupDirectory != null, "Applying copied-profile settings succeeds with verified backup.");
        snapshot = applied.Snapshot!;
        Check(snapshot.Settings.Volume == 61 && !snapshot.Settings.Fullscreen && snapshot.Settings.NoSpriteLimits, "Applied audio/display/sprite settings reload correctly.");
        var copyAfter = Hashes(copy);
        Check(copyBefore.Where(x => x.Key != "config.ini" && x.Key != "foundation.ini").All(x => copyAfter.GetValueOrDefault(x.Key) == x.Value), "Applying settings preserves all saves, keybinds and other profile files.");
        foreach (string file in new[] { "config.ini", "foundation.ini" })
            Check(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(Path.Combine(applied.BackupDirectory!, file)))).ToLowerInvariant() == copyBefore[file], "Backup retains exact original " + file + " bytes.");
        string? diagnostic = Environment.GetEnvironmentVariable("SNESRECOMP_COMPANION_TEST");
        Environment.SetEnvironmentVariable("SNESRECOMP_COMPANION_TEST", "must-not-inherit");
        try
        {
            foreach (var mode in Enum.GetValues<LaunchMode>())
            {
                var start = ProfileService.BuildLaunch(snapshot, new(mode, mode == LaunchMode.Resume ? extra : null));
                Check(!start.UseShellExecute && start.ArgumentList.Contains(copy) && start.Arguments == "", mode + " uses structured arguments and the selected profile with spaces.");
                Check(!start.Environment.Keys.Any(x => x.StartsWith("SNESRECOMP_", StringComparison.OrdinalIgnoreCase)), mode + " strips inherited game diagnostics.");
                if (mode == LaunchMode.Resume) Check(start.ArgumentList.Contains(extra), "Explicit Resume selects save4 instead of silently using save0.");
            }
        }
        finally { Environment.SetEnvironmentVariable("SNESRECOMP_COMPANION_TEST", diagnostic); }
        void Refused(Action action, string description)
        {
            bool refused = false;
            try { action(); } catch (InvalidOperationException) { refused = true; }
            Check(refused, description);
        }
        Refused(() => ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, Path.Combine(owner, "saves", "save0.sav"))), "Resume rejects a checkpoint belonging to another profile.");
        File.WriteAllBytes(Path.Combine(copy, "fixture-resume.state"), [1, 2, 3]);
        Refused(() => ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, extra)), "Resume preserves and reports an existing pending checkpoint conflict.");
        Check(File.ReadAllBytes(Path.Combine(copy, "fixture-resume.state")).SequenceEqual(new byte[] { 1, 2, 3 }), "Conflicting pending checkpoint retains its exact bytes.");
        File.Delete(Path.Combine(copy, "fixture-resume.state"));
        File.AppendAllText(extra, "changed copied test checkpoint");
        Refused(() => ProfileService.BuildLaunch(snapshot, new(LaunchMode.Resume, extra)), "Resume rejects a checkpoint changed since it was listed.");
        Check(ownerBefore.OrderBy(x => x.Key).SequenceEqual(Hashes(owner).OrderBy(x => x.Key)), "Owner profile hashes remain unchanged after all copied-profile checks.");
        File.WriteAllText(Path.Combine(output, "report.json"), JsonSerializer.Serialize(new { passed = true, checks = checks.Count, cases = checks, copied_profile = copy, owner_files_preserved = ownerBefore }, new JsonSerializerOptions { WriteIndented = true }));
        return 0;
    }
}
