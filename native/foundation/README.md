# Authored foundation source — native 0.3.0

This directory contains 58 authored inputs: game-specific native glue, rendering,
input, state adapters, build configuration and generators. ROM bytes, extracted
assets, generated instruction bodies and development checkpoints remain private.
It is an authored snapshot, not a complete standalone runtime checkout.

Use [the source-first instructions](../../BUILDING.md) and the public helper. It
freezes a fresh isolated build and retains a real `compiled_unqualified` receipt;
exact gameplay and installation qualification are separate. Do not build over
an older edited runtime cache or assume a rebuild inherits its checks.
[Current evidence and limits](../../docs/FOUNDATION-PARTIES-CONSTRUCTOR-2026-10-11.md).

The shared runtime is pinned at
`7931b53c4968d9cf3fffeabf3e7f5f21d2ecf3a0`. Four independently hashed patches retain
its guest execution ABI while exposing guarded instruction transactions,
navigation input and modal audio recovery. Most game execution is interpreted;
complete game AOT remains unfinished.

Owned-ROM generators produce the observed original loading/clear routine and
bounded outer constructor, including original call/setup/return sites. Each
instruction retains original bus accesses, stack, cycle charges and scheduler
boundaries. Unsupported contexts and constructor callees remain interpreted.
Generated headers and provenance belong only in ignored private `src/gen`;
the ROM-free setup build has inert fallbacks.

`foundation_field` and `foundation_wide` resolve selected original terrain into
an optional 400-pixel canvas. `foundation_wide_actors` admits exact resource,
roster, completed-packet and raster families, including selected vehicles,
interior periods and the settled laboratory. Unknown states retain original
centered pixels and fallback margins. Center pixels, collision and original
actor allocation remain guarded. These families do not cover the full campaign.
`foundation_battle_wide` supplies separately checked authored side layouts.

`foundation_presentation`, `foundation_scale2x` and `foundation_hd_ui` keep
optional battle information, enhanced pixels and menu-frame artwork distinct.
Neither output scaling nor expanded scenery is a replacement HD world-art pack.
`foundation_journal` derives verified current advice and mutable inventory state,
including both parties; it does not infer permanent completion history. The
optional map shows current terrain, position, world towns and a verified
objective, with no guessed destination for unsupported story states.

`foundation_menu` batches only validated field-menu rows/slides; interactive
submenu producers keep their original handoff. Native reward and held movement
hooks are optional, with keyboard/controller shortcuts configured by Companion.
Original View disables enhancements for that launch. State schema v3 preserves
the VRAM port and audio clock; guarded v1/v2 reads retain their documented limits
and do not rewrite a source checkpoint merely to migrate it.

Broader party/effect/cutscene rendering, later construction/story guidance,
hardware/session coverage and complete native execution remain active work.
Historical documents retain their artifact scopes; synthetic resource checks
and private counter totals are not counts of completed playable maps.
