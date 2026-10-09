using System.Diagnostics;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

public sealed partial class MainForm : Form
{
    readonly string root;
    string profile;
    ProfileSnapshot? snapshot;
    GameSettings edited=new();
    bool loading=true,dirty,busy,helperRunning;
    Process? launcher;
    readonly Dictionary<string,Panel> pages=[];
    readonly Dictionary<string,CompanionButton> navigation=[];
    readonly List<Control> settingControls=[];
    readonly List<Action<GameSettings>> populate=[];
    readonly Panel content=new(){Dock=DockStyle.Fill,Padding=new Padding(32,24,32,0),BackColor=Theme.Canvas};
    readonly Label statusTitle=Theme.Text("Loading profile",11,Theme.Accent,FontStyle.Bold);
    readonly Label status=Theme.Text("",10,Theme.Muted);
    readonly Label readiness=Theme.Text("",10,Theme.Muted);
    readonly Label saveHint=Theme.Text("",10,Theme.Muted);
    readonly Label saveList=Theme.Text("",11,Theme.Muted);
    readonly Label profileFolder=Theme.Text("",10,Theme.Muted);
    readonly Label qolCapability=Theme.Text("",10,Theme.Muted);
    readonly ComboBox checkpoints=Theme.Combo(480);
    readonly CompanionButton apply=Theme.Button("Apply settings",true,164);
    readonly CompanionButton play=Theme.Button("Start at title",true,200);
    readonly CompanionButton resume=Theme.Button("Resume selected copy",false,220);
    readonly CompanionButton original=Theme.Button("Start in Original View",false,220);
    readonly CompanionButton wide=Theme.Button("Likado widescreen preview",false,230);
    readonly CompanionButton hd=Theme.Button("Menu-frame preview",false,210);
    readonly CompanionButton refresh=Theme.Button("Refresh checkpoints",false,195);
    readonly PageColumn launchReport=new(){Visible=false};
    readonly TextBox launchDetails=new(){Multiline=true,ReadOnly=true,ScrollBars=ScrollBars.Vertical,Height=145,Dock=DockStyle.Top,BackColor=Theme.Rail,ForeColor=Theme.Muted,BorderStyle=BorderStyle.FixedSingle,Font=Theme.Body(9),AccessibleName="Launch diagnostics"};
    readonly System.Windows.Forms.Timer timer=new(){Interval=1000};

    public MainForm(string root,string? profile=null)
    {
        this.root=Path.GetFullPath(root);this.profile=Path.GetFullPath(profile??PublicSetupService.GetSelectedProfile(this.root)??Path.Combine(this.root,"local","player-foundation"));
        Text="Secret of the Stars Companion";ClientSize=new Size(1120,760);MinimumSize=new Size(950,650);
        StartPosition=FormStartPosition.CenterScreen;BackColor=Theme.Canvas;ForeColor=Theme.Ink;Font=Theme.Body();AutoScaleMode=AutoScaleMode.Dpi;
        BuildShell();BuildPlay();BuildSetup();BuildDisplay();BuildAudio();BuildControls();BuildHotkeys();BuildEnhancements();BuildSaves();
        apply.Click+=(_,_)=>ApplySettings();play.Click+=(_,_)=>Launch(LaunchMode.Play);original.Click+=(_,_)=>Launch(LaunchMode.OriginalView);
        resume.Click+=(_,_)=>Launch(LaunchMode.Resume);wide.Click+=(_,_)=>Launch(LaunchMode.WidescreenPreview);hd.Click+=(_,_)=>Launch(LaunchMode.HdMenuPreview);
        refresh.Click+=(_,_)=>ReloadProfile();checkpoints.SelectedIndexChanged+=(_,_)=>{UpdateSaveHint();UpdateEnabled();};
        timer.Tick+=(_,_)=>UpdateEnabled();FormClosed+=(_,_)=>{timer.Stop();timer.Dispose();launcher?.Dispose();};
        ReloadProfile();ShowPage(PublicSetupService.GetSelectionProblem(this.root)!=null?"setup":"play");timer.Start();
    }

