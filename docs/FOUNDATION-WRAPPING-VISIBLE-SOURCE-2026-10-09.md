# Scene 0 visible actor source — October 9, 2026

Scene 0 has a later original ordinary actor source with different artwork
descriptors. The hypothesis that every scene 0 ordinary list is blank is false.
The source is selected only at story stage 17 with a particular original flag
clear. It is **static resource evidence**, not a naturally reached later actor
or a wider rendering qualification.

This continues the [natural fixture assessment](FOUNDATION-ACTOR-NATURAL-ASSESSMENT-2026-10-09.md)
and [actual allocation proof](FOUNDATION-ACTOR-ALLOCATION-2026-10-09.md).
Only the original scene 0 selector, its three referenced streams and their one
cursor-list index were inspected. No ROM, checkpoint, story RAM, native/runtime
source, public native manifest, owner installation or actor guard was changed.
There are no additional camera sweeps or artificial actor/base/pose changes.

## Bounded original selection

The three scene 0 streams are `08:87E5`, `08:87FF` and `08:8819`. The original
scene selector chooses them for stage ≤9, stage ≤23, and fallback respectively.
All have 14×14 primary dimensions, wrapping enabled and cursor-list index 203.
Their primary grid indices differ: 3, 252 and 294. The index resolves through
`0A:D800` to the original conditional list at `0A:DF7F`.

The original first-taken selector grammar gives this ordered list:

| Condition, in original order | Payload | Ordinary records | Descriptor family |
| --- | --- | ---: | --- |
| Stage 0, flag selector 1 clear | `0A:E5F7` | 2 | `04F8`, pose 0 |
| Stage 0, flag selector 6 clear | `0A:F88E` | 1 | `04F8`, pose 0 |
| Stage ≤11 | `0A:E165` | 0 | Empty |
| Stage ≤12 | `0A:F585` | 3 | `04F8`, pose 0 |
| Stage ≤16 | `0A:E165` | 0 | Empty |
| Stage <17, or stage 17 and flag selector 9 clear | `0A:F992` | 2 | `0598`, poses 2 and 0 |
| Fallback | `0A:E165` | 0 | Empty |

Earlier taken records suppress later records. In particular, the stage ≤16
branch makes the final conditional payload reachable only when `5372=17` and
`5361 & 40 == 0`. Selector 9 uses original story byte `5361`, mask `40`;
it is not an arbitrary new host flag. The current naturally observed stage 0
and original flag values select `0A:F88E`, matching the prior actual pointer
and `01:CD61` store proof.

There are seven selector records, five distinct payload addresses and eight
ordinary entries across the nonempty lists. Six entries use the already
observed `04F8` blank descriptor family. The remaining two use base `0598`,
world coordinates (1536,528) and (1536,544), poses 2 and 0, and original type 0.
Both phases select distinct OBJ tiles in the second character bank, rather than
the blank `7F` tile. The source supplies ordinary four-piece records; it is not
the separate B0/fixed-slot constructor. No gameplay identity is assigned here.

These counts describe this bounded original data structure. They do not count
playable maps, campaign events or successful actor draws. The source's different
descriptors do not establish that its required tiles/palette were uploaded in
an unobserved later scene.

## Minimum genuine next route

All fourteen named copied checkpoint samples from the preceding assessment
retain stage `5372=0`; none can naturally select the stage 17 payload merely
by moving around or revisiting the same world. This statement covers that
named set only. No owner save or wider checkpoint inventory was searched, and
no story state was changed to manufacture the later selector result.

The next useful fixture must first reach stage 17 with original flag selector 9
clear through genuine story execution. The event or chapter that establishes
those values has not been identified here. Once such a copied checkpoint is
available, the smallest field proof is an original transition into scene 0,
not a long world traversal:

1. Capture stage/flag values and authenticate selected primary stream
   `08:87FF`, grid 252 and its actual loaded resource tuple.
2. Observe `01:C64B → 01:CCDC`, original pointer stores selecting `0A:F992`,
   and actual `01:CD61` stores of `0598` into records 0 and 1.
3. Check the original tile-bank/VRAM/CGRAM lineage for both records and phases,
   then require nontransparent art in a naturally reached strip position.
4. Join the original producer to the complete 544-byte OAM transfer and actual
   displayed packet before checking original center, guest state, priority,
   terrain/OBJ overlap and restore behavior in a disposable candidate.

The current stage 0 metadata fixture remains useful for guard and packet-input
checks, but cannot substitute for this source/art lineage. Because a distinct
later ordinary source does exist, this batch does not assume all world entries
are permanently invisible or relax the party wrapping gate instead. A natural
world-edge camera/raster seam proof remains a separate requirement.

## Evidence and limits

Private report: `local/evidence/wrapping-visible-source-20261009/scene0-source-report.json`.
SHA-256:
`013f65595b0bfdc54722f26e8ae80e6034c8152273e1ab68ad43ac9cebea2dc0`.
Its nine bounded selection/source/protection checks pass. The report explicitly
records `all_scene0_lists_blank_hypothesis=false`, exact original addresses,
payload hashes, the fourteen sampled stage values and read-only checker hashes.
The initial failed all-blank hypothesis report is retained separately.

The earlier actual guest allocation and transparent-art results are unchanged.
No stage 17 guest producer, graphics upload, visible ordinary wrapping margin,
B0 activation, party seam, GPU/audio/controller or campaign certification is
added. All installed producer/resource/packet/center guards remain required.
