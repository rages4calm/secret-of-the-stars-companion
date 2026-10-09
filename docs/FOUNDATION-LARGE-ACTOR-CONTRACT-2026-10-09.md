# B0 two-large-object host contract — October 9, 2026

This additive proof covers the original B0 constructor family in an isolated
host canary. It supplies reusable metadata and 16×16 artwork decoding, but is
not linked into the native game or installed player. All records, CPU contexts,
packets and palette-phase changes in this proof are explicitly synthetic.
No original ROM, save, guest activation, CPU timing or other agent's prototype
is changed. Natural B0 actors and actual guest-hook execution remain unqualified.

## Original constructor seams

The original source is recorded privately in
`local/evidence/party-actor-contract-20261009/party-special-disassembly.txt` and
the earlier `docs/FOUNDATION-PARTY-ACTOR-CONTRACT-2026-10-09.md`.
Both constructors use base B0, then descriptor
`0E:9800 + 8*B0 + 4*record[00]`, supplying two words. Neither uses global
`0475` or ordinary party animation phase `record[0A]`.

- Party `01:D989` reads an 18-byte record under `7E:4000`. Its X/Y are packed
  from low bytes and record byte 5 bits 0/1. It subtracts one from Y; this branch
  does not apply `0471/0473`. Caller return is `01:D865`.
- Regular `01:DB68` follows a 25-byte record under `7E:4100`. At this seam,
  direct-page `02/00` hold world plus offsets minus primary camera, and `1F`
  holds the completed descriptor pointer. Y subtraction occurs inside each
  component loop. Caller return is `01:D86F`.

The canary validates D=0E00, DB/PB=01, M=0, X=1, Y=3, native/decimal-off CPU
context, correct long record pointer, original base/descriptor/mask, and bounded
party index 0..4 or regular index 0..18. FF is inactive. The current presentation
contract requires nonwrapping fields, route 0C, zero sprite offsets, OBJ setting 03,
no priority rotation/interlace and a current eligible field-view signal. That
field-view signal is a synthetic adapter value here; this canary does not replace
the qualified native field-resource eligibility checker.

Each component uses a separate original clipping decision and its permanent
fixed slot: part 0 at slot 0, part 1 at slot 1. X offsets are 0 and 16; Y offset is 0.
Party clipping accepts unsigned values at least 01F9 or below 255/239; the bounded
nonwrapping regular path uses FFF1 instead. The original wrapping comparison
branches are explicitly refused, not reinterpreted as a new coordinate model.
Packed party display representatives are chosen around X 128/Y 112 in a 512-period;
regular display coordinates preserve their world-minus-camera anchor. Actual
raster deltas are separate bounded inputs to the private margin preparation.

## Fixed-slot overwrite rule

The original producer initializes the fixed slots' XY to hidden F080 at
`01:D87F..D8B0`. A visible B0 component writes its fixed low-OAM words and sets
the large-size/X-high group. A culled component skips those low writes while
shifting a zero group into the final shared high byte. Each B0 invocation writes
that complete high byte at its end.

This means a later partially culled writer can leave an earlier component's low
words with different size bits. Treating every B0 record as another independent
margin sprite would duplicate or misrepresent the original fixed-slot result.
The canary therefore keeps only the latest complete writer. A later constructor
that actually overwrites both large slots replaces the earlier metadata;
partial same-slot overwrite closes the entire B0 margin path. Source order is
checked: party precedes regular, and indices increase within each family.
Duplicate or reverse-order captures refuse metadata. Original center rendering
would continue through its original packet regardless of this derived fallback.

Sealing checks both fixed low-slot records and the exact original high byte,
then stores all 544 original staging bytes. Promotion requires channel 7,
`7E:2200`, size 544, B address 04, mode 0, forward/nonfixed A-to-B direction and
complete notification. Every actual packet byte must match the sealed staging
snapshot. Bounds, stale resources, packet differences and reset refuse prepared
margin output. These are host-replayed notifications, not execution of the
original DMA routine; integration must join the existing real START/COMPLETE
observer and its producer epoch rather than infer execution from these tests.

## Reusable artwork decoder and proof

