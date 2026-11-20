"""Apply the Android-only proof cache to the exact verified emitter source."""
import hashlib


POLICY = 'recompiler/v2/architecture_emission_policy.py'
PREDECESSOR = 'b443753488f60ac655a018f774a9b5d2193321efc8b8cbc95afa56e25034ca3f'
OPTIMIZED = '0b2e012edf0c767529f60e5e5303228a757ab253723ed873d83dcc9511bb1733'

ORIGINAL = "def _digest(v):return hashlib.sha256(json.dumps(_freeze(v),sort_keys=True,separators=(',',':')).encode()).hexdigest()"

REPLACEMENT = '''# Only the packaged Android launcher registers this builtin. The normal SDK
# and developer invocations continue to use the original proof function.
import sys
from collections import OrderedDict
if '_sots_digest_snapshot' in sys.builtin_module_names:
    from _sots_digest_snapshot import snapshot as _proof_snapshot
else:
    _proof_snapshot = None
_proof_cache = OrderedDict()
_proof_cache_bytes = 0

def _canonical_digest(v):return hashlib.sha256(json.dumps(_freeze(v),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _digest(v):
    global _proof_cache_bytes
    if _proof_snapshot is None:
        return _canonical_digest(v)
    token = _proof_snapshot(v)
    if token is None or len(token) > 1024 * 1024:
        return _canonical_digest(v)
    cached = _proof_cache.get(token)
    if cached is not None:
        _proof_cache.move_to_end(token)
        return cached
    proof = _canonical_digest(v)
    if _proof_snapshot(v) != token:
        return proof
    while _proof_cache and (len(_proof_cache) >= 256 or _proof_cache_bytes + len(token) > 12 * 1024 * 1024):
        previous, _ = _proof_cache.popitem(last=False)
        _proof_cache_bytes -= len(previous)
    _proof_cache[token] = proof
    _proof_cache_bytes += len(token)
    return proof'''

GRAPH_RESULT = '    return _digest((members,graph.entry,graph.authority_conflict,graph.data_region_exec_pcs,graph.unresolved_indirects,graph.unknown_callee_exit_sites))'
GRAPH_REPLACEMENT = '''    from .decoder import DecodeKey
    entry = graph.entry
    if _proof_snapshot is not None and type(entry) is DecodeKey:
        # _freeze already applies asdict to this exact entry class. Make its
        # detached builtin fields visible to the cache before that recursion.
        entry = dataclasses.asdict(entry)
    return _digest((members,entry,graph.authority_conflict,graph.data_region_exec_pcs,graph.unresolved_indirects,graph.unknown_callee_exit_sites))'''


def optimized_bytes(original):
    if hashlib.sha256(original).hexdigest() != PREDECESSOR:
        raise ValueError('Android emitter optimization predecessor differs')
    text = original.decode('utf-8')
    if text.count(ORIGINAL) != 1 or text.count(GRAPH_RESULT) != 1:
        raise ValueError('Android emitter optimization sites differ')
    return text.replace(ORIGINAL, REPLACEMENT).replace(GRAPH_RESULT, GRAPH_REPLACEMENT).encode('utf-8')


def apply(runtime, source_hashes):
    source = runtime / POLICY
    if source_hashes.get(POLICY) != PREDECESSOR:
        raise ValueError('Android emitter optimization is outside the sealed source lineage')
    result = optimized_bytes(source.read_bytes())
    if hashlib.sha256(result).hexdigest() != OPTIMIZED:
        raise ValueError('Android emitter optimization output differs')
    # Runtime files live in the verified per-attempt capsule. The SDK sources
    # on the packaging host stay at their original pinned revision.
    source.write_bytes(result)
    return {**source_hashes, POLICY: OPTIMIZED}
