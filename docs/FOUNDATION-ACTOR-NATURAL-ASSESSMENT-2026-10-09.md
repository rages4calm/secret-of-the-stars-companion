# Natural actor fixture assessment — October 9, 2026

This focused assessment retains installed native/Companion 0.2.0 and all actor
guards. It found a reproducible natural wrapping-enabled **metadata** fixture,
but its original actor artwork is completely transparent. It does not qualify
wrapping actor pixels or permit enabling the private B0 integration.

Continue from [QoL/setup](FOUNDATION-QOL-SETUP-2026-10-09.md), the
[B0 host contract](FOUNDATION-LARGE-ACTOR-CONTRACT-2026-10-09.md),
[private B0 integration](FOUNDATION-LARGE-ACTOR-INTEGRATION-2026-10-09.md), and
[wrapping actor contract](FOUNDATION-WRAPPING-ACTOR-CONTRACT-2026-10-09.md).
No native/runtime source, installation, ROM, owner checkpoint or configuration
was edited. All processes used copied states, silent dummy SDL drivers and
private output directories. No record, coordinate or activation flag was changed
to manufacture a natural result.

## Bounded coverage

The initial measurement executed **18 replays and inspected 98 snapshots**:
14 existing named checkpoint copies and four 20-step world movement routes.
The checkpoints cover the existing opening room/island, Likado town/interior,
town exit attempts and world/battle namespaces. Snapshot scene selectors are
38, 39, 5, 12 and 0; those are sampled selectors, not a campaign/map inventory.
Only 63 snapshots have the ordinary route/layout context, including 51 with
wrapping enabled. No active-looking B0 or composite record was found there.
One proposed upward route enters battle; its later snapshots are excluded from
field-context findings. The down-then-left route remains in the world field.

Private `local/evidence/actor-natural-20261009/report.json` records the exact
checkpoint list, before/after hashes and context classification. Its SHA-256 is
`38ad093f0a7714e8ae0a34c647cb4ff56596459fdea60f4873738e75605aae2e`.
These measurements are separate from the earlier 9,866-file historical inventory;
that inventory was not repeated or turned into a count of game content.

## Natural right-strip recipe

The copied `local/runs/likado-loop-exit-a/saves/save0.sav` has SHA-256
`6f0df4ba39599853db5330d68f245d8fe61015c83b5d1604d1012fe68710c557`.
Using native 0.2.0 SHA-256
`9241f79ea1a685e0932282c300081a90f9becf503f9a17c5fe6a94b34a08a7e0`,
the successful recipe is:

1. Wait two guest frames and capture the starting field.
2. Press down four times for eight frames per press.
3. Press left twenty times for eight frames per press.
4. Press up six times for eight frames per press.

Each press is followed by a snapshot; the scripted runner's release/step boundary
also advances one frame. This is a 272-frame execution, rather than a single
uninterrupted 32/160/48-frame hold. Its private `input.txt` SHA-256 is
`aee56b12c03b069bfcd9815a2b004ebc9f9675d5fef53d2cadb4b1d1819ecbe1`.
Reward/movement modifiers, native loading shortcuts, fast menus and overlays
were disabled for the measurement.

The original guest keeps scene 0, route `0401=0C`, `0407=1`, primary dimensions
14×14, zero sprite offsets, OBJ setting 03 and no HDMA in these captures.
Regular record 0 remains at original world coordinates (1824,1776).
Its final camera is (1536,1752), so its raw ordinary draw anchor is (288,23)
after the original Y−1 adjustment. Earlier anchors (288,5) and (288,14) also lie
entirely in the private right strip. The original X gate correctly culls it from
the authentic 256-column picture. This route crosses no world-map edge.

The existing save-only diagnostic captured a private checkpoint at host frame
254, during the first fully visible right-strip position. The derived fixture is
`local/evidence/actor-natural-20261009/natural-world-right-actor-a/saves/save0.sav`,
324,251 bytes, SHA-256
`e6b1a0a702a1c297404f7b6a8cd8d8dc070628ee8dbc26442c1074d8d94e3e9a`.
It is an original guest-reached checkpoint, not a patched state. Neither this
checkpoint nor its captured original artwork is included in public source.

