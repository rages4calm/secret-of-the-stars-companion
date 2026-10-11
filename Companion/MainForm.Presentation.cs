using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

public sealed partial class MainForm
{
    readonly List<Action<GameSettings>> presentationHints=[];
    void BuildDisplay()
    {
        var page=Page("display","Display","Choose original pixels, enhanced pixels or experimental widescreen. Apply before launching.");
        Section(page,"Presentation choices","These buttons change pixel enhancement and the two widescreen settings only. Your rewards, controls, sound and other options stay as chosen.");
        var originalPixels=Theme.Button("Original pixels",false,175);
        var enhancedPixels=Theme.Button("Enhanced pixels",false,180);
        var experimentalWide=Theme.Button("Experimental widescreen",false,260);
        originalPixels.Click+=(_,_)=>SetPresentation(false,false);
        enhancedPixels.Click+=(_,_)=>SetPresentation(true,false);
        experimentalWide.Click+=(_,_)=>SetPresentation(true,true);
        settingControls.AddRange([originalPixels,enhancedPixels,experimentalWide]);
        page.Add(Theme.Row(originalPixels,enhancedPixels,experimentalWide),9);
        var choice=Theme.Text("",11,Theme.Accent,FontStyle.Bold);choice.AccessibleName="Current presentation choice";
        Action<GameSettings> showChoice=s=>
        {
            originalPixels.Selected=!s.EnhancedPixels&&!s.ExperimentalFieldWide&&!s.ExperimentalFieldActors;
            enhancedPixels.Selected=s.EnhancedPixels&&!s.ExperimentalFieldWide&&!s.ExperimentalFieldActors;
            experimentalWide.Selected=s.EnhancedPixels&&s.ExperimentalFieldWide&&s.ExperimentalFieldActors;
            choice.Text=originalPixels.Selected?"Original pixels, original viewport":enhancedPixels.Selected?"Enhanced pixels, original viewport":experimentalWide.Selected?"Enhanced pixels with experimental widescreen":
                $"Custom: pixel enhancement {(s.EnhancedPixels?"on":"off")}, terrain margins {(s.ExperimentalFieldWide?"on":"off")}, additional actors {(s.ExperimentalFieldActors?"on":"off")}";
            originalPixels.Invalidate();enhancedPixels.Invalidate();experimentalWide.Invalidate();
        };
        populate.Add(showChoice);presentationHints.Add(showChoice);
        page.Add(choice,18);
        page.Add(Theme.Text("Original pixels preserves the original artwork at your chosen window size. Enhanced pixels smooths pixel edges. Widescreen expands supported scenes; unsupported scenes keep the centered original view and side bars.",10,Theme.Muted),16);
        Section(page,"Fullscreen and smooth presentation");
        AddCheck(page,"Start in fullscreen",s=>s.Fullscreen,(s,v)=>s.Fullscreen=v);
        AddShortcutHints(page,"Fullscreen");
        page.Add(Theme.Text("Default fullscreen shortcuts: F11, F12 or Alt+Enter. Assign a controller button or chord on Hotkeys. Your current shortcuts appear above.",10,Theme.Muted),12);
        var shortcuts=Theme.Button("Change fullscreen hotkeys",false,260);shortcuts.Click+=(_,_)=>ShowPage("hotkeys");page.Add(shortcuts,18);
        var window=Theme.Combo(310);window.AccessibleName="Windowed resolution";
        string[] sizes=["Auto","1280x720","1600x900","1920x1080","2560x1440","3840x2160"];
        populate.Add(s=>{window.Items.Clear();window.Items.AddRange(sizes);if(!window.Items.Contains(s.WindowSize))window.Items.Add(s.WindowSize);window.SelectedItem=s.WindowSize;});
        window.SelectedIndexChanged+=(_,_)=>{if(loading||window.SelectedItem is not string size)return;edited.WindowSize=size;MarkDirty();};settingControls.Add(window);
        page.Add(Theme.Text("Windowed resolution",11,Theme.Ink,FontStyle.Bold),6);page.Add(window,10);
        page.Add(Theme.Text("Choose an exact window size, or Auto to use Window scale below. Fullscreen uses your display. The picture keeps its selected pixel shape with bars where needed.",10,Theme.Muted),18);
        var aspect=Theme.Combo(310);aspect.AccessibleName="Pixel shape";
        string[] aspectValues=["4:3","8:7","1:1"];
        string[] aspectLabels=["Original CRT shape","Square pixels","Square frame"];
        populate.Add(s=>
        {
            aspect.Items.Clear();aspect.Items.AddRange(aspectLabels);
            int index=s.DisplayAspect.ToLowerInvariant() switch{"4:3" or "crt" or "0"=>0,"8:7" or "squarepixels" or "1"=>1,"1:1" or "squareframe" or "2"=>2,_=>-1};
            if(index<0){aspect.Items.Add("Existing: "+s.DisplayAspect);index=3;}aspect.SelectedIndex=index;
        });
        aspect.SelectedIndexChanged+=(_,_)=>{if(loading||aspect.SelectedIndex is < 0 or > 2)return;edited.DisplayAspect=aspectValues[aspect.SelectedIndex];MarkDirty();};settingControls.Add(aspect);
        page.Add(Theme.Text("Pixel shape",11,Theme.Ink,FontStyle.Bold),6);page.Add(aspect,10);
        page.Add(Theme.Text("Original CRT shape keeps the game's traditional proportions. Square pixels fits the wide canvas more closely to 16:9. Pixel shape and window size do not add scenery; use Widescreen for supported scenes.",10,Theme.Muted),18);
        AddNumber(page,"Window scale","Used when Windowed resolution is Auto.",1,8,1,s=>s.WindowScale,(s,v)=>s.WindowScale=v);
        AddCheck(page,"Synchronize presentation with the display",s=>s.VSync,(s,v)=>s.VSync=v);
        var renderer=Theme.Combo(280);renderer.Items.AddRange(["Direct3D 11","OpenGL","Software"]);renderer.AccessibleName="Graphics renderer";
        populate.Add(s=>renderer.SelectedIndex=s.Renderer.ToLowerInvariant() switch{"opengl"=>1,"software"=>2,_=>0});
        renderer.SelectedIndexChanged+=(_,_)=>{if(loading||renderer.SelectedIndex<0)return;edited.Renderer=renderer.SelectedIndex switch{1=>"opengl",2=>"software",_=>"direct3d11"};MarkDirty();};settingControls.Add(renderer);
        page.Add(Theme.Text("Graphics renderer",11,Theme.Ink,FontStyle.Bold),6);page.Add(renderer,10);
        var synchronized=Theme.Button("Use synchronized Direct3D 11",false,320);
        synchronized.Click+=(_,_)=>
        {
            if(!CanEditPresentation()||edited.Renderer=="direct3d11"&&edited.VSync)return;
            edited.Renderer="direct3d11";edited.VSync=true;PopulateEditedSettings();MarkDirty();
        };
        settingControls.Add(synchronized);page.Add(synchronized,8);
        page.Add(Theme.Text("Direct3D 11 with synchronization is the tested Windows default. This button changes only the renderer and synchronization; audio and other choices stay intact.",10,Theme.Muted),18);
        Section(page,"Individual options");
        AddCheck(page,"Enhance pixel edges",s=>s.EnhancedPixels,(s,v)=>s.EnhancedPixels=v);
        AddCheck(page,"Widescreen (experimental)",s=>s.ExperimentalFieldWide&&s.ExperimentalFieldActors,(s,v)=>{s.ExperimentalFieldWide=v;s.ExperimentalFieldActors=v;});
        page.Add(Theme.Text("Widescreen remains off unless you enable it. Terrain and actors expand together when chosen here. Some large or composite actors and later scenes remain unqualified. Original View on Play restores the original viewport for that launch.",10,Theme.Muted),12);
        var preview=Theme.Button("Open Likado preview",false,225);preview.Click+=(_,_)=>Launch(LaunchMode.WidescreenPreview);page.Add(preview,0);launchButtons.Add(preview);
    }

