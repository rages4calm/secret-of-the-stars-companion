using System.Reflection;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class HotkeyUiTests
{
    public static void Run(MainForm form, string root, string profile, string report)
    {
        profile = PublicSetupService.RequireInside(profile, Path.Combine(root, "local"));
        if (!PublicSetupService.IsSourceProfile(profile) || !File.Exists(Path.Combine(profile, ".ui-test-disposable")))
            throw new InvalidOperationException("QoL GUI tests require an explicitly marked disposable source profile.");
        Directory.CreateDirectory(Path.GetDirectoryName(report)!);
        static IEnumerable<Control> Walk(Control parent)
        {
            foreach (Control child in parent.Controls) { yield return child; foreach (var nested in Walk(child)) yield return nested; }
        }
        T Find<T>(string name) where T : Control => Walk(form).OfType<T>().Single(c => c.AccessibleName == name || c.Text == name);
        void Method(string name) => typeof(MainForm).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(form, null);
        void Field(string name, bool value) => typeof(MainForm).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(form, value);
        var checks = new List<string>();
        void Check(string name, bool condition) { if (!condition) throw new InvalidOperationException(name); checks.Add(name); }
        var sourceSaves = Directory.EnumerateFiles(Path.Combine(profile, "saves"), "*", SearchOption.AllDirectories).ToDictionary(p => p, PublicSetupService.HashFile);
        var initial = ProfileService.Load(root, profile);
        Check("Disposable source profile ready for interactive checks", initial.Readiness.Ready);
        var apply = Find<Button>("Apply settings"); var play = Find<Button>("Start at title");
        Check("Initial source GUI title launch enabled with no unapplied changes", play.Enabled && !apply.Enabled);
        if (ProfileService.SupportsQol(initial))
        {
        form.ShowPage("enhancements");
        Find<NumericUpDown>("Experience rate (%)").Value = 275;
        Find<NumericUpDown>("Gold rate (%)").Value = 350;
        Find<NumericUpDown>("Movement boost (%)").Value = 250;
        form.ShowPage("hotkeys");
        Find<CheckBox>("Fast-forward is a toggle").Checked = true;
        Find<ComboBox>("Fast-forward keyboard").Text = "Ctrl+Tab";
        Find<ComboBox>("Fast-forward controller").Text = "Back+R2";
        Find<ComboBox>("Movement boost keyboard").Text = "Left Shift";
        Find<ComboBox>("Movement boost controller").Text = "L2";
        var slot = Find<ComboBox>("Checkpoint shortcut slot"); slot.SelectedIndex = 19;
        Find<ComboBox>("Load checkpoint keyboard").Text = "Ctrl+F20";
        Find<ComboBox>("Save checkpoint controller").Text = "Back+Y";
        slot.SelectedIndex = 0;
        Find<ComboBox>("Load checkpoint keyboard").Text = "F1";
        slot.SelectedIndex = 19;
        Check("Checkpoint slot switch retains edited last-slot keyboard and controller", Find<ComboBox>("Load checkpoint keyboard").Text == "Ctrl+F20" && Find<ComboBox>("Save checkpoint controller").Text == "Back+Y");
        form.ShowPage("controls");
        Find<ComboBox>("A keyboard").Text = "Q"; Find<ComboBox>("A controller").Text = "Y";
        Find<ComboBox>("B keyboard").Text = "W";
        Check("Editing QoL and bindings holds launch until Apply", apply.Enabled && !play.Enabled);
        var beforeConflict = Directory.EnumerateFiles(profile).ToDictionary(p => p, PublicSetupService.HashFile);
        apply.PerformClick();
        Check("Duplicate gamepad assignment refuses GUI Apply without writing", apply.Enabled && !play.Enabled && beforeConflict.All(p => PublicSetupService.HashFile(p.Key) == p.Value));
        Find<ComboBox>("A controller").Text = "Back+X";
        apply.PerformClick();
        var saved = ProfileService.Load(root, profile);
        Check("Interactive QoL numeric settings roundtrip", saved.Settings.XpMultiplierPercent == 275 && saved.Settings.GoldMultiplierPercent == 350 && saved.Settings.MovementSpeedPercent == 250);
        Check("Interactive keyboard controller and toggle settings roundtrip", saved.Settings.FastForwardToggle && saved.Settings.HotkeyBindings["Turbo"] == new HotkeyBinding("Ctrl+Tab", "Back+R2") && saved.Settings.HotkeyBindings["MovementBoost"].Controller == "L2");
        Check("Interactive checkpoint last-slot settings roundtrip", HotkeyCatalog.GetSlot(saved.Settings.HotkeyBindings["Load"].Keyboard, 19) == "Ctrl+F20" && HotkeyCatalog.GetSlot(saved.Settings.HotkeyBindings["Save"].Controller, 19) == "Back+Y");
        Check("Interactive game button bindings roundtrip", saved.Settings.GameplayKeys["player1:a"] == "Q" && saved.Settings.GameplayKeys["player1:b"] == "W" && HotkeyCatalog.GetSlot(saved.Settings.HotkeyBindings["Controls"].Controller, 6) == "Back+X");
        Check("Inactive player2 bindings remain preserved", initial.Settings.HotkeyBindings["ControlsP2"] == saved.Settings.HotkeyBindings["ControlsP2"] &&
            initial.Settings.GameplayKeys.Where(p => p.Key.StartsWith("player2:")).All(p => saved.Settings.GameplayKeys[p.Key] == p.Value));
        Check("Apply clears dirty state and creates verified backup", !apply.Enabled && play.Enabled && Directory.Exists(Path.Combine(profile, "backups")));
        var beforeNoOp = Directory.EnumerateFiles(profile).ToDictionary(p => p, PublicSetupService.HashFile);
        Method("ApplySettings");
        Check("GUI no-op Apply leaves exact profile bytes", beforeNoOp.All(f => PublicSetupService.HashFile(f.Key) == f.Value));
        Check("Every copied profile save remains byte-identical", sourceSaves.All(f => PublicSetupService.HashFile(f.Key) == f.Value));
        Field("sourceBuildRunning", true); Field("helperRunning", true); Field("busy", true); Method("UpdateEnabled");
        Check("Source setup busy locks settings launch and ROM selection", !Find<NumericUpDown>("Experience rate (%)").Enabled && !Find<ComboBox>("Fast-forward keyboard").Enabled && !Find<TextBox>("Owned clean USA ROM path").Enabled && !play.Enabled);
        Field("sourceBuildRunning", false); Field("helperRunning", false); Field("busy", false); Method("UpdateEnabled");
        Check("Source setup completion unlocks settings", Find<NumericUpDown>("Experience rate (%)").Enabled && play.Enabled);
        }
        else Check("Old native version keeps new QoL settings disabled", !Find<NumericUpDown>("Experience rate (%)").Enabled);
        var captures = Path.Combine(Path.GetDirectoryName(report)!, "captures"); Directory.CreateDirectory(captures);
        foreach (var size in new[] { new Size(1120, 760), new Size(950, 650) })
        {
            form.ClientSize = size;
            foreach (var page in new[] { "setup", "controls", "hotkeys", "enhancements" })
            {
                form.ShowPage(page); form.PerformLayout(); form.Refresh();
                using var bitmap = new Bitmap(form.Width, form.Height); form.DrawToBitmap(bitmap, new Rectangle(Point.Empty, bitmap.Size));
                bitmap.Save(Path.Combine(captures, $"{page}-{size.Width}x{size.Height}.png"));
                var view = Walk(form).OfType<Panel>().First(p => p.Visible && p.AutoScroll && p.Parent?.Padding.Left == 32);
                Check($"{page} at {size.Width}x{size.Height} has no horizontal clipping", !view.HorizontalScroll.Visible);
                // Long pages intentionally scroll vertically. Every interactive
                // control must fit the page width and remain reachable by scrolling.
                var outside = Walk(view).Where(c => c is ComboBox or TextBox or NumericUpDown or Button).Where(c =>
                    view.PointToClient(c.Parent!.PointToScreen(c.Location)).X + c.Width > view.ClientSize.Width).Select(c => new { name = c.AccessibleName ?? c.Name, x = view.PointToClient(c.Parent!.PointToScreen(c.Location)).X, width = c.Width, page_width = view.ClientSize.Width }).ToArray();
                Check($"{page} at {size.Width}x{size.Height} interactive controls fit page width: {JsonSerializer.Serialize(outside)}", outside.Length == 0);
            }
        }
        File.WriteAllText(report, JsonSerializer.Serialize(new { passed = true, checks = checks.Count, cases = checks, screenshots = captures,
            protected_saves = sourceSaves, gameplay_executed = false }, new JsonSerializerOptions { WriteIndented = true }));
    }
}
