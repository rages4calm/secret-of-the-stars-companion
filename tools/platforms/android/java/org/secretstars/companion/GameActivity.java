package org.secretstars.companion;

import android.os.Bundle;
import android.view.ViewGroup;
import android.view.Window;
import java.io.IOException;
import org.libsdl.app.SDLActivity;

/** Original implementation of the shared SNES layout and hideable control HUD.
 * Android key events use the native host's existing configurable keyboard path. */
public final class GameActivity extends SDLActivity {
    private TouchControls controls;
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
    @Override protected void onCreate(Bundle state) {
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        super.onCreate(state);
        if (mBrokenLibraries) return;
        var preferences = getPreferences(0);
        controls = new TouchControls(this, preferences.getBoolean("showTouchControls", true),
                SDLActivity::onNativeKeyDown, SDLActivity::onNativeKeyUp,
                shown -> preferences.edit().putBoolean("showTouchControls", shown).apply());
        mLayout.addView(controls, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
        controls.requestApplyInsets();
    }
    @Override protected void onPause() {
        if (controls != null) controls.releaseAll();
        super.onPause();
    }
    @Override public void onWindowFocusChanged(boolean focus) {
        super.onWindowFocusChanged(focus);
        if (!focus && controls != null) controls.releaseAll();
    }
}