    bool CanEditPresentation()
    {
        if(snapshot==null||loading||busy||helperRunning||sourceBuildRunning)return false;
        try{return !ProfileService.IsGameRunning(snapshot);}
        catch(Exception error){SetStatus("Game status could not be read",error.Message,true);return false;}
    }

    void SetPresentation(bool enhanced,bool expanded)
    {
        if(!CanEditPresentation())return;
        if(edited.EnhancedPixels==enhanced&&edited.ExperimentalFieldWide==expanded&&edited.ExperimentalFieldActors==expanded)return;
        edited.EnhancedPixels=enhanced;edited.ExperimentalFieldWide=edited.ExperimentalFieldActors=expanded;
        PopulateEditedSettings();MarkDirty();
    }

    void AddShortcutHints(PageColumn page,params string[] actions)
    {
        var hint=Theme.Text("",10,Theme.Muted);hint.AccessibleName="Current shortcuts: "+string.Join(",",actions);
        Action<GameSettings> showHints=s=>hint.Text=string.Join("\n",actions.Select(id=>
        {
            var action=HotkeyCatalog.Actions.Single(a=>a.Id==id);
            var binding=s.HotkeyBindings.GetValueOrDefault(id)??new(action.Keyboard,action.Controller);
            string keyboard=HotkeyCatalog.IsUnbound(binding.Keyboard)?"unassigned":binding.Keyboard.Replace("Alt+Return","Alt+Enter").Replace(",",", ");
            string controller=HotkeyCatalog.IsUnbound(binding.Controller)?"unassigned":binding.Controller.Replace(",",", ");
            return $"{action.Label}: keyboard {keyboard}  |  controller {controller}";
        }));
        populate.Add(showHints);presentationHints.Add(showHints);
        page.Add(hint,14);
    }
}
