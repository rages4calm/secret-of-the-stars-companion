# Foundation mosaic rendering repair — October 9, 2026

The expanded-map proof uncovered a pre-existing host renderer memory overrun during an overworld battle transition. The original-width 0.1.6 build and the broader-map prototype both crashed; a separately copied natural town-exit route reproduced it too. This failure is not evidence of guest CPU slowdown, an invalid owner checkpoint, or a ROM modification.

## Confirmed cause

The private Win32 debugger capture is `local/evidence/map-contract-crash-20261009/runtime-crash-context.json`. The original build stopped on an access violation reading beyond its allocated priority buffer, at image RVA `0x474DD`, inside `PpuDrawBackground_4bpp_mosaic`. The instruction was a vector load from the priority buffer. The captured PPU register was `MOSAIC=0x83` (block size nine); the active window was `[13,242)`. The cached table still mapped column 13 to zero, while the current size-nine table should map it to nine. The initial run length therefore became `9-(13-0)=-4`. The pixel loop incremented until equality with that negative count and traversed memory outside the buffer.

The table was refreshed at pre-render line zero only. Register replay can change the mosaic size afterward. The crash did not have an empty window: the empty-span guards below are a defensive companion change, qualified separately.

## Bounded repair

Only runtime `snesrecomp/runner/src/snes/ppu.c` changes for this repair. `PpuDrawWholeLine` refreshes the derived modulo table when the register being rendered uses a different mosaic size. The original zero-origin block phase and existing vertical sampling convention are retained. Register latches, guest execution, timing budgets, collision and game progression are unchanged.

The mosaic lookup extends that same grid into negative and right-hand renderer margins using signed modulo; it no longer clamps right-margin samples to column 255. The 4bpp, 2bpp and Mode 7 paths skip nonpositive window intervals and use bounded pixel loops and forward end comparisons. Mosaic effects remain enabled. This is not a claim that every SNES mosaic latch nuance has been independently validated.

Qualified runtime source SHA-256: `1029435178f0b29d8fda286089f69e69cfefe9eccdd7a75b340b9420bd61b747`.

## Standalone renderer evidence

Run the authored, ROM-free checker with a fresh private output directory:

```powershell
python tools/check_foundation_mosaic.py --output local/evidence/mosaic-check-new
```

The checker includes the current runtime source directly, hashes it before and after, and never modifies it. Its C fixture is `tools/foundation_mosaic_canary.c`. The checked receipt is `local/evidence/map-contract-mosaic-qualified-20261009-final/report.json`:

- 192 actual renderer cases across 4bpp, 2bpp and Mode 7; mosaic sizes 1–16; windowed and unwindowed original width and full 800-pixel priority-buffer spans. All 153,600 words match the expected constant-pattern output; buffer canaries remain intact.
- 12,800 phase/progress checks cover columns `[-272,527]` for all 16 sizes. Every initial run advances positively.
- The exact captured old-size-16/current-size-nine cache mismatch reconstructs run `-4`, then refresh produces the correct column-nine sample and completes safely.
- 768 varying-data, scroll, scanline and window cases compare valid original-center output against the prior loop structure reconstructed from these same functions. All 614,400 words match. This preserves the existing positive-run rendering convention, rather than using a second emulator as an oracle.
- Three explicitly host-injected empty spans, one per renderer, leave the entire buffer and canaries untouched. These are synthetic seam tests, not guest-produced campaign fixtures.

Checker SHA-256: `6aaaff3a51f54fb06f71496c6cb70e38843b60e6c9b42b11f1daa8b80d9b6134`. C fixture SHA-256: `616c2cdf6cb916cc13628fc728b74a612ad6d15a80283f3a004bb488df6b6e59`.

The standalone evidence cannot qualify live GPU pacing, audio continuity, controllers or full-game transitions. Those belong to the paired original/expanded native candidate route receipts and the integration continuation. `local/runs/map-wide-mosaic-fix-focused-final-20261009/report.json` records 26/26 passing focused checks for repaired prototype `a50dee2e6ee0db183feac8d3d6f5804c74e9faecafbd47a44d084f6d8a3948bf`, including both previously crashing copied routes at both widths, exact guest-state parity and composed-center parity. It also reproduces the original build's failure and compares its pre-crash trace. Final candidate qualification and installation status are recorded separately.
