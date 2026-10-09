using System.Buffers.Binary;
using System.Text.Json;

namespace SecretOfTheStars.Companion.Core;

public sealed record ProfileUpdateHistory(string Profile, string PreviousProfile, string BuildVersion, string HistoryPath);
internal sealed record UpdateHistory(string Profile, string PreviousProfile, string PreviousSelectionBase64,
    string PreviousManifestSha256, string PreviousExecutableSha256, string TargetReceiptPath,
    string TargetReceiptSha256, Dictionary<string, string> CopiedFiles, DateTime CreatedUtc);

/// <summary>Updates create new profiles. Selection is the sole commit point;
/// rollback never merges newer progress back into an older installation.</summary>
public static class ProfileUpdateService
{
    const string HistoryName = "update-history.json";
    static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    public static string Update(ProfileSnapshot snapshot, string receiptPath) =>
        UpdateCore(snapshot, receiptPath, () => ProfileService.IsGameRunning(snapshot));

    internal static string UpdateCore(ProfileSnapshot snapshot, string receiptPath, Func<bool> running, Action<string>? stage = null)
    {
        var root = snapshot.RootDirectory;
        var previous = PublicSetupService.RequireInside(snapshot.ProfileDirectory, Path.Combine(root, "local", "companion-public", "profiles"));
        EnsureIdle(snapshot, running);
        using var buildLock = AcquireBuildLock(root);
        using var selectionLock = PublicSetupService.AcquireSelectionLock(root);
        var selection = ReadSelection(root, previous);
        var oldSource = PublicSetupService.ReadProfile(previous);
        var target = PublicSetupService.CheckBuild(root, receiptPath);
        var targetReceiptHash = PublicSetupService.HashFile(target.ReceiptPath);
        var romPath = PublicSetupService.ValidateRom(oldSource.RomPath);
        var originals = Inventory(previous);
        if (originals.ContainsKey("companion-resume.state")) throw new InvalidOperationException("A prepared Resume checkpoint is pending. Finish that launch before updating.");
        CheckCompatibility(oldSource, target, originals, previous);
        // Every preflight above is read only. All subsequent writes go to a new
        // folder; a failed transaction is retained there without selection.
        var profile = Path.Combine(Path.GetDirectoryName(previous)!, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-update-" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(profile);
        foreach (var (relative, hash) in originals)
        {
            if (relative is PublicSetupService.ManifestName or HistoryName || relative == PublicSetupService.GameName + ".exe") continue;
            var input = Path.Combine(previous, relative); var output = Path.Combine(profile, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(output)!);
            File.Copy(input, output, false);
            if (PublicSetupService.HashFile(output) != hash) throw new IOException("Profile copy verification failed. The old profile remains selected.");
        }
        stage?.Invoke("copied");
        var executable = Path.Combine(profile, PublicSetupService.GameName + ".exe");
        File.Copy(Path.Combine(Path.GetDirectoryName(target.ReceiptPath)!, "build", PublicSetupService.GameName + ".exe"), executable, false);
        if (PublicSetupService.HashFile(executable) != target.ExecutableSha256) throw new IOException("New native executable copy did not verify.");
        WriteJson(Path.Combine(profile, PublicSetupService.ManifestName), new SourceProfile(target.ReceiptPath, targetReceiptHash, romPath, target.ExecutableSha256, PublicSetupService.RuntimePin));
        var ready = ProfileService.Load(root, profile);
        if (!ready.Readiness.Ready) throw new InvalidOperationException(ready.Readiness.Message);
        var historyPath = Path.Combine(profile, HistoryName);
        WriteJson(historyPath, new UpdateHistory(profile, previous, Convert.ToBase64String(selection),
            originals[PublicSetupService.ManifestName], oldSource.ExecutableSha256, target.ReceiptPath, targetReceiptHash, originals, DateTime.UtcNow));
        stage?.Invoke("ready");
        EnsureIdle(snapshot, running);
        if (!SameInventory(originals, Inventory(previous))) throw new InvalidOperationException("Original profile changed during update. Its selection and data are preserved; retry after refreshing.");
        if (PublicSetupService.HashFile(target.ReceiptPath) != targetReceiptHash || PublicSetupService.CheckBuild(root, target.ReceiptPath).ExecutableSha256 != target.ExecutableSha256)
            throw new InvalidOperationException("Target compilation changed during update.");
        CommitSelection(root, selection, JsonSerializer.SerializeToUtf8Bytes(new { profile, history_sha256 = PublicSetupService.HashFile(historyPath) }, JsonOptions));
        return profile;
    }

    public static ProfileUpdateHistory? GetRollback(string root, string profile)
    {
        try
        {
            var history = ReadHistory(root, profile);
            return new(profile, history.PreviousProfile, PublicSetupService.CheckBuild(root, history.TargetReceiptPath).Version, Path.Combine(profile, HistoryName));
        }
        catch (Exception error) when (error is IOException or InvalidOperationException or ArgumentException or JsonException or KeyNotFoundException or FormatException) { return null; }
    }

    public static string Rollback(ProfileSnapshot snapshot) => RollbackCore(snapshot, () => ProfileService.IsGameRunning(snapshot));

    internal static string RollbackCore(ProfileSnapshot snapshot, Func<bool> running, Action? beforeCommit = null)
    {
        EnsureIdle(snapshot, running);
        using var buildLock = AcquireBuildLock(snapshot.RootDirectory);
        using var selectionLock = PublicSetupService.AcquireSelectionLock(snapshot.RootDirectory);
        var selection = ReadSelection(snapshot.RootDirectory, snapshot.ProfileDirectory);
        if (File.Exists(Path.Combine(snapshot.ProfileDirectory, "companion-resume.state"))) throw new InvalidOperationException("Finish the pending Resume launch before rolling back.");
        var history = ReadHistory(snapshot.RootDirectory, snapshot.ProfileDirectory);
        var previous = PublicSetupService.RequireInside(history.PreviousProfile, Path.Combine(snapshot.RootDirectory, "local", "companion-public", "profiles"));
        if (PublicSetupService.HashFile(Path.Combine(previous, PublicSetupService.ManifestName)) != history.PreviousManifestSha256)
            throw new InvalidOperationException("Previous profile identity changed. Rollback refused; all files remain in place.");
        var prior = ProfileService.Load(snapshot.RootDirectory, previous);
        if (!prior.Readiness.Ready || PublicSetupService.ReadProfile(previous).ExecutableSha256 != history.PreviousExecutableSha256 || ProfileService.IsGameRunning(prior))
            throw new InvalidOperationException("Previous profile is unavailable, modified or running. Rollback refused.");
        var previousSelection = Convert.FromBase64String(history.PreviousSelectionBase64);
        using (var json = JsonDocument.Parse(previousSelection))
            if (json.RootElement.GetProperty("profile").GetString() != previous) throw new InvalidOperationException("Previous selection history is inconsistent.");
        beforeCommit?.Invoke(); EnsureIdle(snapshot, running);
        CommitSelection(snapshot.RootDirectory, selection, previousSelection);
        return previous;
    }

    static UpdateHistory ReadHistory(string root, string profile)
    {
        profile = PublicSetupService.RequireInside(profile, Path.Combine(root, "local", "companion-public", "profiles"));
        var selection = ReadSelection(root, profile);
        var historyPath = Path.Combine(profile, HistoryName); PublicSetupService.RejectLinkedPath(historyPath);
        using var json = JsonDocument.Parse(selection);
        if (!json.RootElement.TryGetProperty("history_sha256", out var hash) || !File.Exists(historyPath) || hash.GetString() != PublicSetupService.HashFile(historyPath))
            throw new InvalidOperationException("No verified previous source profile is available.");
        var history = JsonSerializer.Deserialize<UpdateHistory>(File.ReadAllBytes(historyPath)) ?? throw new InvalidOperationException("Update history is invalid.");
        if (history.Profile != profile || PublicSetupService.HashFile(history.TargetReceiptPath) != history.TargetReceiptSha256)
            throw new InvalidOperationException("Update history or compilation identity changed.");
        return history;
    }

    static void EnsureIdle(ProfileSnapshot snapshot, Func<bool> running)
    {
        if (running()) throw new InvalidOperationException("Close the game before changing its selected profile.");
        foreach (var file in snapshot.Files.Values)
        {
            PublicSetupService.RejectLinkedPath(file.Path);
            if (File.Exists(file.Path) != file.Exists || (file.Exists && PublicSetupService.HashFile(file.Path) != file.Sha256))
                throw new InvalidOperationException("Profile inputs changed since they were loaded. Refresh before updating.");
        }
        var fresh = ProfileService.Load(snapshot.RootDirectory, snapshot.ProfileDirectory);
        if (!fresh.Readiness.Ready || !PublicSetupService.IsSourceProfile(snapshot.ProfileDirectory))
            throw new InvalidOperationException("Choose a ready isolated source profile. Owner installations are not imported by this action.");
    }

    static FileStream AcquireBuildLock(string root)
    {
        var folder = Path.Combine(root, "local", "companion-public"); PublicSetupService.RejectLinkedPath(folder); Directory.CreateDirectory(folder);
        var path = Path.Combine(folder, "build.lock"); PublicSetupService.RejectLinkedPath(path);
        return new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }

    static byte[] ReadSelection(string root, string expected)
    {
        var path = Path.Combine(root, "local", "companion-public", "setup.json"); PublicSetupService.RejectLinkedPath(path);
        var bytes = File.ReadAllBytes(path);
        using var json = JsonDocument.Parse(bytes);
        if (!string.Equals(Path.GetFullPath(json.RootElement.GetProperty("profile").GetString() ?? ""), Path.GetFullPath(expected), StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Another profile is selected. Refresh Setup before changing it.");
        return bytes;
    }

    static void CommitSelection(string root, byte[] expected, byte[] replacement)
    {
        var path = Path.Combine(root, "local", "companion-public", "setup.json");
        PublicSetupService.RejectLinkedPath(path);
        if (!File.ReadAllBytes(path).AsSpan().SequenceEqual(expected)) throw new InvalidOperationException("Source selection changed during the operation. No selection was replaced.");
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough)) { output.Write(replacement); output.Flush(true); }
        if (!File.ReadAllBytes(path).AsSpan().SequenceEqual(expected)) throw new InvalidOperationException("Source selection changed before commit. The new profile is retained without selection.");
        File.Replace(temporary, path, null);
    }

    internal static Dictionary<string, string> Inventory(string folder)
    {
        PublicSetupService.RejectLinkedPath(folder);
        var files = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        void Visit(string directory)
        {
            PublicSetupService.RejectLinkedPath(directory);
            foreach (var file in Directory.EnumerateFiles(directory)) { PublicSetupService.RejectLinkedPath(file); files.Add(Path.GetRelativePath(folder, file), PublicSetupService.HashFile(file)); }
            foreach (var child in Directory.EnumerateDirectories(directory)) Visit(child);
        }
        Visit(folder); return files;
    }
    static bool SameInventory(Dictionary<string, string> a, Dictionary<string, string> b) => a.Count == b.Count && a.All(file => b.TryGetValue(file.Key, out var hash) && hash == file.Value);
    static void WriteJson<T>(string path, T value)
    { using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough); JsonSerializer.Serialize(stream, value, JsonOptions); stream.Flush(true); }

