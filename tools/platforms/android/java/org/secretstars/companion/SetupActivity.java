package org.secretstars.companion;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.function.Consumer;

/** Imports a player's own ROM using Android's document picker. */
public final class SetupActivity extends Activity {
    private static final int PICK_ROM = 1;
    private static final Handler UI = new Handler(Looper.getMainLooper());

    // Setup belongs to the app process so a rotated Activity can reattach to the same job.
    private static SetupActivity resumed;
    private static boolean running;
    private static String message;
    private static String launchRom;

    private TextView status;
    private ProgressBar progress;
    private Button choose;
    private Button play;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(20 * getResources().getDisplayMetrics().density);
        page.setPadding(padding, padding, padding, padding);
        status = new TextView(this);
        status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        page.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        page.addView(progress);
        choose = new Button(this);
        choose.setText("Choose ROM");
        choose.setOnClickListener(view -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.setType("*/*");
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(picker, PICK_ROM);
        });
        page.addView(choose);
        play = new Button(this);
        play.setText("Play");
        play.setOnClickListener(view -> play());
        page.addView(play);
        setContentView(page);
    }

    @Override protected void onResume() {
        super.onResume();
        resumed = this;
        refresh();
    }

    @Override protected void onPause() {
        if (resumed == this) resumed = null;
        super.onPause();
    }

    private static boolean buildsOnPhone() {
        return BuildConfig.LOAD_LOCAL_MODULE && BuildConfig.HAS_PHONE_TOOLCHAIN;
    }

    private String prompt(boolean imported) {
        if (buildsOnPhone()) {
            if (imported) return "Tap Play to start. The phone will finish setup first if needed.";
            return "Choose your clean USA ROM. First-time setup builds the game on your phone.";
        }
        return BuildConfig.LOAD_LOCAL_MODULE
                ? "Developer setup shell. Choose your clean USA ROM to try local import."
                : "Secret of the Stars Android preview. Choose your clean USA ROM.";
    }

    private void refresh() {
        progress.setVisibility(running ? View.VISIBLE : View.GONE);
        choose.setEnabled(!running);
        boolean imported = false;
        try {
            imported = Files.isRegularFile(romPath(this));
        } catch (IOException ignored) {
            // The picker reports unavailable storage if import is attempted.
        }
        status.setText(message == null ? prompt(imported) : message);
        play.setEnabled(!running && imported);
        if (running) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (launchRom != null) {
            Intent game = new Intent(this, GameActivity.class).putExtra("rom", launchRom);
            launchRom = null;
            startActivity(game);
        }
    }

    private static Path directory(Context app) throws IOException {
        File dir = app.getExternalFilesDir(null);
        if (dir == null) throw new IOException("App storage is unavailable.");
        return dir.toPath();
    }

    private static Path romPath(Context app) throws IOException {
        Path dir = buildsOnPhone() ? app.getNoBackupFilesDir().toPath() : directory(app);
        return dir.resolve("game.sfc");
    }

    private static void writeDefault(Path directory, String name, String value) throws IOException {
        Path file = directory.resolve(name);
        if (!Files.exists(file)) Files.write(file, value.getBytes(StandardCharsets.UTF_8));
    }

    private interface SetupTask {
        String run(Context app, Consumer<String> progress) throws IOException;
    }

    private static void update(String text) {
        message = text;
        if (resumed != null) resumed.refresh();
    }

    private void runSetup(String text, String success, SetupTask task) {
        if (running) return;
        Context app = getApplicationContext();
        running = true;
        update(text);
        new Thread(() -> {
            String game = null;
            String result = success;
            try {
                game = task.run(app, next -> UI.post(() -> update(next)));
            } catch (IOException | RuntimeException e) {
                Log.w("SecretStarsSetup", "Could not complete setup", e);
                result = e.getMessage() != null ? e.getMessage() : "Setup stopped. Try again.";
            }
            String readyRom = game;
            String finalStatus = result;
            UI.post(() -> {
                running = false;
                launchRom = readyRom;
                update(finalStatus);
            });
        }, "SOTS-ROM-setup").start();
    }

    private void play() {
        runSetup("Checking local game files...", "Ready to play.", (app, updateProgress) -> {
            Path rom = romPath(app);
            RomImport.verify(rom);
            if (buildsOnPhone()) DeviceSetup.prepare(app, rom, updateProgress);
            else if (BuildConfig.LOAD_LOCAL_MODULE) LocalGameModule.verify(app.getNoBackupFilesDir().toPath());
            Path dir = directory(app);
            writeDefault(dir, "config.ini", "[Graphics]\nRenderer=opengles2\nFullscreen=0\nVSync=1\n"
                    + "NewRenderer=1\nWidescreen=0\n[Sound]\nEnableAudio=1\nAudioFreq=32040\n"
                    + "[General]\nAutosave=0\nSkipLauncher=1\n");
            writeDefault(dir, "foundation.ini", "EnhancedPixels=1\nExperimentalFieldWide=1\n"
                    + "ExperimentalFieldActors=1\nJournal=1\nNavigationMap=1\nMovementSpeedPercent=200\n");
            return rom.toString();
        });
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != PICK_ROM || result != RESULT_OK || data == null || data.getData() == null) return;
        Uri selected = data.getData();
        String success = buildsOnPhone() ? "Setup complete. Tap Play to start." : BuildConfig.LOAD_LOCAL_MODULE
                ? "ROM verified. This developer shell does not include a phone compiler."
                : "ROM imported. Tap Play to start.";
        runSetup("Checking the ROM...", success, (app, updateProgress) -> {
            Path rom = romPath(app);
            try (InputStream in = app.getContentResolver().openInputStream(selected)) {
                if (in == null) throw new IOException("Android could not open the selected ROM.");
                RomImport.save(in, rom);
            }
            if (buildsOnPhone()) DeviceSetup.prepare(app, rom, updateProgress);
            return null;
        });
    }
}
