"""Private exact-ROM, observed-mode constructor lowering. ROM output is local.

No runtime opcode decoding, batching or host call into guest producers.
"""
from pathlib import Path
import argparse,hashlib,json,os,uuid
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
def sha(b):return hashlib.sha256(b).hexdigest()
# Exact bounded forms only: (name, mode, fixed length, base cycles).
OPS={0x8d:('STA','abs',3,4),0xe2:('SEP','imm',2,3),0xa9:('LDA','imm',0,2),0x9c:('STZ','abs',3,4),0xad:('LDA','abs',3,4),0xaa:('TAX','imp',1,2),0x4a:('LSR','acc',1,2),0xa8:('TAY','imp',1,2),0x99:('STA','aby',3,5),0xc2:('REP','imm',2,3),0x9d:('STA','abx',3,5),0x0b:('PHD','imp',1,4),0x48:('PHA','imp',1,3),0x2b:('PLD','imp',1,5),0x22:('JSL','long',4,8),0xbd:('LDA','abx',3,4),0x85:('STA','dp',2,3),0xae:('LDX','abs',3,4),0xa5:('LDA','dp',2,3),0xee:('INC','abs',3,6),0xc9:('CMP','imm',0,2),0xd0:('BNE','rel',2,2),0x6b:('RTL','imp',1,6),0x4c:('JMP','abs',3,3)}
def decode(rom,pc,m,x):
 off=(pc>>16&0x7f)*0x8000+(pc&0x7fff);op=rom[off]
 if op not in OPS:raise ValueError(f'Unsupported bounded opcode{op:02x} at{pc:06x}')
 name,mode,length,cost=OPS[op]
 if not length:length=2+(not m)
 data=rom[off:off+length]
 operand=int.from_bytes(data[1:],'little')if length>1 else 0
 return dict(pc=pc,m=m,x=x,opcode=op,name=name,mode=mode,length=length,operand=operand,cycles=cost,bytes=data.hex())
