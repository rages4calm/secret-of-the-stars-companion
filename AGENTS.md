# Secret of the Stars — public source instructions

This checkout is the public native0.5.5 / Companion0.3.6 source snapshot.
Start with README.md, BUILDING.md, CONTRIBUTING.md and SOURCE-PROVENANCE.json.
Dated handoffs and validation documents describe their recorded versions;
they are not instructions to recreate completed experiments or private runs.

## Scope and working style

Keep changes focused and make routine decisions autonomously. Use focused agents
with non-overlapping ownership when useful; never revert another contributor's
work. Continue without goal tools. Use plain English and distinguish implementation,
compilation, actual execution and campaign evidence.

The game uses native C and a C# Companion. Python supplies build, generation,
inspection and validation tools. Generated game C and the pinned upstream runtime
are deliberately absent from this authored-source repository. Full native/AOT
execution remains unfinished; code counts or a published release do not prove it.

Players verify campaign and story accuracy. Check the code affected by a change;
do not repeat completed private tests, require exhaustive playthroughs or invent
fixtures, flags, coordinates, art roles, call owners or callee exit facts.

## Build and preserve behavior

Use tools/build_public_foundation.py with an owned supported clean USA ROM and
the toolchain in BUILDING.md. Use tools/build_public_companion.py for the launcher.
Build into fresh ignored directories. The public helper verifies the pinned
runtime, ordered patches and authored inputs; preserve unexpected cache edits
instead of resetting or overwriting them.

Update the relevant native/foundation/authored-files.json or
Companion/authored-files.json hashes after deliberate source changes. Preserve
runtime patch/binding lineage and credits. First compiled_unqualified receipts
remain immutable; exact-artifact qualification is separate. Respect checkpoint,
SRAM and execution-state ABI declarations when changing binaries.

Protect current saves/settings before reproduction or installation. Use isolated
copied executables and profiles; changing cwd alone does not isolate the game.
Source-backed cheats or teleports on copied saves must use original loaders and
be labelled as staged evidence. Never overwrite newer player progress.

Preserve the full Guide, Current advice, maps/tracking, configurable controls,
XP/gold/encounter options, movement and fast-forward settings, enhanced original
pixels, wider scenery/actors, Original View and guarded fallback. Retain original
center, collision, activation, pace and coordinate ownership. Replacement HD art,
MSU and CPU experiments remain deferred unless explicitly requested.

## Publication boundary

Publish deliberate authored source and ROM-free launcher packages only. Never
commit ROMs, patched images, generated game bodies/headers, extracted art/audio,
saves, checkpoints, private dumps, binary game builds or unlicensed research
caches. The six manifest-listed docs/screenshots images are the intentional
reviewed documentation exception; do not add private captures by default.

Keep useful developer tests, build tools, documentation and license notices.
Do not hide authored tooling with misleading GitHub Linguist attributes.
Before publication run tools/check_public_source.py once for the changed tracked
boundary. Do not fabricate source or gameplay qualification to enable a package.
Keep native/tools/docs PolyForm and Companion MIT license boundaries intact.

Large local outputs belong in bounded Temp locations. Preserve required inputs;
the steady workspace cap is5,000,000,000 bytes. Cleanup scripts are owner-run only:
never execute cleanup/Preview/VerifyOnly dashboards or retry blocked deletion
through another helper, tool or elevation. Public contact: Discord chrono.trigger.
