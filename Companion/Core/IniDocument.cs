using System.Text;
using System.Text.RegularExpressions;

namespace SecretOfTheStars.Companion.Core;

/// <summary>ASCII key editing over original bytes. Unknown UTF-8/ANSI bytes,
/// BOM, comments, whitespace, ordering and each individual line ending survive.
/// UTF-16 BOM files are decoded strictly and retain their encoding and BOM.</summary>
internal sealed class IniDocument
{
    private sealed record Line(string Text, string Ending);
    private readonly List<Line> lines = new();
    private readonly Encoding encoding;
    private readonly byte[] prefix;
    private static readonly Regex Section = new(@"^\s*\[([^\]]+)\]\s*(?:[;#].*)?$", RegexOptions.CultureInvariant);
    private static readonly Regex Key = new(@"^(\s*)([^=;#]+?)(\s*=\s*)(.*)$", RegexOptions.CultureInvariant);
    private static readonly Regex Value = new(@"^(.*?)(\s+[;#].*)?$", RegexOptions.CultureInvariant);

    public IniDocument(byte[] bytes)
    {
        if (bytes.AsSpan().StartsWith(new byte[] { 0xff, 0xfe }))
        { prefix = new byte[] { 0xff, 0xfe }; encoding = new UnicodeEncoding(false, false, true); }
        else if (bytes.AsSpan().StartsWith(new byte[] { 0xfe, 0xff }))
        { prefix = new byte[] { 0xfe, 0xff }; encoding = new UnicodeEncoding(true, false, true); }
        else
        {
            prefix = bytes.AsSpan().StartsWith(new byte[] { 0xef, 0xbb, 0xbf }) ? new byte[] { 0xef, 0xbb, 0xbf } : Array.Empty<byte>();
            encoding = Encoding.Latin1; // One char per original byte; never transcode unknown UTF-8.
        }
        var text = encoding.GetString(bytes, prefix.Length, bytes.Length - prefix.Length);
        for (var offset = 0; offset < text.Length;)
        {
            var end = offset;
            while (end < text.Length && text[end] != '\r' && text[end] != '\n') end++;
            var after = end;
            if (after < text.Length && text[after++] == '\r' && after < text.Length && text[after] == '\n') after++;
            lines.Add(new Line(text[offset..end], text[end..after]));
            offset = after;
        }
    }

    public string? Get(string section, string key, bool titleGlobal = false)
    {
        string current = "";
        string? found = null;
        foreach (var line in lines)
        {
            var header = Section.Match(line.Text);
            if (header.Success) { current = header.Groups[1].Value.Trim(); continue; }
            var match = Key.Match(line.Text);
            if (match.Success && (titleGlobal || current.Equals(section, StringComparison.OrdinalIgnoreCase)) &&
                match.Groups[2].Value.Trim().Equals(key, titleGlobal ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase))
                found = Value.Match(match.Groups[4].Value).Groups[1].Value.Trim();
        }
        return found; // Native/config parsers consume successive assignments.
    }

    public void Set(string section, string key, string value, bool titleGlobal = false)
    {
        string current = "";
        var changed = false;
        var lastSectionEnd = -1;
        var inTarget = false;
        for (var i = 0; i < lines.Count; i++)
        {
            var header = Section.Match(lines[i].Text);
            if (header.Success)
            {
                if (inTarget) lastSectionEnd = i;
                current = header.Groups[1].Value.Trim();
                inTarget = current.Equals(section, StringComparison.OrdinalIgnoreCase);
                if (inTarget) lastSectionEnd = lines.Count;
                continue;
            }
            var match = Key.Match(lines[i].Text);
            if (!match.Success || (!titleGlobal && !inTarget) ||
                !match.Groups[2].Value.Trim().Equals(key, titleGlobal ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase)) continue;
            var raw = match.Groups[4].Value;
            var split = Value.Match(raw);
            var token = split.Groups[1].Value;
            var lead = token[..(token.Length - token.TrimStart().Length)];
            var tail = token[token.TrimEnd().Length..];
            lines[i] = lines[i] with { Text = match.Groups[1].Value + match.Groups[2].Value + match.Groups[3].Value +
                lead + value + tail + split.Groups[2].Value };
            changed = true; // Update every known duplicate; never leave conflicting first/last values.
        }
        if (changed) return;
        var newline = lines.Select(l => l.Ending).FirstOrDefault(e => e.Length != 0) ?? "\r\n";
        if (lastSectionEnd >= 0)
        {
            if (lastSectionEnd == lines.Count && lines.Count > 0 && lines[^1].Ending.Length == 0)
                lines[^1] = lines[^1] with { Ending = newline };
            lines.Insert(lastSectionEnd, new Line(key + "=" + value, newline));
        }
        else
        {
            if (lines.Count > 0 && lines[^1].Ending.Length == 0) lines[^1] = lines[^1] with { Ending = newline };
            lines.Add(new Line("[" + section + "]", newline));
            lines.Add(new Line(key + "=" + value, newline));
        }
    }

    public byte[] ToBytes() => prefix.Concat(encoding.GetBytes(string.Concat(lines.Select(l => l.Text + l.Ending)))).ToArray();
}
