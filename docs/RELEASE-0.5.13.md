# Native 0.5.13 / Companion 0.3.8

This release adds 16 offline achievements and custom icons for the game and Companion. Existing native execution, widescreen, journal, map, guide, input and quality-of-life options remain available.

## Local achievements

Open the in-game list with **Ctrl+J** or **Back+Y** on a controller. Browse with Up/Down; B or Escape closes it. Unlock notices appear in game. Companion's **Achievements** page reads the selected profile's progress and refreshes while open.

The milestones cover victories, walking, changing parties, key items, using the map and full guide, and four original chapter transitions. They use the local CompanionAchievements core, as in Lagoon. They do not connect to RetroAchievements or require an account.

Progress is saved beside the game executable in `Achievements/secret-of-the-stars/native-qol/unseeded/progress.json`, outside game saves. Loading a checkpoint establishes a baseline; it does not unlock milestones retrospectively. Scripted/finite diagnostic runs do not earn achievements. Storage runs on a separate worker and failure to save never blocks gameplay. Copy the Achievements folder when moving your profile if you want to retain progress.

## Release scope

The port is feature-complete and open for campaign playtesting. Native execution remains enabled by default with guarded compatibility fallback in normal operation. Completed developer checks and source inventories do not establish that every campaign path executes without fallback. Campaign/story accuracy is verified by players; report reproducible issues on GitHub or Discord **chrono.trigger**.

Packages contain authored source, the Companion launcher and notices. Bring your own supported USA ROM; game executables and generated game code are built locally and are not distributed.

## Known presentation limitation

Some battle effects temporarily leave the added side margins black while preserving the original center. Current guards include mosaic, brightness/color-math changes, scrolling and changed background resources. The opening Fire spell in the trailer demonstrates this; steady battle scenery returns to widescreen afterward. This release does not claim every spell effect fills the wide canvas.
