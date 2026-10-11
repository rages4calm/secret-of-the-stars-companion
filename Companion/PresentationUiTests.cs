using System.Reflection;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class PresentationUiTests
{
    public static void Run(MainForm form,string root,string profile,string report)
    {
        profile=PublicSetupService.RequireInside(profile,Path.Combine(root,"local"));
        if(!PublicSetupService.IsSourceProfile(profile)||!File.Exists(Path.Combine(profile,".ui-test-disposable")))
            throw new InvalidOperationException("Presentation GUI tests require an explicitly marked disposable source profile.");
        Directory.CreateDirectory(Path.GetDirectoryName(report)!);
        static IEnumerable<Control> Walk(Control parent)
        {
            foreach(Control child in parent.Controls){yield return child;foreach(var nested in Walk(child))yield return nested;}
        }
        T Find<T>(string name) where T:Control=>Walk(form).OfType<T>().Single(c=>c.AccessibleName==name||c.Text==name);
        void Method(string name,params object[] args)=>typeof(MainForm).GetMethod(name,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(form,args);
        void Field(string name,bool value)=>typeof(MainForm).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(form,value);
        GameSettings Edited()=>(GameSettings)typeof(MainForm).GetField("edited",BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(form)!;
        static string All(GameSettings settings)=>JsonSerializer.Serialize(settings);
        static string Unrelated(GameSettings settings)=>All(settings with {EnhancedPixels=false,ExperimentalFieldWide=false,ExperimentalFieldActors=false});
        static Dictionary<string,string> Files(string directory)=>Directory.EnumerateFiles(directory,"*",SearchOption.AllDirectories).ToDictionary(p=>p,PublicSetupService.HashFile);
        static bool SameFiles(Dictionary<string,string> expected)=>expected.All(p=>File.Exists(p.Key)&&PublicSetupService.HashFile(p.Key)==p.Value);
        var checks=new List<string>();
        void Check(string name,bool condition){if(!condition)throw new InvalidOperationException(name);checks.Add(name);}
        var saves=Files(Path.Combine(profile,"saves"));
        var apply=Find<Button>("Apply settings");var revert=Find<Button>("Revert changes");var play=Find<Button>("Start at title");
        var original=ProfileService.Load(root,profile);
        Check("Loading Display preserves the exact existing viewport choices",All(Edited())==All(original.Settings));
        form.ShowPage("play");Find<Button>("Display options").PerformClick();
        Check("Play exposes Display options without changing settings",!apply.Enabled&&Find<Button>("Original pixels").Visible);
        Find<Button>("Change fullscreen hotkeys").PerformClick();
        Check("Display exposes keyboard and controller fullscreen controls",Find<ComboBox>("Fullscreen controller").Visible);
        Find<ComboBox>("Fullscreen keyboard").Text="Ctrl+F12";Find<ComboBox>("Fullscreen controller").Text="Back+L1";
        Find<ComboBox>("Quest journal keyboard").Text="Ctrl+J";Find<ComboBox>("Quest journal controller").Text="Back+R1+L3";
        form.ShowPage("display");
        var displayBefore=Files(profile);var untouched=All(Edited() with {WindowSize="Auto",DisplayAspect="4:3"});
        Find<ComboBox>("Windowed resolution").SelectedItem="1920x1080";Find<ComboBox>("Pixel shape").SelectedIndex=1;
        Check("Resolution and pixel shape edit only their own pending fields",Edited().WindowSize=="1920x1080"&&Edited().DisplayAspect=="8:7"&&All(Edited() with {WindowSize="Auto",DisplayAspect="4:3"})==untouched&&SameFiles(displayBefore));
        revert.PerformClick();Check("Resolution and pixel shape Revert is lossless",All(Edited())==All(original.Settings with {HotkeyBindings=Edited().HotkeyBindings})&&SameFiles(displayBefore));
        Find<ComboBox>("Fullscreen keyboard").Text="Ctrl+F12";Find<ComboBox>("Fullscreen controller").Text="Back+L1";
        Find<ComboBox>("Quest journal keyboard").Text="Ctrl+J";Find<ComboBox>("Quest journal controller").Text="Back+R1+L3";
        Find<ComboBox>("Windowed resolution").SelectedItem="1920x1080";Find<ComboBox>("Pixel shape").SelectedIndex=1;
        Find<ComboBox>("Graphics renderer").SelectedIndex=1;
        Find<CheckBox>("Synchronize presentation with the display").Checked=false;
        Find<Button>("Enhanced pixels").PerformClick();
        form.ShowPage("audio");Find<CheckBox>("Enable game audio").Checked=false;Find<NumericUpDown>("Volume").Value=55;
        form.ShowPage("enhancements");Find<CheckBox>("Finer menu frames (preview)").Checked=true;
        if(ProfileService.SupportsQol(original))Find<NumericUpDown>("Experience rate (%)").Value=375;
        apply.PerformClick();var custom=ProfileService.Load(root,profile).Settings;
        Check("Custom sound renderer reward frame art and shortcuts are saved",!apply.Enabled&&custom.Renderer=="opengl"&&!custom.VSync&&!custom.EnableAudio&&custom.Volume==55&&custom.HdMenuFrames&&custom.HotkeyBindings["Fullscreen"]==new HotkeyBinding("Ctrl+F12","Back+L1"));
        Check("Applied resolution and pixel shape reload exactly",custom.WindowSize=="1920x1080"&&custom.DisplayAspect=="8:7");
        form.ShowPage("display");
        Check("Fullscreen hints show current custom keyboard and controller bindings",Find<Label>("Current shortcuts: Fullscreen").Text.Contains("Ctrl+F12")&&Find<Label>("Current shortcuts: Fullscreen").Text.Contains("Back+L1"));
        foreach(var (name,enhanced,expanded) in new[]{("Original pixels",false,false),("Enhanced pixels",true,false),("Experimental widescreen",true,true)})
        {
            var before=Files(profile);Find<Button>(name).PerformClick();var pending=Edited();
            Check(name+" changes only its three explicit in-memory fields",pending.EnhancedPixels==enhanced&&pending.ExperimentalFieldWide==expanded&&pending.ExperimentalFieldActors==expanded&&Unrelated(pending)==Unrelated(custom));
            Check(name+" waits for Apply and leaves disk untouched",apply.Enabled&&revert.Enabled&&!play.Enabled&&SameFiles(before));
            apply.PerformClick();var saved=ProfileService.Load(root,profile).Settings;
            Check(name+" applies with custom maps sound rewards and other settings preserved",!apply.Enabled&&play.Enabled&&saved.EnhancedPixels==enhanced&&saved.ExperimentalFieldWide==expanded&&saved.ExperimentalFieldActors==expanded&&Unrelated(saved)==Unrelated(custom));
            before=Files(profile);Find<Button>(name).PerformClick();
            Check(name+" selected again is a no-op with no dirty state or writes",!apply.Enabled&&!revert.Enabled&&SameFiles(before));
        }
        var loaded=ProfileService.Load(root,profile).Settings;var preRevert=Files(profile);
        Find<Button>("Original pixels").PerformClick();form.ShowPage("audio");Find<NumericUpDown>("Volume").Value=35;
        form.ShowPage("hotkeys");Find<ComboBox>("Quest journal keyboard").Text="Ctrl+K";
        revert.PerformClick();
        Check("Revert restores preset sound and hotkey edits without touching any files",All(Edited())==All(loaded)&&!apply.Enabled&&!revert.Enabled&&play.Enabled&&SameFiles(preRevert));
        form.ShowPage("display");Find<Button>("Use synchronized Direct3D 11").PerformClick();
        var synchronized=Edited();
        Check("Explicit synchronized renderer action changes only Renderer and VSync",All(synchronized with {Renderer=loaded.Renderer,VSync=loaded.VSync})==All(loaded)&&synchronized.Renderer=="direct3d11"&&synchronized.VSync);
        revert.PerformClick();Check("Synchronized renderer action can be reverted before writes",All(Edited())==All(loaded)&&SameFiles(preRevert));
        var disk=ProfileService.Load(root,profile);var mixed=ProfileService.Apply(disk,disk.Settings with {ExperimentalFieldWide=true,ExperimentalFieldActors=false});
        Check("Existing mixed terrain and actor choices can be loaded",mixed.Success);Method("ReloadProfile");form.ShowPage("display");
        Check("Mixed viewport choices show Custom without enabling actors",Edited().ExperimentalFieldWide&&!Edited().ExperimentalFieldActors&&Find<Label>("Current presentation choice").Text.StartsWith("Custom:")&&!apply.Enabled);
        Find<CheckBox>("Enhance pixel edges").Checked=false;
        Check("Individual option updates the Custom summary immediately",Find<Label>("Current presentation choice").Text.Contains("pixel enhancement off")&&Edited().ExperimentalFieldWide&&!Edited().ExperimentalFieldActors);
        revert.PerformClick();
        Field("sourceBuildRunning",true);Field("helperRunning",true);Field("busy",true);Method("UpdateEnabled");
        Check("Source build locks all presentation preset and synchronization controls",!Find<Button>("Original pixels").Enabled&&!Find<Button>("Enhanced pixels").Enabled&&!Find<Button>("Experimental widescreen").Enabled&&!Find<Button>("Use synchronized Direct3D 11").Enabled&&!revert.Enabled);
        var busyBefore=All(Edited());Method("SetPresentation",false,false);
        Check("Direct preset action refuses a busy source build without mutating edited choices",All(Edited())==busyBefore);
        Field("sourceBuildRunning",false);Field("helperRunning",false);Field("busy",false);Method("UpdateEnabled");
        Check("Build completion unlocks presentation controls",Find<Button>("Original pixels").Enabled&&play.Enabled);
        // Existing custom renderer values must survive unrelated actions, even
        // though the renderer picker exposes only the three supported choices.
        var configPath=Path.Combine(profile,"config.ini");var config=new IniDocument(File.ReadAllBytes(configPath));
        config.Set("Graphics","Renderer","owner-custom-renderer");
        config.Set("Graphics","WindowSize","1376x768");config.Set("Graphics","DisplayAspect","CRT");
        File.WriteAllBytes(configPath,config.ToBytes());Method("ReloadProfile");form.ShowPage("display");
        Check("Custom window size and original CRT alias load without normalization",Edited().WindowSize=="1376x768"&&Edited().DisplayAspect=="CRT"&&Find<ComboBox>("Windowed resolution").SelectedItem?.ToString()=="1376x768"&&Find<ComboBox>("Pixel shape").SelectedIndex==0&&!apply.Enabled);
        Find<Button>("Original pixels").PerformClick();apply.PerformClick();
        Check("A presentation preset preserves an existing unknown custom renderer",ProfileService.Load(root,profile).Settings.Renderer=="owner-custom-renderer"&&!apply.Enabled);
        Check("An unrelated preset preserves custom size and explicit CRT alias bytes",new IniDocument(File.ReadAllBytes(configPath)).Get("Graphics","WindowSize")=="1376x768"&&new IniDocument(File.ReadAllBytes(configPath)).Get("Graphics","DisplayAspect")=="CRT");
        Find<Button>("Use synchronized Direct3D 11").PerformClick();apply.PerformClick();
        Check("Explicit synchronized action replaces custom renderer only on user action",ProfileService.Load(root,profile).Settings.Renderer=="direct3d11"&&ProfileService.Load(root,profile).Settings.VSync&&!apply.Enabled);
        var protectedBindings=PublicSetupService.HashFile(Path.Combine(profile,"keybinds.ini"));
        Find<Button>("Experimental widescreen").PerformClick();File.AppendAllText(configPath,"\n; concurrent owner choice retained by stale Apply control\n");
        var concurrent=PublicSetupService.HashFile(configPath);apply.PerformClick();
        Check("Stale profile refuses preset Apply and preserves concurrent config bindings and saves",apply.Enabled&&!play.Enabled&&PublicSetupService.HashFile(configPath)==concurrent&&PublicSetupService.HashFile(Path.Combine(profile,"keybinds.ini"))==protectedBindings&&SameFiles(saves));
        revert.PerformClick();Check("Revert after stale refusal never overwrites the concurrent edit",PublicSetupService.HashFile(configPath)==concurrent&&!apply.Enabled);
        Method("ReloadProfile");
        Check("Journal description names verified current opening leads and bounded later coverage",Walk(form).OfType<Label>().Any(l=>l.Text.Contains("David, Aris, Pennon and Bosen")&&l.Text.Contains("later chapters remain uncovered")));
        foreach(var (label,value,expected) in new[]{("missing","",true),("explicit-off","JournalPossession=0\n",false),("explicit-on","JournalPossession=1\n",true)})
        {
            var summaryProfile=Path.Combine(root,"local","runs","presentation-summary-"+label+"-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(summaryProfile);Directory.CreateDirectory(Path.Combine(summaryProfile,"saves"));
            foreach(var name in new[]{"config.ini","keybinds.ini",PublicSetupService.ManifestName,PublicSetupService.GameName+".exe"})File.Copy(Path.Combine(profile,name),Path.Combine(summaryProfile,name));
            var summaryIni=Path.Combine(summaryProfile,"foundation.ini");File.WriteAllText(summaryIni,"[Enhancements]\nJournal=1\n"+value+"Unrelated = keep ; exact comment\n");
            var summaryConfig=PublicSetupService.HashFile(Path.Combine(summaryProfile,"config.ini"));var summaryBindings=PublicSetupService.HashFile(Path.Combine(summaryProfile,"keybinds.ini"));
            using var summaryForm=new MainForm(root,summaryProfile){StartPosition=FormStartPosition.Manual,Location=new Point(-30000,-30000),ShowInTaskbar=false};summaryForm.Show();summaryForm.ShowPage("enhancements");
            T InSummary<T>(string name) where T:Control=>Walk(summaryForm).OfType<T>().Single(c=>c.AccessibleName==name||c.Text==name);
            var possession=InSummary<CheckBox>("Journal item summary");var savedBytes=File.ReadAllBytes(summaryIni);
            Check("Journal item summary "+label+" loads without manufacturing settings",possession.Checked==expected&&ProfileService.Load(root,summaryProfile).Settings.JournalPossession==expected&&savedBytes.SequenceEqual(File.ReadAllBytes(summaryIni)));
            possession.Checked=!expected;InSummary<Button>("Revert changes").PerformClick();
            Check("Journal item summary "+label+" reverts without writes",possession.Checked==expected&&savedBytes.SequenceEqual(File.ReadAllBytes(summaryIni)));
            possession.Checked=!expected;InSummary<Button>("Apply settings").PerformClick();
            Check("Journal item summary "+label+" changes only its explicit key",ProfileService.Load(root,summaryProfile).Settings.JournalPossession==!expected&&File.ReadAllText(summaryIni).Contains("Unrelated = keep ; exact comment\n")&&PublicSetupService.HashFile(Path.Combine(summaryProfile,"config.ini"))==summaryConfig&&PublicSetupService.HashFile(Path.Combine(summaryProfile,"keybinds.ini"))==summaryBindings);
            possession.Checked=expected;InSummary<Button>("Apply settings").PerformClick();
            Check("Journal item summary "+label+" restores the intended current choice",ProfileService.Load(root,summaryProfile).Settings.JournalPossession==expected&&!InSummary<Button>("Apply settings").Enabled);
            summaryForm.Close();
        }
        var captures=Path.Combine(Path.GetDirectoryName(report)!,"presentation-captures");Directory.CreateDirectory(captures);
        foreach(var (factor,size,label) in new[]{(1f,new Size(1120,760),"normal"),(1f,new Size(950,650),"minimum"),(1.25f,new Size(1188,813),"125-percent-layout"),(1.5f,new Size(1425,975),"150-percent-layout")})
        {
            using var scaled=new MainForm(root,profile){StartPosition=FormStartPosition.Manual,Location=new Point(-30000,-30000),ShowInTaskbar=false};
            scaled.Show();if(factor!=1)scaled.Scale(new SizeF(factor,factor));scaled.ClientSize=size;
            foreach(var page in new[]{"play","display","audio","controls","hotkeys","enhancements"})
            {
                scaled.ShowPage(page);scaled.PerformLayout();scaled.Refresh();
                var view=Walk(scaled).OfType<Panel>().Single(p=>p.Visible&&p.AutoScroll);
                var outside=Walk(view).Where(c=>c is ComboBox or TextBox or NumericUpDown or Button).Where(c=>view.PointToClient(c.Parent!.PointToScreen(c.Location)).X+c.Width>view.ClientSize.Width).Select(c=>c.AccessibleName??c.Name).ToArray();
                Check($"{page} {label} has reachable controls and no horizontal clipping",!view.HorizontalScroll.Visible&&outside.Length==0);
                using var image=new Bitmap(scaled.Width,scaled.Height);scaled.DrawToBitmap(image,new Rectangle(Point.Empty,image.Size));image.Save(Path.Combine(captures,$"{page}-{label}.png"));
                if(page=="display")
                {
                    view.AutoScrollPosition=new Point(0,650);scaled.PerformLayout();scaled.Refresh();
                    using var displayImage=new Bitmap(scaled.Width,scaled.Height);scaled.DrawToBitmap(displayImage,new Rectangle(Point.Empty,displayImage.Size));displayImage.Save(Path.Combine(captures,$"display-size-controls-{label}.png"));
                }
            }
            var applyScaled=Walk(scaled).OfType<Button>().Single(c=>c.AccessibleName=="Apply settings");var revertScaled=Walk(scaled).OfType<Button>().Single(c=>c.AccessibleName=="Revert changes");
            Check($"Apply and Revert remain separate and visible at {label}",!applyScaled.Bounds.IntersectsWith(revertScaled.Bounds)&&applyScaled.Right<=applyScaled.Parent!.ClientSize.Width&&revertScaled.Left>=0);
            scaled.Close();
        }
        Check("All copied checkpoint files remain byte-identical throughout preset and layout tests",SameFiles(saves));
        File.WriteAllText(report,JsonSerializer.Serialize(new {passed=true,checks=checks.Count,cases=checks,screenshots=captures,protected_saves=saves,gameplay_executed=false,
            layout_limits="125% and 150% are explicit WinForms layout scaling controls, not a new physical multi-monitor DPI certification."},new JsonSerializerOptions{WriteIndented=true}));
    }
}
