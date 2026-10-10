# Chapter-one journal and original execution assessment

Native 0.2.2 adds current chapter-one advice to the journal. Companion remains
0.3.0. This extends the existing guarded foundation; widescreen still defaults
off, CPU cycle budgets stay original, and later chapters remain unqualified.

## Bosen's current advice

After the original Dr. Gari dialogue, battle, laboratory sequence and rescue,
Bosen asks the party to gather allies and build a town. The original message
030B executes the FA7F control and advances WRAM 5372 from zero to one at
01:D35E, then clears the stage-local flags at 01:D364 and 01:D368.
The journal uses the current stage-one value to display Bosen's advice.
It recomputes directly from restored state, so rollback can remove the lead.
No persistent seen-event history or completed-quest claim is added.

The original stage-zero David lead keeps its stage/flag predicate. Current
Starcrest possession still comes from either original 32-slot inventory, with
removal and restore handled by re-reading those inventories. When stage one
is active, Bosen's advice takes priority and current possession can appear on
the last line. The header fits the journal box, and inventory wording now
refers to party packs. Journal visibility and its configurable keyboard/
controller hotkey remain unchanged. Original View disables the overlay.

The event fixture is explicitly staged development evidence: an existing
original exit-record pointer selects Gari's scene through the original loader,
and player-only battle HP/attack/defense are raised in a disposable checkpoint.
The enemy HP, victory result, story flags, inventory, message and callbacks
are untouched. Ordinary interaction and Fight inputs execute the original
battle and aftermath. This does not certify natural campaign traversal.
Nine copied-executable runs pass 22 original-event/restore controls and retain
136 protected files. No Starcrest award was observed in these samples.
Generic stage-entry uniqueness and later chapters still need separate work.

## Visible world-edge vehicles

Two staged saved-position fixtures execute the original world loader, CFF6
constructor, D045 B0 allocation and DB68 producer. Horizontal and vertical
walking cross the actual 3583-to-zero camera boundary with visible original
Algos artwork. Independent VRAM/descriptor decoding matches 326 horizontal
and 194 vertical body pixels at the discontinuity. Twenty-four complete
544-byte staging packets match the following actual OAM scanout; 196 guest
surface comparisons and 28 original centers are exact.

The original next packet culls the body at camera zero. That disappearance
comes from the original fixed-slot culling rule, rather than invented host
art. The installed actor policy refuses this wrapping B0 allocation and
retains its stale-raster fallback. This proof establishes the original
visible path; it does not qualify seamless margin drawing or naturally
acquired Algos at every world boundary. The [separate wrapping-B0 prototype](../experiments/wrapping-b0/README.md)
authenticates only two proven staged position/resource tuples, preserves
original culling and refuses margins at raw camera discontinuities. Its first
positive proof independently matches 614 changed margin pixels. These
coordinate controls are bounded developer fixtures, not general world support.
It remains excluded from the installed actor policy.

## Productive map work and intentional waits

Paired read-only CPU observations cover world-edge walking, the original world
loader, parked B0 walking and four-direction A8/B0 travel. No visible nonpoll
update deadline was observed. Each direction has one initial zero camera delta, then all 63 remaining held
fields move four pixels. Every visible field reaches the original NMI wait. APU readiness/acknowledgment loops
account for most observed audio-protocol work during loading; these are not
classified as productive guest overload.

Original queued tile building at 01:B3A8..B4B7 is productive work. The pure
metatile-index sequence at 01:B408..B419 executes 11 instructions and costs
34 CPU / 262 opcode-master clocks per sequence. The observed travel route
executes it 2,080 times. This is a concrete candidate for guarded native
execution with original timing, not evidence that a larger CPU budget will
fix scrolling. Reduced guest costs require a separate measured justification. The
[source-only native prototype](../experiments/metatile/README.md) passes original
guest/timing, cold/load and independent interpreter-oracle checks. It remains
default off and excluded from normal installation; no host speedup is claimed.

## Developer replay isolation

`tools/run_foundation_probe.py` copies the executable into a new private profile,
checks the actual executable-directory anchor, validates finite scripts and
safe dump names, and verifies input hashes. Tests cover cold start, a copied
owner checkpoint and refusal controls; all 129 protected owner/ROM/GUI/receipt
files and ten source-executable neighboring files remain unchanged. The first
helper test rejected a correct trailing-separator anchor; its failed report
is retained, and the corrected path-equality check passes all 12 controls.
A silent headless replay report is explicitly developer evidence rather than
gameplay or audio qualification. See [usage](../BUILDING.md#isolated-developer-replay).

## Evidence and remaining scope

Private original execution evidence remains under
`local/evidence/journal-progression-20261009`,
`local/evidence/visible-world-edge-20261009`,
`local/evidence/cpu-progression-20261009` and
`local/evidence/progression-continuation-20261009`.
ROMs, checkpoints, extracted pixels/audio, dumps and native executables are
excluded from public source. The exact native 0.2.2 candidate is
`66bd32140d39f464b0b5f5ef8ba6193d880dd79be274c90fdb373809a9a7614b`.
Its separate finite checks pass 137 journal gates on 26 copied native runs and
131,072 pure predicate assertions; eight control/QoL/menu/checkpoint suites;
249 map gates across 39 cases; and 78 ordinary actor gates on 13 routes.
Three paced Direct3D routes hold about 60 fps with zero steady underflow,
missing-frame or audible-overflow deltas. The initial journal harness expected
two show events although its keyboard injection produces one show and one
hide; the audio counters passed, and a corrected focused repeat passes.
All failed harness reports are retained privately. This qualification remains
separate from the compiled_unqualified source receipt and does not certify
arbitrary rebuilds or a full campaign.

The original Crest award, durable quest history, further chapters, seamless
wide drawing through every packet discontinuity, full campaign/hardware/audio
coverage and complete native/AOT execution remain open. MSU-1 still requires
a verified compatible driver and track map; replacement HD world art is deferred.

## Installed launcher and protection

The unchanged Companion 0.3.0 passes 60 actual source-adoption checks, 31 GUI/
settings checks, 52 compatible 0.2.1-to-0.2.2 profile-update/selection-rollback
checks with actual native checkpoint execution, and 43 checks across six source/
legacy Play, Original View and Resume routes. Real source receipts retain their
compiled_unqualified status. The private legacy control initially omitted the
existing renderer-migration marker; that failure is retained, and a fresh
marker-corrected adapter passes. It is a harness correction, not an audio fix.

The exact 0.2.2 journal build is installed locally. A verified prework backup
and a second preinstallation backup preserve the previous binary, receipts,
authored mirrors and owner data. All 121 owner save/settings files and both
original ROM copies remain byte-identical; no owner checkpoint is migrated or
advanced. The separate wrapping-B0 and native-metatile binaries are not installed.
