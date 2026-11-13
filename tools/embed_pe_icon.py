"""Append authored Windows icon resources without relocating existing PE bytes.

This is a packaging operation, not a native compilation or gameplay qualification.
The input must be an unsigned AMD64 PE32+ executable without resources and with
40 unused zero bytes for another section header. Existing sections, COFF symbols,
string table and overlay retain their original file offsets and bytes. Only an
explicit header allowlist changes. Input and icon files are never modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import struct


def sha(data):
    return hashlib.sha256(data).hexdigest()


def align(value, boundary):
    if boundary <= 0 or boundary & (boundary - 1):
        raise ValueError('PE alignment must be a positive power of two')
    return (value + boundary - 1) & ~(boundary - 1)


def same_path(a, b):
    return os.path.normcase(str(a.resolve())) == os.path.normcase(str(b.resolve()))


def u32(data, at):
    if not 0 <= at <= len(data) - 4:
        raise ValueError('Truncated PE integer')
    return struct.unpack_from('<I', data, at)[0]


def inspect_pe(data):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('Expected a PE executable')
    pe = u32(data, 60)
    if pe + 24 > len(data) or data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('Missing PE signature')
    machine, count, stamp, symbols, nsymbols, optional_size, flags = struct.unpack_from('<HHIIIHH', data, pe + 4)
    optional = pe + 24
    if machine != 0x8664 or optional_size < 152 or optional + optional_size > len(data):
        raise ValueError('Only complete AMD64 PE32+ headers are supported')
    if struct.unpack_from('<H', data, optional)[0] != 0x20b:
        raise ValueError('Expected PE32+')
    if count < 1 or count >= 96:
        raise ValueError('Invalid or excessive section count')
    if u32(data, optional + 108) < 5:
        raise ValueError('Resource and security data directories are required')
    resource = struct.unpack_from('<II', data, optional + 128)
    security = struct.unpack_from('<II', data, optional + 144)
    if resource != (0, 0):
        raise ValueError('Existing resources are refused; preserve the original resource owner')
    if security != (0, 0):
        raise ValueError('Signed executable refused; resource edits invalidate its signature')
    table = optional + optional_size
    end = table + count * 40
    header_size = u32(data, optional + 60)
    if end > len(data):
        raise ValueError('Truncated section table')
    sections = []
    for i in range(count):
        at = table + 40 * i
        name, virtual_size, rva, raw_size, raw_offset, reloc, lines, nreloc, nlines, characteristics = struct.unpack_from('<8sIIIIIIHHI', data, at)
        if raw_size and (raw_offset < header_size or raw_offset + raw_size > len(data)):
            raise ValueError('Existing section raw range is invalid')
        if name.rstrip(b'\0') == b'.rsrc':
            raise ValueError('An existing .rsrc section is refused')
        sections.append(dict(index=i, header_offset=at, name=name.rstrip(b'\0').decode('ascii', errors='replace'),
                             virtual_size=virtual_size, rva=rva, raw_size=raw_size, raw_offset=raw_offset,
                             header_bytes=data[at:at + 40]))
    first_raw = min(s['raw_offset'] for s in sections if s['raw_size'])
    if end + 40 > min(header_size, first_raw, len(data)):
        raise ValueError('No unused 40-byte section-header slot; original file preserved')
    if any(data[end:end + 40]):
        raise ValueError('New section-header slot is not zero padding')
    if bool(symbols) != bool(nsymbols):
        raise ValueError('Inconsistent COFF symbol table metadata')
    coff_end = symbols
    if symbols:
        string_start = symbols + nsymbols * 18
        string_size = u32(data, string_start)
        coff_end = string_start + string_size
        if string_size < 4 or coff_end > len(data):
            raise ValueError('Truncated COFF symbol/string table')
    return dict(pe=pe, optional=optional, count=count, table=table, header_end=end,
                header_size=header_size, first_raw=first_raw, sections=sections,
                symbols=symbols, nsymbols=nsymbols, coff_end=coff_end,
                section_alignment=u32(data, optional + 32), file_alignment=u32(data, optional + 36),
                size_image=u32(data, optional + 56), initialized_size=u32(data, optional + 8))


def read_ico(data):
    if len(data) < 6:
        raise ValueError('Truncated ICO')
    reserved, kind, count = struct.unpack_from('<HHH', data)
    if reserved or kind != 1 or not 1 <= count <= 256 or len(data) < 6 + 16 * count:
        raise ValueError('Expected a bounded Windows ICO image directory')
    entries = []
    for i in range(count):
        w, h, colors, unused, planes, bits, size, offset = struct.unpack_from('<BBBBHHII', data, 6 + 16 * i)
        if unused or not size or offset < 6 + 16 * count or offset + size > len(data):
            raise ValueError('Invalid ICO image range')
        entries.append(dict(width=w, height=h, colors=colors, planes=planes, bits=bits,
                            image=data[offset:offset + size]))
    return entries


def make_resources(entries, rva):
    blob = bytearray()

    def reserve(size, alignment=4):
        at = align(len(blob), alignment)
        blob.extend(b'\0' * (at + size - len(blob)))
        return at

    def directory(count):
        at = reserve(16 + count * 8)
        struct.pack_into('<IIHHHH', blob, at, 0, 0, 0, 0, 0, count)
        return at

    def item(at, index, ident, child, is_directory):
        struct.pack_into('<II', blob, at + 16 + index * 8, ident,
                         child | (0x80000000 if is_directory else 0))

    root = directory(2)
    icons = directory(len(entries))
    groups = directory(1)
    icon_ids = [directory(1) for _ in entries]
    group_id = directory(1)
    image_data_entries = [reserve(16) for _ in entries]
    group_data_entry = reserve(16)
    item(root, 0, 3, icons, True)
    item(root, 1, 14, groups, True)
    for i, image_dir in enumerate(icon_ids):
        item(icons, i, i + 1, image_dir, True)
        item(image_dir, 0, 1033, image_data_entries[i], False)
    item(groups, 0, 1, group_id, True)
    item(group_id, 0, 1033, group_data_entry, False)
    group = bytearray(struct.pack('<HHH', 0, 1, len(entries)))
    for i, entry in enumerate(entries):
        image = entry['image']
        at = reserve(len(image))
        blob[at:at + len(image)] = image
        struct.pack_into('<IIII', blob, image_data_entries[i], rva + at, len(image), 0, 0)
        group.extend(struct.pack('<BBBBHHIH', entry['width'], entry['height'], entry['colors'], 0,
                                 entry['planes'], entry['bits'], len(image), i + 1))
    at = reserve(len(group))
    blob[at:at + len(group)] = group
    struct.pack_into('<IIII', blob, group_data_entry, rva + at, len(group), 0, 0)
    return bytes(blob)


def embed(original, icon):
    pe = inspect_pe(original)
    entries = read_ico(icon)
    old_end = max(s['rva'] + max(s['virtual_size'], s['raw_size']) for s in pe['sections'])
    rva = align(max(old_end, pe['size_image']), pe['section_alignment'])
    resource = make_resources(entries, rva)
    raw_offset = align(len(original), pe['file_alignment'])
    raw_size = align(len(resource), pe['file_alignment'])
    size_image = align(rva + len(resource), pe['section_alignment'])
    if max(raw_offset + raw_size, size_image, pe['initialized_size'] + raw_size) >= 2 ** 32:
        raise ValueError('Result exceeds PE32+ 32-bit section metadata bounds')
    result = bytearray(original)
    result.extend(b'\0' * (raw_offset - len(result)))
    result.extend(resource)
    result.extend(b'\0' * (raw_offset + raw_size - len(result)))
    o = pe['optional']
    edits = [(pe['pe'] + 6, 2, 'NumberOfSections'), (o + 8, 4, 'SizeOfInitializedData'),
             (o + 56, 4, 'SizeOfImage'), (o + 64, 4, 'CheckSum'),
             (o + 128, 8, 'ResourceDirectory'), (pe['header_end'], 40, 'NewSectionHeader')]
    struct.pack_into('<H', result, pe['pe'] + 6, pe['count'] + 1)
    struct.pack_into('<I', result, o + 8, pe['initialized_size'] + raw_size)
    struct.pack_into('<I', result, o + 56, size_image)
    struct.pack_into('<I', result, o + 64, 0)  # Optional for ordinary user-mode executables.
    struct.pack_into('<II', result, o + 128, rva, len(resource))
    struct.pack_into('<8sIIIIIIHHI', result, pe['header_end'], b'.rsrc\0\0\0', len(resource), rva,
                     raw_size, raw_offset, 0, 0, 0, 0, 0x40000040)
    # Restore the explicitly allowed old-header bytes and compare the entire old
    # file, including COFF/debug/overlay content. This fails on any other change.
    restored = bytearray(result[:len(original)])
    for at, size, name in edits:
        restored[at:at + size] = original[at:at + size]
    if bytes(restored) != original:
        raise ValueError('Unexpected change outside the header allowlist')
    section_proofs = []
    for s in pe['sections']:
        start, size, h = s['raw_offset'], s['raw_size'], s['header_offset']
        before, after = original[start:start + size], result[start:start + size]
        if before != after or result[h:h + 40] != s['header_bytes']:
            raise ValueError('An original section/header changed')
        section_proofs.append(dict(index=s['index'], name=s['name'], rva=s['rva'],
                                   raw_offset=start, raw_size=size, sha256=sha(before), unchanged=True))
    cs, ce = pe['symbols'], pe['coff_end']
    if result[cs:ce] != original[cs:ce] or result[pe['pe'] + 12:pe['pe'] + 20] != original[pe['pe'] + 12:pe['pe'] + 20]:
        raise ValueError('COFF metadata or symbol/string data changed')
    report = dict(status='resource_packaged_unqualified', operation='append_authored_icon_resources',
                  input_sha256=sha(original), icon_sha256=sha(icon), output_sha256=sha(result),
                  input_bytes=len(original), output_bytes=len(result), icon_image_count=len(entries),
                  icon_dimensions=[[e['width'] or 256, e['height'] or 256] for e in entries],
                  language=1033, group_id=1, resource_rva=rva, resource_raw_offset=raw_offset,
                  resource_virtual_size=len(resource), resource_raw_size=raw_size,
                  original_section_count=pe['count'], original_section_hashes=section_proofs,
                  original_file_outside_header_allowlist_unchanged=True,
                  changed_header_fields=[name for at, size, name in edits],
                  coff=dict(offset=cs, symbols=pe['nsymbols'], symbol_and_string_bytes=ce - cs,
                            sha256=sha(original[cs:ce]), unchanged=True),
                  original_resources_absent=True, input_authenticode_absent=True,
                  original_entrypoint_and_imports_unchanged=True,
                  native_code_recompiled=False, gameplay_qualification=False,
                  scope='Resource-only derivative. Original compilation/qualification receipts stay immutable; exact-artifact operation qualification is separate.')
    return bytes(result), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--icon', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    source, icon, destination = args.input.resolve(strict=True), args.icon.resolve(strict=True), args.output.resolve()
    receipt = (args.report or destination.with_suffix('.icon-receipt.json')).resolve()
    if any(same_path(destination, p) or same_path(receipt, p) for p in [source, icon]) or same_path(destination, receipt):
        raise ValueError('Source, icon, new output and new receipt paths must be distinct')
    if destination.exists() or receipt.exists():
        raise ValueError('Output or receipt already exists; nothing overwritten')
    if not destination.parent.is_dir() or not receipt.parent.is_dir():
        raise ValueError('Create the explicit output/receipt parent directories first')
    original, icon_bytes = source.read_bytes(), icon.read_bytes()
    result, report = embed(original, icon_bytes)
    report.update(input=str(source), icon=str(icon), output=str(destination))
    with destination.open('xb') as stream:
        stream.write(result)
    if sha(destination.read_bytes()) != report['output_sha256'] or source.read_bytes() != original or icon.read_bytes() != icon_bytes:
        raise ValueError('Post-write identity verification failed; preserve output unqualified')
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, struct.error) as error:
        raise SystemExit(str(error))