    void BuildShell()
    {
        var rail=new Panel{Dock=DockStyle.Left,Width=210,BackColor=Theme.Rail,Padding=new Padding(18,24,18,18)};
        var brand=new Label{Text="Secret of\nthe Stars",Font=Theme.Title(23),ForeColor=Theme.Accent,AutoSize=false,Size=new Size(174,80),Location=new Point(18,25),UseMnemonic=false};
        rail.Controls.Add(brand);rail.Controls.Add(new Label{Text="Companion",Font=Theme.Body(10),ForeColor=Theme.Muted,AutoSize=true,Location=new Point(20,112)});
        int y=157;
        foreach(var (id,label) in new[]{("play","Play"),("setup","Setup"),("display","Display"),("audio","Audio"),("controls","Controls"),("hotkeys","Hotkeys"),("enhancements","Enhancements"),("saves","Saves")})
        {
            var button=Theme.Button(label,false,174);button.Navigation=true;button.Location=new Point(18,y);button.Size=new Size(174,46);button.Click+=(_,_)=>ShowPage(id);rail.Controls.Add(button);navigation[id]=button;y+=52;
        }
        var railFoot=new Label{Text="Windows PC\nOriginal adventure",Font=Theme.Body(10),ForeColor=Theme.Muted,AutoSize=false,Height=54,Dock=DockStyle.Bottom};rail.Controls.Add(railFoot);
        var body=new Panel{Dock=DockStyle.Fill,BackColor=Theme.Canvas};
        var footer=new Panel{Dock=DockStyle.Bottom,Height=88,BackColor=Theme.Rail,Padding=new Padding(32,15,32,12)};
        apply.Dock=DockStyle.Right;apply.Margin=Padding.Empty;
        var notes=new Panel{Dock=DockStyle.Fill,Padding=new Padding(0,0,20,0)};statusTitle.Dock=DockStyle.Top;statusTitle.Height=23;statusTitle.AutoSize=false;status.Dock=DockStyle.Fill;status.AutoSize=false;notes.Controls.Add(status);notes.Controls.Add(statusTitle);
        footer.Controls.Add(notes);footer.Controls.Add(apply);body.Controls.Add(content);body.Controls.Add(footer);Controls.Add(body);Controls.Add(rail);
    }

    PageColumn Page(string id,string title,string introduction)
    {
        var view=new Panel{Dock=DockStyle.Fill,AutoScroll=true,BackColor=Theme.Canvas,Visible=false};
        var column=new PageColumn();view.Controls.Add(column);content.Controls.Add(view);pages[id]=view;
        var heading=Theme.Text(title,25,Theme.Ink);heading.Font=Theme.Title(25);column.Add(heading,8);column.Add(Theme.Text(introduction,11,Theme.Muted),22);return column;
    }

    static void Section(PageColumn page,string title,string? description=null)
    {
        page.Add(Theme.Rule(),18);page.Add(Theme.Text(title,14,Theme.Ink,FontStyle.Bold),6);
        if(description!=null)page.Add(Theme.Text(description,10,Theme.Muted),12);
    }

    void BuildPlay()
    {
        var page=Page("play","Secret of the Stars","Your original adventure, with PC controls and presentation settings.");
        var imagePath=Path.Combine(root,"local","evidence","companion-play-scene.png");
        if(File.Exists(imagePath))
        {
            try
            {
                using var source=Image.FromFile(imagePath);
                var picture=new SceneStrip(new Bitmap(source)){Height=140,BackColor=Theme.Rail,AccessibleName="Secret of the Stars gameplay scene"};
                page.Add(picture,18);
            }
            catch(Exception ex){page.Add(Theme.Text("The local gameplay preview could not be loaded: "+ex.Message,10,Theme.Muted),10);}
        }
        page.Add(Theme.Row(play,original),9);page.Add(readiness,16);
        Section(page,"Continue from a checkpoint");
        page.Add(Theme.Row(checkpoints,resume),6);page.Add(saveHint,16);
        Section(page,"Try a focused preview","Each preview opens a separate profile with a prepared gameplay copy.");
        page.Add(Theme.Row(wide,hd),8);
        page.Add(Theme.Text("Try widescreen in a separate Likado fixture. Menu frames: eight finer border tiles.",10,Theme.Muted),8);
        launchReport.Add(Theme.Text("Launch details",11,Theme.Ink,FontStyle.Bold),6);launchReport.Add(launchDetails,0);page.Add(launchReport,8);
    }

