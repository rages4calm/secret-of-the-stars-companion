# Map coordinates and town clues — native 0.3.1 / Companion 0.3.4

The installed continuation corrects town/objective coordinates and adds two verified current town-building clues. The Companion executable is unchanged. Complete native/AOT execution and full-campaign rendering remain unfinished.

## Exact compilation

| Artifact | SHA-256 |
| --- | --- |
| Native executable | `83ddd8e3fe96d3a57e43d88426198b365f5fb1271a02c349072bf146cdc86c30` |
| Native source receipt | `85177ace5a4252ca39f3db30d4456fe4c1edf00e611ef20a2c595634f6d0f1f8` |
| Unchanged Companion executable | `b6328fc599f9712246a4c24dfadcf6cb200cd4a1a1a561bc1775514d9fac34d0` |
| Unchanged Companion source receipt | `f7a714c015540140c40074c967353fd05854a6a23b9ff367eec5e55301b48faa` |

The native build is `local/source-builds/20261011-152418`, with 58 authored inputs. Companion retains 24 inputs and its existing 0.3.4 compilation. Immutable receipts remain `compiled_unqualified`; exact qualification and installation are separate. The runtime pin, four patches and declared guest/checkpoint ABI are unchanged. Earlier 0.3.0 reports retain their original artifact scope.

## Original entrance coordinates

The original world entrance consumer packs source cells as **Y,X**. Town and objective metadata previously read those bytes as X,Y, transposing pins and some town bounds. Two reads now follow the original format. Independent ROM-byte and executed entrance evidence establish the correction; the player anchor was already correct.

Unknown or ambiguous destinations still produce no guessed objective. Gold/cyan/pink legend colors match their markers. The optional map retains its bounded cache construction, restore reset and no warm-cache terrain resampling.

## Current Bun and architect clues

Original Bun recruitment and the same-branch Morgan payment establish two current clues. Chapter four requires the selected party, current conditions and Bun global state before showing **“Master: take care of Bun.”** Original chapter-five dialogue establishes **“The architect is working.”** Existing Graviton, Dynamite and GIANT priorities override this broad clue where applicable.

These messages describe current original conditions, not durable completion history. No later construction award is inferred from the global Bun flag alone. The source adds no extra journal row or layout cost.

## Corrected development background

An owner screenshot exposed a malformed development checkpoint used in a map demonstration. Its camera had been moved without executing the original background refill. The corruption also appeared in the original 256-pixel picture with the map closed; no map or widescreen renderer change was required.

The replacement fixture exits the town through original input and runs the original world loader. An independent original grid/cell/metatile and VRAM/CGRAM decoder checks all 896 center tile words and all 32,256 added margin pixels. A negative control detects the earlier bad fixture. Seven guest dump types remain equal across map/original/wide variants. Camera-only staging alone is insufficient for rendering or screenshot qualification.

## Separate exact-artifact qualification

| Scope | Result |
| --- | --- |
| Map metadata host parser | 539 controls; original-byte entrance evidence separate |
| Coherent map input and restore | 259 checks / 13 copied native runs |
| Town/current journal, input and restore | 95 checks / 18 copied native runs |
| Journal host/header controls | 65 checks / 25 host cases; 655,360 header-domain controls |
| Original world background and margins | 18 independent controls, including corrupt-fixture refusal evidence |
| Unchanged GUI adoption and changed-native profile update/rollback | 60 + 52 controls; actual 0.3.0→0.3.1 execution and rollback |
| Direct3D playback | Seven finite routes near 60 fps, zero steady underflow/missing-frame/audible-overflow counters |
| Copied installed title/resume/visible Companion | 18 controls; preferences unchanged |

The seven playback routes use six previous exact-0.3.1 captures and the corrected original world route. The corrupt camera-only world capture remains retained and excluded from rendering qualification. Earlier failed input/name/control preparations remain retained rather than counted as passes.

Silent forensic comparison, independent host proof, indexed virtual-controller input and paced playback have distinct scopes. These checks do not certify a physical controller, listening, every hardware load or an uninterrupted campaign. No source-build receipt is relabeled as gameplay-qualified.

## Next work

Apply useful REA dispatch/table findings through separately validated analyzer configuration, continue faithful automatic generation, and extend original party/effect/story rendering and verified later guidance. The newly executed same-Bun chapter-six house dialogue remains separate evidence for a later journal change. ROM, preferences and other projects stay local and protected.
