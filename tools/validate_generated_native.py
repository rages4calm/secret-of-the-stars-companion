"""Validate current pinned native output without the historical format33 projection.

This reads actual generated output. It never supplies metadata to a source graph
factory, changes admission, or grants execution/campaign qualification.
"""
from pathlib import Path
import hashlib
import importlib
import json
import subprocess
import sys
from contextlib import redirect_stdout


FAMILIES = (
    'reviewed_original_task_child', 'reviewed_original_ff20_receiving_starts',
    'source_direct_call_return_instructions', 'source_direct_callee_instructions',
    'source_dynamic_P_boundaries', 'source_nested_direct_call_instructions',
    'source_nested_dynamic_P_frontier', 'source_architectural_return_steps',
    'source_direct_aftercall_closure', 'source_aftercall_dynamic_P_frontier',
    'source_program_direct_call_closure', 'source_program_dynamic_P_frontier',
    'source_program_architectural_frontier', 'source_program_dynamic_P_architectural_returns',
    'source_task_pure_architectural_instructions', 'source_ROM_stack_dispatch_pure_instructions',
    'source_task_graph_architectural_members', 'source_original_initial_task_instructions',
    'source_nested_initial_task_instructions', 'source_original_FF20_byte_dispatch_pure_instructions',
    'source_declared_wait_call_instructions', 'source_ROM_stack_terminal_tail_instructions',
    'source_ROM_stack_direct_call_prefix_instructions', 'source_ROM_stack_numeric_aftercall_instructions',
    'source_original_FF20_architectural_chain_instructions',
)
RECIPES = (
    'return_instruction_graphs', 'callee_instruction_graphs', 'mode_instruction_graphs',
    'nested_instruction_graphs', 'frontier_mode_instruction_graphs', 'return_step_graphs',
    'aftercall_graphs', 'aftercall_mode_graphs', 'program_call_graphs', 'program_mode_graphs',
    'architectural_frontier_graphs', 'program_return_graphs', 'rom_stack_dispatch_graphs',
    'task_architecture_graphs', 'task_member_graphs', 'initial_task_graphs',
    'nested_initial_task_graphs', 'ff20_byte_dispatch_graphs', 'declared_wait_call_source',
    'rom_stack_terminal_tail_source', 'rom_stack_direct_call_prefix_source',
    'rom_stack_numeric_aftercall_source', 'ff20_architectural_chain_source',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def key(row):
    return tuple(row[n] for n in ('pc24', 'm', 'x'))


def _validate_task_source(directory, rom, parsed, manifest, normal, enabled):
    """Re-derive only the bounded original task recipes, never the program."""
    task = importlib.import_module('v2.task_resume')
    instructions = importlib.import_module('v2.architecture_task_sources')
    members = importlib.import_module('v2.architecture_task_member_sources')
    selected = importlib.import_module('v2.task_selected_member_sources')
    calls = importlib.import_module('v2.task_selected_call_sources')
    parent = importlib.import_module('v2.task_parent_member_sources')
    declared = importlib.import_module('v2.architecture_declared_wait_call_sources')
    faithful = importlib.import_module('v2.faithful_prefix')
    importlib.import_module('v2.emit_function').set_faithful_prefix_contracts(
        faithful.prefix_contracts(manifest, parsed))
    instruction_view = instructions._new_task_view(rom, parsed, manifest)
    member_view = members._new_member_view(rom, parsed, manifest)
    selected_view = selected._new_selected_view(rom, parsed, manifest)
    call_view = calls._new_selected_call_view(rom, parsed, manifest)
    parent_view = parent._new_parent_view(rom, parsed, manifest)
    declared_view = declared._new_view(rom, parsed, 'selected')
    rows, recipe, graphs = task.derive(rom, parsed, _instruction_view=instruction_view,
        _member_view=member_view, _selected_view=selected_view, _selected_call_view=call_view,
        _parent_view=parent_view, _declared_call_views=(declared_view,))
    # append_original_prefixes precedes the architecture union in program_emit.
    # Its original ordinary input is recoverable exactly from actual added-key
    # membership; retain those real rows without synthesizing a legacy graph.
    added = {tuple(k) for family in normal['architecture_source_eligibility']['sources']
             for k in family['added']}
    ordinary = [r for r in normal['regions'] if key(r) not in added]
    rows, recipe = task.append_original_prefixes(rom, parsed, rows, recipe, ordinary)
    selected._seal_selected_view(selected_view, rom, parsed, manifest)
    selected_rows, selected_recipe = selected.derive(rom, parsed, selected_view, rows)
    calls._seal_selected_call_view(call_view, rom, parsed, manifest)
    call_rows, call_recipe = calls.derive(rom, parsed, call_view, rows, selected_rows,
                                        enable_native_call_prefix=enabled)
    call_rows, call_recipe = calls.append_declared_wait_calls(rom, parsed, declared_view,
        normal['regions'], call_rows, call_recipe, rows, selected_rows,
        enable_native_call_prefix=enabled)
    parent._seal_parent_view(parent_view, rom, parsed, manifest)
    parent_rows, parent_recipe = parent.derive(rom, parsed, parent_view,
                                              rows + selected_rows + call_rows)
    expected = {'format_version': 9, 'kind': 'source_selected_task_resume',
        'rom_sha256': hashlib.sha256(rom).hexdigest(),
        'recipe': {k: v for k, v in recipe.items() if k != 'spans'}, 'graphs': graphs, 'rows': rows,
        'selected_architectural_members': {'rows': selected_rows, 'recipe': selected_recipe},
        'selected_architectural_calls': {'rows': call_rows, 'recipe': call_recipe},
        'retained_parent_architectural_members': {'rows': parent_rows, 'recipe': parent_recipe}}
    actual = json.loads((directory / 'native_task_resume.json').read_bytes())
    # JSON round-trip converts source tuples exactly as the original writer.
    require(actual == json.loads(json.dumps(expected)),
            'Current task9 metadata differs from original bounded source recipes')
    code = (task.emit_source(rows, recipe) + selected.emit_source(selected_rows, rows) +
            calls.emit_source(call_rows, rows, selected_rows) +
            parent.emit_source(parent_rows, parent_recipe, rows + selected_rows + call_rows))
    require((directory / 'native_task_resume_v2.c').read_bytes() == code.encode('utf8'),
            'Current task9 C differs from canonical original owner-guarded emitters')
    count = len(rows) + len(selected_rows) + len(call_rows) + len(parent_rows)
    require(code.count('cpu_aot_begin_scheduler_region(') == count,
            'Actual task9 physical scheduler case count differs')
    return {'task_scheduler_mode_rows': count,
            'task_metadata_hash': digest(directory / 'native_task_resume.json'),
            'task_C_sha256': digest(directory / 'native_task_resume_v2.c'),
            'task_source_counts': {'original': len(rows), 'selected_noncall': len(selected_rows),
                                   'selected_call': len(call_rows), 'retained_parent': len(parent_rows)}}


def _validate(request):
    runtime = Path(request['runtime']).resolve(strict=True)
    directory = Path(request['directory']).resolve(strict=True)
    rom_path = Path(request['rom']).resolve(strict=True)
    sources = request['source_hashes']
    for name, expected in sources.items():
        path = runtime / name
        require(path.resolve().is_relative_to(runtime) and digest(path) == expected,
                'Pinned runtime source changed: ' + name)
    for name in ('native_regions', 'architecture_eligibility', 'emit_function', 'native_bootstrap', 'program_emit'):
        require('recompiler/v2/' + name + '.py' in sources, 'Missing canonical source pin: ' + name)
    cache = json.loads((directory / '.snesrecomp-cache.json').read_bytes())
    require(cache == request['cache'] and cache.get('format_version') == 59 and
            cache.get('module') == {'id': 'main', 'prefix': ''}, 'Current generation cache identity differs')
    for name, expected in cache['outputs'].items():
        path = directory / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and
                path.resolve().is_relative_to(directory) and digest(path) == expected,
                'Actual generated output/cache differs: ' + name)
    require(digest(rom_path) == request['rom_sha'], 'Actual ROM identity differs')
    rom = rom_path.read_bytes()
    value = json.loads((directory / 'native_regions.json').read_bytes())
    contracts = {
        'format_version': 44, 'kind': 'source_cfg_scheduler_instruction',
        'result_contract': 'full_pc24_transient_original_scheduler',
        'instruction_source': 'source_faithful_and_typed_architectural_before_activation_plumbing',
        'stack_control_contract': 'native-e0-typed-architectural-stack-v1',
        'mode_successors': True, 'mode_successor_contract': 'source-owned-live-mx-instruction-successors-v1',
        'direct_call_contract': 'source-direct-call-architectural-prefix-v1',
        'long_jump_contract': 'source-long-jump-architectural-prefix-v1',
        'indirect_control_contract': 'source-indirect-control-architectural-v1',
        'interrupt_return_contract': 'source-native-e0-interrupt-return-v1',
        'carry_emulation_exchange_contract': 'source-native-e0-carry-emulation-exchange-v1',
        'blockmove_contract': 'source-native-e0-blockmove-one-byte-v1',
        'stack_indirect_y_contract': 'native-e0-source-cached-stack-indirect-y-v1',
        'rom_sha256': request['rom_sha'],
    }
    require(all(value.get(k) == v for k, v in contracts.items()) and
            type(value.get('direct_call_prefix')) is bool and
            value['direct_call_prefix'] is request['direct_call_prefix'], 'Current normal metadata contracts differ')
    architecture = value['architecture_source_eligibility']
    require(set(architecture) == set(RECIPES) | {'contract', 'sources', 'ordinary_roots_added',
            'callee_exit_modes_added', 'task_ownership_changed'}, 'Unknown/missing architecture recipe')
    require(architecture['contract'] == 'source-reviewed-independent-instruction-union-v1' and
            all(architecture[k] is False for k in ('ordinary_roots_added', 'callee_exit_modes_added',
                                                  'task_ownership_changed')), 'Architecture ownership policy differs')
    families = architecture['sources']
    require(tuple(f.get('origin') for f in families) == FAMILIES, 'Current ordered25 source families differ')
    recipe_contracts = {
        'declared_wait_call_source': 'source-declared-wait-call-instruction-v1',
        'rom_stack_terminal_tail_source': 'source-ROM-word-terminal-stack-tail-v1',
        'rom_stack_direct_call_prefix_source': 'source-ROM-word-direct-call-prefix-v1',
        'rom_stack_numeric_aftercall_source': 'source-ROM-word-issued-call-numeric-aftercall-v1',
        'ff20_architectural_chain_source': 'source-original-FF20-PHP-call-live-P-architectural-chain-v1',
    }
    for name, contract in recipe_contracts.items():
        require(isinstance(architecture[name], dict) and architecture[name].get('contract') == contract,
                'Current source recipe contract differs: ' + name)
    def ownership_fences(item):
        if isinstance(item, dict):
            for name, child in item.items():
                if name in ('ordinary_roots_added', 'callee_exit_modes_added', 'task_ownership_changed',
                            'caller_owner_added', 'saved_history_exported', 'saved_P_history_exported',
                            'runtime_dispatch_changed', 'source_bound_changes', 'skipped_continuation_granted'):
                    require(child is False, 'Source recipe exported new authority: ' + name)
                ownership_fences(child)
        elif isinstance(item, list):
            for child in item:
                ownership_fences(child)
    ownership_fences(architecture)
    rows = value['regions']
    table = {key(row): row for row in rows}
    require(len(table) == len(rows) and bool(rows), 'Normal rows empty or duplicated')
    claimed = set()
    for family in families:
        added, reused = [tuple(k) for k in family['added']], [tuple(k) for k in family['reused']]
        require(family.get('refused') == [] and len(set(added)) == len(added) and
                len(set(reused)) == len(reused) and not set(added) & set(reused) and
                not claimed & set(added) and family['source_rows'] == len(added) + len(reused) and
                set(added + reused) <= table.keys(), 'Family source membership/accounting differs')
        claimed.update(added + reused)
    # A fresh isolated interpreter prevents another capture/runtime's v2 module
    # cache from supplying decoder, admission, collector or emitter authority.
    sys.path[:0] = [str(runtime / 'recompiler'), str(runtime / 'tools')]
    names = ('v2_analyze', 'snes65816', 'v2.emit_function', 'v2.native_regions',
             'v2.architecture_eligibility', 'v2.architecture_return_steps', 'v2.native_bootstrap',
             'v2.program_emit', 'v2.program_analysis')
    modules = {name: importlib.import_module(name) for name in names}
    for name, module in tuple(sys.modules.items()):
        if name == 'v2' or name.startswith('v2.') or name in names:
            require(Path(module.__file__).resolve().is_relative_to(runtime), 'Foreign canonical module: ' + name)
    parsed = modules['v2_analyze']._load_cfgs(Path(request['cfg_dir']))
    by_bank = {b: cfg for b, _p, cfg in parsed}
    require(len(by_bank) == len(parsed), 'Duplicate bank policies')
    program = modules['v2.program_emit']
    manifest = modules['v2.program_analysis'].ProgramManifest.from_dict(
        json.loads((directory / 'program_manifest.json').read_bytes()))
    entries, _emitted, _names, _cfgs = program.build_emission_entries(manifest, parsed)
    masks = [r for _b, _p, c in parsed for r in c.data_regions] + [
        (c.bank, a, b) for _bank, _p, c in parsed for a, b in c.authority_data + c.exclude_ranges]
    forced = {pc & 0x7fffff for _b, _p, c in parsed for pc in c.force_lle}
    independent = modules['v2.architecture_eligibility']
    emitter = modules['v2.emit_function'].emit_function
    decoder = modules['snes65816']
    for ident, row in sorted(table.items()):
        pc, m, x = ident
        require(type(pc) is int and type(m) is int and type(x) is int and
                m in (0, 1) and x in (0, 1) and
                pc & 65535 >= 0x8000 and pc >> 16 not in (0x7e, 0x7f), 'Unmapped/invalid typed row')
        cfg = program._cfg_for_bank(by_bank, pc >> 16)
        if cfg is None:
            # The original pinned program emitter deliberately passes None
            # for policy options when an ordinary manifest-emitted bank has
            # no authored cfg (e.g. bank1C). Authenticate that same ordinary
            # emission via its real manifest entries and cached C unit. Source
            # families still pass independent ROM/mask/body admission below.
            require(bool(entries.get(pc >> 16)) and
                    any(name.startswith(f'bank{pc >> 16:02x}') and name.endswith('_v2.c')
                        for name in cache['outputs']),
                    'Missing authored source-family or ordinary emission bank policy: ' + repr(ident))
        require(not independent._mask(parsed, pc, row['length']), 'Masked native row: ' + repr(ident))
        admission_row = row
        if row['mnemonic'] in ('RTS', 'RTL') and 'source_return_contract' not in row:
            # merge_source_union preserves an already-existing ordinary row.
            # Its optional metadata tag is absent even when a source-return
            # family reuses the identical FIELDS/body. Validate the ordered
            # original pop architecture explicitly; do not modify actual rows.
            returns = modules['v2.architecture_return_steps']
            admission_row = dict(row, source_return_contract=returns.SOURCE_RETURN_CONTRACT)
            require(returns.validate_return(rom, parsed, admission_row),
                    'Original untagged return architecture differs: ' + repr(ident))
        if ident in claimed:
            require(independent._independent(rom, parsed, admission_row),
                    'Source-union instruction is not architecture-independent: ' + repr(ident))
        offset = decoder.rom_offset(pc >> 16, pc & 65535)
        ins = decoder.decode_insn(rom, offset, pc & 65535, pc >> 16, m, x)
        require(ins is not None and ins.length == row['length'] and ins.mnem == row['mnemonic'] and
                rom[offset:offset+ins.length].hex() == row['bytes'], 'Original typed ROM decode differs')
        probe = dict(row)
        if 'source_return_contract' in probe:
            require(modules['v2.architecture_return_steps'].validate_return(rom, parsed, row),
                    'Source return architecture differs: ' + repr(ident))
            probe.pop('source_return_contract')
        local, calls = [], []
        emitter(rom, pc >> 16, pc & 65535, m, x, func_name='DiscardedCanonicalNativeValidation',
                data_regions=masks, exclude_ranges=getattr(cfg, 'exclude_ranges', None),
                hle_func=getattr(cfg, 'hle_func', None), hle_spc_upload=getattr(cfg, 'hle_spc_upload', None),
                hle_dispatch=getattr(cfg, 'hle_dispatch', None),
                native_call_prefix_forced=forced, native_region_collector=local,
                native_call_prefix_collector=calls, _native_instruction_members=frozenset({pc}),
                _native_collector_only=True)
        require(any(candidate == probe for candidate in local + calls),
                'Current row differs from canonical original typed instruction: ' + repr(ident))
    bootstrap = modules['v2.native_bootstrap'].derive(rom, parsed)
    require(value['reset_bootstrap'] == bootstrap, 'Original source reset bootstrap differs')
    code = modules['v2.native_regions'].emit(rows, bootstrap=bootstrap) + independent.emit_membership(architecture)
    require((directory / 'native_regions_v2.c').read_bytes() == code.encode('utf8'),
            'Actual normal C differs from canonical rows/bootstrap/membership emitter')
    task_report = _validate_task_source(directory, rom, parsed, manifest, value,
                                        request['direct_call_prefix'])
    for name, expected in sources.items():
        require(digest(runtime / name) == expected, 'Pinned runtime changed during validation: ' + name)
    report = {'status': 'CURRENT44_SOURCE_POPULATION_VALIDATED_PRECOMPILE', 'metadata_format': 44,
            'families': len(families), 'normal_rows': len(rows), 'separate_e1_rows': len(bootstrap['rows']),
            'normal_metadata_sha256': digest(directory / 'native_regions.json'),
            'normal_C_sha256': digest(directory / 'native_regions_v2.c'),
            'canonical_per_instruction_checks': len(rows), 'exact_emitted_C': True,
            'ordinary_roots_added': False, 'execution_qualified': False}
    report['reset_bootstrap_generation'] = {'metadata_format': 44, 'separate_e1_rows': len(bootstrap['rows']),
                                          'declared_entry': bootstrap['entry'], 'ordinary_roots_added': False,
                                          'execution_qualified': False}
    call_rows = [r for r in rows if r['mnemonic'] in ('JSR', 'JSL')]
    report['direct_call_prefix_generation'] = {'metadata_format': 44, 'call_mode_rows': len(call_rows),
        'call_distinct_pcs': len({r['pc24'] for r in call_rows}), 'default_enabled': value['direct_call_prefix'],
        'closed_call_authority': False, 'execution_qualified': False}
    report['indirect_y_generation'] = {'metadata_format': 44, 'normal_rows': len(rows),
        'indirect_y_rows': sum(r.get('contract') == 'native-e0-source-cached-indirect-y-v1' for r in rows),
        'execution_qualified': False}
    report['stack_direct_generation'] = {'metadata_format': 44, 'normal_rows': len(rows),
        'stack_direct_rows': sum(r.get('contract') == 'native-e0-source-cached-stack-direct-v1' for r in rows),
        'stack_indirect_y_rows': sum(r.get('contract') == 'native-e0-source-cached-stack-indirect-y-v1' for r in rows),
        'execution_qualified': False}
    report.update(task_report)
    return report


