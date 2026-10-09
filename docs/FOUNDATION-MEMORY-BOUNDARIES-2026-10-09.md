# Map memory boundary checks: October 9, 2026

The owner pointed out that cutscene crashes in other ports can come from buffers
and memory handling. This focused follow-up tests this game's actual standard
map decoder, alongside the separately reproduced and repaired mosaic overrun.
It changes no native source, guest state, installed executable, timing or saves.

`tools/check_foundation_map_memory.py` compiles the qualified decoder with
Clang undefined-behavior traps. A private child process supplies exact-size
original-ROM and WRAM buffers with inaccessible guard pages immediately before
and after them. Any boundary access or detected undefined operation fails the
child rather than silently continuing. Invalid ROM size tests deliberately use
an inaccessible pointer to ensure rejection occurs before hashing or reading.

All 248 inventoried original primary resource tuples pass:

- 20,088 signed coordinate pairs, including INT_MIN and INT_MAX, independently
  compared to original resources with authentic wrapping/boundary rules.
- 6,200 malformed primary resource/dimension cases refused before publication.
- 6,200 subsequent valid cache recoveries without stale failure state.
- 2,732 invalid argument tests, including null pointers and incorrect sizes.

The output word remains untouched on refused queries. Actual source and original
ROM hashes are checked before/after. Initial evidence is
`local/evidence/map-memory-20261009-1510/report.json`; the installed native source
identities remain `c94be434...` for the decoder and `8e1cc13d...` for its header.
This proof concerns host map buffers and caches. It does not certify every
cutscene, actor constructor, checkpoint buffer, GPU upload or campaign path.

The next focused contracts cover party records, reserved sprite slots and
optional secondary scene streams. Unsupported presentation retains the original
center and side bars while those interfaces are established. No generic extra
buffering or memory expansion is added without evidence of a specific failure.
