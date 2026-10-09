# Secondary map provenance contract

October 9, 2026. Read-only continuation for the next field resource guard. The
qualified 0.1.7 native sources and installed owner files are unchanged. This
document establishes original stream syntax and a bounded follow-up; it does
not certify campaign traversal or install a stricter guard.

## Selector 7: exact consumption and current impact

`01:C91D` selects a stream from the scene pointer table `08:8000`. The inline
dispatcher table at `01:C971..C980` contains bytes
`81 C9 AE C9 D7 C9 FB C9 26 CA 4A CA 6E CA 95 CA`, mapping selector7 to
`01:CA95`. That function reads the party sign at `04B6`, then executes:

```text
01:CA9E A4 04   LDY $04
01:CAA0 C8      INY
01:CAA1 C8      INY
01:CAA2 84 04   STY $04
01:CAA4 60      RTS
```

Its two operands are ignored, but both are consumed. All conditional selectors
0..7 therefore use five-byte records: selector8, operands16, stream16.
Unconditional `FF` uses three bytes: selector8, stream16. The existing
`PrimaryMatches` and historical inspector use four bytes for selector7.

The exact clean ROM has **no selector7 scene record**. All 337 scene entries
yield 409 variant links and 401 distinct selector records: 23 selector0,
49 selector2 and 329 unconditional FF. Correct and historical parsing return
identical record/stream pairs for all409 links. Thus this unused grammar branch
changes **zero current original resource accept/reject decisions**; it does
not justify replacing qualified 0.1.7 on its own. This comparison concerns the
provenance branch, not every downstream PPU eligibility condition.

Private evidence is `local/evidence/secondary-map-20261009/selector7-impact.json`
and the disassembly text files in that directory. A future correction should
use `size = selector == 255 ? 3 : 5`, preserve all409 original links, and add
a host-synthetic selector7 record with two ignored bytes followed by stream16
and an FF fallback. Test both party signs: a taken selector must read the
pointer at offset3; an untaken selector must advance5. A malformed/unsupported
record must fail closed. A four-byte parser can generally misread a pointer or
the next record, but no such malformed or selector7 record exists in this
immutable clean ROM; no current wrong acceptance is demonstrated.

## Full selected stream grammar

The clean ROM SHA256 remains
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
`01:C955` consumes one stream byte; `01:C960` consumes two. The mandatory
stream prefix is15 bytes. Only the first6 describe the primary map:

| Offset | Width | Original meaning |
| --- | ---: | --- |
| 0 | 2 | Flags, retained in DP78/79 |
| 2 | 1 | Primary cell index in high nibble, tile/attribute index in low nibble |
| 3 | 2 | Primary grid-table index masked with3FFF; upper bits feed0555 |
| 5 | 1 | Primary width in high nibble, height in low nibble |
| 6..9 | 4 | Color/palette/graphics setup selectors, consumed separately |
| 10 | 2 | Original object-list selector through08:AA00 |
| 12 | 1 | DP7A scene value |
| 13 | 1 | Original unlock/visit flag selector |
| 14 | 1 | Palette-animation selector, FF disables |

After these15 bytes, optional fields occur in this exact order. Flags without
listed payloads still alter original behavior but do not move the stream cursor.

| Original flag | Payload bytes | Consumer |
| --- | ---: | --- |
| 6000, either bit | 2 | C5D2 special-list selector through08:D700 |
| 1000 | 1 | C64B/CCDC cursor-list selector through0A:D800;0410==2 still skips this byte |
| 0080 | 2 | C66A event/list selector through08:D700 |
| 0040 | 1 | C686 overlay selector |
| 0020 | 1 | C694 flag-tile list selector through08:E900 into0453 |
| 0010 | 2 | C6B4 stage-tile list selector through08:F600 into0456 |
| 0008 | 5 or8 | C712 secondary map block, described below |
| 0004 | 2 | C80A list selector through08:EC00 into0479 |
| 0002 | 1 | C82C party-scoped value into7E:5461 or5462 |
| 0001 | 1 | C88C music selector |

When0010 is absent, the original still selects stage-tile table index0.
When0020 is absent, it does not clear0453; that pointer may remain stale and
must not be mistaken for a selected optional flag-tile resource. Wrapping of
both layers comes from the primary flags bit8000 into0407. It is not a
secondary-header property.

## Secondary block and camera branches

