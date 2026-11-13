using System.Reflection;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;
namespace SecretOfTheStars.Companion;
public sealed partial class MainForm {
 sealed record AchievementDefinition(string Id,string Title,string Description,uint Target);
 static readonly AchievementDefinition[] AchievementCatalog=LoadAchievementCatalog();
 readonly Dictionary<string,Label> achievementStates=[];
 readonly Label achievementSummary=Theme.Text("Local progress",12,Theme.Accent,FontStyle.Bold);
 readonly Label achievementNote=Theme.Text("",10,Theme.Muted);
 string achievementRefreshKey="";
 static AchievementDefinition[] LoadAchievementCatalog(){
  using var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("SotsAchievementCatalog")??throw new InvalidDataException("Achievement catalog missing.");
  using var document=JsonDocument.Parse(stream);
  return document.RootElement.GetProperty("achievements").EnumerateArray().Select(x=>new AchievementDefinition(x.GetProperty("id").GetString()!,x.GetProperty("title").GetString()!,x.GetProperty("description").GetString()!,x.GetProperty("target").GetUInt32())).ToArray();
 }
 void BuildAchievements(){
  var page=Page("achievements","Achievements","Local milestones for your adventure. No account or internet connection required.");
  page.Add(Theme.Text("In game: Ctrl+J, or hold Back and press Y on the controller. Use Up/Down to browse; B or Escape closes the list.",11,Theme.Muted),14);
  page.Add(achievementSummary,7);page.Add(achievementNote,12);
  var refresh=Theme.Button("Refresh local progress",false,215);refresh.Click+=(_,_)=>{achievementRefreshKey="";RefreshAchievements();};page.Add(refresh,18);
  foreach(var a in AchievementCatalog){
   page.Add(Theme.Rule(),12);page.Add(Theme.Text(a.Title,13,Theme.Ink,FontStyle.Bold),4);page.Add(Theme.Text(a.Description,10,Theme.Muted),5);
   var state=Theme.Text("Locked",10,Theme.Muted);achievementStates[a.Id]=state;page.Add(state,13);
  }
 }
 void RefreshAchievements(){
  var folder=snapshot?.ProfileDirectory??profile;
  var path=Path.Combine(folder,"Achievements","secret-of-the-stars","native-qol","unseeded","progress.json");
  try {
   var info=new FileInfo(path);var key=folder+"|"+(info.Exists?info.LastWriteTimeUtc.Ticks+":"+info.Length:"missing");if(key==achievementRefreshKey)return;achievementRefreshKey=key;
   var values=new Dictionary<string,(uint progress,ulong when)>();
   if(info.Exists){
    if(info.Length>1024*1024)throw new InvalidDataException("Local achievement file is too large.");
    using var doc=JsonDocument.Parse(File.ReadAllBytes(path));var root=doc.RootElement;
    if(root.GetProperty("schemaVersion").GetInt32()!=1||root.GetProperty("gameId").GetString()!="secret-of-the-stars"||root.GetProperty("editionId").GetString()!="native-qol")throw new InvalidDataException("Local achievement file belongs to another catalog.");
    foreach(var item in root.GetProperty("achievements").EnumerateArray()){
     var id=item.GetProperty("id").GetString();if(id==null)continue;
     uint progress=item.TryGetProperty("progress",out var pp)&&pp.TryGetUInt32(out var pv)?pv:0;
     ulong when=item.TryGetProperty("unlockedAt",out var up)&&up.ValueKind==JsonValueKind.Number&&up.TryGetUInt64(out var uv)?uv:0;
     values[id]=(progress,when);
    }
   }
   int unlocked=0;
   foreach(var a in AchievementCatalog){var value=values.GetValueOrDefault(a.Id);var label=achievementStates[a.Id];if(value.when!=0){++unlocked;label.Text="Unlocked";label.ForeColor=Theme.Accent;}else{label.Text=a.Target>1?$"{Math.Min(value.progress,a.Target):N0} / {a.Target:N0}":"Locked";label.ForeColor=Theme.Muted;}}
   achievementSummary.Text=$"{unlocked} / {AchievementCatalog.Length} unlocked";
   achievementNote.Text="Progress is stored outside game saves. Loading an advanced save establishes a baseline; it does not award old milestones. Scripted test sessions do not earn achievements. Native 0.5.13 or newer records progress.";
  }catch(Exception ex)when(ex is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or KeyNotFoundException){achievementSummary.Text="Local progress unavailable";achievementNote.Text=ex.Message+" The game remains playable.";}
 }
}
