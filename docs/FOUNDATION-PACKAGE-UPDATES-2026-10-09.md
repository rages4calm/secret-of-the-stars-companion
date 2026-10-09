# Companion packaging and profile updates — 2026-10-09

Companion 0.3.0 adds safe updates and rollback for isolated source-first native
profiles. The qualified local native foundation remains 0.2.0. Its executable,
owner settings, SRAM and checkpoints are retained unchanged.

## Update and rollback behavior

Setup can adopt a real source compilation receipt as before. **Update selected profile**
instead copies the selected profile into a new unique folder, preserving its
settings, saves, backups and unknown files, then replaces the native executable
and build metadata there. Selection changes atomically only after both source
and destination pass the final checks. The old folder is retained.

**Use previous profile** rolls back to the retained predecessor. Progress made in the new profile
stays there; rollback does not merge or discard it. Nested updates retain their
history. The existing owner installation is not automatically imported into
this source-profile workflow.

Busy games/builds, stale selectors or source receipts, linked paths, pending
Resume copies and interrupted copies refuse selection changes. Different native
executables require declared compatible checkpoint identity/schema, SRAM format
and the same execution-state ABI. A receipt without that declaration can reuse
an identical native executable; it cannot establish compatibility with a changed
one. Unknown or ambiguous checkpoint formats are refused. No state conversion
is attempted.

The native builder now records these declarations from the frozen state sources.
Two real builds with different executable hashes exercised the changed-binary
case. This is conservative compatibility evidence, not campaign certification
or a promise that future gameplay changes can reuse all saves.

## ROM-free portable launcher

`tools/package_companion.py` packages exactly the tracked authored source and
one self-contained Windows Companion executable. It excludes the native game,
ROM, generated game bodies, extracted art/music, player profiles and saves.
Verbatim dependency notices remain included. The package retains source/build
instructions and an integrity manifest; `tools/verify_companion_package.py`
checks all recorded file bytes without running the executable.

The prebuilt GUI runs without Python or the .NET SDK. Building the native game
still requires the documented development tools and the user's matching owned
ROM. A fresh package can move before setup. Configured native profile receipts
currently contain absolute paths: keep the configured root stable. Automatic
GUI release downloads and configured-profile migration remain future work.

Package/source compilation metadata deliberately says `compiled_unqualified`.
Local integrity does not authenticate a publisher, and neither an archive nor
successful compilation qualifies gameplay. The separately tested GUI artifact
has SHA-256
`44e6df260925c91b25882bb4be29107bfc7672b3ef52bf06a9baf54068c0bb07`.
Native 0.2.0 remains
`9241f79ea1a685e0932282c300081a90f9becf503f9a17c5fe6a94b34a08a7e0`.

## Bounded qualification

The exact GUI passed 52 update/history/failure/layout checks, 60 source-first
backend checks and 31 QoL GUI checks. Update and rollback each executed an actual
180-frame copied-checkpoint restore. Legacy qualification passed 55 backend and
nine GUI checks plus all six finite launch routes against the unchanged native
0.2.0 artifact. These counts describe separate checks, not additive campaign
coverage.

The package passed 13 integrity/startup/relocation/refusal gates, including real
visible Windows startup with SDK/Python removed from PATH, spaces/Unicode/shell
characters, changed binaries/manifests, escaped paths and retained user data.
Protected installation and installed-window checks are recorded privately.
Physical controllers, other hardware and the full campaign remain separate.

## Widescreen continuation

The [natural actor assessment](FOUNDATION-ACTOR-NATURAL-ASSESSMENT-2026-10-09.md)
found a naturally reached ordinary actor descriptor outside the original view.
Both observed animation frames resolve transparent artwork. This fixture proves
bounded coordinate and guard behavior; it does not qualify visible wrapping
sprites. Large/composite/wrapping guards remain installed. Follow the actual
regular-actor graphics base writer and B0 current-scene activation before
removing those guards. Broader scene coverage, measured native/AOT work, further
verified journal milestones and conditional MSU-1 integration remain open.

The [allocation follow-up](FOUNDATION-ACTOR-ALLOCATION-2026-10-09.md) observes
the original source-pointer/base stores and reserved-B0 refusal. Visible party
art from the same VRAM provides a positive decoder control; the selected ordinary
world record stays transparent. These checks add evidence, not a new rendering
feature or permission to enable the unsupported actor families.
The [B0 scene-writer follow-up](FOUNDATION-B0-SCENE-WRITERS-2026-10-09.md)
identifies the original scene-save/return dispatcher and the circular early
interaction gate. Natural acquisition of bit-80 mode and its selector-6 return
still need a fixture. Static gates do not establish original activation or art.
