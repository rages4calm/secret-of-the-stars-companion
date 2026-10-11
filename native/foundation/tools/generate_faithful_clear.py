"""Generate the bounded original-cost clear island from an owned, verified ROM.

Only the project's ignored src/gen header and its provenance are written. The
generated file contains ROM-derived translation and must not be redistributed.
"""
from pathlib import Path
import argparse, hashlib, json, os, uuid

ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
START = 0x01cb2e
MODULE = 'secret-of-the-stars-faithful-clear-v1'

def digest(data): return hashlib.sha256(data).hexdigest()

def reject_links(path):
    for item in [path, *path.parents]:
        if item.is_symlink() or (item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked path refused: ' + str(item))

def decode(data, start=START):
    nodes = []; offset = 0
    while offset < len(data):
        pc = start + offset; op = data[offset]
        if op == 0x8d:
            if offset + 3 > len(data): raise ValueError('Truncated STA absolute')
            operand = int.from_bytes(data[offset+1:offset+3], 'little')
            nodes.append(dict(pc=pc, mnemonic='STA', mode='absolute', length=3,
                              operand=operand, cycles_m0=5)); offset += 3
        elif op == 0x88:
            nodes.append(dict(pc=pc, mnemonic='DEY', mode='implied', length=1,
                              cycles_x0=2)); offset += 1
        elif op == 0xd0:
            if offset + 2 > len(data): raise ValueError('Truncated BNE relative')
            displacement = int.from_bytes(data[offset+1:offset+2], 'little', signed=True)
            target = (pc & 0xff0000) | ((pc + 2 + displacement) & 0xffff)
            nodes.append(dict(pc=pc, mnemonic='BNE', mode='relative', length=2,
                              target=target, cycles_not_taken=2, cycles_taken=3)); offset += 2
        else: raise ValueError(f'Unsupported bounded opcode {op:02X} at {pc:06X}')
    return nodes

def lower(nodes):
    if [(n['mnemonic'],n['pc']) for n in nodes] != [('STA', START), ('DEY', START+3), ('BNE', START+4)]:
        raise ValueError('Only the reviewed three-PC island is supported')
    if nodes[0]['operand'] != 0x2118 or nodes[2]['target'] != START:
        raise ValueError('Unreviewed destination or branch target')
    lines = ['/* ROM-DERIVED GENERATED OUTPUT. Do not publish. */',
             '/* M=0 X=0 native mode; exact context is owned by the entry adapter. */',
             'static int GeneratedClearSupports(uint32_t pc) {',
             '  switch (pc & 0x7fffff) {']
    for node in nodes: lines += [f"  case 0x{node['pc']:06x}: return 1;"]
    lines += ['  default: return 0;', '  }', '}',
              'static unsigned GeneratedClearStep(CpuState *cpu, uint32_t pc,',
              '                                   unsigned *cycles, uint32_t *next) {',
              '  switch (pc & 0x7fffff) {']
    for ordinal,node in enumerate(nodes):
        lines += [f"  case 0x{node['pc']:06x}: /* decoded {node['mnemonic']} {node['mode']} */"]
        for byte in range(node['length']):
            lines += [f'    (void)interp_bridge_native_read8(cpu, pc + {byte}u);']
        if node['mnemonic'] == 'STA':
            lines += [f"    interp_bridge_native_write16(cpu, ((uint32_t)cpu->DB << 16) | 0x{node['operand']:04x}u, cpu->A);",
                      f"    *cycles = {node['cycles_m0']}u; *next = pc + {node['length']}u;"]
        elif node['mnemonic'] == 'DEY':
            lines += ['    cpu->Y = (uint16_t)(cpu->Y - 1u);',
                      '    cpu->_flag_Z = cpu->Y == 0;',
                      '    cpu->_flag_N = (cpu->Y & 0x8000u) != 0;',
                      '    cpu_mirrors_to_p(cpu);',
                      f"    *cycles = {node['cycles_x0']}u; *next = pc + {node['length']}u;"]
        elif node['mnemonic'] == 'BNE':
            lines += [f"    *cycles = cpu->_flag_Z ? {node['cycles_not_taken']}u : {node['cycles_taken']}u;",
                      f"    *next = (pc & 0xff0000u) | (cpu->_flag_Z ? 0x{(node['pc']+node['length'])&0xffff:04x}u : 0x{node['target']&0xffff:04x}u);"]
        lines += [f'    return {ordinal}u;']
    lines += ['  default: abort(); /* entry adapter checked the exact PC */', '  }', '}', '']
    return '\n'.join(lines)

def atomic_write(path, data):
    reject_links(path)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        reject_links(path); os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()

def generate(rom, project_root, replace_owned=False):
    reject_links(project_root.absolute()); reject_links(rom.absolute())
    project = project_root.resolve(strict=True)
    identity_path = project / 'rom_identity.txt'; reject_links(identity_path)
    identity = {key.strip():value.strip().strip('"')
                for line in identity_path.read_text().splitlines()
                if '=' in line and not line.lstrip().startswith('#')
                for key,value in [line.split('=',1)]}
    image = rom.read_bytes()
    if identity.get('expected_sha256','').strip().lower() != ROM_SHA or len(image) != 1572864 or digest(image) != ROM_SHA:
        raise ValueError('Exact pinned unheadered clean USA ROM required')
    destination = project / 'src/gen'; reject_links(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if not destination.resolve().is_relative_to(project): raise ValueError('Generated path escapes project')
    header = destination / 'faithful_clear.generated.h'
    metadata = destination / 'faithful_clear.provenance.json'
    lock = destination / '.faithful-clear-generation.lock'; reject_links(lock)
    with lock.open('x'):
        pass
    try:
        reject_links(header); reject_links(metadata)
        previous = {path: path.read_bytes() if path.exists() else None for path in (header,metadata)}
        if any(data is not None for data in previous.values()):
            if not replace_owned or any(data is None for data in previous.values()):
                raise ValueError('Existing generated output refused; use --replace-owned only for a verified owned pair')
            old = json.loads(previous[metadata])
            if old.get('module') != MODULE or old.get('rom_sha256') != ROM_SHA or old.get('output_sha256') != digest(previous[header]):
                raise ValueError('Existing output is unrelated or modified; preserved')
        offset = ((START >> 16) & 0x7f)*0x8000 + (START & 0x7fff)
        if image[offset+6] != 0x60: raise ValueError('Original RTS tail changed')
        nodes = decode(image[offset:offset+6]); generated = lower(nodes).encode('ascii')
        provenance = {'module':MODULE,'format_version':1,'rom_sha256':digest(image),
            'generator_sha256':digest(Path(__file__).read_bytes()),'input_offset':offset,
            'instruction_bytes_sha256':digest(image[offset:offset+6]),'nodes':nodes,
            'output_sha256':digest(generated),'runtime_opcode_decode':False,
            'original_return_pc':'01CB34','timing':'Original instruction costs via faithful bridge transaction',
            'limits':'Three guarded M0/X0 instructions, interpreter entry boundary retained; not complete game AOT'}
        new_metadata = (json.dumps(provenance,indent=2)+'\n').encode('utf-8')
        written = {}
        try:
            for path,data in ((header,generated),(metadata,new_metadata)):
                atomic_write(path,data); written[path]=digest(data)
        except Exception:
            for path,known_digest in written.items():
                if path.exists() and digest(path.read_bytes()) == known_digest:
                    if previous[path] is None: path.unlink()
                    else: atomic_write(path,previous[path])
            raise
        return provenance
    finally:
        lock.unlink()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--replace-owned',action='store_true')
    args=parser.parse_args()
    print(json.dumps(generate(args.rom,args.project_root,args.replace_owned),indent=2))

if __name__=='__main__': main()
