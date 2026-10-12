# Native 0.3.6 / Companion 0.3.5 — adjustable random encounters

Companion now puts **Random encounter rate (%)** beside experience, gold and
movement in **Enhancements**. The range is 0–100%, with 100% as the original
setting. Lower values reduce ordinary random battles; 0% disables those battles.
Scripted encounters use the original separate battle request path.

## Player settings

Close the game, open Enhancements, choose a value and press Apply settings.
Revert changes restores the loaded profile. Existing profiles without the new
setting use 100%. Original View forces 100% for that launch while retaining the
saved choice. The control requires native 0.3.6; older selected builds show it
unavailable and require an update through Setup.

The game stores `RandomEncounterPercent` in the local `foundation.ini`.
Invalid values fall back to 100%. This setting preserves XP, gold, movement,
controller bindings, existing checkpoint formats and unrelated custom settings.
The launcher clears inherited diagnostic overrides during normal Play.

## Original random check

The original ordinary-field routine accumulates its existing encounter counter,
then compares it with a terrain-dependent inclusive threshold. The modifier
narrows the accepted counter bins to `floor((threshold + 1) * percent / 100)`.
For example, an original threshold of seven accepts counters zero through seven;
50% accepts zero through three. Small thresholds have integer granularity. A
50% setting is a modifier to that original check, not a promise that every walk
or campaign has exactly half as many fights.

The native callback changes only the carry result at the original random branch.
It does not add a random generator, write the counter, change movement or game
clocks, or introduce unsaved encounter history. The original decline path runs
normally. At 100% without diagnostics, no encounter callback is registered.
Original ROM bytes, table identity, CPU operand state and ordinary-field guards
must match; unknown contexts retain original behavior.

The scripted message `FF26` requests a battle through the original script handler
and shared battle producer without entering this random branch. No enemy,
reward, party, script or boss table is patched. Source separation and actual
scripted execution are recorded separately from natural story progression.

## Exact compiled artifacts

| Artifact | Executable SHA-256 | Immutable compilation receipt SHA-256 |
| --- | --- | --- |
| Native 0.3.6 | `b9ebdf8920e6a39e47235f82b1e0f848a49875ffacfccec5a54f0a78163a1cbd` | `98f3759c6c2ab9ff8d32c7dbf4b7a5e4134569a8a9401652aa4c2200a1e331bb` |
| Companion 0.3.5 | `eb6876c3b5bdcadfa51686bf7ec59c231d29ab0b89d067c5a3aa85f82d086adc` | `2793fd8c9a0abfb99fae041266faf491b1c9f6cf477743d1b402b212755ff37d` |

The real compilation receipts retain `compiled_unqualified`; separate reports
qualify finite execution, launcher, playback and delivery scopes. The 61 native
inputs change only version and the QoL module/header. All 19 generated original
game outputs, nine runtime patches and serialized checkpoint ABI retain 0.3.5
identity. The 24 authored Companion inputs include the new control and its tests.

## Finite checks

The actual compiled C module passes 36 process/callback cases, including default,
zero, reduced, malformed settings, altered source guards, callback registration
failure, restore determinism and preservation of unknown CPU contexts. The
6,776,123 assertions are host/module checks rather than campaign coverage.

The actual launcher passes 91 backend, 85 adoption, 52 update/rollback, 51 current
build UI and 36 older-build UI checks. Four additional copied native title/resume
runs use genuine compilation receipts. New GUI captures use separate current and
old-build folders. Fresh source profiles may legitimately omit `keybinds.ini`;
the tests preserve that absence rather than manufacture a file. Earlier test
precondition and screenshot-folder errors retain separate failed reports.

The initial 13 actual native cases pass 267 scoped comparisons. Default and
explicit 100% preserve the preceding build's complete guest dumps, raw original
picture, completed sprite packets and clocks. Zero and reduced settings decline
original random candidates. Repeated cold restores reproduce the same results.
The first overworld movement-boost case is a guard-refused fallback, not positive
boost qualification. Supplementary original-mode walking and scripted producers
have their own evidence, which must not be inferred from that initial result.

The supplementary original-mode walking and narrow counter-writer checks pass
142 comparisons. Actual held300% walking completes four original16-pixel steps
in the same32 input frames where100% completes two; original boundary clamping
remains. The overworld family still retains its guarded boost fallback.

Original scripted Golan execution passes212 captured comparisons. Original100%,
native100% and native0% preserve all seven guest dump families, every compared
frame/clock and complete544-byte sprite packets through the recorded event
phases. The original FF26 handler writes battle request40 and enemy operand3410;
all three reach battle mode5. Original entrance loading and a normal completed
step produce the event after recorded chapter/transport prerequisites. This is
staged original execution, not natural chapter-five campaign certification.

Seven selected actual Direct3D/audio route contracts pass about60 FPS with zero
steady underflow, missing-frame or audible-overflow deltas. Six pass initially;
the prebattle script initially fails only its sub0.5-second first-nonzero PCM
assertion, with first sound at2.068seconds and all steady counters clean. A
separate already-entered scripted battle passes the same startup/audio checks.
The initial failure remains explicit; no host audio repair or universal playback
claim is made. These routes also exercise original width, enhanced widescreen,
held movement boost, indexed-controller journal and keyboard map input.

## Remaining work

Complete native/AOT execution, campaign-wide widescreen, broader story/party/effect
contexts, further verified quest directions and wider hardware/listening checks
remain unfinished. This is a WIP feature release. Development staging records
prerequisite edits and executes original loaders; it does not certify natural
acquisition or a complete campaign. The source/launcher package contains no ROM,
generated original-game code, save, checkpoint or playable native game binary.