    static void CheckCompatibility(SourceProfile source, SourceBuild target, Dictionary<string, string> files, string profile)
    {
        if (source.ExecutableSha256 == target.ExecutableSha256) return;
        using var oldReceipt = JsonDocument.Parse(File.ReadAllBytes(source.ReceiptPath));
        using var newReceipt = JsonDocument.Parse(File.ReadAllBytes(target.ReceiptPath));
        var old = oldReceipt.RootElement; var next = newReceipt.RootElement;
        if (!old.TryGetProperty("checkpoint_schema", out var oldSchema) || !next.TryGetProperty("checkpoint_schema", out var newSchema) ||
            !oldSchema.TryGetProperty("identity", out var oldIdentity) || !newSchema.TryGetProperty("identity", out var newIdentity) ||
            oldIdentity.GetString() != "sots-clean-foundation-v1" || newIdentity.GetString() != oldIdentity.GetString() ||
            !newSchema.GetProperty("reads").EnumerateArray().Any(v => v.GetInt32() == oldSchema.GetProperty("writes").GetInt32()) ||
            !old.TryGetProperty("save_compatibility", out var oldSram) || !next.TryGetProperty("save_compatibility", out var newSram) ||
            oldSram.GetString() != "secret-of-the-stars-usa-sram-v1" || newSram.GetString() != oldSram.GetString() ||
            !old.TryGetProperty("execution_state_abi_sha256", out var oldAbi) || !next.TryGetProperty("execution_state_abi_sha256", out var newAbi) ||
            oldAbi.GetString() is not string abi || abi.Length != 64 || !abi.All(Uri.IsHexDigit) || newAbi.GetString() != abi)
            throw new InvalidOperationException("Changed native executables require matching declared save/checkpoint compatibility. Preserve this profile and use a fresh adoption when legacy receipt metadata is missing.");
        var supported = newSchema.GetProperty("reads").EnumerateArray().Select(v => v.GetInt32()).ToHashSet();
        foreach (var relative in files.Keys.Where(f => Path.GetExtension(f).Equals(".sav", StringComparison.OrdinalIgnoreCase) || Path.GetExtension(f).Equals(".state", StringComparison.OrdinalIgnoreCase)))
        {
            var bytes = File.ReadAllBytes(Path.Combine(profile, relative));
            var schemas = new List<int>();
            for (int i = 0; i <= bytes.Length - 8; i++)
                if (BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(i, 4)) == 0x53544f53) schemas.Add((int)BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(i + 4, 4)));
            if (schemas.Count != 1 || !supported.Contains(schemas[0])) throw new InvalidOperationException("Checkpoint schema is unknown or incompatible: " + relative);
        }
    }
}
