# Native 0.5.14 / Companion 0.3.8

Battle effects now retain wider original-art scenery through supported mosaic, brightness, color and screen-shake phases. This fixes the Fire spell narrowing seen in the trailer and the shared rendering family used by the other spells. Original effect producers, palettes, windows, actors, DMA and scanline timing remain authoritative.

Screen shake no longer exposes a blank tile as a vertical strip inside the wide canvas. The original center is validated before side rendering. At newly exposed shake edges, only original backdrop-owned pixels can receive the extended BG2 scenery; text, sprites and other layer-owned pixels remain intact. Original View remains available, and changed or unsupported background resources retain guarded fallback.

**Fast Menus** now also shortens the middle steps of battle-menu slides. It retains their first/final frame handoffs, original input polling and queued graphics uploads. Turn Fast Menus off for the original menu timing. Companion remains 0.3.8; all existing achievements and options remain available.

## Check scope

Development used isolated copied checkpoints and source-backed spell/target staging. All 32 named battle-eligible spells were cast at all three tiers through the original queue and effect producers (96 completed casts). These checks cover execution/rendering, not natural spell acquisition, combination acquisition, revival outcome or campaign balance. Focused rendering checks cover the reported shake seams and the battle-menu change at normal speed. Completed achievement and earlier native checks were reused.

Native execution remains enabled by default with guarded compatibility fallback. This release makes no campaign-wide 100% AOT claim. Packages contain authored source, the ROM-free launcher and notices; bring your own supported USA ROM. Report reproducible problems on GitHub or Discord **chrono.trigger**.
