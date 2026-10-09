using SecretOfTheStars.Companion.Core;

namespace SecretOfTheStars.Companion;

public sealed partial class MainForm
{
    void BuildHotkeys()
    {
        var page=Page("hotkeys","Hotkeys","Choose keyboard and controller shortcuts. Changes apply on your next launch.");
        AddCheck(page,"Fast-forward is a toggle",s=>s.FastForwardToggle,(s,v)=>s.FastForwardToggle=v);
        page.Add(Theme.Text("Off: hold the assigned button to fast-forward. On: press once to start and again to stop. Movement boost always uses a held button.",10,Theme.Muted),18);
        page.Add(Theme.Text("Default movement boost: Left Shift / left trigger. Default fast-forward: Tab / right trigger. Existing explicit bindings take precedence.",10,Theme.Muted),12);
        AddCheck(page,"Legacy controller menu gestures",s=>s.LegacyControllerGestures,(s,v)=>s.LegacyControllerGestures=v);
        page.Add(Theme.Text("Allows Select + R for the checkpoint menu and Select + right-stick click for rewind. Turn off to use those combinations for your own shortcuts.",10,Theme.Muted),12);
        page.Add(Theme.Text("Keyboard names accept Ctrl+, Alt+ and Shift+ chords. Controller names follow SDL/Xbox labels; L1/R1 are bumpers, L2/R2 are triggers, L3/R3 are stick clicks. You can type a chord such as Back+R1. None leaves an action unbound.",10,Theme.Muted),18);
        var grid=BindingGrid();
        foreach(var action in HotkeyCatalog.Actions.Where(a=>a.Slots==1))
            BindingRow(grid,action.Label,s=>s.HotkeyBindings[action.Id].Keyboard,(s,v)=>s.HotkeyBindings[action.Id]=s.HotkeyBindings[action.Id] with{Keyboard=v},
                s=>s.HotkeyBindings[action.Id].Controller,(s,v)=>s.HotkeyBindings[action.Id]=s.HotkeyBindings[action.Id] with{Controller=v});
        page.Add(grid,22);
        Section(page,"Checkpoint shortcuts","Select any of the twenty slots to edit its individual save/load bindings. Loading replaces the current game state; bind deliberately.");
        var slots=Theme.Combo(190);slots.AccessibleName="Checkpoint shortcut slot";slots.Items.AddRange(Enumerable.Range(1,20).Select(i=>(object)$"Slot {i}").ToArray());slots.SelectedIndex=0;page.Add(slots,12);
        var state=BindingGrid();
        foreach(var action in HotkeyCatalog.Actions.Where(a=>a.Id is "Load" or "Save"))
            BindingRow(state,action.Label,s=>HotkeyCatalog.GetSlot(s.HotkeyBindings[action.Id].Keyboard,slots.SelectedIndex),
                (s,v)=>s.HotkeyBindings[action.Id]=s.HotkeyBindings[action.Id] with{Keyboard=HotkeyCatalog.SetSlot(s.HotkeyBindings[action.Id].Keyboard,slots.SelectedIndex,20,v)},
                s=>HotkeyCatalog.GetSlot(s.HotkeyBindings[action.Id].Controller,slots.SelectedIndex),
                (s,v)=>s.HotkeyBindings[action.Id]=s.HotkeyBindings[action.Id] with{Controller=HotkeyCatalog.SetSlot(s.HotkeyBindings[action.Id].Controller,slots.SelectedIndex,20,v)});
        slots.SelectedIndexChanged+=(_,_)=>{if(slots.SelectedIndex<0)return;bool was=loading;loading=true;foreach(var bind in populate)bind(edited);loading=was;};
        settingControls.Add(slots);page.Add(state,14);
        page.Add(Theme.Text("Avoid assigning the same button to different actions. Use a controller chord when your face buttons are already used by the game. Escape remains available to close overlays even after a rebind.",10,Theme.Muted),0);
    }

    void BuildGameplayBindings(PageColumn page)
    {
        Section(page,"Game buttons","These are SNES button names. A keyboard binding is one key; controller bindings can use chords.");
        var grid=BindingGrid();
        foreach(var (name,index) in HotkeyCatalog.GameplayOrder.Select((name,i)=>(name,i)))
        {
            string id="player1:"+name;
            BindingRow(grid,name.ToUpperInvariant(),s=>s.GameplayKeys[id],(s,v)=>s.GameplayKeys[id]=v,
                s=>HotkeyCatalog.GetSlot(s.HotkeyBindings["Controls"].Controller,index),
                (s,v)=>s.HotkeyBindings["Controls"]=s.HotkeyBindings["Controls"] with{Controller=HotkeyCatalog.SetSlot(s.HotkeyBindings["Controls"].Controller,index,12,v)});
        }
        page.Add(grid,16);
    }

    static TableLayoutPanel BindingGrid()
    {
        var grid=new TableLayoutPanel{ColumnCount=3,AutoSize=true,Margin=Padding.Empty,BackColor=Theme.Canvas};
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,175));grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,240));grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,210));
        grid.RowCount=1;grid.Controls.Add(Theme.Text("Action",10,Theme.Muted),0,0);grid.Controls.Add(Theme.Text("Keyboard",10,Theme.Muted),1,0);grid.Controls.Add(Theme.Text("Controller",10,Theme.Muted),2,0);
        return grid;
    }

    void BindingRow(TableLayoutPanel grid,string title,Func<GameSettings,string> keyboard,Action<GameSettings,string> setKeyboard,Func<GameSettings,string> controller,Action<GameSettings,string> setController)
    {
        int row=grid.RowCount++;grid.RowStyles.Add(new RowStyle(SizeType.AutoSize));grid.Controls.Add(Theme.Text(title,10,Theme.Ink),0,row);
        foreach(var column in new[]{1,2})
        {
            var combo=Theme.Combo(column==1?220:190);combo.DropDownStyle=ComboBoxStyle.DropDown;combo.AccessibleName=title+(column==1?" keyboard":" controller");combo.Margin=new Padding(0,0,10,8);
            combo.Items.AddRange((column==1?HotkeyCatalog.KeyboardChoices:HotkeyCatalog.ControllerChoices).Cast<object>().ToArray());
            var get=column==1?keyboard:controller;var set=column==1?setKeyboard:setController;
            populate.Add(s=>combo.Text=get(s));combo.TextChanged+=(_,_)=>{if(loading)return;set(edited,combo.Text);MarkDirty();};settingControls.Add(combo);grid.Controls.Add(combo,column,row);
        }
    }
}
