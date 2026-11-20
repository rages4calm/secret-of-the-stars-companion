package org.secretstars.companion;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

final class RomImport {
    static final String SHA256 = "7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600";
    private static final int SIZE = 1_572_864;

    private RomImport() {}

    static MessageDigest newDigest() {
        try {
            return MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new AssertionError(e);
        }
    }

    static String hex(byte[] bytes) {
        char[] result = new char[bytes.length * 2];
        String digits = "0123456789abcdef";
        for (int i = 0; i < bytes.length; i++) {
            int b = bytes[i] & 255;
            result[2 * i] = digits.charAt(b >>> 4);
            result[2 * i + 1] = digits.charAt(b & 15);
        }
        return new String(result);
    }

    static String hash(Path file) throws IOException {
        MessageDigest digest = newDigest();
        try (InputStream in = Files.newInputStream(file)) {
            byte[] block = new byte[32 * 1024];
            for (int count; (count = in.read(block)) != -1;) {
                digest.update(block, 0, count);
            }
        }
        return hex(digest.digest());
    }

    static void verify(Path file) throws IOException {
        if (!Files.isRegularFile(file)) throw new IOException("Choose a ROM first.");
        if (Files.size(file) != SIZE || !SHA256.equals(hash(file))) {
            throw new IOException("Choose the clean, unheadered USA ROM.");
        }
    }

    static void save(InputStream source, Path destination) throws IOException {
        MessageDigest digest = newDigest();
        Path pending = Files.createTempFile(destination.getParent(), "rom-import-", ".tmp");
        try {
            int size = 0;
            try (OutputStream out = Files.newOutputStream(pending)) {
                byte[] block = new byte[16 * 1024];
                for (int count; (count = source.read(block)) != -1;) {
                    if (count > SIZE - size) throw new IOException("Choose the clean, unheadered USA ROM.");
                    size += count;
                    digest.update(block, 0, count);
                    out.write(block, 0, count);
                }
            }
            if (size != SIZE || !SHA256.equals(hex(digest.digest()))) {
                throw new IOException("Choose the clean, unheadered USA ROM.");
            }
            Files.move(pending, destination, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally {
            Files.deleteIfExists(pending);
        }
    }
}
