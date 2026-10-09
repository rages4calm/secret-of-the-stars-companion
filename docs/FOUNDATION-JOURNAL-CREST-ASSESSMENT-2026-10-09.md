# Crest journal milestone assessment — October 9, 2026

The original inventory identity and insertion/removal routes are now established
more precisely. A Crest-specific acquisition event, permanent completion flag,
or naturally reached near-award checkpoint is still unverified. The installed
journal remains the stage-zero David lead; no native, Companion, public-source,
manifest, save-schema or installation change was made in this assessment.

The current rules remain those in
[FOUNDATION-JOURNAL-CPU-2026-10-09.md](FOUNDATION-JOURNAL-CPU-2026-10-09.md) and
[the earlier event assessment](FOUNDATION-JOURNAL-EVENTS-2026-10-09.md). David's
introduction bit and the Crest item ID both involve hexadecimal 40, but they
refer to different state domains. The introduction bit does not mean possession
or completion.

Private source analysis, copied-state summaries and hashes are under
`local/evidence/journal-crest-20261009/`, with `report.json` as the receipt.
The hash-checked clean ROM remains
`7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`.
Opcode bytes and decoded original text stay private.

## Exact inventory source seams

The item-name table at `04:C000` has index **40 hex**, entry `04:C080`, pointing
to `04:C3F5`, whose original name is `STARCREST`. Exact decoded consumers start
at `00:8A09` and `02:976C`; these correct the earlier addresses that pointed one
byte into each instruction. The original dialogue item-name consumer at
`02:B0EC` uses the same table.

| Source seam | Original behavior established statically |
| --- | --- |
| `00:FF47` → `00:872E` | Generic inventory insertion; argument FF skips insertion. |
| `00:873F` | Stores the item argument at `7E:5373 + X`; X comes from `04BA` or `04BB`, selected by the sign of `04B6`. |
| `00:8748/874D` | Advances the corresponding original inventory cursor after insertion. |
| `00:86D2`, stores `00:86ED/8701` | Removes an item by compacting later slots and clearing the tail to FF. |
| `01:C40F` → `01:D406` | Searches the selected 32-byte inventory block; result `0424` is temporary. |

These routines establish an observable item store, not the event that awards
the Crest. In particular, `00:872E..8750` contains no story-bit or stage write.
Several original callers can insert items: battle reward processing, item/menu
handling and dialogue control. A hit in the generic writer must retain its
actual caller, item argument, party/cursor context and award-source identity.

Possession is mutable: the original removal routine can eliminate an item and
shift its slot. Searching for 40 in a fixed slot would be incorrect, while
searching both inventories still would not establish an irreversible historical
milestone. The insertion route selects parties by the sign of `04B6`; the
lookup chooses its second block for a nonzero selector. No broader selector
equivalence is assumed outside the game's observed contexts.

The original stage-advance writer is still `01:D35E`, reached when the generic
flag routine receives argument 7F. It clears `5360/5361` after incrementing
`5372`. This is a generic chapter transition. No Crest-specific caller or
condition for it was established here, so stage one is not labeled "Crest
completed."

## Bounded fixture result

The assessment reads **54 historical copied snapshots from twelve named opening
routes**: David dialogue/final/exit, world-cave, five cave-route attempts, cave
interaction, battle-badbad and battle-return. All sampled stages are zero and
none of the two 32-slot inventory blocks contains item 40. These are sampled
snapshots, not proof that the item never appeared between them.

The historical `battle-badbad-a` victory image reports **4 EP and 4 gold**. Its
before/after inventory remains empty, and `battle-return-a` reaches ordinary
field mode in scene zero with story bytes C0/00 and stage zero. The fixture name
does not identify a Crest encounter or establish proximity to its award.

The qualified native 0.2.0 victory controls were also read from
`local/evidence/qol-release-20261009/qol-restore-final/`. Their four before/after
snapshots likewise show no item 40, no stage advance and unchanged C0/00 story
bytes. That route is the documented copied two-Red-Slime fixture. These existing
captures have executable SHA-256
`9241f79ea1a685e0932282c300081a90f9becf503f9a17c5fe6a94b34a08a7e0`;
they do not qualify a new Crest route.

The older snapshots named `cave-entry` and the later `cave-interact` samples
remain in wrapping scene zero. Their filenames are not evidence of a dungeon
transition or a learned mountain identity. This investigation does not extend
those unsuccessful attempts into a speculative walkthrough.

No new gameplay process or owner checkpoint was executed. Existing copied
fixture files were read only; their byte hashes are recorded. A new replay is
appropriate once there is a concrete source event or a genuine checkpoint near
it, rather than repeating unrelated ordinary victories.

## Chest route and remaining gap

The original ordinary chest handler is `01:8F79`. It matches the active scene's
flag-list coordinate, refuses an already-opened flag, and reads the selected
content through `01:8FFF..9008` from `0A:D000`. Successful ordinary handling
sets its original opened bit at `01:8FFA`; special content has a separate route
at `01:906C`.

No literal item 40 appears in the checked 512-byte content span or in the
contents selected by the 55 flag-list tables inspected. This narrows the search;
it does not establish that a scripted award is absent, that every event uses
these tables, or that any chest flag is the Crest flag. Raw opcode/control-byte
searches also remain candidates until linked to an original selected event.

The unresolved gate is the **actual original source that supplies item 40, or
an original progression event that explicitly represents obtaining the Crest**.
Neither the sampled inventory absence nor the generic writer assigns that
event an identity. No Crest-specific completion rule is ready to install.

## Smallest next proof

Use a naturally reached copied checkpoint at the identified original event.
Retain normal input and observe the source event plus a candidate `00:873F`
store with item argument 40, actual party/cursor context and before/after
inventory. Watch the story bytes and stage separately; a simultaneous change
still needs its original caller and condition before being named completion.

Then establish whether the item is consumed, removed, transferred or reacquired,
and whether a durable original flag survives those actions and chapter changes.
The first journal implementation should express only the resulting verified
state: for example current possession if that is all the evidence establishes,
rather than a historical completed quest.

Compare observation off/on with exact guest state, and test cold restoration
and an actual rollback to before the event. Content should derive from restored
original state wherever possible. A future native historical log would require
an explicit deterministic state/schema contract; an external append-only record
would leak later knowledge into an older checkpoint.

Do not force the item, a story flag, chapter byte, scene or award callback to
manufacture this proof. The installed journal, saved progress and existing
guards remain unchanged while the event prerequisite is unresolved.