`01:C712..C765` consumes mode8, definitions8, secondary grid index16. The
secondary grid index is not masked. Definitions reverse the primary roles:
the **low nibble selects cells** through0A:8000, and the **high nibble selects
metatiles and attributes** through03:8000 and09:8000. They populate0509,
0503 and055C; grid goes to0516.

When mode bit80 is set, `C76D..C77B` consumes dimensions8, high-nibble width
to046F and low-nibble height to0470. This five-byte secondary block activates
producer050D. Mode80 retains the initial camera. Mode81 first divides040A/040C
by4 and then doubles them, giving half scale; mode82 retains quarter scale.
The code applies half scale to any other negative mode except80/82, but only
80,81,82 occur in these original referenced streams. `D080` copies the chosen
camera to the selected layer and renders its original initialization, temporarily
disabling the primary producer. It then restores primary active state.

When mode bit80 is clear, `C7BF..C7FB` instead consumes two signed16 velocity
words into045F and0462, writes sign-extension bytes0461/0464, clears0452 and
producer050D, and starts secondary camera02B1/02B3 at0. The block is8 bytes,
with **no dimensions byte**. The independent velocity/parallax path continues
at `B106..B18E`. Old secondary dimensions and pointers can remain in WRAM;
they do not authorize native decoding while producer050D is inactive.

A missing0008 header likewise leaves producer050D inactive and mode0452 zero.
Do not require old inactive-layer pointers to match a new stream, decode their
boundary tile, or assign primary camera motion to that layer. Do not compare
a moving active camera to its loader's initial value; authenticate its resource
and mode, then retain the actual per-line raster scroll contract.

## Conditions and auxiliary list lengths

The condition dispatcher calls original `D375`, which reads stage5372 and
story flags without requiring any host invocation of its guest scratch writes.
For operands a,b, selectors are:

| Selector | Taken condition |
| --- | --- |
| 0 | stage<a, or stage==a and storyValue(b)==0 |
| 1 | stage==a and storyValue(b)!=0 |
| 2 | stage<=a |
| 3 | stage==a and low nibble5361==b |
| 4 | storyValue(a OR80)!=0 |
| 5 | storyValue(a OR80)==0 |
| 6 | nibble a in packed5362 array equals b |
| 7 | party byte04B6 has bit80 set; ignores both operands |
| FF | Always taken |

`storyValue(s)` for s<78 uses5360 plus whether bit08 is set, with mask80 shifted
by s&7. Selector7E reads low nibble5361. SelectorFF uses the caller's supplied
packed nibble index. Other selectors use5362+((s&7F)>>3), mask80>>(s&7).
The first taken record wins; possible-variant membership alone is weaker.

Cursor-list selection at `CCDC..CD16` reuses this condition grammar in bank0A.
Its selected payload at `CD27..CD9C` contains coordinate16, flags16,
target16 and type8: seven bytes. Type2 consumes one additional uint16 script
selector, making nine bytes. Types0/1 have no extra payload. CoordinateFFFF
terminates the list before a type byte is read. This auxiliary list does not
add variable bytes to the scene stream: only its one-byte index is consumed.

Flag-tile E records have four bytes (location16, flag16), while stage-tile F
records have five (location16, threshold8, selector8, replacement8). Both end
on locationFFFF, a two-byte sentinel. Preserve their current live decision
rules separately from selecting the scene stream. Cursor payloads and tile
condition lists are bounded by their original byte index; do not scan arbitrary
following bank data to find a plausible sentinel.

## Static coverage and copied evidence

New read-only `tools/inspect_foundation_secondary_maps.py` authenticates the
clean ROM, parses all referenced variants and writes ROM-derived reports only
under local/. It preserves the earlier inspector and writes no runtime state.

All395 distinct referenced streams parse without overlap. Of394 boundaries
to a next referenced stream,393 end exactly at that next start. One stream
0897E9 ends0897FE with23 bytes before the next referenced stream; this gap is
not certified as unused content. The final referenced stream08A9A8 ends08A9BD;
its downstream extent is not inferred from a missing next reference.

305 streams contain secondary blocks:285 mode80,9 mode81,2 mode82 and9
mode00.90 contain no secondary block. The two mode82 streams are088833 and
08884F. These are structure counts, not counts of playable maps or encounters.
All226 referenced cursor-list indices parse403 linked condition variants and
their selected payload syntaxes. All65 referenced flag/stage table indices
(including default stage0) terminate within the byte-index contract; largest
observed payload including sentinel is67 bytes.

