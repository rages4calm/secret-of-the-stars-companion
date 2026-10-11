using System.Text.RegularExpressions;

namespace SecretOfTheStars.Companion.Core;

public sealed record HotkeyAction(string Id, string Label, string Keyboard, string Controller, int Slots = 1);

public static class HotkeyCatalog
{
    public static readonly string[] GameplayOrder = ["up", "down", "left", "right", "select", "start", "a", "b", "x", "y", "l", "r"];
    public static readonly string[] KeyboardChoices = ["None", "Tab", "Left Shift", "Right Shift", "Left Ctrl", "Right Ctrl", "Left Alt", "Right Alt", "Space", "Return", "Escape", "Backspace", "Up", "Down", "Left", "Right", "Home", "End", "PageUp", "PageDown", "Insert", "Delete", "Keypad +", "Keypad -", "Alt+Return", "Ctrl+R", "Shift+P", .. Enumerable.Range(0, 26).Select(i => ((char)('A' + i)).ToString()), .. Enumerable.Range(0, 10).Select(i => i.ToString()), .. Enumerable.Range(1, 24).Select(i => "F" + i)];
    public static readonly string[] ControllerChoices = ["None", "A", "B", "X", "Y", "Back", "Guide", "Start", "L3", "R3", "L1", "R1", "L2", "R2", "DpadUp", "DpadDown", "DpadLeft", "DpadRight"];
    static string Slots(params string[] bound) => string.Join(',', bound.Concat(Enumerable.Repeat("None", 20 - bound.Length)));
    public static readonly HotkeyAction[] Actions =
    [
        new("Turbo", "Fast-forward", "Tab", "R2"),
        new("MovementBoost", "Movement boost", "Left Shift", "L2"),
        new("Fullscreen", "Fullscreen", "Alt+Return,F11,F12", "None"),
        new("BattleInfo", "Battle information", "H", "R3"),
        new("Journal", "Quest journal", "J", "L3"),
        new("Map", "Current-area map", "M", "Back+L3"),
        new("Reset", "Restart game", "Ctrl+R", "None"),
        new("Pause", "Pause", "Shift+P", "None"),
        new("PauseDimmed", "Pause and dim screen", "P", "None"),
        new("SaveStateMenu", "Checkpoint menu", "F7", "None"),
        new("Rewind", "Rewind menu", "F8", "None"),
        new("Screenshot", "Screenshot (OpenGL)", "None", "None"),
        new("WindowBigger", "Larger window", "None", "None"),
        new("WindowSmaller", "Smaller window", "None", "None"),
        new("VolumeUp", "Volume up", "Keypad +", "None"),
        new("VolumeDown", "Volume down", "Keypad -", "None"),
        new("DisplayPerf", "Performance display", "F", "None"),
        new("ToggleRenderer", "Switch renderer", "R", "None"),
        new("ToggleWidescreen", "Runtime widescreen switch", "Alt+W", "None"),
        new("Load", "Load checkpoint", Slots("F1", "F2", "F3", "F4", "F5", "F6", "None", "None", "F9", "F10"), Slots(), 20),
        new("Save", "Save checkpoint", Slots("Shift+F1", "Shift+F2", "Shift+F3", "Shift+F4", "Shift+F5", "Shift+F6", "None", "None", "Shift+F9", "Shift+F10"), Slots(), 20),
        new("Controls", "Player 1", "", "DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,B,A,Y,X,L1,R1", 12),
        new("ControlsP2", "Player 2", "", "DpadUp,DpadDown,DpadLeft,DpadRight,Back,Start,B,A,Y,X,L1,R1", 12)
    ];

