package org.secretstars.companion;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.List;

/** Accepts only the module slot in this app's internal, non-backed-up directory. */
final class LocalGameModule {
    static final String FORMAT = "sots-android-arm64-native-module-v1";
    private static final String PHONE_FORMAT = "sots-android-first-run-v1";
    private static final long MAX_BYTES = 256L * 1024 * 1024;

    private LocalGameModule() {}

    static Path verify(Path noBackupFiles) throws IOException {
        Path slot = noBackupFiles.resolve("native-game");
        Path seal = slot.resolve("module.ready");
        Path library = slot.resolve("libmain.so");
        if (!Files.isDirectory(slot, LinkOption.NOFOLLOW_LINKS)
                || !Files.isRegularFile(seal, LinkOption.NOFOLLOW_LINKS)
                || !Files.isRegularFile(library, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException(BuildConfig.HAS_PHONE_TOOLCHAIN
                    ? "The native game is waiting for first-time setup."
                    : "On-device compilation is pending in this developer build.");
        }
        if (Files.size(seal) > 256 || Files.isWritable(library)) {
            throw new IOException("The private native module is incomplete or writable.");
        }
        boolean onPhone = BuildConfig.HAS_PHONE_TOOLCHAIN;
        List<String> lines = Files.readAllLines(seal);
        if (lines.size() != (onPhone ? 4 : 3)
                || !(onPhone ? PHONE_FORMAT : FORMAT).equals(lines.get(0))
                || !RomImport.SHA256.equals(lines.get(1)) || !lines.get(2).matches("[0-9a-f]{64}")
                || (onPhone && !BuildConfig.SETUP_CAPSULE_SHA256.equals(lines.get(3)))) {
            throw new IOException("The private native module does not match this setup version.");
        }
        validateElf(library);
        if (!lines.get(2).equals(RomImport.hash(library))) {
            throw new IOException("The private native module did not pass its integrity check.");
        }
        return library;
    }

    static void install(Path noBackupFiles, Path builtLibrary) throws IOException {
        validateElf(builtLibrary);
        try (FileChannel file = FileChannel.open(builtLibrary, StandardOpenOption.WRITE)) {
            file.force(true);
        }
        if (!builtLibrary.toFile().setReadOnly() || Files.isWritable(builtLibrary)) {
            throw new IOException("Android could not make the compiled game read-only.");
        }
        Path slot = noBackupFiles.resolve("native-game");
        Files.createDirectories(slot);
        if (!Files.isDirectory(slot, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("The private native game directory is unavailable.");
        }
        Path seal = slot.resolve("module.ready");
        Path pendingSeal = builtLibrary.resolveSibling("module.ready");
        Files.write(pendingSeal, Arrays.asList(PHONE_FORMAT, RomImport.SHA256, RomImport.hash(builtLibrary),
                BuildConfig.SETUP_CAPSULE_SHA256), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        try (FileChannel file = FileChannel.open(pendingSeal, StandardOpenOption.WRITE)) {
            file.force(true);
        }
        Files.deleteIfExists(seal);
        Files.move(builtLibrary, slot.resolve("libmain.so"), StandardCopyOption.ATOMIC_MOVE,
                StandardCopyOption.REPLACE_EXISTING);
        Files.move(pendingSeal, seal, StandardCopyOption.ATOMIC_MOVE);
    }

    private static void validateElf(Path library) throws IOException {
        if (!Files.isRegularFile(library, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("The setup tools did not produce a native game module.");
        }
        long size = Files.size(library);
        if (size < 64 || size > MAX_BYTES) throw new IOException("The private native module is incomplete.");
        byte[] ident = new byte[64];
        try (InputStream in = Files.newInputStream(library)) {
            int offset = 0;
            while (offset < ident.length) {
                int count = in.read(ident, offset, ident.length - offset);
                if (count < 0) throw new IOException("Truncated native module.");
                offset += count;
            }
        }
        ByteBuffer header = ByteBuffer.wrap(ident).order(ByteOrder.LITTLE_ENDIAN);
        if (ident[0] != 0x7f || ident[1] != 'E' || ident[2] != 'L' || ident[3] != 'F'
                || ident[4] != 2 || ident[5] != 1 || ident[6] != 1
                || header.getShort(16) != 3 || header.getShort(18) != 183) {
            throw new IOException("The private native module must be an ARM64 shared library.");
        }
    }
}
