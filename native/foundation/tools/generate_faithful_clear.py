"""Generate the bounded original-cost clear island from an owned, verified ROM.

Only the project's ignored src/gen header and its provenance are written. The
generated file contains ROM-derived translation and must not be redistributed.
"""
from pathlib import Path
import argparse, hashlib, json, os, uuid

ROM_SHA = '7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
START = 0x01cb2e
MODULE = 'secret-of-the-stars-faithful-clear-v2'
ROUTINE_START=0x01cb19
ROUTINE_CALL=0x01c45e

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

def decode_routine(data,start=ROUTINE_START,m=1,x=1):
    result=[];offset=0
    while offset<len(data):
        pc=start+offset;op=data[offset];before=(m,x)
        if op in (0xe2,0xc2):
            length=2;name='SEP' if op==0xe2 else 'REP';mode='status';cycles=3
        elif op in (0xa9,0xa0):
            length=2+(not (m if op==0xa9 else x));name='LDA' if op==0xa9 else 'LDY';mode='immediate';cycles=length
        elif op==0x8d: length=3;name='STA';mode='absolute';cycles=4+(not m)
        elif op==0x88: length=1;name='DEY';mode='implied';cycles=2
        elif op==0xd0: length=2;name='BNE';mode='relative';cycles=2
        elif op==0x60: length=1;name='RTS';mode='implied';cycles=6
        elif op==0x20: length=3;name='JSR';mode='absolute';cycles=6
        else: raise ValueError(f'Unsupported opcode {op:02X} at {pc:06X}')
        if offset+length>len(data): raise ValueError('Truncated '+name)
        node=dict(pc=pc,opcode=op,mnemonic=name,mode=mode,length=length,m=before[0],x=before[1],cycles=cycles)
        if length>1: node['operand']=int.from_bytes(data[offset+1:offset+length],'little')
        if op==0xd0:
            node['target']=(pc&0xff0000)|((pc+2+int.from_bytes(data[offset+1:offset+2],'little',signed=True))&0xffff)
        if op in (0xe2,0xc2):
            mask=node['operand']
            if mask&0x20:m=int(op==0xe2)
            if mask&0x10:x=int(op==0xe2)
        node['m_after']=m;node['x_after']=x
        result.append(node);offset+=length
    return result