def lower(nodes):
 out=['/* ROM-DERIVED PRIVATE GENERATED OUTPUT: DO NOT PUBLISH */',
 'static void CZ(CpuState*c,unsigned v,int byte){c->_flag_Z=(v&(byte?255u:65535u))==0;c->_flag_N=(v&(byte?128u:32768u))!=0;cpu_mirrors_to_p(c);}',
 'static unsigned CR(CpuState*c,uint32_t a,int byte){unsigned l=interp_bridge_native_read8(c,a);return byte?l:l|((unsigned)interp_bridge_native_read8(c,(a+1u)&0xffffffu)<<8);}',
 'static void CP(CpuState*c,unsigned v){interp_bridge_native_write8(c,c->S,(uint8_t)v);--c->S;}',
 'static unsigned CL(CpuState*c){++c->S;return interp_bridge_native_read8(c,c->S);}',
 'static unsigned GeneratedConstructorStep(CpuState*c,uint32_t pc,unsigned*cycles,uint32_t*next){switch(pc){']
 # Per-PC machine code is static; width comes from the independently checked mode.
 for ordinal,n in enumerate(nodes):
  pc=n['pc'];name=n['name'];mode=n['mode'];value=n['operand'];length=n['length'];cost=n['cycles']
  out.append(f'case 0x{pc:06x}:{{ /* original decoded {name} {mode} */')
  for b in range(length):out.append(f'(void)interp_bridge_native_read8(c,pc+{b}u);')
  out.append(f'*cycles={cost}u;*next=pc+{length}u;')
  if mode in('abs','abx','aby')and name not in('JMP',):
   ix='c->X'if mode=='abx'else'c->Y'if mode=='aby'else'0u'
   out.append(f'uint32_t a=(((uint32_t)c->DB<<16)+0x{value:04x}u+{ix})&0xffffffu;')
  elif mode=='dp':out.append(f'uint32_t a=(c->D+0x{value:02x}u)&65535u;*cycles+=(c->D&255u)!=0;')
  if name in('LDA','LDX'):
   width='c->m_flag'if name=='LDA'else'c->x_flag';dest='A'if name=='LDA'else'X'
   if mode=='imm':out.append(f'unsigned v=0x{value:x}u;')
   else:out.append(f'unsigned v=CR(c,a,{width});')
   out.append(f'*cycles+=!{width};')
   if mode=='abx':out.append(f'*cycles+=!c->x_flag||((0x{value:04x}u>>8)!=((0x{value:04x}u+c->X)>>8));')
   if name=='LDA':out.append('c->A=c->m_flag?(c->A&0xff00u)|(v&255u):v;')
   else:out.append('c->X=c->x_flag?v&255u:v;')
   out.append(f'CZ(c,c->{dest},{width});')
  elif name in('STA','STZ'):
   out.append('*cycles+=!c->m_flag;')
   v='c->A'if name=='STA'else'0u'
   out.append(f'if(c->m_flag)interp_bridge_native_write8(c,a,(uint8_t){v});else interp_bridge_native_write16(c,a,{v});')
  elif name in('SEP','REP'):
   out.append(f'c->P {"|="if name=="SEP"else"&="} {f"0x{value:02x}u"if name=="SEP"else f"(uint8_t)~0x{value:02x}u"};cpu_p_to_mirrors(c);if(c->x_flag){{c->X&=255u;c->Y&=255u;}}')
  elif name in('TAX','TAY'):
   dest='X'if name=='TAX'else'Y';out.append(f'c->{dest}=c->x_flag?c->A&255u:c->A;CZ(c,c->{dest},c->x_flag);')
  elif name=='LSR':out.append('unsigned v=c->A;c->_flag_C=v&1u;if(c->m_flag)c->A=(v&0xff00u)|((v&255u)>>1);else c->A=v>>1;CZ(c,c->A,c->m_flag);')
  elif name=='PHD':out.append('CP(c,c->D>>8);CP(c,c->D);')
  elif name=='PHA':out.append('*cycles+=!c->m_flag;if(!c->m_flag)CP(c,c->A>>8);CP(c,c->A);')
  elif name=='PLD':out.append('unsigned l=CL(c),h=CL(c);c->D=l|(h<<8);CZ(c,c->D,0);')
  elif name=='JSL':out.append(f'CP(c,c->PB);CP(c,0x{((pc+length-1)>>8)&255:02x}u);CP(c,0x{(pc+length-1)&255:02x}u);*next=0x{value:06x}u;')
  elif name=='RTL':out.append('unsigned l=CL(c),h=CL(c),b=CL(c);*next=(b<<16)|((l|(h<<8))+1u)&65535u;')
  elif name=='JMP':out.append(f'*next=(pc&0xff0000u)|0x{value:04x}u;')
  elif name=='INC':out.append('unsigned v=CR(c,a,c->m_flag)+1u;if(c->m_flag)interp_bridge_native_write8(c,a,v);else{*cycles+=2;interp_bridge_native_write8(c,(a+1u)&0xffffffu,v>>8);interp_bridge_native_write8(c,a,v);}CZ(c,v,c->m_flag);')
  elif name=='CMP':out.append(f'unsigned v=c->m_flag?c->A&255u:c->A;*cycles+=!c->m_flag;c->_flag_C=v>=0x{value:x}u;CZ(c,v-0x{value:x}u,c->m_flag);')
  elif name=='BNE':
   disp=value-256 if value>=128 else value;target=(pc&0xff0000)|((pc+2+disp)&65535)
   out.append(f'if(!c->_flag_Z){{++*cycles;*next=0x{target:06x}u;}}')
  else:raise ValueError(name)
  out.append(f'return {ordinal}u;}}')
 out.extend(['default:abort();}}',''])
 return '\n'.join(out)
def links(p):
 for q in[p,*p.parents]:
  try:stat=q.lstat()
  except FileNotFoundError:continue
  if q.is_symlink()or getattr(stat,'st_file_attributes',0)&0x400:raise ValueError('Linked path refused')

MODULE='secret-of-the-stars-faithful-constructor-v1'

