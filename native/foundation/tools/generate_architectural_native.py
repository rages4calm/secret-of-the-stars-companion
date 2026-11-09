"""Generate private architectural native C from the owner's clean USA ROM.

Inputs are an explicit ROM-free PC/M/X/E inventory and reviewed SDK text pins.
The ordinary frozen SNESRecomp output is neither read as code nor regenerated.
Unsupported semantics fail generation; this tool never substitutes replay/NOPs.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

POLICY='utf8-crlf-to-lf-only-v1'
ROM_SHA='7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600'
ROM_SIZE=1572864

def digest(data):return hashlib.sha256(data).hexdigest()

def text_digest(data):
    data.decode('utf-8')
    return digest(data.replace(b'\r\n',b'\n'))

def read_json(path):
    def pairs(items):
        value={}
        for k,v in items:
            if k in value:raise ValueError('Duplicate JSON key')
            value[k]=v
        return value
    def bad(value):raise ValueError('Non-finite JSON constant: '+value)
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,parse_constant=bad)

def relative_file(base,name):
    if not isinstance(name,str):raise ValueError('Expected a relative source path')
    p=Path(name)
    if p.is_absolute()or '..'in p.parts or not p.parts:
        raise ValueError('Expected a relative source path')
    return base/p

def checked_inputs(rom_path,sdk,manifest_path,keys_path=None):
    manifest=read_json(manifest_path)
    if manifest.get('schema')!=1 or manifest.get('abi')!='native-blocks69' or manifest.get('text_pin_policy')!=POLICY:
        raise ValueError('Unknown architectural native manifest/ABI/text policy')
    if manifest.get('original_rom_sha256')!=ROM_SHA or manifest.get('original_rom_size')!=ROM_SIZE:
        raise ValueError('Manifest does not identify the original Secret of the Stars USA ROM')
    rom=Path(rom_path).read_bytes()
    if len(rom)!=ROM_SIZE or digest(rom)!=ROM_SHA:raise ValueError('Expected the unmodified Secret of the Stars USA ROM')
    pins=manifest.get('sdk_files')
    if not isinstance(pins,dict)or not {'recompiler/v2/emit_native_blocks.py','runner/src/native_blocks.h'}<=set(pins):
        raise ValueError('Missing reviewed compiler/ABI pins')
    for name,expected in pins.items():
        path=relative_file(sdk,name)
        if text_digest(path.read_bytes())!=expected:raise ValueError('SDK source changed: '+name)
    key_path=Path(keys_path)if keys_path is not None else relative_file(Path(manifest_path).parent,manifest['keys_file'])
    if text_digest(key_path.read_bytes())!=manifest['keys_sha256']:raise ValueError('Architectural source keys changed')
    keys=read_json(key_path)
    if not isinstance(keys,list)or len(keys)!=manifest['key_count']:raise ValueError('Wrong source key count')
    for key in keys:
        if(not isinstance(key,list)or len(key)!=4 or any(type(v)is not int for v in key)
           or not 0<=key[0]<=0xffffff or any(v not in (0,1)for v in key[1:])
           or(key[3]and key[1:3]!=[1,1])):raise ValueError('Invalid PC/M/X/E key')
    if len({tuple(k)for k in keys})!=len(keys):raise ValueError('Duplicate architectural key')
    symbol=manifest.get('symbol');profile=manifest.get('profile')
    if not isinstance(symbol,str)or not re.fullmatch(r'[A-Za-z_]\w*',symbol):raise ValueError('Invalid program symbol')
    if type(profile)is not int or not 0<=profile<=0xffffffff:raise ValueError('Invalid source profile')
    return manifest,rom,keys,key_path

def generate(rom_path,sdk,manifest_path,output,keys_path=None,reuse_source=None,reuse_receipt=None):
    sdk=Path(sdk).resolve(strict=True);manifest_path=Path(manifest_path).resolve(strict=True);output=Path(output).absolute()
    if output.exists():raise ValueError('Fresh unique native output required')
    manifest,rom,keys,key_path=checked_inputs(rom_path,sdk,manifest_path,keys_path)
    reused=None
    generator_pin=text_digest(Path(__file__).read_bytes())
    if (reuse_source is None)!=(reuse_receipt is None):raise ValueError('Reuse requires both source and receipt')
    if reuse_source is not None:
        previous=read_json(reuse_receipt)
        expected={'schema':1,'status':'generated_private_architectural_native_unqualified','abi':'native-blocks69',
                  'original_rom_sha256':ROM_SHA,'manifest_normalized_sha256':text_digest(manifest_path.read_bytes()),
                  'keys_sha256':text_digest(key_path.read_bytes()),'key_count':len(keys),'symbol':manifest['symbol'],
                  'profile':manifest['profile'],'sdk_files':manifest['sdk_files'],'text_pin_policy':POLICY,
                  'generator_normalized_sha256':generator_pin,'generator_sha256':digest(Path(__file__).read_bytes()),'ordinary_generated_code_regenerated':False}
        for name,value in expected.items():
            if previous.get(name)!=value:raise ValueError('Reused generation binding differs: '+name)
        data=Path(reuse_source).read_bytes()
        if digest(data)!=previous.get('output_sha256'):raise ValueError('Reused native C changed')
        reused={'source':str(Path(reuse_source).resolve()),'source_sha256':digest(data),
                'receipt':str(Path(reuse_receipt).resolve()),'receipt_sha256':digest(Path(reuse_receipt).read_bytes())}
    else:
        # Import the exact reviewed compiler and its pinned existing modules.
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(sdk/'recompiler'))
        spec=importlib.util.spec_from_file_location('sots_arch_native_generator',sdk/'recompiler/v2/emit_native_blocks.py')
        compiler=importlib.util.module_from_spec(spec);sys.modules[spec.name]=compiler;spec.loader.exec_module(compiler)
        text=compiler.emit_native_blocks(rom,symbol=manifest['symbol'],profile=manifest['profile'],keys=keys,include_reset=False)
        data=text.encode('utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb')as stream:stream.write(data)
    receipt={'schema':1,'status':'generated_private_architectural_native_unqualified','abi':'native-blocks69',
             'original_rom_sha256':ROM_SHA,'manifest_sha256':digest(manifest_path.read_bytes()),
             'manifest_normalized_sha256':text_digest(manifest_path.read_bytes()),'keys_sha256':text_digest(key_path.read_bytes()),
             'key_count':len(keys),'symbol':manifest['symbol'],'profile':manifest['profile'],
             'sdk_files':manifest['sdk_files'],'generator_sha256':digest(Path(__file__).read_bytes()),'generator_normalized_sha256':generator_pin,'text_pin_policy':POLICY,'output':str(output),'output_sha256':digest(data),
             'ordinary_generated_code_regenerated':False,'native_execution_qualified':False,'native_AOT_complete':False,
             'scope':manifest['scope']}
    if reused is not None:receipt['reused_from']=reused
    report=output.parent/'architectural-native-generation.json'
    with report.open('x',encoding='utf-8')as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True,type=Path);p.add_argument('--sdk',required=True,type=Path)
    p.add_argument('--manifest',required=True,type=Path);p.add_argument('--keys',type=Path)
    p.add_argument('--reuse-source',type=Path);p.add_argument('--reuse-receipt',type=Path)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--output',type=Path);group.add_argument('--out-dir',type=Path)
    a=p.parse_args()
    try:
        output=a.output if a.output is not None else a.out_dir/relative_file(Path('.'),read_json(a.manifest)['output'])
        receipt=generate(a.rom,a.sdk,a.manifest,output,a.keys,a.reuse_source,a.reuse_receipt)
    except (OSError,ValueError,ImportError)as error:p.exit(1,'Native generation refused: '+str(error)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
