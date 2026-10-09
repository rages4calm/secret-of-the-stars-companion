# Menu correctness, battle-display controls and synchronized presentation

This continuation supersedes the earlier October 9 menu build. Read the original
handoff and porting references for the preserved native-port direction. Current
qualified executable and test paths are recorded in `local/evidence/build-receipt.json`.

Installed executable SHA-256:
`e5caa27db76ac3faa321ea452821589d8d943f9519f970667eb6dc6f1087e8f8`.
Installation receipt: `local/evidence/player-ui-repair-20261009.json`.
The hash-verified backup is `local/owner-backups/ui-repair-20261009-104638`.
All owner saves, original/working ROM hashes, keybinds and enhancement preferences
were retained. Graphics Renderer/OutputMethod/VSync were the only configuration
values changed; fullscreen and sound settings were retained.

## Owner reports and reproduction

The owner reported a clipped STATUS/SORT panel, intermittent background flashes,
an unclear enemy-HP toggle and visibly torn/lagging downward scrolling. The owner
also observed the scrolling defect during our real Windows diagnostic; a steady
frame-rate counter does not contradict that observation.

The prior broad FastMenus batching reproduced the missing submenu border in a
copied indoor fixture. Original timing kept the border intact. BG3 tilemap bytes
confirmed missing border words, rather than an output-scaling explanation.

Native batching now excludes row-upload waits inside interactive routine
`02C000` (guest return `029152`). These share asynchronous submenu/cursor producers
and must retain their frame handoff. Validated outer construction and slide waits
remain eligible. Interactive slides are eligible only for the four validated
slide call sites; interactive row producers remain excluded. Context is derived
from active guest stack and original call instructions, with the existing queue
validation and finite per-frame budget.

The regression tool walks all six menu selections in indoor and outdoor copied
fixtures. It compares submenu, returned-menu and closed-field BG3 maps with
original timing, normalizing only the cursor palette blink bit. The earlier
binary must reproduce mismatches for the regression to pass. This bounds the
claim to those scenes and selections. A static background crop did not reproduce
the separate flashing report; other transient background artifacts remain open.
The main-menu pixels open in three guest frames and close in one in the checked
fixture, versus 21 and eight originally. Completion of visible rows does not
prove the interactive routine is already accepting another button. The earlier
four-frame confirm check used VRAM differences as its success signal, which was
insufficient. It is retained as a diagnostic, with rapid back not returning to
the field. Required checks now compare completed submenu maps with original
timing and verify field pixels after back. Input buffering during construction
is outstanding; do not promise instantaneous submenu interaction.

## Enemy-HP display

The display is our optional native `BattleInfo` enhancement. The old “X:HIDE”
label referred to the SNES X button, which the keyboard maps to S; literal
keyboard X is confirm. The new label explicitly offers **H** or **right-stick
click**. Both use SDL event paths independently of keyboard gameplay-seat routing.
Held-key repeats do not toggle repeatedly. The old SNES-X shortcut remains.
Select plus right-stick click still belongs to rewind, and reset/overlay recovery
clears queued HUD input.

`tools/check_foundation_hud_input.py` checks actual SDL keyboard events and a
virtual controller, hidden pixels matching original output, once-per-press
toggles and identical guest dumps. Physical owner hardware is not newly certified.
`BattleInfo=0` remains the persistent off setting in `foundation.ini`.

## Scrolling and presentation

The former profile requested `VSync=1`, but the software presenter logged actual
`vsync=0`. The SDL3 compatibility helper deliberately skips setting VSync on its
software renderer. The local display reports approximately 74.970 Hz, compared
with the original guest simulation's 60.098812 Hz.

The Direct3D 11 trial reports actual `vsync=1` in fullscreen and preserves six
final guest captures exactly between original and enhanced pixels. The finite
town walks include both horizontal and downward movement. GPU presentation is
now the player default. A one-time launcher migration backs up the known former
software profile, changes only Graphics Renderer/OutputMethod/VSync, and retains
fullscreen, sound, input bindings, enhancement preferences and saves. Custom
renderer choices and subsequent edits remain untouched.