def validate_current_outputs(directory, cache, rom, runtime, cfg_dir, direct_call_prefix=True, *, source_hashes=None):
    if source_hashes is None:
        # Compatibility with an already-running helper that has validated this
        # exact99 runtime before generation. New public callers pass their
        # independently verified source map explicitly. Never derive pins from
        # mutable source files or from generated native metadata itself.
        runtime = Path(runtime).resolve(strict=True)
        marker = json.loads(runtime.with_name(runtime.name + '-patch-receipt.json').read_bytes())
        identity = marker['runtime_cache_identity']
        ordered = identity['ordered_patch_sha256']
        require(marker['runtime_pin'] == '7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0' and
                len(ordered) == 99 and hashlib.sha256(('\n'.join(ordered)+'\n').encode()).hexdigest() ==
                '44c84f7e6bff300340df6f32759f3dfad2494b4dda88b47cbe3b57997cc8bbbb',
                'Explicit verified source map required for another runtime')
        source_hashes = marker['patched_sources']
    request = {'directory': str(Path(directory).resolve()), 'cache': cache, 'rom_sha': digest(rom),
               'rom': str(Path(rom).resolve()), 'runtime': str(Path(runtime).resolve()),
               'cfg_dir': str(Path(cfg_dir).resolve()), 'source_hashes': source_hashes,
               'direct_call_prefix': direct_call_prefix}
    result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--stdin'],
                            input=json.dumps(request), capture_output=True, text=True,
                            encoding='utf8', timeout=1200)
    require(result.returncode == 0, 'Current canonical validation refused: ' + result.stderr[-12000:])
    return json.loads(result.stdout)


if __name__ == '__main__':
    require(sys.argv[1:] == ['--stdin'], 'Use the isolated validator API')
    with redirect_stdout(sys.stderr):
        report = _validate(json.load(sys.stdin))
    print(json.dumps(report))
