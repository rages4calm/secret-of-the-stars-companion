# Guide destinations and broader widescreen — native 0.4.3

Native 0.4.3 adds player-selected guide town tracking, a broader ordinary
wrapped-map actor path, and a clearer battle panel. Companion stays 0.3.6.
The owner and play testers verify campaign behavior; developer checks cover
implementation, rendering, input and finite playback.

## Track a guide town

Open the journal, switch to Guide with the configured Game Select button,
and browse to a page that shows **MAP: town**. Press the configured **Game X**
button to track it. Close the journal and open the map using your Map hotkey.
The chosen town blinks pink and the matching legend says **GUIDE DESTINATION**.
Press Game X on the same guide page again to clear it.

Twenty guide pages name a trackable town. The marker resolves the original
town name identity against the currently selected original world entrance
records. It uses the game's coordinates, including a stable identity for the
player-renamed Old Hill. Unmapped caves, shrines, castles, Kaja's house and
upper-world destinations show a clear unavailable state. Tracking requires
the ordinary world map and enabled map/objective settings.

This is an explicit player choice, independent of automatic quest advice.
It does not mark a quest complete or infer the next event. The temporary
selection clears on reset/restore, leaving the world, unavailable resources
or losing the original town point. Automatic objective data remains separate;
a chosen guide target takes presentation priority while tracked.

The map retains its bounded incremental terrain work and cached original
town points. The fresh town lookup occurs on the tracking action, rather than
parsing or hashing the ROM every frame.

## Broader ordinary actor rendering

Ordinary wrapped-map parties and NPCs are no longer limited to named chapters,
leaders or NPC rosters. The new path uses the selected map's independent X/Y
periods, original descriptors, completed 544-byte sprite packet and displayed
raster. It supports all five ordinary party records and nineteen regular
records under those producer contracts. An enabled special layer with all
eight flags zero uses the same original no-prefix path.

The exact selected resource, descriptor bounds, packet/DMA join, raster camera,
two-field producer age and bounded displacement checks remain. Original
activation, collision, allocation, ordering, center and timing remain intact.
Previously supported world/vehicle paths retain their own contracts.

The selected stream encodes dimensions from 1 to 15. This ordinary path needs
an X period of at least 512 pixels and a Y period of at least 256; a 256-pixel
horizontal map would need multiple visible copies of an actor. Active variable
effects, nonzero sprite offsets and incompatible OBJ/raster layouts retain
fallback. This implements a reusable producer family; it does not certify
every campaign scene or add variable-effect artwork.

## Battle panel

Original HP value FFFF bypasses damage subtraction at 00:E16C. The panel now
shows **IMMUNE** for that state instead of 65535/65535 and omits the numerical
bar. Golan's original Graviton transformation changes the enemy to its finite
HP record. Other finite HP values retain the numerical display and bar.
Original black loading/exit transitions suppress the panel using battle
lifecycle and actual PPU blank/brightness state.

## Current build and checks

- Native executable SHA-256: `90289390832748cb237de3535efda5127a6e7639aa6d91cb4dcc22b225492a0b`.
- Immutable compilation receipt SHA-256: `98d0b91016fe1675931b4df5fe2c105e1ac4a0d7977a432346350c4bce95e863`.
- Sixty-two authored native inputs; Companion 0.3.6 remains unchanged.
- The thirteen runtime patches and declared execution ABI are unchanged.
- Focused guide input/reset, original-town resolution and panel rendering pass.
- Actual enhanced-wide guide, map, battle and staged ordinary-world compositions
  are inspected; a finite Direct3D11/audio route passes separately.

Compilation receipts keep their genuine compiled_unqualified status. Focused
installation checks are separate. Staged developer rendering fixtures are not
natural campaign progression. Full native/AOT execution, active effects and
broader hardware coverage remain WIP. The written 42-page guide already covers
the ending; human campaign testing does not block this implementation bundle.