The original software walks already sustained approximately 60 guest frames per
second, with work well below the frame budget. Camera scroll coordinates changed
on consecutive moving frames in the checked route. This does not measure tearing
or physical latency. GPU synchronization addresses the confirmed disabled-sync
condition; 60-to-75 Hz cadence can still look uneven. No display refresh settings,
guest CPU speed, movement speed or game/audio timing were changed. No interpolation
or blanket framebuffer blending was introduced. Further work should distinguish
display cadence from genuine guest slowdown before considering selective native
replacements or title-specific camera interpolation.

See [the focused guest CPU assessment](FOUNDATION-CPU-PERFORMANCE-2026-10-09.md).
The beam driver preserves original master-clock budgets; faster PC/AOT work can
therefore retain hardware slowdown. This is a separate target from output sync,
and the owner explicitly requests removing such bottlenecks where proved.

SDL's documented interfaces support explicit renderer selection and querying
VSync results: [SDL_CreateRenderer](https://wiki.libsdl.org/SDL3/SDL_CreateRenderer),
[SDL_SetRenderVSync](https://wiki.libsdl.org/SDL3/SDL_SetRenderVSync).

The final fullscreen GPU walk maintains approximately 60.10 guest frames per
second. Enhanced presentation's median total processing is 7.01 ms, p95 7.58 ms;
no measured presentation interval exceeds 25 ms. These dispatch measurements do
not capture display scanout or prove perceptual smoothness. The installed copied
cold-run reached Windows video, actual VSync=1 and nonzero audio at 0.271 seconds.
Title-first launch, original-view overrides, fullscreen transitions, refused
checkpoint handling, virtual-controller gameplay/overlays, HUD toggles, v1/v2
audio replay and malformed checkpoint guards pass. Latest results, including the
remaining rapid-input diagnostic failure, are preserved in the build receipt.

## Quest-journal foundation assessment

A native journal is feasible using the existing text/composition, SDL input and
post-frame/reset interfaces. It does not require expanding the guest menus or
redistributing modified original assets. The first bounded target should be an
observed-clue log for the opening chapter, then verified completion milestones.

Captured David dialogue says to seek the **Crest of Stars** and places it
“somewhere in the mountain.” Those are observed clues, not a verified mountain
map identity or completion predicate. Private evidence is recorded in
`local/evidence/quest-journal-assessment-20261009.json`, with captured dialogue pages.

The subsequent [journal event assessment](FOUNDATION-JOURNAL-EVENTS-2026-10-09.md)
identifies David message ID `0x0749`, observed lead stream positions and the
introduction bit `WRAM 0x5360 & 0x40`. This bit is stage-scoped and resets later;
it is neither Crest completion nor a permanent historical journal. Static text
consumer `02:AA8D` is a candidate hook; dynamic hook coverage remains unverified.
The private receipt is `local/evidence/journal-events-20261009.json`.

Next, trace the guarded consumer dynamically, verify the crest acquisition flag
and relevant location IDs before automatic completion. Reconcile entries on
new-game, checkpoint load and rewind; do not infer story completion from a
temporary menu buffer or expose unseen quests. Start with observed leads and a
small explicit event table. **No journal UI, persistence or automatic quest
tracking is implemented in this release.**

## Preserved scope and next work

Normal launch remains title-first; explicit fixture resume is separate. Owner
ROM and latest saves stay protected, and all reproduction uses copied fixtures.
Original View disables the optional gameplay/pixel enhancements while retaining
synchronized presentation. Most CPU execution remains interpreted; the seven
experimental AOT WRAM differences and reference timing/NPC divergence remain open.

Actual HD replacement art, populated true widescreen scenery, added content and
a verified compatible MSU-1 driver/pack remain outstanding. Scale2x is selectable
enhanced pixel art, not replacement HD artwork. Next focused work is the bounded
CPU-deadline observation, a first observed-clue journal consumer proof, and map loading/streaming
for correct side scenery and persistent resource identities. Reuse owner-provided
EarthBound/Zelda tools when applicable without editing their installations.
