using System.Diagnostics;

namespace SecretOfTheStars.Companion.Core;

public sealed record GameSettings
{
    public bool Fullscreen { get; set; }
    public int WindowScale { get; set; } = 4;
    public bool VSync { get; set; } = true;
    public string Renderer { get; set; } = "direct3d11";
    public bool NoSpriteLimits { get; set; }
    public bool EnableAudio { get; set; } = true;
    public int Volume { get; set; } = 70;
    public bool EnableGamepad { get; set; } = true;
    public bool EnableGamepad2 { get; set; }
    public int Deadzone { get; set; } = 3277;
    public bool BattleInfo { get; set; } = true;
    public bool EnhancedPixels { get; set; } = true;
    public bool FastMenus { get; set; } = true;
    public bool Journal { get; set; } = true;
    public bool JournalPossession { get; set; } = true;
    public bool NavigationMap { get; set; } = true;
    public bool NavigationMapObjective { get; set; } = true;
    public bool HdMenuFrames { get; set; }
    public bool ExperimentalFieldWide { get; set; }
    public bool ExperimentalFieldActors { get; set; }
    public int XpMultiplierPercent { get; set; } = 100;
    public int GoldMultiplierPercent { get; set; } = 100;
    public int MovementSpeedPercent { get; set; } = 200;
    public bool FastForwardToggle { get; set; }
    public bool LegacyControllerGestures { get; set; } = true;
    public Dictionary<string, HotkeyBinding> HotkeyBindings { get; set; } = HotkeyCatalog.CreateBindings();
    public Dictionary<string, string> GameplayKeys { get; set; } = HotkeyCatalog.CreateGameplayKeys();
    public GameSettings DeepCopy() => this with
    {
        HotkeyBindings = new(HotkeyBindings, StringComparer.Ordinal),
        GameplayKeys = new(GameplayKeys, StringComparer.Ordinal)
    };
}

public sealed record HotkeyBinding(string Keyboard, string Controller);

public sealed record ReadinessInfo(bool Ready, string Message);
public sealed record SaveEntry(string Label, string Path, DateTime LastWriteTimeUtc, long Size)
{
    internal string Sha256 { get; init; } = "";
}
public enum LaunchMode { Play, Resume, OriginalView, WidescreenPreview, HdMenuPreview }
public sealed record LaunchRequest(LaunchMode Mode, string? SavePath = null);
public sealed record ApplyResult(bool Success, string Message, ProfileSnapshot? Snapshot = null,
    string? BackupDirectory = null);

public sealed class ProfileSnapshot
{
    public string RootDirectory { get; internal init; } = "";
    public string ProfileDirectory { get; internal init; } = "";
    public GameSettings Settings { get; internal init; } = new();
    public ReadinessInfo Readiness { get; internal init; } = new(false, "Not loaded.");
    public IReadOnlyList<SaveEntry> Saves { get; internal init; } = Array.Empty<SaveEntry>();
    internal GameSettings OriginalSettings { get; init; } = new();
    internal IReadOnlyDictionary<string, FileIdentity> Files { get; init; } =
        new Dictionary<string, FileIdentity>();
}

internal sealed record FileIdentity(string Path, bool Exists, string Sha256, byte[] Bytes);
