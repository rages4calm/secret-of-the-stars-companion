using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

public sealed partial class MainForm
{
    readonly TextBox setupRom = new() { Width = 550, AccessibleName = "Owned clean USA ROM path", BackColor = Theme.Rail, ForeColor = Theme.Ink, Font = Theme.Body(10), BorderStyle = BorderStyle.FixedSingle };
    readonly ComboBox sourceBuilds = Theme.Combo(550);
    readonly CompanionButton chooseRom = Theme.Button("Choose owned ROM", false, 195);
    readonly CompanionButton buildSource = Theme.Button("Build from source", true, 195);
    readonly CompanionButton useBuild = Theme.Button("Use selected build", false, 195);
    readonly CompanionButton refreshBuilds = Theme.Button("Refresh builds", false, 165);
    readonly CompanionButton updateProfile = Theme.Button("Update selected profile", true, 245);
    readonly CompanionButton rollbackProfile = Theme.Button("Use previous profile", false, 245);
    readonly Label updateHint = Theme.Text("Updates are available for an isolated source profile. Owner saves are never imported automatically.", 10, Theme.Muted);
    bool rollbackAvailable;
    readonly TextBox setupDiagnostics = new() { Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Height = 180, Dock = DockStyle.Top,
        BackColor = Theme.Rail, ForeColor = Theme.Muted, Font = Theme.Body(9), AccessibleName = "Source setup diagnostics" };
    CancellationTokenSource? setupCancellation;
    bool sourceBuildRunning;

    void BuildSetup()
    {
        var page = Page("setup", "Setup", "Select your owned ROM and build a private local game. No original game data is downloaded or included.");
        page.Add(Theme.Text("Clean unheadered USA ROM", 14, Theme.Ink, FontStyle.Bold), 8);
        page.Add(setupRom, 8); page.Add(chooseRom, 14);
        page.Add(Theme.Text("The exact USA release is validated by size and SHA-256. Your selected file stays in its original location and is read only.", 10, Theme.Muted), 18);
        Section(page, "Build prerequisites", "Install Git, Python 3.11+, Rust/Cargo, CMake, Ninja and a working Windows Clang toolchain on PATH. BUILDING.md describes the developer setup. Missing tools are reported in the build diagnostics.");
        page.Add(buildSource, 20);
        Section(page, "Existing source builds", "Use a successful local compilation without borrowing a private qualification receipt. Every adoption creates a new isolated profile.");
        page.Add(sourceBuilds, 8); page.Add(refreshBuilds, 8); page.Add(useBuild, 18);
        page.Add(Theme.Text("Source builds are gameplay unqualified until tested. Play starts at the title; this setup does not import another installation's saves.", 10, Theme.Muted), 18);
        Section(page, "Preserve a source profile", "Update clones the selected source profile's settings and saves into a new folder with the selected build. The old folder is retained. Different executables require declared save compatibility; fresh adoption above starts without imported progress.");
        page.Add(updateProfile, 8); page.Add(rollbackProfile, 8); page.Add(updateHint, 18);
        page.Add(setupDiagnostics, 12);
        chooseRom.Click += (_, _) =>
        {
            using var dialog = new OpenFileDialog { Title = "Choose your clean USA ROM", Filter = "SNES ROM (*.sfc;*.smc)|*.sfc;*.smc|All files (*.*)|*.*", CheckFileExists = true };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            try { setupRom.Text = PublicSetupService.ValidateRom(dialog.FileName); SetStatus("ROM validated", "The selected file stays in place. Build source or use an existing compilation."); }
            catch (Exception error) { SetStatus("ROM not supported", error.Message, true); }
        };
        refreshBuilds.Click += (_, _) => RefreshSourceBuilds();
        updateProfile.Click += (_, _) =>
        {
            try
            {
                if (snapshot is null || sourceBuilds.SelectedItem is not SourceBuild selected) throw new InvalidOperationException("Choose a source profile and a local compilation.");
                busy = true; UpdateEnabled();
                var next = ProfileUpdateService.Update(snapshot, selected.ReceiptPath);
                busy = false; SelectSourceProfile(next); ShowPage("setup");
                SetStatus("Source profile updated", "Settings and saves were copied and verified. The previous folder remains available; compilation is verified and gameplay remains unqualified.");
            }
            catch (Exception error) { SetStatus("Profile update refused", error.Message, true); }
            finally { busy = false; UpdateEnabled(); }
        };
        rollbackProfile.Click += (_, _) =>
        {
            try
            {
                if (snapshot is null) throw new InvalidOperationException("Choose the updated source profile.");
                busy = true; UpdateEnabled();
                var previous = ProfileUpdateService.Rollback(snapshot);
                busy = false; SelectSourceProfile(previous); ShowPage("setup");
                SetStatus("Previous profile selected", "Both profiles and their separate progress are retained. Rollback switches the selection; it does not merge newer saves into the older folder.");
            }
            catch (Exception error) { SetStatus("Profile rollback refused", error.Message, true); }
            finally { busy = false; UpdateEnabled(); }
        };
        useBuild.Click += (_, _) =>
        {
            try
            {
                if (sourceBuilds.SelectedItem is not SourceBuild selected) throw new InvalidOperationException("Choose an existing source compilation.");
                SelectSourceProfile(PublicSetupService.AdoptBuild(root, selected.ReceiptPath, setupRom.Text));
            }
            catch (Exception error) { SetStatus("Build could not be selected", error.Message, true); }
        };
        buildSource.Click += async (_, _) =>
        {
            if (sourceBuildRunning) return;
            try
            {
                PublicSetupService.ValidateRom(setupRom.Text);
                sourceBuildRunning = helperRunning = busy = true; setupCancellation = new CancellationTokenSource();
                setupDiagnostics.Clear(); SetStatus("Building private local source", "Generation and compilation may take several minutes. Progress and full local log paths appear here."); UpdateEnabled();
                var progress = new Progress<string>(line =>
                {
                    if (IsDisposed || Disposing) return;
                    if (setupDiagnostics.TextLength > 180000) setupDiagnostics.Text = setupDiagnostics.Text[^120000..];
                    setupDiagnostics.AppendText(line + Environment.NewLine);
                });
                var selectedProfile = await PublicSetupService.BuildAsync(root, setupRom.Text, progress, setupCancellation.Token);
                if (!IsDisposed && !Disposing) { helperRunning = busy = sourceBuildRunning = false; SelectSourceProfile(selectedProfile); RefreshSourceBuilds(); }
            }
            catch (OperationCanceledException) { if (!IsDisposed && !Disposing) SetStatus("Build stopped", "Partial build output and existing profiles are preserved.", true); }
            catch (Exception error) { if (!IsDisposed && !Disposing) { setupDiagnostics.AppendText(error.Message + Environment.NewLine); SetStatus("Source build did not finish", error.Message, true); } }
            finally
            {
                sourceBuildRunning = helperRunning = busy = false; setupCancellation?.Dispose(); setupCancellation = null;
                if (!IsDisposed && !Disposing) UpdateEnabled();
            }
        };
        FormClosing += (_, _) => setupCancellation?.Cancel();
        try { if (File.Exists(Path.Combine(profile, PublicSetupService.ManifestName))) setupRom.Text = PublicSetupService.ReadProfile(profile).RomPath; }
        catch (Exception error) { setupDiagnostics.Text = error.Message; }
        RefreshSourceBuilds();
        if (PublicSetupService.GetSelectionProblem(root) is string problem) setupDiagnostics.AppendText(problem + Environment.NewLine);
    }

