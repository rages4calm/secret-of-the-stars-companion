using System.Security.Cryptography;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class UiTests
{
    public static void Run(MainForm form, string root, string profile, string report)
    {
        string testRoot = Path.Combine(root, "local", "runs") + Path.DirectorySeparatorChar;
        if (!profile.StartsWith(testRoot, StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("UI tests require a copied profile under local/runs.");
        static IEnumerable<Control> Controls(Control parent)
        {
            foreach (Control child in parent.Controls)
            { yield return child; foreach (Control nested in Controls(child)) yield return nested; }
        }
        static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
        var protectedFiles = Directory.EnumerateFiles(Path.Combine(profile, "saves"), "*", SearchOption.AllDirectories)
            .Append(Path.Combine(profile, "keybinds.ini")).ToDictionary(path => path, Hash);
        var original = ProfileService.Load(root, profile).Settings;
        int initialBackups = Directory.Exists(Path.Combine(profile,"backups")) ? Directory.GetDirectories(Path.Combine(profile,"backups"),"settings-*").Length : 0;
        var checks = new List<string>();
        void Check(bool passed, string description) { if (!passed) throw new InvalidOperationException(description); checks.Add(description); }
        T Find<T>(string name) where T : Control => Controls(form).OfType<T>().Single(c => c.AccessibleName == name || c.Text == name);
        var apply = Find<Button>("Apply settings");
        var play = Find<Button>("Start at title");
        Check(!apply.Enabled && play.Enabled, "Initial GUI has no unapplied changes and Play is enabled.");
        form.ShowPage("controls");
        Find<CheckBox>("Enable player 1 controller").Checked = !original.EnableGamepad;
        var deadzone = Controls(form).OfType<NumericUpDown>().Single(c => c.AccessibleName?.Contains("deadzone") == true);
        deadzone.Value = 15;
        Check(apply.Enabled && !play.Enabled, "Changing controller options enables Apply and holds Play until settings are applied.");
        apply.PerformClick();
        var changed = ProfileService.Load(root, profile).Settings;
        Check(changed.EnableGamepad == !original.EnableGamepad && changed.Deadzone == (int)Math.Round(32767 * 0.15), "GUI checkbox and percentage deadzone reach the exact native settings.");
        Check(!apply.Enabled && play.Enabled, "Successful Apply clears dirty state and restores Play.");
        form.ShowPage("enhancements");
        Find<CheckBox>("Battle information").Checked = !original.BattleInfo;
        apply.PerformClick();
        Check(ProfileService.Load(root, profile).Settings.BattleInfo == !original.BattleInfo, "GUI battle-information toggle reaches foundation settings.");
        form.ShowPage("display");
        var expanded = Find<CheckBox>("Widescreen (experimental)");
        expanded.Checked = true;
        apply.PerformClick();
        var expandedSettings = ProfileService.Load(root,profile).Settings;
        Check(expandedSettings.ExperimentalFieldWide && expandedSettings.ExperimentalFieldActors,"GUI expanded Likado toggle enables both checked terrain and actor settings.");
        expanded.Checked = false;
        apply.PerformClick();
        expandedSettings = ProfileService.Load(root,profile).Settings;
        Check(!expandedSettings.ExperimentalFieldWide && !expandedSettings.ExperimentalFieldActors,"GUI expanded Likado toggle restores both original viewport settings.");
        Check(protectedFiles.All(p => Hash(p.Key) == p.Value), "GUI Apply preserves all copied saves and exact custom keybindings.");
        Check(Directory.GetDirectories(Path.Combine(profile, "backups"), "settings-*").Length == initialBackups+4, "Each GUI Apply creates a verified settings backup.");
        File.WriteAllText(report, JsonSerializer.Serialize(new { passed = true, checks = checks.Count, cases = checks }, new JsonSerializerOptions { WriteIndented = true }));
    }
}
