using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace SecretOfTheStars.Companion;

/// <summary>Checks our real interactive window, not an offscreen bitmap.</summary>
internal sealed class WindowReadiness : IDisposable
{
    [DllImport("user32.dll")] [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(IntPtr handle);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr handle, int command);
    private readonly Form form;
    private readonly string report;
    private readonly bool closeAfterTest;
    private readonly System.Windows.Forms.Timer timer = new() { Interval = 200 };
    private readonly Stopwatch elapsed = new();
    private bool wasNativeVisible, restored;
    public bool Passed { get; private set; }

    public WindowReadiness(Form form, string report, bool closeAfterTest)
    {
        this.form = form; this.report = Path.GetFullPath(report); this.closeAfterTest = closeAfterTest;
        form.Shown += OnShown; timer.Tick += (_, _) => Observe();
    }
    private void OnShown(object? sender, EventArgs args)
    {
        wasNativeVisible = IsWindowVisible(form.Handle);
        // Interactive launches are explicitly expected to be visible. A legacy
        // SW_HIDE request must not leave a live but unreachable app window.
        form.ShowInTaskbar = true;
        if (!wasNativeVisible) { ShowWindow(form.Handle, 1); restored = true; } // SW_SHOWNORMAL, our own window.
        if (form.WindowState == FormWindowState.Minimized) form.WindowState = FormWindowState.Normal;
        if (!Screen.AllScreens.Any(screen => screen.WorkingArea.IntersectsWith(form.Bounds)))
        {
            var area = Screen.PrimaryScreen?.WorkingArea ?? Screen.AllScreens[0].WorkingArea;
            form.Location = new(Math.Max(area.Left, area.Left + (area.Width - form.Width) / 2),
                Math.Max(area.Top, area.Top + (area.Height - form.Height) / 2)); restored = true;
        }
        elapsed.Start(); timer.Start();
    }
    private void Observe()
    {
        using var process = Process.GetCurrentProcess(); process.Refresh();
        var nativeVisible = form.IsHandleCreated && IsWindowVisible(form.Handle);
        var intersects = Screen.AllScreens.Any(screen => screen.WorkingArea.IntersectsWith(form.Bounds));
        var ready = form.Visible && form.ShowInTaskbar && nativeVisible && intersects &&
            form.WindowState != FormWindowState.Minimized && process.MainWindowHandle != IntPtr.Zero;
        if (elapsed.ElapsedMilliseconds < 600 || (!ready && elapsed.ElapsedMilliseconds < 5000)) return;
        timer.Stop(); Passed = ready;
        var payload = new
        {
            passed = ready, purpose = "Interactive top-level window readiness; no settings or game actions",
            process_id = Environment.ProcessId, executable = Environment.ProcessPath,
            managed_visible = form.Visible, native_visible = nativeVisible, shown_in_taskbar = form.ShowInTaskbar,
            native_visible_at_shown = wasNativeVisible, restored_interactive_visibility = restored,
            window_handle = form.Handle.ToInt64(), main_window_handle = process.MainWindowHandle.ToInt64(),
            window_title = process.MainWindowTitle, window_state = form.WindowState.ToString(),
            intersects_display_work_area = intersects,
            bounds = new { form.Bounds.X, form.Bounds.Y, form.Bounds.Width, form.Bounds.Height },
            elapsed_ms = elapsed.ElapsedMilliseconds
        };
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(report)!);
            File.WriteAllText(report, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException)
        { Passed = false; if (closeAfterTest) MessageBox.Show(error.Message, "Companion window report", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        if (closeAfterTest) form.Close();
    }
    public void Dispose() { timer.Stop(); timer.Dispose(); form.Shown -= OnShown; }
}
