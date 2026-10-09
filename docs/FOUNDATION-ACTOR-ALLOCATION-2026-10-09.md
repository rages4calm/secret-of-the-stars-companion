# Original actor allocation follow-up — October 9, 2026

The transparent world record in the
[natural assessment](FOUNDATION-ACTOR-NATURAL-ASSESSMENT-2026-10-09.md) is now
traced to its actual original selected source. The original game loads base
`04F8`, whose descriptors select blank tile `7F`. This is a measured original
allocation path, rather than a replacement made by the wider renderer. Visible
wrapping actor qualification is still missing; all installed actor guards remain.

This follow-up uses installed native 0.2.0 SHA-256
`9241f79ea1a685e0932282c300081a90f9becf503f9a17c5fe6a94b34a08a7e0`.
It does not change native/runtime source, manifests, installation, owner saves
or settings. Original ROM and copied fixture hashes remain unchanged. The
earlier natural assessment and its failed artwork gate are retained untouched.
Private evidence is `local/evidence/actor-allocation-20261009/`.

## Actual original record creation

The copied `likado-north-exit-a/saves/save0.sav` has SHA-256
`651d7e8241c812565f97d51be2abd395846ce505f4e69a140c0319d05fc56a3e`.
A finite silent replay waits two frames, then presses down for 48 frames, left
for 96, up for 240 and right for 160, taking a snapshot after each press,
followed by a 120-frame wait and a final snapshot. It naturally leaves scene 5
and enters wrapping-enabled scene 0.
The private recipe SHA-256 is
`a05fe2e1bf864bd9ec42291f021f68305a471b37d01cfb488aaa739e531a63aa`.
The actual runner advances 670 frames, including its input-release boundaries.

At guest frame 24494, the original interpreter executes `01:CD61` with D=`0900`,
DB=`01`, M=0, X-width=1, Y=5 and A=`04F8`. The existing scoped observer records
the two original byte stores into `7E:4105/4106`. These are halves of one original
16-bit graphics-base store, not two actors.

A separate source-pointer replay observes `01:CD0E` and `01:CD14` installing
`0A:F88E` into direct-page bytes `0900..0902` at the same guest frame. The original
source entry resolves to world coordinates (1824,1776), base `04F8` and pose 0.
Its next entry is the original `FFFF` terminator. All four subsequent sampled
world records match those source coordinates/base exactly. This selected list
contains one ordinary record; further movement of that same list cannot produce
a different visible NPC resource. The record's gameplay or story identity is
not inferred from its blank artwork.

The private nine-byte source-entry hash is
`d28d3e5afaf2c774199fb6d214691c6d0e221c54bb5c1f6ff334bc0023afdf10`.
Original entry bytes and disassembly remain private. Snapshot direct-page data
after the loader is not used as the source proof: later tasks reuse that page.
The proof uses the actual pointer-store events at the allocation seam.

## Original OBJ inputs and bounded DMA observation

Independent four-plane decoding checks the same actual VRAM input for the
regular record and the visible ordinary party record at four world snapshots.
Both regular animation phases still decode **zero nontransparent pixels**.
The party control decodes 174, 191, 167 and 167 nontransparent pixels respectively.
This establishes that the captured original OBJ data contains visible artwork
and that the blank regular result is specific to its selected descriptors/tile.
Palette changes cannot make color index 0 opaque.

A new private checkpoint is saved through the existing save-only diagnostic at
host frame 75, before the observed base allocation. Its SHA-256 is
`768e7dd01711e009a7c0fe8333a7be78c749c182bf388eda016146d558e46cc0`.
Separate cold runs take nine snapshots from guest frame 24452 through 24532,
straddling the scene change and the allocation at 24494. OBJ setting 03 addresses
the first character bank at VRAM word `6000`. Its 8 KiB capture remains identical
at all nine samples, contains 5163 nonzero bytes, and tile `7F` remains entirely
zero before and after allocation. Thus the base change does not expose a
previously nonblank `7F` tile in this checked window.

The existing DMA logger supplies actual starts from the cold replay, including
original VRAM transfers into word `3E00` and `0000`, plus CGRAM transfers. Its
VRAM/CGRAM log is capped at 50 events per process. No conclusion about every
inter-snapshot upload, an unlogged later OBJ transfer, or DMA completion follows
from that finite log. The installed DMA history dump is empty in this build;
it is not used as evidence that no transfer occurred. A full upload-to-displayed
actor lineage would still require an isolated instrumentation candidate.

## Separate fidelity gates and next seam

The actor-store replay matches 42 WRAM/VRAM/SRAM/OAM/CGRAM/register/framebuffer
captures against observation disabled. The source-pointer replay independently
matches another 42. The cold DMA-debug replay matches 63 captures against its
own debug-disabled cold reference. These are three separate scopes, rather than
a campaign count. The actor-address filter logs7323 events including hardware
register addresses; only 977 are actual `7E` actor-record stores. The report
preserves that distinction.

The same actual world-entry trace executes `01:D059`, writing `FF` into reserved
record 18 at `7E:42C2`. The later world snapshots retain source scene `5441=FFFF`,
current scene 0 and flag `409=00`. This is positive evidence of the original
reserved-B0 refusal path, not just absence of an active-looking record.

The next useful visible wrapping fixture needs a different original selected
actor entry or a naturally enabled reserved source. For the latter, first trace
the original scene writers `01:A534/A5DA` together with their caller and source
position fields; their story meaning remains unresolved. Then require actual
`01:CFF6/01:D045` activation/base stores, the `01:DB68` constructor, full completed
544-byte OAM identity and nontransparent original art before a private margin
composition proof. Replacing the current `04F8` base or setting `5441` by hand
would manufacture that result. No larger chapter playthrough or speculative
actor spawn is included in this assessment.

`resolved-allocation-report.json` SHA-256:
`6d1f595bca9971818538fe134405aca2b575e1b090c1a5ab78f6438c24b38ef0`.
Its ten measured allocation/parity/control/protection checks pass. Its status
explicitly remains `original_blank_record_selection_proven_visible_margin_art_unqualified`.
The report records all private script, recipe, trace, checkpoint and subsidiary
report hashes. No visible wrapping, B0/composite, world-edge timing, terrain/OBJ
occlusion, audio/controller or campaign qualification is added.