Authored, ROM-free helpers are `tools/foundation_large_actor_canary.c/.h`.
The host driver and independent Python oracle are
`tools/check_foundation_large_actors.c/.py`. They contain no copied original
opcode bodies, original tile pixels, ROM descriptors, saves or extracted art
arrays. The original image's checksum and bounded source addresses establish
identity; descriptor words are read only from the owner's local unchanged ROM.
All derived packets, word lists and pixel outputs remain under ignored `local/`.

Under OBJ setting 03, large objects are 16×16. The decoder follows the actual
PPU's tile-column nibble wrap and tile-row carry, selects the correct character
bank from tileword bit 8, applies whole 16×16 H/V flips, decodes all four bitplanes
and uses the supplied current CGRAM. Color index 0 stays transparent. This is
object artwork decoding; final OBJ priority, windows, color math, background
composition and physical display pacing are outside this host proof.

`local/evidence/large-actor-prototype-20261009/authored-canary-proof/report.json`
passes all five aggregate gates. Its **137 unique metadata cases** contain
**60 positives and 77 refusals**. They cover both coordinate families,
component clipping boundaries, eight representative direct pose selectors,
both masks, ignored ordinary phase, complete last-writer replacement,
partial collision refusal, source order, CPU/context/descriptor guards,
transfer settings, resource changes, line/raster bounds, aliases and reset.

Explicit extreme-buffer cases use SIZE_MAX and null RAM/VRAM/CGRAM/output/packet
views; invalid sizes refuse before a buffer read. Wrong image hash, short image
and missing image refuse binding. The driver verifies ROM, input RAM, tile data,
palette data and input packets remain unchanged after every case.

The separate independent byte-plane oracle compares **8,388,608 palette pixels**:
16,384 synthetic tilewords across two CGRAM inputs. It covers all 256 base tiles,
both character banks, all eight OBJ palettes and all four full-object flip
combinations. There are zero word-image mismatches; the second palette input
changes output while preserving exact independent agreement. This synthetic
palette rotation does not certify execution of a game's animation script.

Frozen authored helper C SHA-256:
`76bc6a53a27de0a858a677a67c07a61a4617f65dc72522396320c4739e04c8b0`.
Header SHA-256:
`070dabbc102889f198082f111820be19809d430df6c5666ed368e53e948545f4`.
Driver C SHA-256:
`6c12ccf7a6dc86775abb6bdb2627ed699abcc8a9804da9415567c068ac3798cb`.
Checker Python SHA-256:
`a4bc407b776b88aeb3998d0971c9a15d6e36d863fecf47c750b7deec73272a61`.

The earlier private-only helper at
`local/evidence/large-actor-prototype-20261009/src/` remains frozen separately:
C `6a7a16755808d3bfecfc9c8f9a815a44a4fcc1c2b408a7d7c5bad13c9e739394`,
H `57a4002e6178627434349a819dc558887e4765658e81b096e02992d55f783f2c`.
Its `host-proof-2/report.json` passes 111 cases and the same pixel oracle;
original ROM, input fixtures and the then-qualified authored/live actor paths
remain byte-identical before/after that measurement. The authored canary adds
extreme/null checks independently of subsequent release source promotion.

## Next integration requirement

A future isolated integration must observe B0 after the original fixed-slot
initialization, use the actual party D989/regular DB68 contexts, retain the shared
resource/epoch identity, and join the real completed 544-byte packet. Ordinary,
reserved and B0 families must coordinate slot ownership; they cannot all append
metadata with duplicate virtual ranks. Actual original/wide center/state parity,
per-line PPU composition and a genuinely reached B0 producer are still required.
No actor is spawned and no owner checkpoint is edited to manufacture that proof.

```powershell
python tools/check_foundation_large_actors.py --rom local/inputs/clean-usa.sfc --base-dump local/runs/actor-wide-20261009-133859/sweep-on/dump/start --clang C:/Users/crono/.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe --out local/evidence/large-actor-canary-fresh
```

Use a fresh private output directory. The supplied base dump contributes only
the captured tile/palette input; its ordinary actor is not presented as a
natural B0 actor. The release continues to exclude this family until its own
integration and runtime receipts qualify it.
