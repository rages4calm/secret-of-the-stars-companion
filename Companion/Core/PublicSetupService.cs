using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;

namespace SecretOfTheStars.Companion.Core;

public sealed record SourceBuild(string ReceiptPath, string Version, string ExecutableSha256, DateTime CreatedUtc)
{
    public override string ToString() => $"{Version} · {CreatedUtc.ToLocalTime():g} · compiled, gameplay unqualified";
}

internal sealed record SourceProfile(string ReceiptPath, string ReceiptSha256, string RomPath,
    string ExecutableSha256, string RuntimePin, string Status = "compiled_unqualified");

/// <summary>Source-first setup. Private build receipts describe compilation;
/// they never substitute for a gameplay qualification receipt.</summary>
public static class PublicSetupService
{
    internal const string GameName = "SecretOfTheStarsSNESRecomp";
    internal const string RomHash = "7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600";
    internal const string RuntimePin = "7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0";
    internal const string ManifestName = "source-profile.json";
    private static readonly StringComparison Paths = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;

    public static bool IsSourceProfile(string profile) => File.Exists(Path.Combine(Path.GetFullPath(profile), ManifestName));

    public static string ValidateRom(string path)
    {
        path = Path.GetFullPath(path); RejectLinkedPath(path);
        if (!File.Exists(path) || new FileInfo(path).Length != 1572864 || HashFile(path) != RomHash)
            throw new InvalidOperationException("Choose your exact clean, unheadered USA ROM (1,572,864 bytes). The selected file is read only and is not copied.");
        return path;
    }

