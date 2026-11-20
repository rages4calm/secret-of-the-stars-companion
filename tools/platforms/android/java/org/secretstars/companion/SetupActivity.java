package org.secretstars.companion;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/** Imports a player's own ROM using Android's document picker. */
public final class SetupActivity extends Activity {
    private static final int PICK_ROM = 1;
    private static final Handler UI = new Handler(Looper.getMainLooper());

    // Setup belongs to the app process so a rotated Activity can reattach to the same job.
    private static SetupActivity resumed;
    private static boolean running;
    private static String message;
    private static String launchRom;
    private static long setupStarted;
    private static int completedUnits;
    private static int totalUnits;

    private TextView status;
    private TextView elapsed;
    private ProgressBar progress;
    private Button choose;
    private Button play;
    private final Runnable clock = new Runnable() {
        @Override public void run() {
            if (resumed != SetupActivity.this || !running) return;
            updateElapsed();
            UI.postDelayed(this, 1000);
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(20 * getResources().getDisplayMetrics().density);
        page.setPadding(padding, padding, padding, padding);
        TextView title = new TextView(this);
        title.setText(getTitle());
        title.setTextAppearance(android.R.style.TextAppearance_Material_Title);
        title.setPadding(0, 0, 0, padding);
        page.addView(title);
        status = new TextView(this);
        status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        status.setTextIsSelectable(true);
        page.addView(status);
        elapsed = new TextView(this);
        page.addView(elapsed);
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
        scroll.addView(page);
        if (Build.VERSION.SDK_INT >= 35) {
            scroll.setOnApplyWindowInsetsListener((view, insets) -> {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return insets;
            });
        }
        setContentView(scroll);
    }

    @Override protected void onResume() {
        super.onResume();
        resumed = this;
        refresh();
    }

    @Override protected void onPause() {
        if (resumed == this) resumed = null;
        UI.removeCallbacks(clock);
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
        progress.setIndeterminate(totalUnits == 0);
        if (totalUnits > 0) {
            progress.setMax(totalUnits);
            progress.setProgress(completedUnits);
        }
        elapsed.setVisibility(running ? View.VISIBLE : View.GONE);
        UI.removeCallbacks(clock);
        if (running) clock.run();
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

    private void updateElapsed() {
        long seconds = (SystemClock.elapsedRealtime() - setupStarted) / 1000;
        elapsed.setText(String.format(Locale.ROOT, "Setup time %d:%02d", seconds / 60, seconds % 60));
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
        String run(Context app, DeviceSetup.Progress progress) throws IOException;
    }

    private static void update(String text, int completed, int total) {
        message = text;
        completedUnits = completed;
        totalUnits = total;
        if (resumed != null) resumed.refresh();
    }

    private void runSetup(String text, String success, SetupTask task) {
        if (running) return;
        Context app = getApplicationContext();
        running = true;
        setupStarted = SystemClock.elapsedRealtime();
        update(text, 0, 0);
        new Thread(() -> {
            String game = null;
            String result = success;
            try {
                game = task.run(app, (next, completed, total) -> UI.post(() -> update(next, completed, total)));
            } catch (IOException | RuntimeException e) {
                Log.w("SecretStarsSetup", "Could not complete setup", e);
                result = e.getMessage() != null ? e.getMessage() : "Setup stopped. Try again.";
            }
            String readyRom = game;
            String finalStatus = result;
            UI.post(() -> {
                running = false;
                launchRom = readyRom;
                update(finalStatus, 0, 0);
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
