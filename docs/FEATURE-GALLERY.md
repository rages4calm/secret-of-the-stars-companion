# Secret of the Stars: PC feature gallery

Six actual captures: four retain their native **0.2.5** / Companion **0.3.1** scope, the navigation map is from native **0.2.7**, and the updated Enhancements page is Companion **0.3.5** using native **0.3.6**. These show additions to the original SNES release: wider scenery, a battle HP sidebar, quest guidance, adjustable rewards, travel and random encounters, and configurable PC/controller hotkeys.

This is an early playable foundation. Complete native/AOT game execution and full-campaign widescreen coverage remain unfinished. Gameplay captures use isolated development checkpoints; launcher captures show example settings. Original artwork belongs to the game's rightsholders; no extracted art pack or game data is distributed here.

## Wider world, including original vehicles

![Actual wider world, including original vehicles](screenshots/widescreen-world.png)

A true 400-pixel scene shows terrain and an original parked vehicle beyond the original viewport. Selected-resource, completed-packet and raster guards preserve the original center; unsupported scenes use the original view. This is an isolated staged development checkpoint, not a naturally completed campaign.

## Battle health at a glance

![Actual battle health at a glance](screenshots/battle-health-sidebar.png)

The optional native battle sidebar displays enemy HP and health bars beside the original battle view. Hide or show it with your assigned keyboard/controller action in Companion Hotkeys. The redundant HUD-key footer has been removed.

## Quest directions while the game runs

![Actual quest directions while the game runs](screenshots/quest-journal.png)

The journal shows an objective, route advice and current progress from verified original dialogue and flags. This Mayor/Ringo clue was executed through the original event after a staged chapter prerequisite. Further chapters and permanent quest history remain in development.

## Choose your own pace

![Actual choose your own pace](screenshots/companion-enhancements.png)

Separate XP and gold modifiers range from 100% to 1000%; held ordinary movement boost ranges from 100% to 300%. Companion 0.3.5 adds a 0–100% ordinary random encounter modifier for native 0.3.6: default 100 keeps the original check and 0 disables qualified random battles, while scripted battles remain enabled. Reduced values scale integer threshold bins, not an exact campaign fight frequency. These are example settings from an isolated profile (275% XP, 350% gold, 250% movement); random encounters are shown at the original 100%. Apply/Revert manage pending changes; Original View preserves the saved encounter choice. [Encounter setting and limits](FOUNDATION-ENCOUNTER-RATE-2026-10-11.md).

## Keyboard and controller hotkeys

![Actual keyboard and controller hotkeys](screenshots/companion-hotkeys.png)

Assign fullscreen, HUD, journal, movement boost, checkpoints and more to keyboard/controller actions. Fast-forward supports hold or toggle. These are example custom bindings; game-button mapping has its own Controls page.

[Build from your own ROM](../BUILDING.md) · [Current encounter implementation and validation limits](FOUNDATION-ENCOUNTER-RATE-2026-10-11.md) · [Capture hashes and provenance](screenshots/captures.json).

## Position, towns and a verified destination

<img src="screenshots/navigation-map.png" alt="Navigation map" width="1200">

This is an actual 1920×1080 screenshot from the game's final GPU output, with
enhanced pixels and widescreen enabled. Gold marks your position, cyan marks original town entrances, and the optional
pink destination blinks. The legend text matches those marker colors. This is
actual native0.2.7 output from a copied original
Morgan payment/world-return route with staged prerequisites. The terrain,
position and Decatas marker are checked independently against original data.
Local maps show current-area terrain and position. Assigned Map bindings and the
objective toggle live in Companion. The world, battle, journal and Hotkeys images
retain their native0.2.5/Companion0.3.1 capture scope; the Enhancements image is
the actual newer Companion0.3.5 page with native0.3.6.