    public static Dictionary<string, HotkeyBinding> CreateBindings() => Actions.ToDictionary(a => a.Id, a => new HotkeyBinding(a.Keyboard, a.Controller), StringComparer.Ordinal);
    public static Dictionary<string, string> CreateGameplayKeys()
    {
        var defaults = new[] { "Up", "Down", "Left", "Right", "Right Shift", "Return", "X", "Z", "S", "A", "C", "V" };
        return Enumerable.Range(1, 2).SelectMany(player => GameplayOrder.Select((key, i) => (Id: $"player{player}:{key}", Key: defaults[i]))).ToDictionary(p => p.Id, p => p.Key, StringComparer.Ordinal);
    }
    public static string GetSlot(string value, int slot)
    {
        var tokens = value.Split(',');
        return slot < tokens.Length && !string.IsNullOrWhiteSpace(tokens[slot]) ? tokens[slot].Trim() : "None";
    }
    public static string SetSlot(string value, int slot, int count, string binding)
    {
        var values = value.Split(',').ToList();
        while (values.Count < count) values.Add("None");
        values[slot] = binding.Trim();
        return string.Join(',', values);
    }
    public static bool IsUnbound(string token) => string.IsNullOrWhiteSpace(token) || token.Equals("None", StringComparison.OrdinalIgnoreCase) || token.Equals("(unbound)", StringComparison.OrdinalIgnoreCase);

    public static string NormalizeBindingToken(string token, bool controller)
    {
        token = token.Trim();
        if (controller) return string.Join('+', token.Split('+').Select(p => p.Trim().Equals("Lb", StringComparison.OrdinalIgnoreCase) ? "L1" : p.Trim().Equals("Rb", StringComparison.OrdinalIgnoreCase) ? "R1" : p.Trim()).OrderBy(p => p, StringComparer.OrdinalIgnoreCase));
        var modifiers = Regex.Match(token, @"^(?:(?:Ctrl|Alt|Shift)\+)+", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant).Value;
        return string.Join('+', modifiers.Split('+', StringSplitOptions.RemoveEmptyEntries).OrderBy(p => p, StringComparer.OrdinalIgnoreCase).Append(token[modifiers.Length..]));
    }

    public static bool MapDefaultTaken(GameSettings settings, string candidate, bool controller)
    {
        var target = NormalizeBindingToken(candidate, controller);
        var values = Actions.Where(a => a.Id is not ("Map" or "ControlsP2") && (controller || a.Id != "Controls"))
            .Select(a => controller ? settings.HotkeyBindings[a.Id].Controller : settings.HotkeyBindings[a.Id].Keyboard);
        if (!controller) values = values.Concat(GameplayOrder.Select(button => settings.GameplayKeys["player1:" + button]));
        return values.SelectMany(value => value.Split(',')).Any(token => !IsUnbound(token) && NormalizeBindingToken(token, controller).Equals(target, StringComparison.OrdinalIgnoreCase));
    }