    void BuildDisplay()
    {
        var page=Page("display","Display","Choose how the original pixel art appears on your screen.");
        AddCheck(page,"Start in fullscreen",s=>s.Fullscreen,(s,v)=>s.Fullscreen=v);
        AddCheck(page,"Synchronize presentation with the display",s=>s.VSync,(s,v)=>s.VSync=v);
        AddNumber(page,"Window scale","Original-pixel multiples for windowed play.",1,8,1,s=>s.WindowScale,(s,v)=>s.WindowScale=v);
        var renderer=Theme.Combo(280);renderer.Items.AddRange(["Direct3D 11","OpenGL","Software"]);renderer.AccessibleName="Graphics renderer";
        populate.Add(s=>renderer.SelectedIndex=s.Renderer.ToLowerInvariant() switch{"opengl"=>1,"software"=>2,_=>0});
        renderer.SelectedIndexChanged+=(_,_)=>{if(loading||renderer.SelectedIndex<0)return;edited.Renderer=renderer.SelectedIndex switch{1=>"opengl",2=>"software",_=>"direct3d11"};MarkDirty();};settingControls.Add(renderer);
        page.Add(Theme.Text("Graphics renderer",11,Theme.Ink,FontStyle.Bold),6);page.Add(renderer,20);
        Section(page,"Enhanced pixel art");
        AddCheck(page,"Enhance pixel edges",s=>s.EnhancedPixels,(s,v)=>s.EnhancedPixels=v);
        page.Add(Theme.Text("Keeps the original artwork and palette. This is edge enhancement, with original pixels available when turned off.",10,Theme.Muted),16);
        Section(page,"Widescreen");
        AddCheck(page,"Widescreen (experimental)",s=>s.ExperimentalFieldWide&&s.ExperimentalFieldActors,
            (s,v)=>{s.ExperimentalFieldWide=v;s.ExperimentalFieldActors=v;});
        page.Add(Theme.Text("Expands supported field maps, title scenery and battle backgrounds. Original controls and menus stay centered. Some scenes retain side bars while coverage grows. Original View restores the original viewport.",11,Theme.Muted),12);
        var preview=Theme.Button("Open Likado preview",false,225);preview.Click+=(_,_)=>Launch(LaunchMode.WidescreenPreview);page.Add(preview,0);launchButtons.Add(preview);
    }

    void BuildAudio()
    {
        var page=Page("audio","Audio","Set the original game's sound for your next launch.");
        AddCheck(page,"Enable game audio",s=>s.EnableAudio,(s,v)=>s.EnableAudio=v);
        AddNumber(page,"Volume","Game sound level, from 0 to 100 percent.",0,100,5,s=>s.Volume,(s,v)=>s.Volume=v);
        Section(page,"Soundtrack");
        page.Add(Theme.Text("The original soundtrack is available. An optional MSU-1 soundtrack still needs a compatible Secret of the Stars driver and pack.",11,Theme.Muted),10);
    }

    void BuildControls()
    {
        var page=Page("controls","Controls","Controller play is supported. Keep your existing bindings while tuning input.");
        AddCheck(page,"Enable player 1 controller",s=>s.EnableGamepad,(s,v)=>s.EnableGamepad=v);
        AddNumber(page,"Analog stick deadzone (%)","Increase if a stick drifts. Lower values respond to smaller movements.",0,100,1,s=>(int)Math.Round(s.Deadzone*100.0/32767),(s,v)=>s.Deadzone=(int)Math.Round(v*32767.0/100));
        BuildGameplayBindings(page);
        Section(page,"Game hotkeys");
        var bindings=Theme.Button("Configure hotkeys",false,230);bindings.Click+=(_,_)=>ShowPage("hotkeys");page.Add(bindings,12);
        page.Add(Theme.Text("Assign fast-forward, movement boost, fullscreen, journal and checkpoint shortcuts on Hotkeys. Escape always closes the rewind menu.",10,Theme.Muted),0);
    }

