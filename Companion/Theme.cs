using System.Drawing.Drawing2D;

namespace SecretOfTheStars.Companion;

internal static class Theme
{
    public static readonly Color Canvas=Color.FromArgb(0x11,0x1b,0x30), Rail=Color.FromArgb(0x09,0x14,0x2a), Panel=Color.FromArgb(0x14,0x24,0x3d);
    public static readonly Color Ink=Color.FromArgb(0xeb,0xee,0xf7), Muted=Color.FromArgb(0xa6,0xb4,0xca), Accent=Color.FromArgb(0xf2,0xdb,0x7e);
    public static readonly Color Line=Color.FromArgb(0x36,0x49,0x65), Danger=Color.FromArgb(0xff,0xb1,0xa5);
    public static Font Body(float size=11,FontStyle style=FontStyle.Regular)=>new("Segoe UI",size,style);
    public static Font Title(float size=30)=>new("Georgia",size,FontStyle.Regular);
    public static Label Text(string text,float size=11,Color? color=null,FontStyle style=FontStyle.Regular)=>new(){Text=text,AutoSize=true,Font=Body(size,style),ForeColor=color??Ink,BackColor=Color.Transparent,UseMnemonic=false,Margin=new Padding(0,0,0,8)};
    public static CompanionButton Button(string text,bool primary=false,int width=190)=>new(){Text=text,Primary=primary,Size=new Size(width,44),Margin=new Padding(0,0,12,0),AccessibleName=text};
    public static CheckBox Check(string text)=>new(){Text=text,AutoSize=true,Font=Body(),ForeColor=Ink,BackColor=Canvas,Margin=new Padding(0,0,0,6),Padding=new Padding(0,5,0,5),AccessibleName=text};
    public static ComboBox Combo(int width=260)
    {
        var c=new ComboBox{DropDownStyle=ComboBoxStyle.DropDownList,FlatStyle=FlatStyle.Flat,DrawMode=DrawMode.OwnerDrawFixed,ItemHeight=28,Width=width,Font=Body(),BackColor=Rail,ForeColor=Ink,Margin=Padding.Empty};
        c.DrawItem+=(_,e)=>{if(e.Index<0)return;using var b=new SolidBrush((e.State&DrawItemState.Selected)!=0?Panel:Rail);e.Graphics.FillRectangle(b,e.Bounds);TextRenderer.DrawText(e.Graphics,c.Items[e.Index]?.ToString(),c.Font,new Rectangle(e.Bounds.X+8,e.Bounds.Y,e.Bounds.Width-14,e.Bounds.Height),Ink,TextFormatFlags.VerticalCenter|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);e.DrawFocusRectangle();};return c;
    }
    public static NumericUpDown Number(int minimum,int maximum,int increment=1,int width=140)=>new(){Minimum=minimum,Maximum=maximum,Increment=increment,Width=width,Height=34,Font=Body(12),BackColor=Rail,ForeColor=Ink,BorderStyle=BorderStyle.FixedSingle,Margin=Padding.Empty};
    public static FlowLayoutPanel Row(params Control[] controls){var p=new FlowLayoutPanel{AutoSize=true,WrapContents=true,Margin=Padding.Empty,BackColor=Canvas};p.Controls.AddRange(controls);return p;}
    public static Panel Rule()=>new(){Height=1,BackColor=Line,Margin=Padding.Empty};
}

