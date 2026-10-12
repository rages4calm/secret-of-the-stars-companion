# Secret of the Stars: PC feature gallery

Six actual captures: world/battle images retain native **0.2.5** and Hotkeys Companion **0.3.1** scope; the full story guide and navigation map are fresh native **0.4.4** 1080p window captures; Enhancements is Companion **0.3.5** using native **0.3.6**. These show additions to the original SNES release: wider scenery, a battle HP sidebar, full story guidance and guide-town tracking, adjustable rewards/travel/encounters, and configurable PC/controller hotkeys.

This is an early playable foundation. Complete native/AOT game execution and full-campaign widescreen coverage remain unfinished. Gameplay captures use isolated development checkpoints; launcher captures show example settings. Original artwork belongs to the game's rightsholders; no extracted art pack or game data is distributed here.

## Wider world, including original vehicles

![Actual wider world, including original vehicles](screenshots/widescreen-world.png)

A true 400-pixel scene shows terrain and an original parked vehicle beyond the original viewport. Selected-resource, completed-packet and raster guards preserve the original center; unsupported scenes use the original view. This is an isolated staged development checkpoint, not a naturally completed campaign.

## Battle health at a glance

![Actual battle health at a glance](screenshots/battle-health-sidebar.png)

The optional native battle sidebar displays enemy HP and health bars beside the original battle view. Hide or show it with your assigned keyboard/controller action in Companion Hotkeys. The redundant HUD-key footer has been removed.

## Full story guide and town tracking

<img src="screenshots/quest-journal.png" alt="Story guide with Old Hill selected" width="1200">

Browse 42 pages in 14 sections through the ending. This page explains bringing Cody home; Game X has selected Old Hill for the map. Current advice remains a separate view. Page selection does not mark a quest complete. This is an actual 1920×1080 native0.4.4 window capture from an isolated staged developer checkpoint, converted without resizing. Campaign directions are being checked by the owner and play testers.

## Choose your own pace

![Actual choose your own pace](screenshots/companion-enhancements.png)

Separate XP and gold modifiers range from 100% to 1000%; held ordinary movement boost ranges from 100% to 300%. Companion 0.3.5 adds a 0–100% ordinary random encounter modifier for native 0.3.6: default 100 keeps the original check and 0 disables qualified random battles, while scripted battles remain enabled. Reduced values scale integer threshold bins, not an exact campaign fight frequency. These are example settings from an isolated profile (275% XP, 350% gold, 250% movement); random encounters are shown at the original 100%. Apply/Revert manage pending changes; Original View preserves the saved encounter choice. [Encounter setting and limits](FOUNDATION-ENCOUNTER-RATE-2026-10-11.md).

## Keyboard and controller hotkeys

![Actual keyboard and controller hotkeys](screenshots/companion-hotkeys.png)

Assign fullscreen, HUD, journal, movement boost, checkpoints and more to keyboard/controller actions. Fast-forward supports hold or toggle. These are example custom bindings; game-button mapping has its own Controls page.

[Build from your own ROM](../BUILDING.md) · [Current encounter implementation and validation limits](FOUNDATION-ENCOUNTER-RATE-2026-10-11.md) · [Capture hashes and provenance](screenshots/captures.json).

## Position, towns and your selected destination

<img src="screenshots/navigation-map.png" alt="Navigation map tracking Old Hill" width="1200">

Actual 1920×1080 final GPU output, with enhanced pixels and widescreen enabled.
Gold marks your position, cyan marks original town entrances, and the pink
marker blinks at Old Hill after selecting it with Game X in Guide. The legend
matches those colors. The point comes from the original town entrance data;
this is a player choice, independent of automatic quest advice.

Local maps show current-area terrain and position. Assign the Map action and
toggle objectives in Companion. This frame uses an isolated developer checkpoint
with staged prerequisites; it is not a natural campaign run. BMP-to-PNG
conversion preserves the captured pixels with no screenshot resizing.