    void BuildEnhancements()
    {
        var page=Page("enhancements","Enhancements","Optional improvements, with the original presentation available on Play.");
        page.Add(qolCapability,10);
        Section(page,"Rewards and movement");
        AddNumber(page,"Experience rate (%)","100% is the original reward; 200% gives twice the experience earned in battle.",100,1000,25,s=>s.XpMultiplierPercent,(s,v)=>s.XpMultiplierPercent=v);
        AddNumber(page,"Gold rate (%)","Changes earned battle gold. Purchases, sales and existing savings keep their original amounts.",100,1000,25,s=>s.GoldMultiplierPercent,(s,v)=>s.GoldMultiplierPercent=v);
        AddNumber(page,"Movement boost (%)","Hold your assigned movement button for faster field travel. 200% is twice the normal movement rate.",100,300,25,s=>s.MovementSpeedPercent,(s,v)=>s.MovementSpeedPercent=v);
        AddFeature(page,"Faster field menus","Shortens checked menu slides and rows while keeping gameplay timing intact.",s=>s.FastMenus,(s,v)=>s.FastMenus=v);
        AddFeature(page,"Battle information","Shows native enemy HP information. Hide it with H or the right stick.",s=>s.BattleInfo,(s,v)=>s.BattleInfo=v);
        AddFeature(page,"Quest journal","Open with J or the left stick. Tracks David's first lead, using your current saved story progress.",s=>s.Journal,(s,v)=>s.Journal=v);
        AddFeature(page,"Remove scanline sprite limits","Allows more sprites per scanline. The game's original actor allocation is unchanged.",s=>s.NoSpriteLimits,(s,v)=>s.NoSpriteLimits=v);
        Section(page,"Menu-frame artwork");
        AddCheck(page,"Finer menu frames (preview)",s=>s.HdMenuFrames,(s,v)=>s.HdMenuFrames=v);
        page.Add(Theme.Text("Replaces eight menu-border tiles. World art and text keep their current appearance; full replacement-art packs are deferred.",10,Theme.Muted),0);
    }

    void BuildSaves()
    {
        var page=Page("saves","Saves","Checkpoint sources remain in your profile. Resume launches a prepared copy.");
        page.Add(Theme.Text("Available checkpoints",14,Theme.Ink,FontStyle.Bold),12);page.Add(saveList,18);page.Add(refresh,22);
        Section(page,"Start or resume");
        page.Add(Theme.Text("Start at title opens the game's normal title flow. Resume selected copy continues from the checkpoint you choose on Play. A pending restore conflict is reported instead of silently selecting a different checkpoint.",11,Theme.Muted),16);
        var go=Theme.Button("Choose checkpoint on Play",false,255);go.Click+=(_,_)=>ShowPage("play");page.Add(go,20);
        Section(page,"Profile folder");
        page.Add(profileFolder,8);
        page.Add(Theme.Text("No checkpoint deletion or save migration is performed here. Applying options backs up configuration files.",10,Theme.Muted),0);
    }

    readonly List<Control> launchButtons=[];
    void AddCheck(PageColumn page,string text,Func<GameSettings,bool> get,Action<GameSettings,bool> set)
    {
        var control=Theme.Check(text);settingControls.Add(control);populate.Add(s=>control.Checked=get(s));
        control.CheckedChanged+=(_,_)=>{if(loading)return;set(edited,control.Checked);MarkDirty();};page.Add(control,7);
    }
    void AddFeature(PageColumn page,string title,string description,Func<GameSettings,bool> get,Action<GameSettings,bool> set)
    {AddCheck(page,title,get,set);page.Add(Theme.Text(description,10,Theme.Muted),18);}
    void AddNumber(PageColumn page,string title,string description,int min,int max,int step,Func<GameSettings,int> get,Action<GameSettings,int> set)
    {
        page.Add(Theme.Text(title,11,Theme.Ink,FontStyle.Bold),5);page.Add(Theme.Text(description,10,Theme.Muted),7);
        var control=Theme.Number(min,max,step);control.AccessibleName=title;settingControls.Add(control);populate.Add(s=>control.Value=Math.Clamp(get(s),min,max));
        control.ValueChanged+=(_,_)=>{if(loading)return;set(edited,(int)control.Value);MarkDirty();};page.Add(control,20);
    }