    public static void Validate(GameSettings settings, GameSettings? original = null)
    {
        foreach (var action in Actions)
        {
            if (!settings.HotkeyBindings.TryGetValue(action.Id, out var binding)) throw new ArgumentException("Missing binding: " + action.Label);
            HotkeyBinding? old = null;
            if (original != null) original.HotkeyBindings.TryGetValue(action.Id, out old);
            if (!action.Id.StartsWith("Controls", StringComparison.Ordinal) && (original == null || old?.Keyboard != binding.Keyboard)) ValidateKeyboard(binding.Keyboard, true);
            if (original == null || old?.Controller != binding.Controller) ValidateController(binding.Controller);
        }
        foreach (var name in CreateGameplayKeys().Keys)
        {
            if (!settings.GameplayKeys.TryGetValue(name, out var binding)) throw new ArgumentException("Missing gameplay binding: " + name);
            if (original == null || original.GameplayKeys.GetValueOrDefault(name) != binding) ValidateKeyboard(binding, false);
        }
        ValidateConflicts(settings, original, false);
        ValidateConflicts(settings, original, true);
    }
    static void ValidateConflicts(GameSettings settings, GameSettings? original, bool controller)
    {
        var seen = new Dictionary<string, (string Label, string Id, bool Changed)>(StringComparer.OrdinalIgnoreCase);
        foreach (var action in Actions.Where(a => a.Id != "ControlsP2" && (controller || a.Id != "Controls")))
        {
            var binding = settings.HotkeyBindings[action.Id];
            var value = controller ? binding.Controller : binding.Keyboard;
            var old = original?.HotkeyBindings.GetValueOrDefault(action.Id);
            string? oldValue = controller ? old?.Controller : old?.Keyboard;
            var tokens = value.Split(',');
            for (int i = 0; i < tokens.Length; i++)
            {
                if (IsUnbound(tokens[i])) continue;
                bool changed = original == null || tokens[i].Trim() != GetSlot(oldValue ?? "", i);
                string label = action.Id == "Controls" && i < GameplayOrder.Length ? "game " + GameplayOrder[i].ToUpperInvariant() : action.Slots > 1 ? action.Label + " slot " + (i + 1) : action.Label;
                string id = action.Id + (action.Slots > 1 || action.Id == "Controls" ? ":" + i : "");
                var token = NormalizeBindingToken(tokens[i], controller);
                if (seen.TryGetValue(token, out var existing) && existing.Id != id && (changed || existing.Changed))
                    throw new ArgumentException($"{tokens[i].Trim()} is assigned to both {existing.Label} and {label}. Clear one binding or choose a different {(controller ? "controller button" : "key")}.");
                seen[token] = (label, id, changed);
            }
        }
        if (!controller)
            foreach (var button in GameplayOrder)
            {
                string name = "player1:" + button, token = NormalizeBindingToken(settings.GameplayKeys[name], false);
                if (IsUnbound(token)) continue;
                bool changed = original == null || token != original.GameplayKeys.GetValueOrDefault(name)?.Trim();
                string label = "game " + button.ToUpperInvariant();
                if (seen.TryGetValue(token, out var existing) && (changed || existing.Changed))
                    throw new ArgumentException($"{token} is assigned to both {existing.Label} and {label}. Clear one binding or choose a different key.");
                seen[token] = (label, name, changed);
            }
    }
    public static void ValidateKeyboard(string value, bool chords)
    {
        if (value.Length > 2048 || value.IndexOfAny(['\r', '\n', '\0', ';', '#', '=']) >= 0) throw new ArgumentException("Invalid keyboard binding.");
        foreach (var token in value.Split(','))
        {
            if (IsUnbound(token)) continue;
            var key = token.Trim();
            if (chords) key = Regex.Replace(key, @"^(?:(?:Ctrl|Alt|Shift)\+)+", "", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            // SDL's printable key names plus documented named keys. A literal
            // plus is a key, not an extra modifier delimiter.
            if (key.Length == 1 && !char.IsControl(key[0])) continue;
            if (Regex.IsMatch(key, @"^F(?:[1-9]|1[0-9]|2[0-4])$", RegexOptions.IgnoreCase)) continue;
            if (KeyboardChoices.Contains(key, StringComparer.OrdinalIgnoreCase) && !key.Contains('+')) continue;
            if (new[] { "Keypad +", "Keypad -", "Keypad *", "Keypad /", "Keypad .", "Keypad =", "Keypad Enter", "Keypad 0", "Keypad 1", "Keypad 2", "Keypad 3", "Keypad 4", "Keypad 5", "Keypad 6", "Keypad 7", "Keypad 8", "Keypad 9" }.Contains(key, StringComparer.OrdinalIgnoreCase)) continue;
            if (new[] { "CapsLock", "Numlock", "ScrollLock", "PrintScreen", "Pause", "Application", "Left GUI", "Right GUI" }.Contains(key, StringComparer.OrdinalIgnoreCase)) continue;
            throw new ArgumentException("Unknown keyboard key: " + token.Trim());
        }
        if (!chords && value.Contains(',')) throw new ArgumentException("Choose one key for a gameplay button.");
    }
    public static void ValidateController(string value)
    {
        if (value.Length > 2048 || value.IndexOfAny(['\r', '\n', '\0', ';', '#', '=']) >= 0) throw new ArgumentException("Invalid controller binding.");
        foreach (var token in value.Split(','))
        {
            if (IsUnbound(token)) continue;
            foreach (var part in token.Split('+'))
                if (!ControllerChoices.Contains(part.Trim(), StringComparer.OrdinalIgnoreCase) && !new[] { "Lb", "Rb" }.Contains(part.Trim(), StringComparer.OrdinalIgnoreCase)) throw new ArgumentException("Unknown controller button: " + part.Trim());
        }
    }
}
