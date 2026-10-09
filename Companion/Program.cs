using System.Diagnostics;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class Program
{
    [STAThread]
    static int Main(string[] args)
    {
        bool diagnostic = args.Contains("--capture") || args.Contains("--self-test") || args.Contains("--launch-test") || args.Contains("--ui-test") || args.Contains("--visible-test");
        try
        {
            string? Value(string key)
            {
                int i = Array.IndexOf(args, key);
                if (i < 0) return null;
                if (i + 1 == args.Length || args[i + 1].StartsWith("--")) throw new ArgumentException("Missing value for " + key);
                return args[i + 1];
            }
            string root = Path.GetFullPath(Value("--root") ?? FindRoot());
            string? profile = Value("--profile");
            if (Value("--self-test") is string tests) return CoreTests.Run(root, Path.GetFullPath(tests));
            if (Value("--launch-test") is string mode)
            {
                var snapshot = ProfileService.Load(root, profile);
                var launchMode = Enum.Parse<LaunchMode>(mode, true);
                var start = ProfileService.BuildLaunch(snapshot, new(launchMode, Value("--save")));
                start.ArgumentList.Add("-VerifyFrames");
                start.ArgumentList.Add(Value("--verify-frames") ?? "180");
                start.RedirectStandardOutput = start.RedirectStandardError = true;
                using var process = Process.Start(start) ?? throw new IOException("Launch helper did not start.");
                var stdout = process.StandardOutput.ReadToEndAsync();
                var stderr = process.StandardError.ReadToEndAsync();
                if (!process.WaitForExit(60000)) throw new TimeoutException("Launch verification exceeded 60 seconds.");
                var report = new { mode, exit_code = process.ExitCode, stdout = stdout.GetAwaiter().GetResult(), stderr = stderr.GetAwaiter().GetResult() };
                File.WriteAllText(Value("--report") ?? Path.Combine(snapshot.ProfileDirectory, "companion-launch-test.json"), JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
                return process.ExitCode;
            }
            ApplicationConfiguration.Initialize();
            using var form = new MainForm(root, profile);
            if (Value("--ui-test") is string uiReport)
            {
                if (profile == null) throw new ArgumentException("UI interaction tests require an explicit copied profile.");
                int result = 1;
                form.StartPosition = FormStartPosition.Manual; form.Location = new(-30000, -30000); form.ShowInTaskbar = false;
                form.Shown += (_, _) =>
                {
                    try { UiTests.Run(form, root, Path.GetFullPath(profile), uiReport); result = 0; }
                    catch (Exception ex) { File.WriteAllText(uiReport, JsonSerializer.Serialize(new { passed = false, error = ex.ToString() })); }
                    finally { form.Close(); }
                };
                Application.Run(form);
                return result;
            }
            if (Value("--capture") is string capture)
            {
                Directory.CreateDirectory(capture);
                form.StartPosition = FormStartPosition.Manual;
                form.Location = new(-30000, -30000);
                form.ShowInTaskbar = false;
                var pages = new Queue<string>(["play", "display", "audio", "controls", "enhancements", "saves"]);
                using var timer = new System.Windows.Forms.Timer { Interval = 250 };
                timer.Tick += (_, _) =>
                {
                    if (pages.Count == 0) { timer.Stop(); form.Close(); return; }
                    string page = pages.Dequeue();
                    form.ShowPage(page); form.PerformLayout(); form.Refresh();
                    using var bitmap = new Bitmap(form.Width, form.Height);
                    form.DrawToBitmap(bitmap, new Rectangle(Point.Empty, bitmap.Size));
                    bitmap.Save(Path.Combine(capture, page + ".png"));
                };
                form.Shown += (_, _) => timer.Start();
                Application.Run(form);
                return 0;
            }
            string? visibleTest = Value("--visible-test");
            var windowReport = visibleTest ?? Value("--window-report") ?? Path.Combine(root, "local", "companion", "logs",
                "window-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + Environment.ProcessId + ".json");
            using var window = new WindowReadiness(form, windowReport, visibleTest != null);
            Application.Run(form);
            return visibleTest != null && !window.Passed ? 1 : 0;
        }
        catch (Exception ex)
        {
            if (diagnostic)
            {
                int i = Array.IndexOf(args, "--report");
                string path = i >= 0 && i + 1 < args.Length ? args[i + 1] : Path.Combine(AppContext.BaseDirectory, "companion-error.json");
                File.WriteAllText(path, JsonSerializer.Serialize(new { passed = false, error = ex.ToString() }, new JsonSerializerOptions { WriteIndented = true }));
            }
            else MessageBox.Show(ex.Message, "Secret of the Stars Companion", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    static string FindRoot()
    {
        for (var directory = new DirectoryInfo(AppContext.BaseDirectory); directory != null; directory = directory.Parent)
            if (File.Exists(Path.Combine(directory.FullName, "tools", "Start-Foundation.ps1"))) return directory.FullName;
        throw new DirectoryNotFoundException("Launch Companion from this project, or pass --root followed by the project folder.");
    }
}