    public void ShowPage(string page)
    {
        page=page.ToLowerInvariant();if(!pages.ContainsKey(page))throw new ArgumentException("Unknown Companion page: "+page,nameof(page));
        foreach(var item in pages)item.Value.Visible=item.Key==page;pages[page].BringToFront();
        foreach(var item in navigation){item.Value.Selected=item.Key==page;item.Value.Invalidate();}
    }

    void ReloadProfile()
    {
        if(busy)return;
        try
        {
            snapshot=ProfileService.Load(root,profile);edited=snapshot.Settings.DeepCopy();loading=true;
            profileFolder.Text=profile;
            foreach(var bind in populate)bind(edited);dirty=false;loading=false;
            string? prior=(checkpoints.SelectedItem as SaveChoice)?.Entry.Path;
            checkpoints.Items.Clear();foreach(var save in snapshot.Saves)checkpoints.Items.Add(new SaveChoice(save));
            if(checkpoints.Items.Count>0){int index=0;for(int i=0;i<checkpoints.Items.Count;i++)if(((SaveChoice)checkpoints.Items[i]!).Entry.Path==prior)index=i;checkpoints.SelectedIndex=index;}
            readiness.Text=snapshot.Readiness.Ready?"Starts at the title. Your checkpoints stay available below.":snapshot.Readiness.Message;
            saveList.Text=snapshot.Saves.Count==0?"No checkpoints found. Save your progress in the game to create one.":string.Join("\n\n",snapshot.Saves.Select(s=>$"{s.Label}    {s.LastWriteTimeUtc.ToLocalTime():g}"));
            UpdateSaveHint();SetStatus(snapshot.Readiness.Ready?"Ready to play":"Profile needs attention",snapshot.Readiness.Ready?"Your profile is ready. Settings apply to the next game launch.":snapshot.Readiness.Message,!snapshot.Readiness.Ready);
        }
        catch(Exception ex){snapshot=null;loading=false;readiness.Text=ex.Message;SetStatus("Profile could not be loaded",ex.Message,true);}
        UpdateEnabled();
    }

    void UpdateSaveHint()
    {
        saveHint.Text=checkpoints.SelectedItem is SaveChoice selected?$"{selected.Entry.Label} saved {selected.Entry.LastWriteTimeUtc.ToLocalTime():g}. The source stays unchanged.":"No checkpoint selected. Start at title to begin or continue through the game's own save menu.";
    }
    void MarkDirty(){dirty=true;SetStatus("Changes not applied","Apply settings before launching to use your new choices.");UpdateEnabled();}

    void ApplySettings()
    {
        if(snapshot==null)return;
        try
        {
            var result=ProfileService.Apply(snapshot,edited);
            if(!result.Success){SetStatus("Settings were not applied",result.Message,true);return;}
            snapshot=result.Snapshot??ProfileService.Load(root,profile);edited=snapshot.Settings.DeepCopy();loading=true;foreach(var bind in populate)bind(edited);loading=false;dirty=false;SetStatus("Settings applied",result.Message);
        }
        catch(Exception ex){loading=false;SetStatus("Settings were not applied",ex.Message,true);}
        UpdateEnabled();
    }

    void Launch(LaunchMode mode)
    {
        if(snapshot==null)return;
        try
        {
            if(dirty){SetStatus("Apply your settings first","Use Apply settings, then launch with the saved choices.");return;}
            string? path=mode==LaunchMode.Resume?(checkpoints.SelectedItem as SaveChoice)?.Entry.Path:null;
            if(mode==LaunchMode.Resume&&path==null){SetStatus("Choose a checkpoint","Select an available checkpoint on Play before resuming.");return;}
            var start=ProfileService.BuildLaunch(snapshot,new LaunchRequest(mode,path));
            start.UseShellExecute=false;start.RedirectStandardOutput=true;start.RedirectStandardError=true;start.CreateNoWindow=true;
            launcher?.Dispose();launcher=Process.Start(start)??throw new IOException("The launch helper did not start.");busy=true;helperRunning=true;launchReport.Visible=false;
            SetStatus(mode switch{LaunchMode.Resume=>"Opening checkpoint copy",LaunchMode.WidescreenPreview=>"Opening Likado widescreen preview",LaunchMode.HdMenuPreview=>"Opening menu-frame preview",_=>"Opening game"},"Settings are locked while the launch helper or game is running.");
            _=ObserveLaunch(launcher);
        }
        catch(Exception ex){busy=false;SetStatus("The game could not be launched",ex.Message,true);}
        UpdateEnabled();
    }

