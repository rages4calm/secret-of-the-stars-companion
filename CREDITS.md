# Credits

## Project work

**Carl Prewitt Jr. ([rages4calm](https://github.com/rages4calm))** maintains the
Secret of the Stars Companion project, its game-specific native enhancements,
Windows launcher integration, inspection/replay tools and development direction.

The Companion adapts original MIT-licensed UI/navigation patterns from
[EarthBound Companion](https://github.com/rages4calm/earthbound-companion), also
by Carl Prewitt Jr. [Zelda Companion](https://github.com/rages4calm/zelda-companion)
informed the launcher workflow and presentation goals. Another project's game
assets, Redux conversion or randomizer code are not included here.

## Runtime and incorporated lineage

| Credit | Role |
| --- | --- |
| **Matthew Stanley and contributors — [RetroPortingToolKit/snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp)** | Pinned shared runtime, analyzer/scaffolding, hardware execution, desktop host and upstream enhancement framework; PolyForm Noncommercial 1.0.0 |
| **snesrev and contributors — [zelda3](https://github.com/snesrev/zelda3), [smw](https://github.com/snesrev/smw)** | Retained upstream SNES runner/hardware/input/widescreen lineage; MIT notices remain applicable |
| **angelo_wf / elzo_d and contributors — [LakeSnes](https://github.com/angelo-wf/lakesnes)** | Retained 65816 interpreter lineage; MIT |
| **Near and contributors — [ares](https://github.com/ares-emulator/ares)** | Shared runtime coprocessor lineage; ISC; inclusion does not imply this game uses those chips |
| **Colin Curtin — [perplexes/snesrecomp](https://github.com/perplexes/snesrecomp)** | Analyzer foundation acknowledged by the upstream Rust recompiler; MIT |
| **Sam Lantinga and SDL contributors — [SDL](https://github.com/libsdl-org/SDL)** | SDL3 3.4.10 windowing, rendering, audio and input; zlib license |
| **Matthew Stanley / [psxrecomp](https://github.com/mstan/psxrecomp), JRickey / [gba-recomp](https://github.com/JRickey/gba-recomp)** | Shared color-LUT lineage; exact retained notices are under `licenses/color-lut/` |
| **Jason McKesson — [glLoadGen](https://github.com/Alfonse/glLoadGen)** | Upstream generated OpenGL loader |
| **Sean Barrett and contributors — [stb](https://github.com/nothings/stb)** | Upstream image-loading dependency; MIT/public-domain licensing |
| **SupraBT / StarOceanSNESRecomp, Andreas Naive, Brad Jorsch and John Weidman** | Upstream S-DD1 implementation/research lineage; see the retained runtime attribution for its exact scope and notices |
| **retcomm-rbengine and recomp-net contributors** | Upstream shared infrastructure/submodules; recorded pins are retained, but this project does not implement netplay |
| **.NET Foundation and contributors; Microsoft** | .NET/Windows Desktop/WinForms launcher platform and runtime; retained notices under `licenses/` |

The full upstream attribution is retained verbatim in
[`licenses/SNESRECOMP-THIRD-PARTY-ATTRIBUTION.md`](licenses/SNESRECOMP-THIRD-PARTY-ATTRIBUTION.md).
Its upstream-relative paths and historical notes remain unchanged. Consult the
pinned runtime for the corresponding source files; this repository publishes
the project patch rather than vendoring the entire runtime.

## Scale2x

**Andrea Mazzoleni** developed Scale2x. This project's enhanced-pixel pass is an
independent implementation of the [published algorithm](https://www.scale2x.it/algorithm),
with project-specific tolerance/presentation behavior. It does not import the
Scale2x GPL source library. [Authors](https://www.scale2x.it/authors) ·
[Algorithm-use information](https://www.scale2x.it/download).

## Research and inspiration

These credits acknowledge references, not bundled implementations or a promise
that their features work in this game:

- **BlueImp78 — [Secret of the Stars Battle Info Hack](https://github.com/BlueImp78/Secret-of-The-Stars-Battle-Info-Hack)**:
  battle-state research. No license was found in the inspected source. Its
  assembly, patched ROM and cached source are excluded. The current enemy-HP
  panel is authored native code; this project does not distribute the hack.
- **kandowontu2 and contributors — [Star Fox Enhanced](https://github.com/kandowontu2/starfox-enhanced)**:
  separated logic/render timing and performance reference.
- **Matthew Stanley — [MegaManXSNESRecomp](https://github.com/mstan/MegaManXSNESRecomp)
  and [MegaManX2Recomp](https://github.com/mstan/MegaManX2Recomp)**:
  CPU-budget and sprite-limit architecture references.
- **Cellenseres and contributors — [Lufia2SNESRecomp](https://github.com/Cellenseres/Lufia2SNESRecomp),
  [Lufia2Decomp](https://github.com/Cellenseres/Lufia2Decomp),
  [snesrecomp-platform](https://github.com/Cellenseres/snesrecomp-platform)**:
  SNES port/recompilation workflow references.
- **blackerking and contributors — [UrbanRecomp](https://github.com/blackerking/UrbanRecomp)**:
  game-native presentation/reference work.
- **RPGHacker and Asar contributors — [Asar](https://github.com/RPGHacker/asar)**:
  tool used in a private assembly experiment; the tool and that experiment's
  unlicensed source are not bundled.

## Original game

**Tecmo and the original Secret of the Stars creators/rightsholders** retain
credit and rights for the game, its art, music, text, characters and trademarks.
This is an unofficial fan project, without affiliation or endorsement.
No project license grants rights to the original ROM or content generated or
extracted from it. Every developer/player supplies their own original input.

Corrections to attribution are welcome through a focused issue or pull request.
