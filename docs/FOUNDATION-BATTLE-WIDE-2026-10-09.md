# Battle widescreen original-tile continuation — October 9, 2026

The host presentation module now contains explicit side recipes for all 16 original battle backdrop resources. It adds 72 pixels on each side of the original 256-pixel center. These are newly authored arrangements of original tile cells, not hidden scenery, replacement HD artwork, extra battle space or altered guest logic. Root owns integration, final executable qualification and installation; this document does not certify an installed build.

## Exact resource contract

The clean 1,572,864-byte ROM SHA256 is `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`. No ROM writes are performed. The original loader at `01:B8E8`, with column producer `01:B81B..B8E7`, reads selector `$0529`. Sixteen header bytes at `0E:D800` select cell pointers from `0E:F800` and metatile pointers from `0E:DC10`. Each 64-byte grid at `0E:D810 + selector*64` describes eight by eight 32-pixel cells; it produces the complete 32 by 32 BG2 tileword map at VRAM word `5800`.

Graphics/palette records at `0F:9400 + selector*4` contain graphics-set, palette6, palette7 and palette-animation selectors. Graphics IDs at `0F:9200` map to bank `10+(id>>3)`, address `8000+((id&7)<<12)`, four 4KB chunks at VRAM bytes 4000..7FFF. The module compares every character chunk used by the center or side recipe to its exact ROM source. It also compares all 1,024 original BG2 map words, rejecting partial transitions, unknown resource maps or graphics replacement. Palette animation markers 3..10 dispatch the original CGRAM animation scripts through `08:F800`/`08:F200`; they do not select replacement graphics. Each clone uses actual per-line CGRAM, without a host palette-phase cache.

The accepted hardware contract is battle mode5, brightness15, BG mode9, mosaic size1, BGSC49/59/51, character base0400, OBJ setting3, main mask17/subscreen0, original windows10011/main-window17, color math0, BG2 scroll0, SETINI0. Unsupported layout, scroll, fade or incomplete-resource states retain the original center. No enemy, command, glyph, OBJ, controller or CPU timing is relocated.

## Authored side recipes

`native/foundation/src/foundation_battle_wide.c` owns only private ROM-derived caches and clone BG2 side words. The forest0 recipe is unchanged. Forest/cave/ground layouts continue original repeated cell rhythms. Cloud/peak selectors1/2/4/6 and cliff10 extend local edge contours with individual horizontally reflected 32-pixel cells; cell quadrants reverse and tileword H-flip bit4000 toggles. The complete original battle image is never mirrored or repeated. Desert5 excludes another sun. Hall11 excludes side torches/door; lab12 aligns pipe columns across cell rows and excludes large tanks; cosmic13 uses clean star cells excluding figure/laser copies; ornate14 and castle15 preserve their distinct texture recipes. Original periodic floor tile rows keep their mathematical phase.

Only BG2 receives the side mask. Source PPU/VRAM are unchanged. Lines1..224 write nine words per margin into the unused second BG2 map half; original columns0..31 remain unchanged. Parent compositor retains its original-center pixel gate. `FoundationBattleWideReset` invalidates the binding/cache on reset or restore. Eligibility rechecks current resources, not historical camera or story state.

## Focused evidence

The authored, ROM-free harness is `tools/check_foundation_battle_wide.py` with portable C helper `tools/check_foundation_battle_wide.c`. It compiles the authored module against the actual current PPU renderer, reconstructs original resource tables into dedicated private fixtures, and independently decodes all visible margin tilewords from the ROM in Python. It never runs a guest campaign, writes a save, changes an owner profile or edits the ROM.

All 16 selectors passed with two actual CGRAM inputs: 1,835,008 original-center pixels matched; 16,704 independently decoded visible margin words matched; 288 rejection cases passed. The helper did not mutate source PPU state. Wrong original map word, used graphics byte, scene, selector, scroll, out-of-range line, source alias and VRAM alias reject. Synthetic palette rotation changes every backdrop output and still preserves exact center parity, proving use of current palette rather than a stale host color cache; this is not natural animation-script qualification.

Private report: `local/evidence/battle-wide-20261009-readonly/all 16-final-proof/report.json`. Private refined contact sheet: `backdrop-extension-refined-contact-sheet.png` in the same directory. Root visually approved all 16 compositions; native mountain output was also inspected. The base natural copied forest checkpoint was `local/runs/world-cave-a/saves/save0.sav`, SHA256 `918e744cc800225f9ef532da6b23dc652c533a26c3c68b55c204a0000efc61f5`. Its copied natural dump supplies original enemy/menu rendering; the other resource loads are explicitly synthetic host fixtures, not later-campaign encounters or execution of the original loader.

Frozen module C SHA256: `44b1db121ee6807ecb93327249d35129838a8b2c46b051d28a41ffb139533976`. H SHA256: `cca47f34826157894565eb194da46d1a54bc91548444b22d7d9615ef8eb1dc6a`. Author/live module files match. Actual PPU used by this proof SHA256: `1029435178f0b29d8fda286089f69e69cfefe9eccdd7a75b340b9420bd61b747`.

Reproduce from the workspace root:

```powershell
python tools/check_foundation_battle_wide.py --rom local/inputs/clean-usa.sfc --base-dump local/evidence/battle-wide-20261009-readonly/battle/dump/ready --output local/evidence/battle-wide-20261009-readonly/all 16-final-proof --clang C:/Users/crono/.local/share/retcomm/toolchains/cmake-clang-v1/latest/bin/clang.exe
```

This proves the complete original battle resource family under the guarded presentation layout. Natural later battles, transitions, battle effects, palette-script playback, physical controller/audio and broad campaign remain separate runtime checks. Output scaling or this original-tile extension does not establish HD replacement artwork.