    public static string? GetSelectedProfile(string root)
    {
        try { return ReadSelectedProfile(root); }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or KeyNotFoundException or ArgumentException)
        { return null; } // Preserve stale selection and allow the Setup page to repair it.
    }

    public static string? GetSelectionProblem(string root)
    {
        try { _ = ReadSelectedProfile(root); return null; }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or KeyNotFoundException or ArgumentException)
        { return "Previous source selection could not be loaded; its files are preserved. Choose the ROM and adopt a valid compilation in Setup. " + error.Message; }
    }

    private static string? ReadSelectedProfile(string root)
    {
        var state = Path.Combine(Path.GetFullPath(root), "local", "companion-public", "setup.json");
        if (!File.Exists(state)) return null;
        RejectLinkedPath(state);
        using var json = JsonDocument.Parse(File.ReadAllBytes(state));
        var selected = json.RootElement.GetProperty("profile").GetString() ?? throw new InvalidOperationException("Public setup profile is missing.");
        selected = RequireInside(selected, Path.Combine(root, "local", "companion-public", "profiles"));
        _ = ReadProfile(selected); return selected;
    }

    public static IReadOnlyList<SourceBuild> DiscoverBuilds(string root)
    {
        var directory = Path.Combine(Path.GetFullPath(root), "local", "source-builds");
        if (!Directory.Exists(directory)) return [];
        RejectLinkedPath(directory);
        var builds = new List<SourceBuild>();
        foreach (var folder in Directory.EnumerateDirectories(directory))
        {
            var receipt = Path.Combine(folder, "source-build-receipt.json");
            try { if (File.Exists(receipt)) builds.Add(CheckBuild(root, receipt)); }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or KeyNotFoundException) { /* An incomplete/modified build is not offered. */ }
        }
        return builds.OrderByDescending(b => b.CreatedUtc).ToArray();
    }

    public static string AdoptBuild(string root, string receiptPath, string romPath)
    {
        root = Path.GetFullPath(root); romPath = ValidateRom(romPath);
        using var selectionLock = AcquireSelectionLock(root);
        var build = CheckBuild(root, receiptPath);
        var buildFolder = Path.GetDirectoryName(build.ReceiptPath)!;
        var profiles = Path.Combine(root, "local", "companion-public", "profiles");
        RejectLinkedPath(profiles); Directory.CreateDirectory(profiles);
        var profile = Path.Combine(profiles, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(profile);
        // Always create a fresh profile. An existing source-build profile and
        // every owner checkpoint/config remain untouched.
        var executable = Path.Combine(profile, GameName + ".exe");
        File.Copy(Path.Combine(buildFolder, "build", GameName + ".exe"), executable, false);
        foreach (var name in new[] { "config.ini", "foundation.ini", "keybinds.ini" })
        {
            var source = Path.Combine(buildFolder, "profile", name);
            RejectLinkedPath(source);
            if (File.Exists(source)) File.Copy(source, Path.Combine(profile, name), false);
        }
        var configPath = Path.Combine(profile, "config.ini");
        var config = new IniDocument(File.Exists(configPath) ? File.ReadAllBytes(configPath) : []);
        config.Set("General", "Autosave", "0"); config.Set("General", "SkipLauncher", "1");
        File.WriteAllBytes(configPath, config.ToBytes());
        if (HashFile(executable) != build.ExecutableSha256) throw new IOException("Copied executable verification failed; incomplete isolated profile preserved.");
        var sourceProfile = new SourceProfile(build.ReceiptPath, HashFile(build.ReceiptPath), romPath, build.ExecutableSha256, RuntimePin);
        WriteNewJson(Path.Combine(profile, ManifestName), sourceProfile);
        Directory.CreateDirectory(Path.Combine(profile, "saves"));
        var ready = ProfileService.Load(root, profile); // Verify the entire identity before selecting it.
        if (!ready.Readiness.Ready) throw new InvalidOperationException(ready.Readiness.Message);
        var setup = Path.Combine(root, "local", "companion-public", "setup.json");
        RejectLinkedPath(setup);
        var temporary = setup + "." + Guid.NewGuid().ToString("N") + ".tmp";
        WriteNewJson(temporary, new { profile });
        if (File.Exists(setup)) File.Replace(temporary, setup, null); else File.Move(temporary, setup);
        return profile;
    }

    public static async Task<string> BuildAsync(string root, string romPath, IProgress<string>? progress = null, CancellationToken cancellation = default)
    {
        root = Path.GetFullPath(root); romPath = ValidateRom(romPath);
        var helper = Path.Combine(root, "tools", "build_public_foundation.py");
        RejectLinkedPath(helper);
        if (!File.Exists(helper)) throw new FileNotFoundException("The public native build helper is missing.", helper);
        var prior = DiscoverBuilds(root).Select(b => b.ReceiptPath).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var logs = Path.Combine(root, "local", "companion-public", "logs");
        RejectLinkedPath(logs); Directory.CreateDirectory(logs);
        // Two launchers must not race on the shared runtime or second-granularity
        // build folders. A failed/cancelled build leaves prior source work intact.
        var lockPath = Path.Combine(root, "local", "companion-public", "build.lock"); RejectLinkedPath(lockPath);
        using var buildLock = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        var logPath = Path.Combine(logs, "build-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N")[..8] + ".log");
        progress?.Report("Build diagnostics: " + logPath);
        var start = new ProcessStartInfo("python") { WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (var arg in new[] { "-u", helper, "--rom", romPath }) start.ArgumentList.Add(arg);
        var sdlPackage = Environment.GetEnvironmentVariable("SDL3_DIR");
        if (!string.IsNullOrWhiteSpace(sdlPackage)) { start.ArgumentList.Add("--sdl3-dir"); start.ArgumentList.Add(sdlPackage); }
        using var log = new StreamWriter(new FileStream(logPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read)) { AutoFlush = true };
        using var gate = new SemaphoreSlim(1, 1);
        using var process = Process.Start(start) ?? throw new IOException("Python did not start.");
        async Task Drain(StreamReader reader)
        {
            while (await reader.ReadLineAsync() is string line)
            {
                await gate.WaitAsync(); try { await log.WriteLineAsync(line); } finally { gate.Release(); }
                progress?.Report(line);
            }
        }
        var output = Drain(process.StandardOutput); var errors = Drain(process.StandardError);
        try { await process.WaitForExitAsync(cancellation); }
        catch (OperationCanceledException)
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync(); await Task.WhenAll(output, errors);
            throw;
        }
        await Task.WhenAll(output, errors);
        if (process.ExitCode != 0) throw new InvalidOperationException($"Build exited with code {process.ExitCode}. Inspect {logPath}. Existing profiles and runtime edits were preserved.");
        var created = DiscoverBuilds(root).FirstOrDefault(b => !prior.Contains(b.ReceiptPath)) ?? throw new InvalidOperationException("Build finished without a valid new compilation receipt. Inspect " + logPath);
        return AdoptBuild(root, created.ReceiptPath, romPath);
    }

    internal static SourceProfile ReadProfile(string profile)
    {
        var path = Path.Combine(profile, ManifestName); RejectLinkedPath(path);
        var source = JsonSerializer.Deserialize<SourceProfile>(File.ReadAllBytes(path)) ?? throw new InvalidOperationException("Source profile manifest is invalid.");
        if (source.Status != "compiled_unqualified" || source.RuntimePin != RuntimePin) throw new InvalidOperationException("Source profile status/runtime is unsupported.");
        return source;
    }

    internal static SourceBuild CheckBuild(string root, string receiptPath)
    {
        receiptPath = RequireInside(receiptPath, Path.Combine(root, "local", "source-builds"));
        if (Path.GetFileName(receiptPath) != "source-build-receipt.json") throw new InvalidOperationException("Choose an actual source build receipt.");
        using var json = JsonDocument.Parse(File.ReadAllBytes(receiptPath)); var receipt = json.RootElement;
        if (receipt.GetProperty("status").GetString() != "compiled_unqualified" || !receipt.GetProperty("public_build").GetBoolean() ||
            receipt.GetProperty("rom_sha256").GetString() != RomHash || receipt.GetProperty("runtime_pin").GetString() != RuntimePin)
            throw new InvalidOperationException("Receipt does not describe a supported public source compilation.");
        var binary = Path.Combine(Path.GetDirectoryName(receiptPath)!, "build", GameName + ".exe"); RejectLinkedPath(binary);
        var expected = receipt.GetProperty("executable_sha256").GetString() ?? "";
        if (!File.Exists(binary) || HashFile(binary) != expected) throw new InvalidOperationException("Source build executable differs from its compilation receipt.");
        return new SourceBuild(receiptPath, receipt.GetProperty("version").GetString() ?? "unknown", expected, File.GetLastWriteTimeUtc(receiptPath));
    }

    internal static string RequireInside(string path, string directory)
    {
        path = Path.GetFullPath(path); directory = Path.GetFullPath(directory).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!path.StartsWith(directory, Paths)) throw new InvalidOperationException("Source setup path is outside its isolated local folder.");
        RejectLinkedPath(path); return path;
    }

    internal static void RejectLinkedPath(string path)
    {
        for (var current = Path.GetFullPath(path); !string.IsNullOrEmpty(current); current = Path.GetDirectoryName(current))
            if ((File.Exists(current) || Directory.Exists(current)) && (File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0)
                throw new InvalidOperationException("Linked setup paths are not supported: " + current);
    }

    internal static string HashFile(string path) { using var input = File.OpenRead(path); return Convert.ToHexString(SHA256.HashData(input)).ToLowerInvariant(); }
    internal static FileStream AcquireSelectionLock(string root)
    {
        var folder = Path.Combine(Path.GetFullPath(root), "local", "companion-public");
        RejectLinkedPath(folder); Directory.CreateDirectory(folder);
        var path = Path.Combine(folder, "selection.lock"); RejectLinkedPath(path);
        return new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }
    private static void WriteNewJson<T>(string path, T value)
    {
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough);
        JsonSerializer.Serialize(stream, value, new JsonSerializerOptions { WriteIndented = true }); stream.Flush(true);
    }
}
