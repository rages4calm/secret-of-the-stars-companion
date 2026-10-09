# Reserved B0 scene writers — October 9, 2026

This narrow read-only follow-up identifies the original scene-save/return chain
behind the two writers named in the
[natural actor assessment](FOUNDATION-ACTOR-NATURAL-ASSESSMENT-2026-10-09.md).
It does not produce a natural active B0 fixture or qualify rendered B0 margins.
Native 0.2.0 and Companion 0.3.0 remain unchanged. No guest run, RAM edit,
checkpoint creation, source/runtime change, build or guard promotion occurred.

Private evidence is `local/evidence/b0-scene-writers-20261009/report.json`,
SHA-256 `132c5e6f90f3a65b6a644aeb3d5cda708368633218b03ef4729205df214c62f2`.
Its verified disassembly and original-byte spans remain private. This document
contains authored findings and address references, not copied game instructions
or assets. The exact clean ROM was hash-checked after the read and is unchanged.

## Confirmed original dispatch and writers

`01:8C2D` enters the indexed field-mode dispatcher at `01:A15A`.
The shared dispatcher at `00:84D9`, reached through `00:FF20`, selects the
same-bank address from the table beginning at `01:A160`. Selector 3 enters
`01:A4E0`; selector 5 enters `01:A57A`; selector 6 enters `01:A620`.
The table is data and is not interpreted as an instruction stream.

Both investigated writers save the scene that was current **before** a scene
transition. They also save the original camera plus the screen-center offset
(128,112) into the B0 source coordinates at `7E:544B/5455`, through the original
coordinate helper and its wrap handling. They then select scene 2 and reload
through `01:C400`. A writer hit alone therefore does not prove that the original
B0 source scene matches the newly loaded scene.

| Route | Scene store | Confirmed local entry condition |
| --- | --- | --- |
| Selector 3 / `01:A4E0` | `01:A534` | Normal field action reaches `01:8D48`; `0409` bits 20/80/40 are clear and the original object-hit result `0403` is 90 hex. |
| Selector 5 / `01:A57A` | `01:A5DA` | Normal field controller reaches its `0408=0` action branch; the lower-priority action mask at `04B0` matches `02E3`, the earlier `04B2` action branch does not take priority, and `0409` bit 80 is set. |

These are original masks and field modes, not physical controller labels.
Existing explicit bindings and the game's current masks remain authoritative.
Selector 3 first executes original event DB hex; selector 5 runs its original
sound/control setup. The story names of these events and the travel object are
not established by this decoding.

## Why the selector-3 interaction cannot bootstrap the early fixtures

The original hit-list constructor at `01:9523..95C3` walks regular records and
records their original interaction coordinates at `7E:4092`. The lookup at
`01:95EE..960B` returns hit codes 80–91 hex. Hit 90 is index 16: regular
record 16 at `7E:4290`, rather than an arbitrary map tile or unrelated NPC.

The existing special-actor source path activates that proxy at `01:CFF2` only
after `7E:5441` already matches current `040E` and `0409` has its sign bit clear.
Thus selector 3 depends on an already established B0 source. Asking the current
opening fixture to interact with an object does not establish the missing source
scene. All fourteen previously sampled early checkpoints have `0409=00` and
`5441=FFFF`; this follow-up reused that bounded assessment, without resampling
the campaign or assigning a gameplay identity to an invisible record.

## Return route and the precise unresolved prerequisite

Selector 6 at `01:A620` clears `0409/0408`, restores the saved camera from
`0492/0494`, restores current scene from `7E:5441`, and reloads through
`01:C400`. Its original dispatch is visible in the unwind tail at
`01:9F14..9F21`; the enclosing natural event/caller has not been established.

After that return, the static source conditions can permit the normal B0 path:
`01:CFD4..CFE5` requires `0409` sign clear and `5441 == 040E`;
`01:CFF6` activates record 18; `01:D045` assigns base B0. Actual
`01:DB68` constructor context and complete 544-byte staging/DMA/scanout identity
still need original execution. The alternative selector-4 return at
`01:A54D` restores the saved scene but sets `0409=82`, which fails the sign gate;
it is not interchangeable with selector 6 for this proof.

The smallest bounded follow-up is a copied checkpoint **already naturally in
the original bit-80 field mode**, followed by its configured original action,
the `01:A5DA` scene save, and the original selector-6 return. Another useful
starting checkpoint would already have matching source/current scenes with
the sign gate clear. Neither prerequisite is present in the fourteen checked
early samples. The story script/event that first grants bit 80 or establishes
the saved B0 source, and the natural selector-6 exit trigger, remain unresolved.
This is a precise prerequisite gap, not a proposed campaign walkthrough.

The next observation should retain the dispatcher selector, original caller/
task/direct-page context, scene and mode before/after the store/return, source
coordinates, activation/base writes, actual constructor descriptor and completed
packet. Positive original-art opacity, raster/color/terrain overlap, center/
guest fidelity and restore reset remain separate gates. Do not set `5441`,
`0409`, a base, pose or coordinate to manufacture a natural fixture. The private
B0 canary and installed large/composite/wrapping guards retain their existing
status.