    async Task ObserveLaunch(Process process)
    {
        try
        {
            // Start both drains before waiting: a full stderr/stdout pipe must
            // never block the helper while the UI waits for it to finish.
            var output=process.StandardOutput.ReadToEndAsync();var errors=process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();string stdout=await output,stderr=await errors;
            if(IsDisposed||Disposing)return;
            helperRunning=false;busy=false;
            if(process.ExitCode!=0)
            {
                launchDetails.Text=$"Helper exit code: {process.ExitCode}\r\n\r\n"+stderr+"\r\n"+stdout;launchReport.Visible=true;ShowPage("play");
                string summary=(stderr+"\n"+stdout).Split(['\r','\n'],StringSplitOptions.RemoveEmptyEntries).FirstOrDefault()?.Trim()??"The helper returned no error details.";
                SetStatus("Launch failed",summary+" See Launch details on Play.",true);
            }
            else if(snapshot!=null&&ProfileService.IsGameRunning(snapshot))SetStatus("Game is running","Close the game before changing settings or opening another session.");
            else SetStatus("Session finished","The launch helper finished successfully. Settings can now be changed.");
            UpdateEnabled();
        }
        catch(Exception ex)
        {
            if(IsDisposed||Disposing)return;
            helperRunning=false;busy=false;launchDetails.Text=ex.ToString();launchReport.Visible=true;SetStatus("Launch status could not be read",ex.Message,true);UpdateEnabled();
        }
    }

    void UpdateEnabled()
    {
        bool running=false,gameActive=false;
        try{gameActive=snapshot!=null&&ProfileService.IsGameRunning(snapshot);running=gameActive||helperRunning;}catch(Exception ex){SetStatus("Game status could not be read",ex.Message,true);running=true;}
        if(busy&&!running){busy=false;SetStatus("Game closed","Settings can now be changed and applied.");}
        bool ready=snapshot?.Readiness.Ready==true;
        foreach(var control in settingControls)control.Enabled=snapshot!=null&&!running;
        bool supportsQol=snapshot!=null&&ProfileService.SupportsQol(snapshot);
        foreach(var control in settingControls)
            if(control.AccessibleName is "Experience rate (%)" or "Gold rate (%)" or "Movement boost (%)" or "Fast-forward is a toggle" or "Legacy controller menu gestures" or "Movement boost keyboard" or "Movement boost controller" or "Battle information keyboard" or "Battle information controller" or "Quest journal keyboard" or "Quest journal controller")
                control.Enabled=snapshot!=null&&!running&&supportsQol;
        qolCapability.Text=supportsQol?"":"Reward rates, movement boost and native hotkey changes require foundation 0.2.0 or newer. Build or select a new compilation on Setup.";
        apply.Enabled=snapshot!=null&&!running&&dirty;play.Enabled=original.Enabled=ready&&!running&&!dirty;
        wide.Enabled=hd.Enabled=ready&&!running&&!dirty&&snapshot!=null&&!PublicSetupService.IsSourceProfile(snapshot.ProfileDirectory);
        resume.Enabled=ready&&!running&&!dirty&&checkpoints.SelectedItem is SaveChoice;
        foreach(var button in launchButtons)button.Enabled=ready&&!running&&!dirty;
        checkpoints.Enabled=snapshot!=null&&!running;refresh.Enabled=snapshot!=null&&!running&&!dirty;
        SetSetupEnabled(!running&&!dirty&&!busy&&!helperRunning);
        if(gameActive){statusTitle.Text="Game is running";statusTitle.ForeColor=Theme.Accent;status.Text="Close the game before changing settings or opening another session.";}
    }

    void SetStatus(string title,string message,bool error=false){statusTitle.Text=title;statusTitle.ForeColor=error?Theme.Danger:Theme.Accent;status.Text=message;}
    sealed record SaveChoice(SaveEntry Entry){public override string ToString()=>$"{Entry.Label}  ({Entry.LastWriteTimeUtc.ToLocalTime():g})";}
}
