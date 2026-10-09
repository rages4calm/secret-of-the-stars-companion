# Reserved B0 mode acquisition — October 9, 2026

This focused read-only continuation of the
[scene-writer assessment](FOUNDATION-B0-SCENE-WRITERS-2026-10-09.md) identifies
the original travel mechanic as the **Algos UFO**. The original acquisition
script can establish the saved B0 scene before boarding; bit 80 of `0409` is a
travel mode, not the acquisition flag. No natural active B0 fixture was created
or executed, and no widescreen guard or installation changed.

Private evidence is `local/evidence/b0-mode-acquisition-20261009/report.json`,
SHA-256 `51b6ea193c2d304b7e23bd9107341928553262d553c13e4dbc75af9b42dac6df`.
The curated `verified-source-disassembly.txt` separates instruction ranges from
inline dispatch data. Exploratory files contain raw candidates and some spans
that cross data or unverified CPU widths; they are not the final instruction
evidence. ROM-derived bytes, text and disassembly stay private. The clean USA
ROM was hash-checked after this read and remains unchanged. No guest execution,
RAM fabrication, save operation, source/runtime edit or build occurred.

## Original acquisition and first saved-scene write

The original message dispatcher selects message `0607` through group descriptor
`02:BC4F`, pointer entry `06:800E`, indirect record `06:820E`, and stream
`06:8566`. The extra indirection is implemented by `02:BA98`; interpreting the
record itself as dialogue would give the wrong stream.

This stream requests inventory items `77..7B` and removes their selected slots
through the original item routines. It then announces Algos acquisition and
executes the scene-save command at `06:85A2`. This identifies the vehicle using
the original game, independently of a walkthrough. The stream does not by itself
prove that the enclosing field event checked all prerequisites before selecting
message `0607`.

The command reader at `02:AA87..AAB2` dispatches escaped command 31 through
`02:9106`, `02:AC03` and table entry `02:AC69` to `02:B4EC`. That handler selects
one of four saved-scene addresses from `02:B52A`, constructs a bank-7E pointer,
and performs the original indirect store at `02:B50E`. Slot 3 is `7E:5441`.
The acquisition argument sets it to scene `0136`; this is a genuine bootstrap
writer and does not require the preexisting source-scene match discussed in
the previous assessment. The special scene-0136 branch also sets `0491=40`
and `048F=80`. The following original command at `06:85A7` assigns party source
scene `0141`, with coordinates `0100/0380`, through `02:B76F`.

Those scene numbers are source identities. This assessment has not independently
mapped them to named locations or traced the field event record selecting
message `0607`. A raw occurrence of that message word elsewhere is not sufficient
to identify its natural caller.

## How bit 80 is acquired and retained

`01:A559` is the confirmed literal sign-setting store in the checked direct
writer family: selector 4 writes `0409=82`, restores the camera and current
scene from the saved B0 source, and reloads through `01:C400`. This is the
return from the shared scene-2 interior to active travel. After acquisition,
the parked B0 proxy permits the original boarding action, which enters scene 2;
the selector-4 return enables travel. Acquisition and the travel-mode return are
separate steps.

`02:DD76` can also restore a previously saved mode from `7E:5457` when switching
parties. This retains an existing vehicle state; it does not explain first
acquisition. The direct-store/bit-operation scan is bounded and is not a proof
that every generic indirect event write in the whole game has been found.

The original action in the signed mode can take selector 5 back into the
interior, preserving the current source through `01:A5DA`. Selector 4 resumes
travel and keeps the sign gate set; selector 6 returns to ordinary movement and
clears it. These routes must remain distinct when constructing a B0 fixture.

## Original selector-6 exit and refusal conditions

The original exit-table reader at `01:9851` recognizes exit type 4 and jumps
from `01:98A9` to `01:994C`. That validator first requests `0554=80` and sets
the movement-request bit. It changes the request to `C0` when the saved terrain
is unsuitable or the other party occupies the exact saved source/camera position.
The accepted terrain values in this branch are `00` and `08..0B`; the other
party's signed travel mode bypasses the position refusal. These are confirmed
numeric conditions, not a newly inferred collision policy or landing override.

The movement-kind dispatcher at `01:9C3E` sends kind 4 to `01:9EDE`; kind 16
enters `01:9E94` and can reach the same tail after reading its exit destination.
With a nonzero request and bit 40 clear, `01:9F14` clears the request, unwinds
the two saved return bytes, clears the loading flag, advances the field task,
and dispatches selector 6 through `01:8C2D`. A `C0` request clears and returns
without that unwind. Selector 6 then restores `5441` and the saved camera while
clearing `0409/0408`, as established previously.

This resolves the original enclosing exit/movement caller. It does not identify
which particular named interior stair uses that exit record in a live run.

## Smallest natural fixture and remaining gate

A walkthrough corroborates a late-game Algos route involving the five metal
items, the Old Hill shrine after Godem, and its launch console. It also describes
walking inside the vehicle and returning outside. These location/story details
are external corroboration; the exact selecting field record and its flags
remain untraced. [Secret of the Stars walkthrough](https://retromaggedon.com/index.php/tecmo-secret-of-the-stars-snes-walkthrough/).

The fourteen bounded early samples from the natural actor assessment all have
`0409=00` and `5441=FFFF`. No short natural acquisition route from those samples
has been demonstrated. No supplied title guide/manual was found by the bounded
filename search of the reference cache; this does not claim the cache contains
no relevant content under other names.

The next useful fixture is a copied checkpoint already naturally at the Algos
acquisition event, or already inside/across its original travel return. Preserve
the original configured actions and observe message `0607`, command 31's actual
slot/scene store, selector 4/5/6, `0554` acceptance, caller/task/direct-page,
scene/mode and coordinates before and after. For a parked B0 picture, require
the natural sign-clear return and a matching saved/current source scene.

Then retain the separate constructor and presentation gates: the actual
`01:DB68` descriptor, B0 base write, completed 544-byte staging/DMA packet,
original-art opacity and raster identity, exact center/guest parity, and derived
cache reset on restore. A static acquisition writer or an invisible naturally
reached descriptor does not qualify visible B0 margins. Do not synthesize
inventory, story flags, `5441`, `0409`, poses or coordinates to replace the
missing natural checkpoint. Installed large/composite/wrapping guards retain
their existing status.
