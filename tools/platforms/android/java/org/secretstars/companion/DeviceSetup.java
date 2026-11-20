package org.secretstars.companion;

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/** Runs the sealed setup tools in app-private storage and publishes the local module on success. */
final class DeviceSetup {
    private static final String TAG = "SecretStarsSetup";
    private static final String ASSET = "ondevice.zip";
    private static final long MAX_ARCHIVE = 512L * 1024 * 1024;
    private static final long MAX_UNPACKED = 1024L * 1024 * 1024;
    private static final int MAX_ENTRIES = 40_000;
    private static final Pattern COMPILE_COUNTS = Pattern.compile("SOTS_UNITS:([0-9]{1,6})/([0-9]{1,6})");

    private DeviceSetup() {}

    interface Progress {
        void update(String text, int completed, int total);

        default void phase(String text) {
            update(text, 0, 0);
        }
    }

    static void prepare(Context app, Path rom, Progress progress) throws IOException {
        Path privateDir = app.getNoBackupFilesDir().toPath();
        Path work = privateDir.resolve("phone-setup");
        Files.createDirectories(work);
        if (!Files.isDirectory(work, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("Android could not open its private setup directory.");
        }
        try (FileChannel lease = FileChannel.open(work.resolve("setup.lock"), StandardOpenOption.CREATE,
                StandardOpenOption.WRITE, LinkOption.NOFOLLOW_LINKS); FileLock lock = lease.tryLock()) {
            if (lock == null) throw new IOException("First-time setup is already running.");
            Path stage = work.resolve("build");
            try {
                LocalGameModule.verify(privateDir);
                removeTemporaryFiles(stage);
                return;
            } catch (IOException pending) {
                // No module for the current capsule. Build in a separate working directory.
            }

            deleteTree(stage);
            Files.createDirectory(stage);
            try {
                progress.phase("Preparing first-time setup...");
                verifyArchive(app.getAssets());
                Path capsule = Files.createDirectory(stage.resolve("capsule"));
                unpack(app.getAssets(), capsule);
                Path output = stage.resolve("libmain.so");
                runTools(app, rom, stage, capsule, output, progress);
                progress.phase("Installing the compiled game...");
                LocalGameModule.install(privateDir, output);
            } finally {
                removeTemporaryFiles(stage);
            }
        }
    }

    private static void removeTemporaryFiles(Path stage) {
        try {
            deleteTree(stage);
        } catch (IOException cleanup) {
            Log.w(TAG, "Could not remove temporary build files", cleanup);
        }
    }

    private static void verifyArchive(AssetManager assets) throws IOException {
        MessageDigest digest = RomImport.newDigest();
        long size = 0;
        try (InputStream in = assets.open(ASSET, AssetManager.ACCESS_STREAMING)) {
            byte[] buffer = new byte[64 * 1024];
            for (int count; (count = in.read(buffer)) != -1;) {
                size += count;
                if (size > MAX_ARCHIVE) throw new IOException("The packaged setup tools are too large.");
                digest.update(buffer, 0, count);
            }
        }
        if (!BuildConfig.SETUP_CAPSULE_SHA256.equals(RomImport.hex(digest.digest()))) {
            throw new IOException("The packaged setup tools did not pass their integrity check.");
        }
    }

    private static void unpack(AssetManager assets, Path capsule) throws IOException {
        Set<Path> entries = new HashSet<>();
        byte[] buffer = new byte[64 * 1024];
        long length = 0;
        try (ZipInputStream zip = new ZipInputStream(assets.open(ASSET, AssetManager.ACCESS_STREAMING))) {
            for (ZipEntry entry; (entry = zip.getNextEntry()) != null;) {
                String name = entry.getName();
                if (entry.isDirectory()) name = name.substring(0, name.length() - 1);
                if (name.length() > 512 || name.indexOf('\\') >= 0 || name.indexOf('\0') >= 0) {
                    throw new IOException("The packaged setup tools have an invalid entry.");
                }
                for (String part : name.split("/", -1)) {
                    if (part.isEmpty() || part.equals(".") || part.equals("..")) {
                        throw new IOException("The packaged setup tools have an invalid path.");
                    }
                }
                Path target = capsule.resolve(name);
                if (!target.startsWith(capsule) || !entries.add(target) || entries.size() > MAX_ENTRIES) {
                    throw new IOException("The packaged setup tools have an invalid file list.");
                }
                if (entry.isDirectory()) {
                    if (zip.read() != -1) throw new IOException("The packaged setup directory contains data.");
                    Files.createDirectories(target);
                } else {
                    Files.createDirectories(target.getParent());
                    try (OutputStream out = Files.newOutputStream(target, StandardOpenOption.CREATE_NEW)) {
                        for (int count; (count = zip.read(buffer)) != -1;) {
                            length += count;
                            if (length > MAX_UNPACKED) throw new IOException("The setup tools exceed their storage limit.");
                            out.write(buffer, 0, count);
                        }
                    }
                }
                zip.closeEntry();
            }
        }
        if (!Files.isDirectory(capsule.resolve("pyhome")) || !Files.isRegularFile(capsule.resolve("bundle.json"))
                || !Files.isRegularFile(capsule.resolve("build_on_phone.py"))) {
            throw new IOException("The packaged setup tools are incomplete.");
        }
    }

    private static void runTools(Context app, Path rom, Path stage, Path capsule, Path output,
            Progress progress) throws IOException {
        String nativeDir = app.getApplicationInfo().nativeLibraryDir;
        Path launcher = new File(nativeDir, "libpython-launcher.so").toPath();
        if (!Files.isRegularFile(launcher) || !Files.isExecutable(launcher)) {
            throw new IOException("Android could not find the installed setup launcher.");
        }
        Path temp = Files.createDirectory(stage.resolve("tmp"));
        ProcessBuilder command = new ProcessBuilder(launcher.toString(), "-I", capsule.resolve("build_on_phone.py").toString(),
                "--capsule", capsule.toString(), "--rom", rom.toString(), "--output", output.toString(),
                "--native-lib-dir", nativeDir);
        command.directory(stage.toFile());
        command.redirectErrorStream(true);
        Map<String, String> env = command.environment();
        env.put("SOTS_PYTHON_HOME", capsule.resolve("pyhome").toString());
        env.put("LD_LIBRARY_PATH", nativeDir);
        env.put("TMPDIR", temp.toString());
        env.put("HOME", stage.toString());
        Process process = command.start();
        String phase = "starting Python";
        String lastLine = "";
        String failureDetail = "";
        try {
            process.getOutputStream().close();
            try (BufferedReader log = new BufferedReader(new InputStreamReader(process.getInputStream(),
                    StandardCharsets.UTF_8))) {
                for (String line; (line = log.readLine()) != null;) {
                    if (line.equals("SOTS_SETUP:verify")) {
                        phase = "verifying the packaged tools";
                        progress.phase("Verifying the packaged tools...");
                    } else if (line.equals("SOTS_SETUP:runtime")) {
                        phase = "checking the runtime sources";
                        progress.phase("Checking the runtime sources...");
                    } else if (line.equals("SOTS_SETUP:preflight")) {
                        phase = "checking the generator inputs";
                        progress.phase("Checking the generator inputs...");
                    } else if (line.equals("SOTS_SETUP:generate")) {
                        phase = "generating code from the ROM";
                        progress.phase("Generating game code from the ROM...");
                    } else if (line.equals("SOTS_SETUP:headers")) {
                        phase = "preparing the generated headers";
                        progress.phase("Preparing the generated headers...");
                    } else if (line.equals("SOTS_SETUP:validate")) {
                        phase = "checking the generated code";
                        progress.phase("Checking the generated code against the ROM...");
                    } else if (line.equals("SOTS_SETUP:cpu")) {
                        phase = "generating native CPU code";
                        progress.phase("Generating native CPU code...");
                    } else if (line.equals("SOTS_SETUP:compile")) {
                        phase = "compiling the native game";
                        progress.phase("Compiling the native game. Keep this screen open.");
                    } else if (line.equals("Linking game")) {
                        phase = "linking the native game";
                        progress.phase("Linking the native game...");
                    } else if (line.startsWith("SOTS_UNITS:")) {
                        Matcher counts = COMPILE_COUNTS.matcher(line);
                        if (counts.matches()) {
                            int completed = Integer.parseInt(counts.group(1));
                            int total = Integer.parseInt(counts.group(2));
                            if (total > 0 && completed <= total) {
                                progress.update("Compiling the native game. " + completed + " of " + total
                                        + " source files compiled.", completed, total);
                            }
                        }
                    } else if (line.startsWith("SOTS_ERROR:")) {
                        int start = "SOTS_ERROR:".length();
                        failureDetail = line.substring(start, Math.min(start + 600, line.length()));
                    } else if (!line.trim().isEmpty()) {
                        lastLine = line.substring(0, Math.min(800, line.length()));
                    }
                }
            }
            int result = process.waitFor();
            if (result != 0) {
                String detail = failureDetail.isEmpty() ? lastLine : failureDetail;
                Log.w(TAG, "Setup failed while " + phase + " (exit " + result + "): " + detail);
                throw new IOException("Setup stopped while " + phase + " (code " + result + ")."
                        + (detail.isEmpty() ? " The setup tool returned no diagnostic output." : "\n\n" + detail));
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IOException("Setup was interrupted. Tap Play to retry.", interrupted);
        } finally {
            if (process.isAlive()) process.destroyForcibly();
        }
    }

    private static void deleteTree(Path root) throws IOException {
        if (!Files.exists(root, LinkOption.NOFOLLOW_LINKS)) return;
        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file);
                return FileVisitResult.CONTINUE;
            }

            @Override public FileVisitResult postVisitDirectory(Path dir, IOException failure) throws IOException {
                if (failure != null) throw failure;
                Files.delete(dir);
                return FileVisitResult.CONTINUE;
            }
        });
    }
}