Copied WRAM snapshots for scenes12,38,39 select original streams088938,
088B6D,088B84 respectively. Both active layer tuples, dimensions, wrap,
secondary mode and default stage pointer match in each snapshot. Their exact
WRAM hashes and decoded metadata are in
`local/evidence/secondary-map-20261009/report.json`. This does not add guest
execution, center-pixel, controller, audio or campaign proof.

## Smallest follow-up native seam

Replace possible-primary-only provenance with one bounded selected-stream
parser. Parse original flags and optional cursor widths, then compare primary
and active secondary tuples **from that same stream**, dimensions, wrap and
current secondary mode. Authenticate0456 against selected/default stage index;
authenticate0453 when the flag field is present and required. Retain existing
original-table span checks, conditional tile decisions, PPU layout guard and
exact center-pixel gate. Inactive secondary must remain inactive.

Selection depends on current live story bytes; it cannot be cached only with
map-resource pointers. Story changes can legitimately precede the next scene
reload. A strict mismatch should preserve the original center until a matching
stream is loaded, rather than invent a host reload or rewrite guest state.
Reset/restore must invalidate derived selection caches. Scope the first native
proof to these three copied scenes, a conditional selector0/2 boundary, a
foreign but valid BG2 tuple, absent secondary, mode00/81/82 synthetic resource
contracts and cold/restore invalidation. All409 original variants should retain
static parsing coverage; natural special-parallax transitions remain a later
bounded gameplay proof.

## Private prototype continuation, not promoted

The prototype is confined to
`local/evidence/secondary-prototype-20261009/src/foundation_field.c/.h`.
`SelectedMatches` runs before cache reuse on every eligible view refresh. It
selects the first taken original scene record, parses the exact optional
grammar, compares both active layer tuples/dimensions, wrap and secondary
mode, and binds the actual selected/default conditional pointers. Velocity-only
or absent secondary remains inactive; its old pointer/dimension words are not
reconstructed. The unused selector7 record consumes five bytes. No guest
memory, ports, cycles, save state or owner profile is written.

Review found an important packed-nibble caller detail. `C981/C9AE` loads the
operand word with A=a, accumulator B=b, then SEP20/LDA06 puts b in A while
leaving B=b. When b==FF, the accessor's `D383 XBA` therefore selects packed
nibble FF, not nibble0 or a. Cases4/5 likewise use b as the packed nibble when
a OR80 becomes FF. Case6 explicitly swaps and loads FF, leaving B=a, so it
uses nibble a. No clean scene selector0 uses b==FF; its actual b values are
0,1,2,3,4,5,7,12,13,14,15. The private C and new Python oracle were corrected.
Ten additional literal-offset cases distinguish these conventions without
using that Python oracle to decide the expected result.

Absent0020 does **not** mean the original E-list is stale or unusable. Across
313 distinct active resource tuples in these streams,67 streams contain
reachable E metatiles (71 layer links). Exactly two omit0020: scenes216 and221,
streams089B96/089C06. They share primary grid181, definitions66, dimensions4x5;
the E metatile at world928,544 uses key3A22 and metatile1. Referenced original
E-list47 at08:EBC4 associates that key with flag144. Thus preserving an actual
retained pointer can preserve original behavior. Static counts and detailed
coordinates are in `E-without-header-inventory.json` in the private prototype
directory. This inventory is not evidence of a naturally visited loading path.

When a flag field is present, the prototype requires its exact selected
pointer. When absent, an actual0453 pointer can authenticate if it equals an
E-list pointer referenced by an original scene stream, and the entire four-byte
record list plus FFFF sentinel fits the original list extent and byte-index
bound. Extents end at the next distinct pointer or08:EC00. Its current flags
are then read with the original E condition rule. An unknown retained pointer
declines E resolution. This follows the same actual RAM pointer as the guest;
it does not assert which earlier loader selected that pointer. Both scene216
and221 host fixtures verify original list47 with flag144 clear/set, producing
IDs1/2 and exact independently decoded quadrant words. Natural retained-list
history remains unverified.