def atomic_write(path,data):
 links(path)
 temporary=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  with temporary.open('xb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
  links(path);os.replace(temporary,path)
 finally:
  if temporary.exists():temporary.unlink()

def generate(rom_path,project_root,replace_owned=False):
 links(rom_path.absolute());links(project_root.absolute())
 project=project_root.resolve(strict=True);identity=project/'rom_identity.txt';links(identity)
 fields={key.strip():value.strip().strip('"')for line in identity.read_text().splitlines()if '='in line and not line.lstrip().startswith('#')for key,value in[line.split('=',1)]}
 rom=rom_path.read_bytes()
 if fields.get('expected_sha256','').lower()!=ROM_SHA or len(rom)!=1572864 or sha(rom)!=ROM_SHA:raise ValueError('Exact pinned unheadered clean USA ROM required')
 out=project/'src/gen';links(out);out.mkdir(parents=True,exist_ok=True)
 if not out.resolve().is_relative_to(project):raise ValueError('Generated path escapes project')
 modes={};work=[(0x01d080,1,1),(0x01c403,1,1),(0x01c6fa,1,1),(0x01c7af,1,1)];seen=set();nodes={}
 while work:
  pc,m,x=work.pop()
  if(pc,m,x)in seen:continue
  if not(0x1d080<=pc<=0x1d106 or pc in(0x1c403,0x1c6fa,0x1c7af)):continue
  seen.add((pc,m,x));n=decode(rom,pc,m,x);nodes[pc]=n;modes.setdefault(pc,[]).append([m,x]);nextpc=pc+n['length']
  if n['name']=='RTL':continue
  if n['name']=='JMP':work.append(((pc&0xff0000)|n['operand'],m,x));continue
  if n['name']=='BNE':
   d=n['operand'];d=d-256 if d>=128 else d;work.append(((pc&0xff0000)|((pc+2+d)&65535),m,x))
  if n['name']in('SEP','REP'):
   if n['operand']&32:m=int(n['name']=='SEP')
   if n['operand']&16:x=int(n['name']=='SEP')
  if pc==0x1d0b6:m,x=1,0
  if pc==0x1d0d4:m,x=0,1
  if pc in(0x1c6fa,0x1c7af):work.append((0x1c403,m,x));continue
  work.append((nextpc,m,x))
 if len(nodes)!=60 or len(seen)!=62 or nodes[0x1d106]['name']!='RTL':raise ValueError('Unreviewed constructor graph')
 instructions=[nodes[k]for k in sorted(nodes)]
 for pc in modes:
  if len({decode(rom,pc,m,x)['length']for m,x in modes[pc]})!=1:raise ValueError('Ambiguous immediate width')
 generated=lower(instructions).encode('ascii')
 sites=sorted(set(nodes)|{0x1c6fe,0x1c7b3,0x1b006,0x1b1d6,0xff35,0x861d})
 sites_data=('/* Private ROM-derived sites: do not publish. */\nstatic const uint32_t ConstructorSites[]={'+','.join(hex(p)for p in sites)+'};\n').encode('ascii')
 header=out/'constructor.generated.h';site_header=out/'constructor_sites.generated.h';metadata=out/'constructor.provenance.json';paths=(header,site_header,metadata)
 lock=out/'.constructor-generation.lock';links(lock)
 with lock.open('x'):pass
 try:
  for path in paths:links(path)
  previous={path:path.read_bytes()if path.exists()else None for path in paths}
  if any(v is not None for v in previous.values()):
   if not replace_owned or any(v is None for v in previous.values()):raise ValueError('Existing output refused; verified owned complete trio required')
   old=json.loads(previous[metadata])
   if old.get('module')!=MODULE or old.get('rom_sha256')!=ROM_SHA or old.get('output_sha256')!=sha(previous[header])or old.get('sites_sha256')!=sha(previous[site_header]):raise ValueError('Unrelated or modified output preserved')
  proof={'module':MODULE,'format_version':1,'rom_sha256':sha(rom),'generator_sha256':sha(Path(__file__).read_bytes()),'output_sha256':sha(generated),'sites_sha256':sha(sites_data),'nodes':instructions,'modes':modes,'entry_pcs':sites,'runtime_opcode_decode':False,'callee_exit_authority':{'01D0B6_to_01B006':[1,0],'01D0D4_to_00FF35':[0,1]},'instruction_bytes_sha256':sha(b''.join(bytes.fromhex(n['bytes'])for n in instructions)),'scope':'Outer constructor60PCs/62modes only; original producer/coordinate remain interpreted; original instruction cost and scheduler boundary'}
  data=(json.dumps(proof,indent=2)+'\n').encode('utf-8');written={}
  try:
   for path,value in[(header,generated),(site_header,sites_data),(metadata,data)]:
    atomic_write(path,value);written[path]=sha(value)
  except Exception:
   for path,known in written.items():
    if path.exists()and sha(path.read_bytes())==known:
     if previous[path]is None:path.unlink()
     else:atomic_write(path,previous[path])
   raise
  return proof
 finally:lock.unlink()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--project-root',type=Path,required=True);p.add_argument('--replace-owned',action='store_true');a=p.parse_args()
 print(json.dumps(generate(a.rom,a.project_root,a.replace_owned),indent=2))
if __name__=='__main__':main()
