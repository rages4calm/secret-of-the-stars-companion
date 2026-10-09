# Reward modifiers and held walking boost

The native QoL module adds independent earned-battle XP and gold percentages,
plus an assignable held walking boost. Rewards default to the exact original
100%. Movement defaults to 200% while the configured boost button is held;
ordinary unheld movement retains its original pace.

```ini
[Enhancements]
XpMultiplierPercent=100
GoldMultiplierPercent=100
MovementSpeedPercent=200
```

XP and gold accept 100–1000%; walking accepts 100–300%. Settings are read at
startup. Original View can override them for that launch with
`SNESRECOMP_FOUNDATION_XP_PERCENT=100`,
`SNESRECOMP_FOUNDATION_GOLD_PERCENT=100` and
`SNESRECOMP_FOUNDATION_MOVEMENT_PERCENT=100`. Those overrides do not rewrite the
player's saved settings. Keyboard/controller bindings are resolved by the
runtime's editable `MovementBoost` action; the launcher exposes those controls.
Fast-forward is a separate host action and can use hold or toggle behavior.

## Earned rewards

The original clean-USA enemy reward reader at `00:BA3C` collects each defeated
enemy's reward row and saturates the battle totals at 65,535. The original
handoff at `00:AE9B` then supplies those completed totals to character XP and
the selected party's wallet. The native rule scales those totals exactly once
at that handoff. It does not watch global gold changes, edit shop/sale routines
or grant extra starting money.

Fractional rates round down once per completed battle: a natural two-Red-Slime
battle has 4 XP and 4 gold, so 125% awards 5 of each. Its 200% result is 8/8,
150% XP with 300% gold is 6/12, and 1000% is 40/40. The original 16-bit battle
cap remains; the original character/wallet consumers retain their own
24-bit 9,999,999 ceiling and original party/level logic. This is not a new
uncapped reward or economy system.

The callback verifies the original instruction signature and battle coroutine
register/stack context. At 100%, no reward callback is registered unless local
diagnostic tracing is requested. Unsupported registration/context retains the
original path. Future AOT promotion of this routine must explicitly carry this
policy into the promoted body; interpreter hooks do not cover arbitrary newly
compiled routines automatically.

## Walking and collision

`01:9142` keeps the original next-tile collision/event decision. The native rule
changes only the original ordinary one-pixel walk operands at `01:B076` and
`01:B0AF`, with the matched Mode80 secondary operands at `01:B139` and
`01:B141`. It never jumps directly to a new coordinate, runs extra world frames
or increases the audio/NPC clock.

Every increment is clamped to the remaining distance to the next 16-pixel
boundary, including at 300%. The original `01:B044` completion test therefore
still reaches the exact tile edge before the next collision/event check.
Fractional-rate cadence comes from the restored guest frame counter, not an
unsaved host accumulator. Secondary motion follows the primary advance already
recorded in WRAM, so a deadline, checkpoint or button release between the two
consumers can finish that advance without remembering a discarded future.

Eligibility is deliberately bounded: ordinary controllable field state,
matching primary/Mode80 secondary camera/vector lineage, normal one-pixel
motion and zero currents. Menus, battle, scripted locks, parallax/half-scale
secondary modes, special vehicles/motion and other unsupported families retain
their original movement. Full-campaign walking coverage remains open.

## Evidence and limits

`tools/check_foundation_qol.py` uses private copied natural battle, town and
house fixtures. The development canary passed the 125/150/200/300/1000% earned
reward cases, four-direction 150/200/300% walking, exact unheld/original
comparisons, a blocked town endpoint, actual SDL keyboard/virtual-controller
boost input, and the natural house exit. Primary/secondary cameras stayed
matched and completed on original tile boundaries. The default battle's six
guest captures matched the previous qualified 0.1.9 executable exactly.

`tools/check_foundation_qol_restore.py` reproduces separate held/unheld menu
and opening-cutscene pairs, which also matched the six guest
captures exactly. A private checkpoint before the final victory confirmation
awarded 5/5 after the original confirmation on cold restore; a checkpoint after
the reward retained 5/5 without a second handoff or double award. Those are
focused genuine routes, not a campaign certification.

`tools/check_foundation_qol.c` separately exercises 21 ROM-free arithmetic,
context-rejection, tile-edge and pending-secondary guards against the actual
module. Synthetic pending-instruction state is not claimed as a naturally
observed partial guest checkpoint. These checks use software rendering, dummy
SDL devices and audio disabled. They do not establish audible performance,
physical-controller compatibility or every later battle, party and field.

The final integrated build receives its own executable hash and qualification
receipt. A separately compiled canary does not by itself qualify an installed
release. ROMs, checkpoint copies, private dumps and generated code stay local.
