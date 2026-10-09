"""Read-only preflight for the exact Secret of the Stars USA foundation.

Outputs metadata only. It never patches, extracts, or executes ROM code.
The known input is deliberately strict; patched images need a new recipe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

EXPECTED = {
    "size": 1572864,
    "crc32": "ef968ed1",
    "md5": "d26babb046182e3a564fb1bdddce7e42",
    "sha1": "958a0a835e2e39f382cb37a99098a3cdd4812cf7",
    "sha256": "7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600",
}

# Addresses identified by upstream hijacks.asm, not verified routine entries.
HOOKS = {
    "nmi_upload_site": 0x008366,
    "turn_reset_site": 0x029122,
    "battle_start_site": 0x0084A0,
    "damage_enemy_site": 0x00DCA4,
    "kill_enemy_site": 0x00DCAB,
    "every_frame_site": 0x1C8069,
}


def mirrored_sum(data: bytes) -> int:
    """Sum a non-power-of-two image as mirrored to its next power of two."""
    size = len(data)
    if not size:
        return 0
    prefix = 1 << (size.bit_length() - 1)
    total = sum(data[:prefix])
    tail = data[prefix:]
    if tail:
        tail_capacity = 1 << (len(tail) - 1).bit_length()
        total += mirrored_sum(tail) * (prefix // tail_capacity)
    return total & 0xFFFF


def lorom_offset(address: int) -> int:
    if address & 0xFFFF < 0x8000:
        raise ValueError("Not an upper-half standard LoROM address")
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def inspect(path: Path) -> dict:
    raw = path.read_bytes()
    copier = 512 if len(raw) % 0x8000 == 512 else 0
    data = raw[copier:]
    identity = {
        "size": len(data),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    matches = identity == EXPECTED
    result = {
        "schema_version": 1,
        "rom_file": path.name,
        "file_size": len(raw),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "copier_header_bytes": copier,
        "identity": identity,
        "matches_supported_clean_input": matches,
        "original_rechecked_unchanged": hashlib.sha256(path.read_bytes()).hexdigest()
        == hashlib.sha256(raw).hexdigest(),
        "scope": "Metadata and source-derived hook preflight; no gameplay verification",
    }
    if not matches:
        result["error"] = "Unsupported input; no game-specific header or hook interpretation performed"
        return result
    base = 0x7FC0
    u16 = lambda offset: struct.unpack_from("<H", data, base + offset)[0]
    checksum = u16(0x1E)
    result["header"] = {
        "offset": "0x007fc0",
        "title": data[base:base + 21].decode("ascii").rstrip(),
        "map_mode": f"0x{data[base + 0x15]:02x}",
        "mapping": "standard LoROM, SlowROM",
        "cartridge_type": f"0x{data[base + 0x16]:02x}",
        "cartridge": "ROM + RAM + battery; no enhancement chip indicated",
        "region": "USA / North America",
        "revision_byte": data[base + 0x1B],
        "declared_rom_capacity": 1024 << data[base + 0x17],
        "sram_size_bytes": 1024 << data[base + 0x18],
        "checksum": f"0x{checksum:04x}",
        "complement": f"0x{u16(0x1C):04x}",
        "checksum_pair_valid": checksum ^ u16(0x1C) == 0xFFFF,
        "computed_mirrored_checksum": f"0x{mirrored_sum(data):04x}",
        "computed_checksum_matches": mirrored_sum(data) == checksum,
        "reset_vector": f"0x{u16(0x3C):04x}",
        "native_nmi_vector": f"0x{u16(0x2A):04x}",
    }
    result["battle_info_source_preflight"] = {
        "revision": "650721747fd808daeb4e2a9745f16150b2d00c91",
        "hook_sites": [
            {"name": name, "guest_address": f"0x{addr:06x}",
             "rom_offset": f"0x{lorom_offset(addr):06x}",
             "inside_original": lorom_offset(addr) < len(data)}
            for name, addr in HOOKS.items()
        ],
        "new_code_guest_address": "0xb28000",
        "new_code_rom_offset": f"0x{lorom_offset(0xB28000):06x}",
        "new_code_outside_original": lorom_offset(0xB28000) >= len(data),
        "patched_size_and_identity": "Not yet built or measured",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--report", type=Path, help="Write metadata to a .json file")
    args = parser.parse_args()
    source = args.rom.resolve(strict=True)
    if args.report:
        output = args.report.resolve()
        if output == source or output.suffix.lower() != ".json":
            parser.error("Report must be a separate .json file")
    result = inspect(source)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.report:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    valid = result["matches_supported_clean_input"] and result["original_rechecked_unchanged"]
    if valid:
        valid = result["header"]["computed_checksum_matches"]
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
