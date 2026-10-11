# Original second-party rendering — native 0.3.2

The existing native 0.3.2 build now has additional original-game checks for Kustera town walking, actual party switching in a house, and a copied-checkpoint party restore. This is broader qualification of the unchanged renderer, not a new binary release. Full-campaign widescreen coverage remains unfinished.

The exact executable is `3f849747d161361b0e25bc2fcf6aa98332520d5e1d115bbd0385512f3d6dd6f9`, with immutable compilation receipt `fcb76c093614330196942c312e1233e8d4721d182c1b29d561e9447e551c3afd`. The receipt remains `compiled_unqualified`; the separate finite qualification passes 497 checks across 12 copied-executable runs. Companion remains 0.3.4.

## What was checked

- Kustera walks east, south, west and north, including reverse movement, in the chapter-six town. Original collision still limits movement around the town hall. Six original NPC records and the party's actual leader artwork are retained.
- The original menu performs SWAP in both directions between the two parties' house scenes. The original loaders select each party's resources and conditional NPC roster. A recruited NPC is absent after the original reload; this is the current game's roster result, not a permanent quest-history claim.
- Restoring a coherent copied Aqutallion town checkpoint from Kustera clears derived renderer state and reacquires completed original packets. The visible leader art changes correctly. Reverse checkpoint restoration was not checked in this pass; this restore is separate from the actual menu SWAP route.

Original 256-pixel output, 400-pixel terrain output and 400-pixel actor output match on guest state, machine clocks, seven captured state/output domains and the original center. The original-control runs disable the custom loading islands and exclude all 31 compiled entry points bound to this build's manifest.

Independent artwork decoding verifies 387,072 terrain-margin pixels from both layers and 370 added NPC pixels. Both distinct NPC animation phases have positive witnesses. The checks bind 3,323 completed 544-byte packets to their original producers and displayed contexts; live metadata is not substituted for a displayed packet. Original center sprite culling remains intact.

## Retained failures and limits

The initial nine-run report missed three animation-phase witnesses and remains recorded as a failure. Three targeted original walking runs supply the missing witnesses, with independently decoded opposing phases that differ. The earlier unsuccessful town reverse-SWAP attempt also remains recorded; the genuine house route proves both switching directions.

Recorded recruitment, story and other-party-location prerequisites were staged in disposable copies. Outcomes and packets were produced by the original game. These checks do not establish natural campaign progression, completed city construction, second-party wrapping-world margins, every effect/cutscene, new physical-controller coverage or GPU/audio playback. Unknown contexts keep the original-view fallback.

Private evidence is retained under `local/evidence/second-party-renderer-assessment-20261011`; it is not distributed. The final qualification digest is `0247de82c51f47c23174a61bb4962a22d8e83b306d8c510f3b11d8c58324bb7c`.

## Download and next work

The [native 0.3.2 / Companion 0.3.4 WIP release](https://github.com/rages4calm/secret-of-the-stars-companion/releases/tag/v0.3.2-wip) provides the ROM-free launcher/source ZIP, checksum and version manifest. It contains no playable native game, ROM, saves or extracted game data. Setup still needs your owned ROM and the development tools listed in [BUILDING.md](../BUILDING.md).

That release is frozen at source commit `422d63727de876389266a5401c7b2a4acfe4ac6e`; subsequent documentation does not replace its package or silently change its receipts. The package SHA-256 is `f656c0105737ae5a26026e613a88a2f127292bd1b8502edf73c2ae0b08ad765c`.

Next work remains broader story/effect coverage, verified later journal advice and faithful native generation. New private native candidates and election/ticket guidance are not installed merely because their source or original-event assessments pass. See the [0.3.2 implementation and qualification](FOUNDATION-AUTOMATIC-TOWN-2026-10-11.md) and [roadmap](../ROADMAP.md).
