using System.Reflection;
using System.Text.Json;
using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

internal static class NavigationMapUiTests
{
    public static void Run(MainForm form,string root,string profile,string olderReceipt,string report)
    {
        profile=PublicSetupService.RequireInside(profile,Path.Combine(root,"local"));
        if(!PublicSetupService.IsSourceProfile(profile)||!File.Exists(Path.Combine(profile,".ui-test-disposable")))
            throw new InvalidOperationException("Map GUI checks require an explicitly marked disposable source profile.");
        olderReceipt=PublicSetupService.RequireInside(olderReceipt,Path.Combine(root,"local","source-builds"));
        var older=PublicSetupService.CheckBuild(root,olderReceipt);
        if(!Version.TryParse(older.Version,out var oldVersion)||oldVersion>=new Version(0,2,6))
            throw new InvalidOperationException("Older-build checks require a genuine source compilation preceding native0.2.6.");
        Directory.CreateDirectory(Path.GetDirectoryName(report)!);
        static IEnumerable<Control> Walk(Control parent){foreach(Control c in parent.Controls){yield return c;foreach(var n in Walk(c))yield return n;}}
        static T Find<T>(Form f,string name)where T:Control=>Walk(f).OfType<T>().Single(c=>c.AccessibleName==name||c.Text==name);
        static void Method(Form f,string name)=>typeof(MainForm).GetMethod(name,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(f,null);
        static void Field(Form f,string name,bool value)=>typeof(MainForm).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(f,value);
        static GameSettings Edited(Form f)=>(GameSettings)typeof(MainForm).GetField("edited",BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(f)!;
        static string All(GameSettings s)=>JsonSerializer.Serialize(s);
        static Dictionary<string,string> Files(string dir)=>Directory.EnumerateFiles(dir,"*",SearchOption.AllDirectories).ToDictionary(p=>p,PublicSetupService.HashFile);
        static bool Same(Dictionary<string,string> files)=>files.All(p=>File.Exists(p.Key)&&PublicSetupService.HashFile(p.Key)==p.Value);
        var cases=new List<string>();void Check(string name,bool ok){if(!ok)throw new InvalidOperationException(name);cases.Add(name);}
        var initial=ProfileService.Load(root,profile);var saves=Files(Path.Combine(profile,"saves"));
        Check("Actual source profile supports map edits",initial.Readiness.Ready&&ProfileService.SupportsNavigationMap(initial));
        var apply=Find<Button>(form,"Apply settings");var revert=Find<Button>(form,"Revert changes");
        form.ShowPage("enhancements");var map=Find<CheckBox>(form,"Current-area map");
        Check("Enhancements exposes the enabled optional current-area map",map.Enabled&&map.Checked==initial.Settings.NavigationMap);
        Check("Map help describes verified pins and nonpausing current-area scope",Walk(form).OfType<Label>().Any(c=>c.Text.Contains("while gameplay continues")&&c.Text.Contains("no visited-area history")&&c.Text.Contains("verified objective locations")&&c.Text.Contains("Unavailable destinations have no pin")));
        var objective=Find<CheckBox>(form,"Show current objective on map");
        Check("Objective choice loads without changing its value when the map is disabled",objective.Checked==initial.Settings.NavigationMapObjective&&objective.Enabled==initial.Settings.NavigationMap);
        var before=Files(profile);map.Checked=!map.Checked;
        Check("Disabling the map keeps the saved objective choice",objective.Checked==initial.Settings.NavigationMapObjective&&objective.Enabled==map.Checked);
        Check("Map toggle waits for Apply with disk bytes intact",apply.Enabled&&revert.Enabled&&Same(before));
        revert.PerformClick();Check("Map Revert restores its loaded value without writes",All(Edited(form))==All(initial.Settings)&&Same(before)&&!apply.Enabled);
        Find<Button>(form,"Change enhancement hotkeys").PerformClick();
        var keyboard=Find<ComboBox>(form,"Current-area map keyboard");var controller=Find<ComboBox>(form,"Current-area map controller");
        Check("Map keyboard and controller choices are visible and editable",keyboard.Visible&&controller.Visible&&keyboard.Enabled&&controller.Enabled);
        keyboard.Text="Ctrl+M";controller.Text="Back+Guide";
        Check("Custom map bindings remain in memory before Apply",apply.Enabled&&Same(before));
        form.ShowPage("enhancements");map.Checked=false;apply.PerformClick();var custom=ProfileService.Load(root,profile);
        Check("Map setting and custom bindings round-trip",!apply.Enabled&&!custom.Settings.NavigationMap&&custom.Settings.HotkeyBindings["Map"]==new HotkeyBinding("Ctrl+M","Back+Guide"));
        var unchanged=custom.Settings.DeepCopy();unchanged.NavigationMap=initial.Settings.NavigationMap;unchanged.HotkeyBindings["Map"]=initial.Settings.HotkeyBindings["Map"];
        Check("Map edits preserve every unrelated setting and custom binding",All(unchanged)==All(initial.Settings));
        Check("Map edits preserve legacy gesture selection and guest SELECT",custom.Settings.LegacyControllerGestures==initial.Settings.LegacyControllerGestures&&custom.Settings.HotkeyBindings["Controls"]==initial.Settings.HotkeyBindings["Controls"]);
        var originalView=ProfileService.BuildLaunch(custom,new(LaunchMode.OriginalView));
        Check("Source Original View explicitly disables the map",originalView.Environment.TryGetValue("SNESRECOMP_FOUNDATION_NAVIGATION_MAP",out var mapOverride)&&mapOverride=="0");
        Check("Source Original View explicitly disables objective pins",originalView.Environment.TryGetValue("SNESRECOMP_FOUNDATION_NAVIGATION_MAP_OBJECTIVE",out var objectiveOverride)&&objectiveOverride=="0");
        Check("Source Play preserves the saved map choice without an ambient override",!ProfileService.BuildLaunch(custom,new(LaunchMode.Play)).Environment.ContainsKey("SNESRECOMP_FOUNDATION_NAVIGATION_MAP"));
        form.ShowPage("hotkeys");keyboard.Text="J";before=Files(profile);apply.PerformClick();
        Check("Changed map keyboard collision refuses before any write",apply.Enabled&&Same(before));revert.PerformClick();
        controller.Text=HotkeyCatalog.GetSlot(initial.Settings.HotkeyBindings["Turbo"].Controller,0);before=Files(profile);apply.PerformClick();
        Check("Changed map controller collision refuses before any write",apply.Enabled&&Same(before));revert.PerformClick();
        controller.Text="Back";before=Files(profile);apply.PerformClick();
        Check("Changed map controller cannot take the existing guest SELECT button",apply.Enabled&&Same(before));revert.PerformClick();
        keyboard.Text="Ctrl+M\nInjected=1";before=Files(profile);apply.PerformClick();
        Check("Map binding injection refuses before any write",apply.Enabled&&Same(before));revert.PerformClick();
        keyboard.Text="None";controller.Text="None";apply.PerformClick();
        Check("Explicit unbound map choices win over defaults",!apply.Enabled&&ProfileService.Load(root,profile).Settings.HotkeyBindings["Map"]==new HotkeyBinding("None","None"));
        Field(form,"sourceBuildRunning",true);Field(form,"helperRunning",true);Field(form,"busy",true);Method(form,"UpdateEnabled");
        Check("Busy source build disables map and objective options and both hotkey controls",!map.Enabled&&!objective.Enabled&&!keyboard.Enabled&&!controller.Enabled);
        Field(form,"sourceBuildRunning",false);Field(form,"helperRunning",false);Field(form,"busy",false);Method(form,"UpdateEnabled");
        Check("Build completion restores map controls",map.Enabled&&keyboard.Enabled&&controller.Enabled);
        form.ShowPage("enhancements");map.Checked=true;var configPath=Path.Combine(profile,"config.ini");
        File.AppendAllText(configPath,"\n; concurrent map-test edit retained\n");var configHash=PublicSetupService.HashFile(configPath);apply.PerformClick();
        Check("Stale Apply refuses and preserves concurrent config",apply.Enabled&&PublicSetupService.HashFile(configPath)==configHash);revert.PerformClick();Method(form,"ReloadProfile");
        var source=ProfileService.Load(root,profile);var sourceManifest=PublicSetupService.ReadProfile(profile);
        foreach(var (label,line,expected) in new[]{("missing","",true),("explicit-off","NavigationMap=0\nNavigationMapObjective=0\n",false),("explicit-on","NavigationMap=1\nNavigationMapObjective=1\n",true)})
        {
            var clone=Path.Combine(root,"local","runs","map-option-"+label+"-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(clone);Directory.CreateDirectory(Path.Combine(clone,"saves"));
            foreach(var name in new[]{"config.ini","keybinds.ini",PublicSetupService.ManifestName,PublicSetupService.GameName+".exe"})if(File.Exists(Path.Combine(profile,name)))File.Copy(Path.Combine(profile,name),Path.Combine(clone,name));
            if(!File.Exists(Path.Combine(clone,"keybinds.ini")))File.WriteAllText(Path.Combine(clone,"keybinds.ini"),"; synthetic missing-original-keybindings control\n[player1]\n");
            var cloneConfig=Path.Combine(clone,"config.ini");
            if(label=="missing")File.WriteAllText(cloneConfig,"[Graphics]\nRenderer=software\n[KeyMap]\nUnknown = Ctrl+Q ; keep\n[GamepadMap]\nUnknown = Back+Guide ; keep\n");
            else{var config=new IniDocument(File.ReadAllBytes(cloneConfig));config.Set("KeyMap","Map","M");config.Set("GamepadMap","Map","Back+L3");File.WriteAllBytes(cloneConfig,config.ToBytes());}
            var ini=Path.Combine(clone,"foundation.ini");File.WriteAllText(ini,"[Enhancements]\n"+line+"Unrelated = keep ; exact comment\n");
            using var option=new MainForm(root,clone){StartPosition=FormStartPosition.Manual,Location=new Point(-30000,-30000),ShowInTaskbar=false};option.Show();option.ShowPage("enhancements");
            var opt=Find<CheckBox>(option,"Current-area map");var pin=Find<CheckBox>(option,"Show current objective on map");var bytes=File.ReadAllBytes(ini);
            Check(label+" loads map setting without manufacturing files",opt.Checked==expected&&bytes.SequenceEqual(File.ReadAllBytes(ini)));
            Check(label+" loads objective choice and preserves it while map is off",pin.Checked==expected&&pin.Enabled==expected);
            Check(label+" loads default map bindings with SELECT and legacy gestures intact",ProfileService.Load(root,clone).Settings.HotkeyBindings["Map"]==new HotkeyBinding("M","Back+L3")&&ProfileService.Load(root,clone).Settings.LegacyControllerGestures);
            opt.Checked=!expected;Find<Button>(option,"Revert changes").PerformClick();
            Check(label+" reverts without writes",opt.Checked==expected&&bytes.SequenceEqual(File.ReadAllBytes(ini)));
            var bindingsHash=PublicSetupService.HashFile(Path.Combine(clone,"keybinds.ini"));var cfgHash=PublicSetupService.HashFile(Path.Combine(clone,"config.ini"));
            opt.Checked=!expected;Find<Button>(option,"Apply settings").PerformClick();
            Check(label+" changed-only map Apply preserves comments and config bindings",ProfileService.Load(root,clone).Settings.NavigationMap==!expected&&File.ReadAllText(ini).Contains("Unrelated = keep ; exact comment\n")&&PublicSetupService.HashFile(Path.Combine(clone,"config.ini"))==cfgHash&&PublicSetupService.HashFile(Path.Combine(clone,"keybinds.ini"))==bindingsHash);
            opt.Checked=expected;Find<Button>(option,"Apply settings").PerformClick();
            Check(label+" restores intended setting",ProfileService.Load(root,clone).Settings.NavigationMap==expected&&!Find<Button>(option,"Apply settings").Enabled);
            opt.Checked=true;Find<Button>(option,"Apply settings").PerformClick();var objectiveBefore=File.ReadAllBytes(ini);
            pin.Checked=!expected;Find<Button>(option,"Revert changes").PerformClick();
            Check(label+" objective Revert preserves exact bytes",pin.Checked==expected&&objectiveBefore.SequenceEqual(File.ReadAllBytes(ini)));
            pin.Checked=!expected;Find<Button>(option,"Apply settings").PerformClick();
            Check(label+" objective Apply changes only its explicit preference",ProfileService.Load(root,clone).Settings.NavigationMapObjective==!expected&&File.ReadAllText(ini).Contains("Unrelated = keep ; exact comment\n")&&PublicSetupService.HashFile(Path.Combine(clone,"config.ini"))==cfgHash&&PublicSetupService.HashFile(Path.Combine(clone,"keybinds.ini"))==bindingsHash);
            var conflicting=new IniDocument(File.ReadAllBytes(cloneConfig));conflicting.Set("KeyMap","Map","J");conflicting.Set("GamepadMap","Map","R2");File.WriteAllBytes(cloneConfig,conflicting.ToBytes());
            var inherited=ProfileService.Load(root,clone);var retained=File.ReadAllBytes(cloneConfig);var noOp=ProfileService.ApplyCore(inherited,inherited.Settings.DeepCopy(),()=>false);
            Check(label+" inherited binding conflicts stay byte-identical on no-op",noOp.Success&&noOp.BackupDirectory is null&&retained.SequenceEqual(File.ReadAllBytes(cloneConfig)));
            var unrelated=ProfileService.ApplyCore(inherited,inherited.Settings with{Volume=inherited.Settings.Volume==65?66:65},()=>false);
            Check(label+" unrelated edit preserves inherited map conflicts",unrelated.Success&&unrelated.Snapshot!.Settings.HotkeyBindings["Map"]==new HotkeyBinding("J","R2"));
            option.Close();
        }
        foreach(var (label,key,pad,mapKey,mapPad,expectedKey,expectedPad) in new[]{
            ("missing-default-taken","m","L3+Back","","","None","None"),
            ("missing-modified-key","Ctrl+M","L3","","","M","Back+L3"),
            ("explicit-map-wins","M","Back+L3","Map=M\n","Map=Back+L3\n","M","Back+L3"),
            ("explicit-none-wins","Ctrl+M","L3","Map=None\n","Map=None\n","None","None")})
        {
            var clone=Path.Combine(root,"local","runs","map-fallback-"+label+"-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(clone);Directory.CreateDirectory(Path.Combine(clone,"saves"));
            foreach(var name in new[]{"keybinds.ini","foundation.ini",PublicSetupService.ManifestName,PublicSetupService.GameName+".exe"})if(File.Exists(Path.Combine(profile,name)))File.Copy(Path.Combine(profile,name),Path.Combine(clone,name));
            var cloneConfig=Path.Combine(clone,"config.ini");
            File.WriteAllText(cloneConfig,"[Graphics]\nRenderer=software\n[KeyMap]\nMovementBoost="+key+"\n"+mapKey+"Unknown = Ctrl+Q ; keep\n[GamepadMap]\nJournal="+pad+"\n"+mapPad+"Unknown = Back+Guide ; keep\n");
            var inherited=ProfileService.Load(root,clone);var retained=Files(clone);
            Check(label+" map defaults reflect exact existing bindings",inherited.Settings.HotkeyBindings["Map"]==new HotkeyBinding(expectedKey,expectedPad)&&inherited.Settings.HotkeyBindings["MovementBoost"].Keyboard==key&&inherited.Settings.HotkeyBindings["Journal"].Controller==pad);
            using var option=new MainForm(root,clone){StartPosition=FormStartPosition.Manual,Location=new Point(-30000,-30000),ShowInTaskbar=false};option.Show();option.ShowPage("hotkeys");
            Check(label+" actual hotkey controls show the effective map binding",Find<ComboBox>(option,"Current-area map keyboard").Text==expectedKey&&Find<ComboBox>(option,"Current-area map controller").Text==expectedPad&&Same(retained));
            var noOp=ProfileService.ApplyCore(inherited,inherited.Settings.DeepCopy(),()=>false);
            Check(label+" loading and no-op never write implicit map defaults",noOp.Success&&noOp.BackupDirectory is null&&Same(retained));
            var cfgHash=PublicSetupService.HashFile(cloneConfig);var unrelated=ProfileService.ApplyCore(inherited,inherited.Settings with{XpMultiplierPercent=inherited.Settings.XpMultiplierPercent==150?160:150},()=>false);
            Check(label+" unrelated enhancement edit preserves absent or explicit map config bytes",unrelated.Success&&PublicSetupService.HashFile(cloneConfig)==cfgHash&&unrelated.Snapshot!.Settings.HotkeyBindings["Map"]==new HotkeyBinding(expectedKey,expectedPad));option.Close();
        }
        // Genuine preceding source receipt proves capability refusal, never a
        // fabricated old version string on the new executable.
        var oldProfile=PublicSetupService.AdoptBuild(root,olderReceipt,sourceManifest.RomPath);var old=ProfileService.Load(root,oldProfile);before=Files(oldProfile);
        Check("Genuine preceding binary is ready but lacks map capability",old.Readiness.Ready&&!ProfileService.SupportsNavigationMap(old));
        var refused=ProfileService.ApplyCore(old,old.Settings with{NavigationMap=!old.Settings.NavigationMap},()=>false);
        Check("Older map setting refuses without writes",!refused.Success&&Same(before));
        refused=ProfileService.ApplyCore(old,old.Settings with{NavigationMapObjective=!old.Settings.NavigationMapObjective},()=>false);
        Check("Older objective setting refuses without writes",!refused.Success&&Same(before));
        var oldBindings=old.Settings.DeepCopy();oldBindings.HotkeyBindings["Map"]=new("Ctrl+M","Back+Guide");refused=ProfileService.ApplyCore(old,oldBindings,()=>false);
        Check("Older map bindings refuse without writes",!refused.Success&&Same(before));
        using(var unsupported=new MainForm(root,oldProfile){StartPosition=FormStartPosition.Manual,Location=new Point(-30000,-30000),ShowInTaskbar=false})
        {
            unsupported.Show();unsupported.ShowPage("enhancements");Check("Older GUI map checkbox is disabled",!Find<CheckBox>(unsupported,"Current-area map").Enabled);
            Check("Older GUI objective checkbox is disabled",!Find<CheckBox>(unsupported,"Show current objective on map").Enabled);
            unsupported.ShowPage("hotkeys");Check("Older GUI map bindings are disabled",!Find<ComboBox>(unsupported,"Current-area map keyboard").Enabled&&!Find<ComboBox>(unsupported,"Current-area map controller").Enabled);unsupported.Close();
        }
        var capture=Path.Combine(Path.GetDirectoryName(report)!,"map-captures");Directory.CreateDirectory(capture);
        foreach(var size in new[]{new Size(1120,760),new Size(950,650)})
        {
            form.ClientSize=size;
            foreach(var page in new[]{"enhancements","hotkeys"})
            {
                form.ShowPage(page);form.PerformLayout();form.Refresh();var view=Walk(form).OfType<Panel>().Single(c=>c.Visible&&c.AutoScroll);
                Check(page+" at "+size.Width+" has reachable map controls without horizontal clipping",!view.HorizontalScroll.Visible);
                using var image=new Bitmap(form.Width,form.Height);form.DrawToBitmap(image,new Rectangle(Point.Empty,image.Size));image.Save(Path.Combine(capture,page+"-"+size.Width+".png"));
            }
        }
        Check("All copied checkpoint bytes remain unchanged",Same(saves));
        File.WriteAllText(report,JsonSerializer.Serialize(new{passed=true,checks=cases.Count,cases,screenshots=capture,older_receipt_sha256=PublicSetupService.HashFile(olderReceipt),gameplay_executed=false,scope="Actual disposable GUI/settings and source launch-environment checks; no native rendering, audio, physical-pad or campaign qualification."},new JsonSerializerOptions{WriteIndented=true}));
    }
}
