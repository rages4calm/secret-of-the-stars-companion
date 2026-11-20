# Secret of the Stars 0.5.14.2 — pacing fix

Removes an unnecessary full-frame delay when the PC has already missed its
next frame deadline. Normal-speed limiting, loader debt handling and turbo
scheduling retain their existing behavior. Game logic, saved-state layouts
and native feature version 0.5.14 are unchanged. Companion remains 0.3.8.
All existing features and the 0.5.14.1 Setup fix remain.

Supported field/title scenery now follows original fade brightness instead of
losing its side margins whenever brightness drops below maximum. Deliberately
blank scanlines remain black without invalidating the rest of a wide frame.
Original center checks and unknown-resource/mosaic fallback remain in place;
this is not a claim that every transition effect now has wider scenery.

Early Current journal advice now explicitly points to Winds' southeast house
and Beegees' church instead of masking those directions with a vague town-building
objective. The full story guide and progression flags are unchanged.

An affected i3-10110U laptop confirmed the repeated ~15.7 ms waits disappeared
in the diagnostic build. It still measured 20–26 FPS at the title screen: game
execution and CPU raster work remained expensive. Those runs changed renderer
and power settings, so their FPS difference is not a controlled benchmark.
Both samples had audio disabled. The player reports overheating; throttling is
plausible but has not been measured or established as the sole remaining cause.
The issue is not declared resolved. Switching graphics APIs alone is unlikely
to address the dominant measured CPU work.

Source review identified repeated per-instruction native lookup and state
synchronization as a further optimization candidate, not a measured root cause.
No speculative backend changes are included in this hotfix.

Download the ROM-free ZIP and extract it into a fresh folder. Run Setup using
your supported clean USA ROM. An already-built installation needs rebuilding
from this updated source to receive the runtime fix. No ROM or native game
executable is distributed. Campaign-wide native/AOT execution is not certified;
guarded compatibility fallback remains enabled.
