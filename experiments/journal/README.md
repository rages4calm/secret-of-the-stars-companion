# Experimental current-inventory journal

This isolated module reports mutable STARCREST possession. It does not identify
the original award event, a completed quest, or an irreversible story flag.
Neither the canonical foundation manifest nor the installed journal is changed.

The pure predicate in `foundation_journal.h` scans the two original 32-byte item blocks at WRAM 5373
and 5393 for item 40 hex. It returns a bitmask identifying inventory groups.
It reads guest state without writing it or retaining an acquisition history.
The item identity and original insertion/removal/search seams are documented in
`docs/FOUNDATION-JOURNAL-CREST-ASSESSMENT-2026-10-09.md`.

The experimental `foundation_journal.c` preserves the existing stage-scoped
David lead when possession is absent. Set
`SNESRECOMP_EXPERIMENTAL_JOURNAL_POSSESSION=1` to show current possession instead
when an inventory contains the item. The journal still uses its configured
keyboard/controller action. Recompute at drawing and after each frame so a
checkpoint load cannot leak possession from a later state.
Positive cards use a short close-action header and "In your pack now"; absent
items preserve the canonical card byte-for-byte.

Staged developer checkpoints test the reader and its restoration behavior.
They are expressly manufactured fixtures, not natural acquisition, original
award/removal gameplay, or campaign completion evidence. Original settings,
CPU timing, guest state and save schema remain untouched.

Compile `check_possession.c` with the runtime's `host_main.h` include directory
for ROM-free checks against that same predicate. A real experimental game build and separate guest/render/input checks
are needed before any player installation can be considered.

Build an isolated candidate with `tools/build_experimental_b0.py --experiment
journal`, supplying a matching real canonical source-build receipt and your
owned ROM. Its receipt remains experimental and cannot be adopted through
Companion's normal source Setup.

`check_journal_possession.py` requires explicit candidate/reference binaries,
ROM, fixture, runtime, compiler, output directory and evidence root. It refuses
an occupied output directory or an unsupported checkpoint layout. The focused
fixture has two empty inventories and cursors 00/20; manufactured item insertion
updates the respective original cursor. Manufactured removal and compaction are
clearly labeled and preserve their source snapshots. The item lookup at
01:D406 checks all 32 slots without stopping at FF or reading an insertion
cursor. Only that observed nonzero-item lookup contract motivates this reader.

Qualification compares the original canonical journal with experiment off and
on, uses actual SDL keyboard/controller events, and exercises cold restore,
in-process restoration to an absent-item fixture, and a real console reset.
The same inline predicate has ROM-free checks for every slot, bounds, read-only
behavior, unrelated story/stage bytes and removal. These are host/state proofs,
not natural award/removal gameplay, full campaign, hardware-controller or paced
GPU/audio certification.

The October 9 private polished candidate passed 101 integration checks across
33 finite native runs plus 199 checks against the same pure inline predicate.
Positive-card pixels outside the existing rectangle match the original guest
framebuffer exactly; shortening its header repairs the inherited long header's
overflow without changing the canonical no-item/off card. Evidence and images
stay private under `local/evidence/journal-staged-20261009/field-final2/` in the
owner workspace. The experimental binary remains separate from installations.
