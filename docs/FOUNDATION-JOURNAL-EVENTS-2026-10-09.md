# Secret of the Stars: first quest journal event foundation

October 9, 2026. This is a focused, read-only assessment of the copied David
dialogue fixture. It establishes a first stable event identity for an eventual
native journal. No journal UI, persistence, title source change or installed
binary change is included. Owner progress was not run or edited.

## Confirmed first lead

The observed dialogue tells the player to seek the Crest of Stars and says it
is somewhere in the mountain. The captures are
`local/runs/david-dialogue-a/dump/page03.fb.bmp` and `page07.fb.bmp`.
No particular mountain, entrance or route has been established. The journal
should repeat the observed lead without introducing a destination the player
has not learned.

The clean USA ROM remains the target, SHA256
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
The original copied fixture ran the historical executable recorded in its
`run.json`; this assessment does not certify a newer executable or reference
emulator against those captures.

## Message and consumer identity

The fixture has message ID `0x0749` at WRAM `0x0434` throughout the David
pages, and zero between completed interactions. The current text pointer at
WRAM `0x0A84..0x0A86` is:

| Capture | Current pointer | Meaning |
| --- | --- | --- |
| page03 | `28:A9BF` | The preceding page contains the Crest lead. |
| page07 | `28:AA44` | The preceding page contains the mountain lead. |
| page10 | `28:AA7C` | Later, shorter David interaction. |

The pointers are at page boundaries: they identify the following control byte,
rather than the beginning of the displayed page. The corresponding encoded
ROM text and actual BG3 glyph words agree with the captures. Letters use
`0x81..0x9A`, with `0x80` for a space in these strings.

Static original-code inspection identifies `02:BA4C` as message selection
(also exposed by jump entry `02:910C`) and `02:BA71` as its pointer-table
consumer. For ID `0x0749`, group entry `02:BC57` selects bank `0x28`, a
conditional record at `28:82A8`, and the initial/short David text branches.
`02:AA8D` reads a text/control byte using `LDA [$84],Y`, and `02:ABC5`
advances the current pointer after consuming a segment. These are concrete
candidate observation sites, not installed hooks or newly traced dynamic
function coverage. The reader requires its original direct-page and CPU-width
contract; do not assume any occurrence of `LDA [$84],Y` means David dialogue.

A minimal native event observer should guard the exact ROM, message ID,
consumer instruction/context and consumed stream position. It can recognize
the two observed leads without decoding every script or inventing quest
progress from rendered text. A pointer-only after-frame check would be a
fixture-specific fallback, since an unusual advance might skip the boundary.

## David introduction bit: supported, with a bounded meaning

WRAM `0x5360` is `0x80` in pages 01 through 07, then `0xC0` by page09.
The initial David branch ends with control `FA 01`. Its static path is
`02:B068` → `01:C409` → `01:D30F`, whose argument `1` sets bit `0x40`
in WRAM `0x5360`. The subsequent message selection chooses the shorter
David branch. The observed before/after state and the original writer agree.

This supports naming the bit **David introduction completed in the current
story stage**. It does **not** establish that the Crest was acquired. The
same original flag writer handles argument `0x7F` by incrementing stage byte
`0x5372` and clearing `0x5360/0x5361`. An ever-seen journal cannot rely on
that bit alone across later story stages. The fixture's SRAM dump is unchanged
between page01 and page09; persistent save-slot mapping of these story bytes
has not been established by this assessment.

## Crest completion: candidate only

The item-name pointer table at `04:C000` has entry `0x40` pointing to
`04:C3F5`, which decodes to `STARCREST`. Consumers at `00:8A0A` and
`02:976D` address this table using an item byte multiplied by two. This is
a strong static candidate for item ID `0x40`.

Generic lookup entry `01:C40F` jumps to `01:D406`, which scans 32 byte IDs
starting at WRAM `0x5373`, or the second party block at `0x5393` according
to `0x04B6`, and returns its result through `0x0424`. That temporary result
is not a persistent completion flag.

No captured Crest acquisition, inventory display, removal, transition or save
restore confirms this candidate. No Crest completion rule is enabled. Inventory
possession might be useful evidence, but it would still need qualification
against the story's actual acquisition milestone and any consumption behavior.

## Next bounded implementation

Implement a first-stage **observed clues/current lead** journal behind an
independent option. Observe the actual message consumer for the first David
lead and retain the original quest wording. Initially report completion as
unknown. Test David, an unrelated dialogue and repeated David interaction on
copied fixtures; ensure guest dumps remain identical with the observer on/off.

Before persistence, define new-game reset, cold checkpoint load and rewind
behavior. Any new deterministic seen-event state belongs in versioned
checkpoint data and must restore with the game. An external append-only log
must not accidentally reveal future clues after rewind or attach one save's
progress to another. The existing stage/bit can reconcile the checked current
stage on load, but cannot reconstruct a full historical journal.

Then obtain one bounded, natural Crest acquisition fixture, verify item ID
`0x40` and the real story writer, compare before/after inventory and progression,
and test copied cold resume. This avoids requesting another owner campaign.

The private receipt is `local/evidence/journal-events-20261009.json`. ROM-derived
captures, original encoded data and saves remain local. Existing native coverage,
reference-fidelity, HD, widescreen and conditional MSU-1 limits remain unchanged.