def lower_routine(nodes):
    reviewed=[(0x01c45e,'JSR',0xcb19),(0x01cb19,'SEP',0x20),(0x01cb1b,'LDA',0x80),
      (0x01cb1d,'STA',0x2115),(0x01cb20,'REP',0x30),(0x01cb22,'LDY',0x1800),
      (0x01cb25,'LDA',0x4800),(0x01cb28,'STA',0x2116),(0x01cb2b,'LDA',0),
      (0x01cb2e,'STA',0x2118),(0x01cb31,'DEY',None),(0x01cb32,'BNE',0xfa),(0x01cb34,'RTS',None)]
    if [(n['pc'],n['mnemonic'],n.get('operand')) for n in nodes]!=reviewed or nodes[-2]['target']!=0x01cb2e:
        raise ValueError('Unreviewed routine/control graph')
    if [(n['m'],n['x']) for n in nodes] != [(1,1)]*5+[(0,0)]*8:
        raise ValueError('Unreviewed mode variants')
    out=['/* PRIVATE ROM-DERIVED GENERATED OUTPUT: DO NOT PUBLISH. */',
      'static const uint32_t GeneratedRoutinePCs[13] = {'+','.join(f"0x{n['pc']:06x}u" for n in nodes)+'};',
      'static unsigned GeneratedRoutineStep(CpuState *cpu, uint32_t pc, unsigned *cycles, uint32_t *next) {',
      ' switch (pc & 0x7fffffu) {']
    for i,n in enumerate(nodes):
        out += [f" case 0x{n['pc']:06x}: /* decoded {n['mnemonic']} M{n['m']}X{n['x']} */",' {']
        for byte in range(n['length']):out += [f'  (void)interp_bridge_native_read8(cpu, pc+{byte}u);']
        name=n['mnemonic'];operand=n.get('operand');nextpc=(n['pc']+n['length'])&0xffff
        if name in ('REP','SEP'):
            out += [f"  cpu->P {('&= (uint8_t)~' if name=='REP' else '|= ')}0x{operand:02x}u;",
              '  cpu_p_to_mirrors(cpu);','  if (cpu->x_flag) { cpu->X &= 255u; cpu->Y &= 255u; }']
        elif name in ('LDA','LDY'):
            reg='A' if name=='LDA' else 'Y';width8=n['m'] if name=='LDA' else n['x']
            if width8 and name=='LDA':out += [f'  cpu->A = (cpu->A & 0xff00u) | 0x{operand:02x}u;']
            else:out += [f'  cpu->{reg} = 0x{operand:04x}u;']
            out += [f'  cpu->_flag_Z = 0x{operand:x}u == 0;',f'  cpu->_flag_N = (0x{operand:x}u & 0x{(0x80 if width8 else 0x8000):x}u) != 0;','  cpu_mirrors_to_p(cpu);']
        elif name=='STA':
            fn='interp_bridge_native_write8' if n['m'] else 'interp_bridge_native_write16'
            out += [f'  {fn}(cpu, ((uint32_t)cpu->DB << 16) | 0x{operand:04x}u, cpu->A);']
        elif name=='DEY':
            out += ['  cpu->Y = (uint16_t)(cpu->Y-1u);','  cpu->_flag_Z = cpu->Y == 0;','  cpu->_flag_N = (cpu->Y & 0x8000u) != 0;','  cpu_mirrors_to_p(cpu);']
        elif name=='JSR':
            ret=nextpc-1
            out += [f'  interp_bridge_native_write8(cpu, cpu->S, 0x{ret>>8:02x}u);','  --cpu->S;',
              f'  interp_bridge_native_write8(cpu, cpu->S, 0x{ret&255:02x}u);','  --cpu->S;']
            nextpc=operand
        elif name=='RTS':
            out += ['  ++cpu->S; unsigned low = interp_bridge_native_read8(cpu, cpu->S);',
              '  ++cpu->S; unsigned high = interp_bridge_native_read8(cpu, cpu->S);',
              '  *next = (pc & 0xff0000u) | ((low | (high << 8)) + 1u);']
        if name=='BNE':
            out += [f"  *cycles = cpu->_flag_Z ? 2u : 3u; *next = (pc & 0xff0000u) | (cpu->_flag_Z ? 0x{nextpc:04x}u : 0x{n['target']&65535:04x}u);"]
        else:
            out += [f"  *cycles = {n['cycles']}u;"]
            if name!='RTS':out += [f'  *next = (pc & 0xff0000u) | 0x{nextpc:04x}u;']
        out += [f'  return {i}u;',' }']
    out += [' default: abort();',' }','}','']
    return '\n'.join(out)

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
            if old.get('module') not in (MODULE,'secret-of-the-stars-faithful-clear-v1') or old.get('rom_sha256') != ROM_SHA or old.get('output_sha256') != digest(previous[header]):
                raise ValueError('Existing output is unrelated or modified; preserved')
        offset = ((START >> 16) & 0x7f)*0x8000 + (START & 0x7fff)
        if image[offset+6] != 0x60: raise ValueError('Original RTS tail changed')
        legacy_nodes = decode(image[offset:offset+6])
        nodes=decode_routine(image[0xc45e:0xc461],ROUTINE_CALL)+decode_routine(image[0xcb19:0xcb35])
        generated=(lower(legacy_nodes)+lower_routine(nodes)).encode('ascii')
        provenance = {'module':MODULE,'format_version':2,'rom_sha256':digest(image),
            'generator_sha256':digest(Path(__file__).read_bytes()),'input_offset':offset,
            'instruction_bytes_sha256':digest(image[0xc45e:0xc461]+image[0xcb19:0xcb35]),'nodes':nodes,'legacy_nodes':legacy_nodes,
            'input_ranges':[[0xc45e,0xc461],[0xcb19,0xcb35]],
            'output_sha256':digest(generated),'runtime_opcode_decode':False,
            'return_instruction_pc':'01CB34','verified_return_target':'01C461','return_generated':True,'timing':'Original instruction costs via faithful bridge transaction',
            'limits':'Complete guarded CB19-CB34 routine and C45E caller; original scheduler frontend retained, explicit three-PC legacy variant available; not complete game AOT'}
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