The additive checker is `tools/check_foundation_secondary_provenance.py`.
Private report `local/evidence/secondary-prototype-20261009/proof-e/report.json`
passes1,893 gates: all395 stream structures;172,576 native-versus-Python
original selection decisions; all409 linked original variants reached using
valid stage/flag patterns, including seven requiring mixed bits;96 synthetic
stage/flag/nibble/party condition cases; ten accumulator-B literal cases;
12 authentic E coordinate samples and12 authentic F coordinate samples,
with12 E and4 F replacement branches; the two retained-E scene fixtures;
and wrong-secondary/wrong-list refusal, live-selection cache invalidation,
reset and recovery. The three existing natural snapshots remain separately
positive with5,376 original VRAM/independent-ROM/native center words equal.
No new gameplay run follows from these host checks.

The metadata-only harness hook bypasses condition selection solely to test
all395 original stream syntaxes; it is not a production eligibility API.
The409 selected-variant cases invoke real condition selection. The historical
all248-resource proof is preserved. Its fabricated no-match0453/0456 sentinel
adapters are intentionally incompatible with the stricter pointer contract;
new fixtures use original selected/default tables and actual resulting
conditional state, rather than relaxing provenance to keep old synthetic
fixtures passing.

Frozen private C SHA256:
`b58b866ebb82161a7ea6ecb3af0eb4402f69f8b910c420feb4dbfda2ee59d4ae`.
Private H SHA256:
`f774eb8833427762ee920e7e40a7d3f2c2070edc19e20c2f6faffa9d206720a1`.
Root review is required before any promotion or candidate build. The qualified
author/live source hash below is unchanged.

## Attribute-index correction and guarded memory proof

The first guard-page prototype run found two conservative full-decoder
declines although selected-stream provenance passed: mode82 streams088833 and
08884F in scenes1/2. Their secondary definitions99 reference metatile212.
The attribute9 base09:8910 plus212 equals09:89E4, exactly the next original
attribute-table pointer. The historical decoder inferred that neighboring
pointer was the end of the previous attribute array, so it refused the read.
Grid, cell and tile spans already passed.

Original `01:B704` executes SEP30, `B706 TAY` copies the raw8-bit metatile ID,
`B707 STY0520` preserves it, `B70A LDA[$2C],Y` reads the selected attribute
base plus that ID, and `B70C AND0F` selects its low nibble. There is no
next-table-pointer length check. The literal original byte at09:89E4 is00;
tile212 quadrants at03:C5E8+212*8 are1E04,1E04,1E47,1E47.

Root authorized this precise private correction: attribute bounds are
`min(selected_base+256, same_ROM_bank_end)` and only the actually referenced
IDs are read. Selected scene, metatile and attribute base identities remain
exact; all original cell and tile span guards remain unchanged. No bank-wide
scan or read beyond the raw8-bit ID range was introduced. This supersedes
private C216163aa, with corrected private Cb58b866e above. Shared qualified
sources have not been changed by this agent.

New `tools/check_foundation_selected_map_memory.py` leaves the historical
memory checker untouched. It compiles the actual private module with
`-fsanitize=undefined -fsanitize-trap=all` and isolates execution in a child
with Windows SetErrorMode3. Both ends of the exact clean ROM and131072-byte
WRAM buffers are PAGE_NOACCESS. All409 authentic selected host views activate
the corrected decoder:719 active layers,58,239 extreme-coordinate pairs
including INT_MIN/MAX against independent decoding,17,863 malformed-resource
refusals and recoveries,3,276 invalid arguments,409 reset/rebind/reference-list
cache rebuilds and four retained-E clear/set phases pass. Eight literal
metatile212 quadrant comparisons prove the source-backed boundary correction.

A separately compiled qualified reference accepts407 of these409 views. Only
the two identified mode82 resource cases change acceptance. The initial guard
run's decline was an explicit assertion, not an access violation or UB trap.
Corrected memory proof `local/evidence/secondary-prototype-20261009/memory-d/report.json`
passes with child exit0, no trap and all tracked source hashes unchanged during
the test. The focused provenance proof was rerun as proof-e and still passes
all1,893 gates with the same5,376 natural center words.

These are guarded host adapter proofs; retained-list loading history, natural
mode82 camera transitions, gameplay timing, controller and campaign remain
separate runtime checks. No owner save, ROM or profile was altered.

During this research author/live `foundation_field.c` SHA256 stayed
`c94be434bb8f7410b25041cb90f62af1f79cb7f7455a9b4d49e1e6fcc304bbd4`.
No module, build, owner save or installation was changed.
