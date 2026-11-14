# 0.5.14.1 — first-time Setup hotfix

Fixes Setup stopping with **Combined20 source format/family identity differs**, even after a correct USA ROM passes validation. The helper was applying a historical generated-code format check to the newer pinned compiler output.

The helper now validates the current format and all 25 source families directly, including original ROM bytes, masks, canonical instruction bodies, reset bootstrap and the exact generated C. Compiler/runtime source pins and output hashes remain checked. This does not disable validation or accept other ROM versions.

**If you hit that error:** extract this new ZIP into a fresh folder, open the Companion, select the same supported clean USA ROM and run Setup. Keep your existing game/profile and saves. Retrying the old package does not update its build helper automatically.

Native game features remain 0.5.14; Companion remains 0.3.8. Existing working installations do not need to rebuild just for this installer fix. Packages remain ROM-free and contain no game executable or generated game code.
