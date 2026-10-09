# Isolated live B0 integration — October 9, 2026

The B0 prototype now builds against the current native 0.2.0 foundation and
executes the real interpreter observer and DMA-engine interfaces. Its
**ordinary-actor fidelity is checked; natural B0 rendering remains unqualified**.
The owner keeps native 0.2.0 and Companion 0.3.0. No owner installation, save,
setting, canonical native input or runtime patch changed.

## Reproducible experimental source

The alternate authored module is
[`experiments/b0/foundation_wide_actors.c`](../experiments/b0/foundation_wide_actors.c),
SHA-256 `56d50e2bb30bfb57bed71acc64e3a69fc6c47aa279ed9d2cfc6cfca058502316`.
It reuses the published ROM-free large-actor helpers. The normal foundation
build does not select it; canonical actor SHA-256 remains
`57456b84c79601f1ce3756b3caea6eb18923f777e0502e70fdef886866ae2d88`.

[`tools/build_experimental_b0.py`](../tools/build_experimental_b0.py) takes a
real matching canonical source-build receipt and owned ROM, validates the source
and pinned patched runtime, and compiles into a fresh ignored experimental
folder. The canonical build and generated inputs remain unchanged. There is no
ROM, original generated code, artwork, save or binary in the public source.

Its `compiled_unqualified_experimental` receipt is deliberately distinct from
normal native build metadata: `public_build=false` and
`matches_authored_snapshot=false`. Normal Companion Setup's canonical-status
check refuses that receipt. The helper creates no owner profile or passing
gameplay receipt. [Build instructions](../experiments/b0/README.md).

The helper was exercised against the actual owned ROM and matching current
48-input build. The resulting experimental executable has SHA-256
`98fdf7fa43207feed5af791def8ee510ac3f36f0a46be9df32ead3019c3af021`.
The runtime pin and seventeen-file patch are unchanged. Compilation is separate
from the bounded checks below. A prior private candidate has its own hash,
`da13266a9d498816c180b6150fd494936f27bb03aba370b656771cbcd0c45af0`;
both candidates were checked separately rather than transferring qualification
between executable hashes.

## Actual guest and DMA evidence

The exact public-helper candidate passed the existing 78 ordinary actor gates
across 13 finite routes: ordinary and enhanced-pixel margins, menus, copied
checkpoint creation/cold restore, actual rollback and original-width behavior.
Observed original metadata joins the complete packet and actual DMA completion;
the ordinary NPC artwork genuinely enters and leaves the original view.

A separate six-process comparison uses the installed native 0.2.0 executable
and the experimental candidate on identical copied town, menu and natural
world-entry inputs. All **133** WRAM/VRAM/SRAM/OAM/CGRAM/register/original-picture
comparisons match. All **16 complete 400-pixel host surfaces** match, including
their original centers. The wrapping-world guard continues to refuse its
derived packets. Both probes retain exact input and owner hashes.

Passive counters show real original ordinary producer hooks and real OAM
transfer starts/completions in these guest runs. For example, the 115-field
ordinary sweep observes 115 producer starts, 115 transfer starts and 115
completions; 114 packets become valid and genuine margin art is drawn. The
extra party/regular B0 constructor hooks at `01:D989` and `01:DB68` each have
**zero hits**. Their registration is not misreported as B0 execution.

## Separate synthetic B0 raster proof

The same exact experimental module was separately linked with the actual PPU
and existing independent oracle. Eleven aggregate checks pass across **56
synthetic host cases** and **1,806,336 margin pixels**. The registered-callback
driver tests fixed slots 0/1, descriptor/coordinate/transfer guards, last-writer
behavior, checked completion/reset, palette/flip/window/fixed-color behavior and
ordinary coexistence. Five genuine ordinary packet pairs retain their full
outputs. These host contexts are not naturally activated B0 actors.

Original-center parity in this oracle is the deliberate authentic-center
stitch, not an assertion that the empty-OAM private margin PPU independently
renders the original center. Full terrain/OBJ occlusion, subscreen/half-color
combinations, arbitrary raster windows and world-edge timing remain open.
Headless/silent proofs do not qualify paced GPU/audio or physical controllers.

Private aggregate evidence:
`local/evidence/b0-live-integration-20261009-final/assessment-report.json`.
It records exact source/build/report hashes, both installed artifact hashes,
the protected owner inventory and the separate scope/counts. The first failed
private build, missing its generated `funcs.h` copy, is retained; the final
helper explicitly copies that generated header into its isolated output.

## Remaining natural gates

The [Algos acquisition trace](FOUNDATION-B0-MODE-ACQUISITION-2026-10-09.md)
identifies original message `0607`, its saved-scene bootstrap, travel-mode return
and validated selector-6 exit. Its selecting field event/story conditions and a
naturally reached checkpoint remain missing. No short acquisition route from
the sampled opening saves is established.

The [later ordinary wrapping source](FOUNDATION-WRAPPING-VISIBLE-SOURCE-2026-10-09.md)
requires stage 17 and original flag selector 9 clear. All fourteen sampled
fixtures remain stage zero. Its changed primary stream/grid, actual graphics
upload and opacity must be authenticated in that later state.

Before promoting this module, require a naturally reached original B0
constructor, nontransparent original art, complete displayed-packet lineage,
terrain/OBJ/color/raster fidelity, cold restoration and a real rollback across
activation. The prototype still uses guarded eligible nonwrapping fields;
general wrapping and world-edge support is not granted by the B0 decoder.
The installed large/composite/wrapping guards remain intact.