internal sealed class CompanionButton : Button
{
    bool hover,pressed;
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)] public bool Primary{get;set;}
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)] public bool Navigation{get;set;}
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)] public bool Selected{get;set;}
    public CompanionButton(){SetStyle(ControlStyles.UserPaint|ControlStyles.OptimizedDoubleBuffer|ControlStyles.AllPaintingInWmPaint,true);FlatStyle=FlatStyle.Flat;FlatAppearance.BorderSize=0;Font=Theme.Body(11,FontStyle.Bold);Cursor=Cursors.Hand;UseVisualStyleBackColor=false;}
    protected override void OnMouseEnter(EventArgs e){hover=true;Invalidate();base.OnMouseEnter(e);}
    protected override void OnMouseLeave(EventArgs e){hover=pressed=false;Invalidate();base.OnMouseLeave(e);}
    protected override void OnMouseDown(MouseEventArgs e){pressed=true;Invalidate();base.OnMouseDown(e);}
    protected override void OnMouseUp(MouseEventArgs e){pressed=false;Invalidate();base.OnMouseUp(e);}
    protected override void OnGotFocus(EventArgs e){Invalidate();base.OnGotFocus(e);}
    protected override void OnLostFocus(EventArgs e){Invalidate();base.OnLostFocus(e);}
    protected override void OnPaintBackground(PaintEventArgs e)=>e.Graphics.Clear(Parent?.BackColor??Theme.Canvas);
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.Clear(Parent?.BackColor??Theme.Canvas);e.Graphics.SmoothingMode=SmoothingMode.AntiAlias;
        var r=new Rectangle(1,1,Width-3,Height-3);using var path=new GraphicsPath();const int d=8;
        path.AddArc(r.Left,r.Top,d,d,180,90);path.AddArc(r.Right-d,r.Top,d,d,270,90);path.AddArc(r.Right-d,r.Bottom-d,d,d,0,90);path.AddArc(r.Left,r.Bottom-d,d,d,90,90);path.CloseFigure();
        Color fill=!Enabled?Theme.Panel:Primary?(pressed?Color.FromArgb(217,190,94):hover?Color.FromArgb(255,233,153):Theme.Accent):Selected?Theme.Panel:hover?Color.FromArgb(32,51,78):Navigation?Theme.Rail:Theme.Panel;
        using var brush=new SolidBrush(fill);e.Graphics.FillPath(brush,path);
        if(!Navigation||Selected){using var pen=new Pen(Focused&&ShowFocusCues?Theme.Accent:Primary?fill:Theme.Line,Focused&&ShowFocusCues?2:1);e.Graphics.DrawPath(pen,path);}
        if(Navigation&&Selected){using var marker=new SolidBrush(Theme.Accent);e.Graphics.FillRectangle(marker,6,13,3,Height-26);}
        TextRenderer.DrawText(e.Graphics,Text,Font,new Rectangle(Navigation?20:10,2,Width-(Navigation?30:20),Height-4),!Enabled?Theme.Muted:Primary?Theme.Rail:Selected?Theme.Accent:Theme.Ink,(Navigation?TextFormatFlags.Left:TextFormatFlags.HorizontalCenter)|TextFormatFlags.VerticalCenter|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);
        if(Focused&&ShowFocusCues)ControlPaint.DrawFocusRectangle(e.Graphics,new Rectangle(7,7,Width-14,Height-14),Primary?Theme.Rail:Theme.Accent,fill);
    }
}

internal sealed class PageColumn : TableLayoutPanel
{
    public PageColumn(){ColumnCount=1;AutoSize=true;AutoSizeMode=AutoSizeMode.GrowAndShrink;Dock=DockStyle.Top;BackColor=Theme.Canvas;Margin=Padding.Empty;Padding=new Padding(0,0,0,28);ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));}
    public void Add(Control control,int gap=16){int row=RowCount++;RowStyles.Add(new RowStyle(SizeType.AutoSize));control.Margin=new Padding(0,0,0,gap);control.Anchor=AnchorStyles.Left|AnchorStyles.Top;if(control is Panel)control.Anchor|=AnchorStyles.Right;Controls.Add(control,0,row);}
    protected override void OnLayout(LayoutEventArgs e){foreach(Control c in Controls)if(c is Label l)l.MaximumSize=new Size(Math.Max(1,ClientSize.Width-4),0);base.OnLayout(e);}
}

internal sealed class SceneStrip(Image image) : Panel
{
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);if(Width<1||Height<1)return;
        float scale=Math.Max((float)Width/image.Width,(float)Height/image.Height);
        float sw=Width/scale,sh=Height/scale;
        var source=new RectangleF((image.Width-sw)/2,(image.Height-sh)/2,sw,sh);
        e.Graphics.InterpolationMode=InterpolationMode.NearestNeighbor;e.Graphics.PixelOffsetMode=PixelOffsetMode.Half;
        e.Graphics.DrawImage(image,new Rectangle(0,0,Width,Height),source,GraphicsUnit.Pixel);
    }
    protected override void Dispose(bool disposing){if(disposing)image.Dispose();base.Dispose(disposing);}
}
