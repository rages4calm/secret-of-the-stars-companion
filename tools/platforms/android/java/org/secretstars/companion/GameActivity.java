package org.secretstars.companion;

import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.KeyEvent;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.io.IOException;
import java.util.HashSet;
import org.libsdl.app.SDLActivity;

/** Original implementation of the shared SNES layout and hideable control HUD.
 * Android key events use the native host's existing configurable keyboard path. */
public final class GameActivity extends SDLActivity {
    private final HashSet<Integer> held = new HashSet<>();
    private LinearLayout controls;
    private boolean shown;
    private String localModule;

    @Override protected String[] getLibraries() {
        return BuildConfig.LOAD_LOCAL_MODULE ? new String[]{"SDL3"} : new String[]{"SDL3", "main"};
    }

    @Override public void loadLibraries() {
        if (BuildConfig.LOAD_LOCAL_MODULE) {
            try {
                localModule = LocalGameModule.verify(getNoBackupFilesDir().toPath()).toString();
            } catch (IOException e) {
                throw new IllegalStateException(e.getMessage(), e);
            }
        }
        super.loadLibraries();
        if (localModule != null) System.load(localModule);
    }

    @Override protected String getMainSharedObject() {
        return localModule == null ? super.getMainSharedObject() : localModule;
    }
    @Override protected String[] getArguments() {
        return new String[]{"--no-launcher", "--rom", getIntent().getStringExtra("rom")};
    }
    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (mBrokenLibraries) return;
        FrameLayout root = new FrameLayout(this);
        controls = new LinearLayout(this); controls.setOrientation(LinearLayout.VERTICAL);
        LinearLayout toolbar = row();
        add(toolbar,"Journal",KeyEvent.KEYCODE_J); add(toolbar,"Map",KeyEvent.KEYCODE_M);
        add(toolbar,"Boost",KeyEvent.KEYCODE_SHIFT_LEFT); add(toolbar,"Turbo",KeyEvent.KEYCODE_TAB);
        controls.addView(toolbar);
        LinearLayout pad=row();
        add(pad,"Up",KeyEvent.KEYCODE_DPAD_UP); add(pad,"Down",KeyEvent.KEYCODE_DPAD_DOWN);
        add(pad,"Left",KeyEvent.KEYCODE_DPAD_LEFT); add(pad,"Right",KeyEvent.KEYCODE_DPAD_RIGHT);
        add(pad,"A",KeyEvent.KEYCODE_X); add(pad,"B",KeyEvent.KEYCODE_Z);
        add(pad,"X",KeyEvent.KEYCODE_S); add(pad,"Y",KeyEvent.KEYCODE_A);
        controls.addView(pad);
        LinearLayout system=row();
        add(system,"L",KeyEvent.KEYCODE_C); add(system,"R",KeyEvent.KEYCODE_V);
        add(system,"Select",KeyEvent.KEYCODE_SHIFT_RIGHT); add(system,"Start",KeyEvent.KEYCODE_ENTER);
        controls.addView(system);
        FrameLayout.LayoutParams bottom=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);
        root.addView(controls,bottom);
        Button toggle=new Button(this); toggle.setFocusable(false); toggle.setText("Controls");
        toggle.setOnClickListener(v -> setShown(!shown));
        root.addView(toggle,new FrameLayout.LayoutParams(dp(100),dp(48),Gravity.TOP|Gravity.RIGHT));
        addContentView(root,new FrameLayout.LayoutParams(-1,-1));
        setShown(getPreferences(0).getBoolean("showTouchControls",true));
    }
    private LinearLayout row(){LinearLayout row=new LinearLayout(this); row.setMotionEventSplittingEnabled(true); return row;}
    private void add(LinearLayout row,String label,int key){
        Button b=new Button(this); b.setFocusable(false); b.setText(label);b.setAlpha(.65f);
        row.addView(b,new LinearLayout.LayoutParams(0,dp(48),1));
        b.setOnTouchListener((v,e)->{
            int action=e.getActionMasked();
            if(action==MotionEvent.ACTION_DOWN){if(held.add(key))onNativeKeyDown(key);v.setPressed(true);return true;}
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){if(held.remove(key))onNativeKeyUp(key);v.setPressed(false);return true;}
            return true;
        });
    }
    private void release(){for(int key:held)onNativeKeyUp(key);held.clear();}
    private void setShown(boolean value){if(!value)release();shown=value;controls.setVisibility(value?View.VISIBLE:View.GONE);getPreferences(0).edit().putBoolean("showTouchControls",value).apply();}
    @Override protected void onPause(){if(!mBrokenLibraries)release();super.onPause();}
    @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);if(!focus&&!mBrokenLibraries)release();}
}