    void SelectSourceProfile(string selectedProfile)
    {
        profile = selectedProfile; ReloadProfile(); RefreshUpdateState(); ShowPage("play");
        SetStatus("Source build selected", "Fresh isolated profile ready. Compilation is verified; gameplay remains unqualified. Start at the title to test it.");
    }

    void RefreshSourceBuilds()
    {
        try
        {
            sourceBuilds.Items.Clear(); foreach (var source in PublicSetupService.DiscoverBuilds(root)) sourceBuilds.Items.Add(source);
            if (sourceBuilds.Items.Count > 0) sourceBuilds.SelectedIndex = 0;
            RefreshUpdateState();
        }
        catch (Exception error) { setupDiagnostics.Text = error.Message; }
    }

    void RefreshUpdateState()
    {
        var previous = ProfileUpdateService.GetRollback(root, profile);
        rollbackAvailable = previous is not null;
        updateHint.Text = previous is null ? "No verified previous source profile is selected. Update creates a retained predecessor without importing owner saves." :
            "Previous profile: " + Path.GetFileName(previous.PreviousProfile) + ". Its earlier progress stays separate from progress in the current folder.";
    }

    void SetSetupEnabled(bool enabled)
    {
        enabled &= !sourceBuildRunning;
        foreach (var control in new Control[] { setupRom, sourceBuilds, chooseRom, buildSource, useBuild, refreshBuilds }) control.Enabled = enabled;
        updateProfile.Enabled = enabled && PublicSetupService.IsSourceProfile(profile) && sourceBuilds.SelectedItem is SourceBuild;
        rollbackProfile.Enabled = enabled && rollbackAvailable;
    }
}