## Fidelity passed; artwork qualification failed

Separate original-width and wide runs compare **31 snapshot pairs / 186 guest
capture comparisons**: WRAM, VRAM, SRAM, OAM, CGRAM and original framebuffer.
Every comparison matches. Six composed 400-column surfaces preserve the exact
256-column original center. A cold replay of the derived checkpoint adds two
snapshot pairs / twelve guest comparisons and two exact composed-center checks.
These are capture parity checks, not full scheduler or campaign certification.

The actual installed observer reports 272 party-producer callbacks at its
registered `01:D8B1` seam, 272 DMA START callbacks and 272 DMA COMPLETE callbacks
during the extended wide route. The original module rejects wrapping context;
zero valid wrapping packets and zero actor side pixels are promoted. The three
fully visible-position snapshots have identical complete original 544-byte
staging/scanout packets. Callback occurrence plus snapshot equality does not
establish an eligible wrapping actor's producer-to-packet epoch.

The attempted artwork gate is a real negative. Original base `04F8`, pose 0 and
both original phase values resolve through descriptors `0E:BFC0/BFC8`. All four
pieces select tile `7F`. Independent four-plane decoding from the actual captured
VRAM/CGRAM finds **zero nontransparent pixels** at all three fully visible
anchors. Geometry and a retained active record therefore cannot support a
visible actor claim. No replacement tile, RAM mutation or synthetic actor was
substituted to turn this test positive. The record's gameplay identity is not
inferred from its invisible artwork.

`natural-fixture-proof.json` retains the failed artwork gate and its checker exit
1; seven integrity/parity/guard checks passed. Its SHA-256 is
`8b33ee4ff6ee526c4cc14c3b6d8282996239c854ac1ffb855bdd4ead8b4bb9eb`.
The separate `natural-fixture-assessment.json` explicitly records
`metadata_fixture_only_artwork_gate_failed` and `promote_wrapping_actor_guard=false`.
It contains the exact recipe, fixture, executable, reports and private checker
hashes; its SHA-256 is
`a2d54d30dc66729d3ad37f3549c848eaa7cf412550974fe316592f4bc2e6d474`.
The existing installed guard remains required.

## Smallest useful next proofs

For a visible ordinary wrapping fixture, first observe the original selected
actor-list allocation and base writer `01:CD61` into the record addressed through
`C0`. The inspected loader initializes `C0` to `7E:4100` and supplies original
record coordinates/base/pose from its selected source stream. A bounded entry
replay should retain the selected source pointer and actual writes to
`4100..42DA`, then test descriptor/VRAM nontransparency before attempting more
camera routes. The present `04F8` world record provides no visible artwork;
additional movement of that same record cannot supply the missing art proof.
Observe existing original activation, rather than setting a new base/pose.

For reserved B0, the original writer `01:CFF6` activates record 18 and `01:D045`
stores base B0 only after the scene/flag gates described in the
[special actor contract](FOUNDATION-SPECIAL-ACTOR-CONTRACT-2026-10-09.md).
All fourteen named checkpoint samples have `409=00` but stored source scene
`7E:5441=FFFF`, different from their current scene. The original scene-match
gate therefore blocks this natural B0 source. Narrow original writer spans at
`01:A534` and `01:A5DA` store current `040E` into `5441`; their caller/story
meaning is not yet established. The next useful B0 fixture should reach one of
those original writes, then the activation/base stores, actual `01:DB68`
constructor context and completed 544-byte DMA packet. Existing copied early
fixtures cannot certify that route by changing `5441` manually.

The private B0 integration still needs an isolated native candidate with actual
guest hooks, fixed-slot overwrite ordering, natural descriptor/art positivity,
terrain/OBJ overlap, color math and original-center/guest/restore parity. A true
world-edge wrapping fixture additionally needs original latch/camera ordering
across the 3584-pixel seam. Neither requirement is met by this interior metadata
fixture. No B0/composite/wrapping actor guard or installed binary is changed.
