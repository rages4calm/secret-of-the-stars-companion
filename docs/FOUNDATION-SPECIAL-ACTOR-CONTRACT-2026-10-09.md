# Regular records 17/18 and reserved OAM — October 9, 2026

This focused read-only assessment extends `FOUNDATION-PARTY-ACTOR-CONTRACT-2026-10-09.md`. It does not implement special actors, mutate guest state or enable new actors. The exact original constructor supports a narrow extension for **ordinary four-piece records 17/18**, while base `00B0` is a distinct two-large-OBJ constructor. Original writers normally assign that distinct family to record 18, so increasing the regular array to 19 alone would not cover the original behavior.

Private evidence is `local/evidence/special-actor-contract-20261009/`: `special-fixture-report.json` records source/input hashes and bounded capture coverage; `special-writer-disassembly.txt` retains original-ROM derived instructions. The previously decoded constructor/emitter instructions remain in `local/evidence/party-actor-contract-20261009/party-special-disassembly.txt`.

## Record, descriptor and preclip contract

The regular list is 19 records at `7E:4100 + 25*index`. Record 17 begins at `7E:42A9`; record 18 begins at `7E:42C2`. Both use the ordinary regular layout unless their base selects the branch below:

| Bytes | Meaning in this constructor |
| --- | --- |
| `+00` | Pose selector; `FF` inactive. |
| `+01..02` | 16-bit world X. |
| `+03..04` | 16-bit world Y. |
| `+05..06` | Sprite base index. |

`01:DA9C..DAB4` computes X=`worldX+0471-02AD` and Y=`worldY+0473-02AF`. These are world-minus-camera coordinates, unlike packed party screen positions. `01:DAB6` is the existing useful read-only capture point: both coordinates are ready, no original clipping gate has run, M=0/X=1, Y=3, record pointer is at direct-page `1C`, index at `14`, base at `1A`, coordinates at `16/18`, and the regular call returns to `01:D86F`.

The regular gates accept unsigned coordinate `>=FFF1` or `<00FF` for X / `<00EF` for Y. Wrapping paths between `DAB8..DAE6` additionally adjust negative values using the segment dimensions loaded into direct-page `30/32`. A first fixed-slot extension can retain the existing nonwrapping and zero-offset qualification rather than claim those paths from static decoding alone.

After the original gates, Y is decremented at `DAEB`. For low pose selectors 0–3, the descriptor is `0E:9800 + 8*(base + 2*pose + (0475>>7))`. This phase comes from the global field counter, not the party record's `+0A` byte. The four words retain the original mask at direct-page `10`: `EFFF` when `0400` is nonzero, `FFFF` otherwise. Their existing tile bank/palette/flip/priority bits and the displayed frame's actual VRAM/CGRAM remain authoritative.

## The reserved emitter is compact, not index-fixed

`01:DB13` compares index with `11` hex. Indices below 17 call `DE2A`, using ordinary cursor `046B`; indices 17/18 call `DE82` through `01:DB1C`.

`DE82` emits the same four 8×8 pieces and descriptor words as `DE2A`, but starts from direct-page cursor `34`, not `046B`. Producer setup sets `34=0010` at `D827` and high-OAM pointer `38=0201` at `D822`. The four pieces use `(x,y)` offsets `(0,0),(8,0),(0,8),(8,8)` from `01:DED3`. `DEC4` advances cursor `34` by 16 bytes; `DEC8` advances `38` by one byte. `DECE` stores high-OAM at `7E:2200+38`'s previous value.

Therefore the first **visible ordinary** special record uses slots 4–7, and the second uses slots 8–11. If record 17 is inactive or clipped, visible ordinary record 18 uses slots 4–7. They do not consume or advance `046B`. Validation must keep this cursor separate from ordinary party/NPC append order.

At the beginning of each producer, `D87F..D8B0` parks the first 12 slots by writing X/Y word `F080`, and sets their high-OAM groups to `55`. Clipped records leave parked slots; leftover tile/attribute words are not cleared and must not be interpreted as actors. The final packet completion fills the remaining ordinary OAM slots and high-OAM bytes through `DDF8..DE29`, while reserved slot groups remain under their own constructor's control.

With OBJ rotation disabled, the physical priority order is reserved slots 4–11 before ordinary output beginning at slot 12. A margin pass that assigns these entries the current `12+index*4` ranks would place them after ordinary actors and reverse ties. Stable virtual ranks 4–11 can preserve their order before party/NPC pieces. Physical validation still uses the compact original cursor described above, even when a culled record receives a virtual margin rank.

## Original writers: record 18 commonly takes the other branch

The original writer near `CEEB` checks scene/flag state before enabling these records. It also explicitly enables the regular constructor through `0401` bit `08`; native presentation should observe its result and never replace these conditions.

- `CF65` writes pose 2 to record 17. `CF71..CF84` copy world coordinates from `7E:5449/5453` and write base `00A0`. A branch at `CF1C` also assigns pose 2 but subtracts 32 from the source Y before storing it; it wraps the Y high byte from the map height when appropriate. `CF92` writes `FF` when its source scene/flag condition fails. Later original control paths at `A2A8` temporarily hide this record and `A3ED` restore its pose from the party record; these are original activation decisions.
- `CFF6` writes pose 2 to record 18. `D004..D02B` store world X=`544B-8`, Y=`5455-48`, with original wrapping high-byte repair when needed. `D045` stores base `00B0`; `D059` writes `FF` when its source condition fails.

At `DA92/DA97`, base `00B0` branches to `DB2D` **before the index-17 reserved four-piece test**. That path uses descriptor `0E:9800 + 8*00B0 + 4*pose`, two large pieces with `(x,y)` offsets `(0,0),(16,0)` from `01:DEDB`, and fixed slots 0/1. It explicitly sets OBJ size bits and writes their group at `7E:2400`. It neither consumes `046B` nor the `34` four-piece cursor. Record 18 is consequently not universally a slots-8–11 actor. These interfaces do not establish a story name for either record.

## Safe next proof and evidence limits

Ordinary non-B0 entries 17/18 can share the existing displayed-packet lifecycle and private 8×8 artwork decode. Extend only the observer's active-record classification and retained metadata; capture them at `DAB6`, validate their compact reserved-slot words/high bits separately, and preserve their earlier priority ranks. Promote metadata only after the same complete 544-byte staging packet, successful DMA and actual PPU OAM identity. Continue to reset it on restore/resource changes. This needs no guest OAM writes, activation changes, sprite-limit change or actor spawning.

The B0 family requires a separate two-large-piece decode and fixed-slot validation before it can use that lifecycle. Its useful preclip capture point is `01:DB68`: direct-page `02/00` hold world-plus-offset-minus-camera X/Y, `1F` already holds the descriptor, and component gates have not run. Y minus one is applied later per component at `DB7C`. It uses the pose selector directly; the global `0475` animation phase is not added. The original two components keep physical slots 0/1 even when one is clipped, unlike the compact ordinary reserved emitter.

The current guarded `OBSEL=03` uses the PPU evaluator's `{8,16}` size row; high-OAM size 1 makes each B0 component 16×16. The existing `ppu_evaluateSprites` source gives the exact addressing convention: after whole-object Y flip, `usedTile = (((tile>>4)+(row>>3))<<4) | (((tile&15)+(usedCol>>3))&15)`, where whole-object X flip changes `usedCol` from `col` to `15-col`. VRAM word address is `(objBase + usedTile*16 + (row&7)) & 7FFF`, with the upper two planes at `+8`. A 16×16 private object needs 256 color entries rather than the current 64-entry 8×8 buffer. The original pose-2 descriptor words at `0E:9D88` are `34AC,34AE` before masking. These source-derived details make a bounded B0 extension feasible, but are not a substitute for positive original packet/center/pixel evidence.

The targeted inventory read all 46 existing WRAM dumps in exactly four local namespaces: `clean-to-outdoors` (21), `first-room` (4), `sonya-talk` (1), and `david-dialogue-a` (20). Both records are inactive in every sampled dump. This is an opening/cutscene/dialogue evidence gap, not proof they never appear. No natural special actor fixture, campaign identity or rendered margin output is qualified here. The separate ordinary-party receipt already has original OAM lineage evidence; this assessment does not convert that into special-family coverage.

Clean ROM SHA-256: `7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600`. Bounded source spans: `01:D80F..D8B0` SHA `45065edcc0d7fd7c11a7cb70d68105a3ddf3dd0506e0687c8e40a4dd5c4c02c6`; regular constructor `01:DA56..DB2C` SHA `b994393e35f10f97885a1fa7e578e0b06e88569e81157062696aa42476f7eb8a`; reserved emitter `01:DE82..DED2` SHA `b5818e0d81d3423148ada3f7e433d40cf38c1928b58b6d8da257b0e3aa15e473`.

## Private ordinary-reserved C replay proof

The additive private prototype is `local/evidence/special-actor-prototype-20261009/reserved_replay.c`, with `check_reserved_replay.py`. It remains outside qualified native/runtime source and is not enabled in a player build. The frozen receipt is `qualification-frozen/report.json`: **59 replay cases and 40 gates pass**. A repeat uses a fresh directory beneath the prototype:

```powershell
python local/evidence/special-actor-prototype-20261009/check_reserved_replay.py --output local/evidence/special-actor-prototype-20261009/qualification-new
```

The one genuine reserved-record input contains the actual inactive records 17/18 from an existing Likado producer. Its complete staging bytes match the adjacent actual PPU packet, all 544 bytes. The other **58 cases are host-synthetic reserved replays**, using copied genuine active ordinary record bytes from `7E:414B` and exact clean-ROM descriptor resources. The matrix also uses the original record-17 writer's pose-2/base-A0 combination. Those cases modify in-memory host copies only; no guest process runs and no record is spawned or activated in the game. Natural active reserved-family coverage remains **zero**.

The C core reconstructs active/culled metadata and original four-word descriptors, checks masks and clean-ROM identity, computes the independent compact `34/38` cursors, and validates each emitted staging piece and high-OAM pair. Culled/inactive entries do not consume physical reserved slots. Unconsumed slots must retain their parked X/Y/high bits; old tile words there are correctly ignored. Stable private ranks 4–11 remain before party/NPC ranks, separately from compact physical slots.

The independent Python original-source decoder agrees with every C result for both phases and both original masks, including X/Y boundary samples, one/both visible members, mixed visibility, and both culled. It verifies record 18 uses slots 4–7 when record 17 is inactive or clipped. The lifetime model requires an explicitly complete 544-byte OAM packet, identical resource identity and matching producer generation/epoch. It refuses old epochs and pre-restore generations even when all packet bytes happen to be identical. A query before first display leaves queued metadata intact; after completion, mutable current pose/camera bytes do not replace the displayed producer's metadata.

Refusal cases cover B0/A8 families, unsupported pose/descriptor bounds, nonzero offsets, wrapping, wrong presentation context/mask, wrong reserved cursors, changed/truncated ROM or RAM, malformed piece coordinates/words/high bits, incomplete/truncated OAM, unrelated full-packet byte mismatch, changed resources, stale packets and restore reset. Every read input, the private sources and the compiled SHA implementation/header are hash-checked afterward.

Prototype C SHA-256: `73c34eb0534ff3c5748af3c15f95b97c745852611460a9ffb45f7a4ad7ff1897`. Checker SHA-256: `c7298c9617ca9f9a0f52ea9854fbe095109fbd1e96301a4cd65fe5cb8cf2f9ab`. Private DLL SHA-256: `731ba1066c196d7b2ef5f77ec2047db1c507840611f2685169e4de7321141fc5`.

This qualifies metadata reconstruction, staging validation, ordering and a synthetic completion/lifetime model. It does **not** exercise actual DMA callbacks, rendered special-actor pixels, audio, controllers, guest activation or natural campaign transitions. Integration after the ordinary-party proof should reuse the already observed actual DMA transfer identity; its token must originate at transfer start, never be inferred solely from packet byte equality or a fixed field delay. The live hook still needs the original `DAB6` CPU/stack context, and the field resource resolver still supplies actual scene eligibility. Neither is replaced by this standalone replay's declared context.

## Combined private observer integration

The next private copy is `local/evidence/special-actor-prototype-20261009/src/foundation_wide_actors.c/h`, based on the frozen ordinary-party prototype C SHA `6c30df2bae22d446b727c987b78139f3dcf4a9998dc51a260007223cf49134ed`. It retains five party records and extends the regular list to 19. The completed staging validator separately reconstructs the compact reserved `34/38` cursor for visible ordinary records 17/18. It requires the correct parked X/Y/high bits in unused reserved slots, without interpreting their stale tile words as actors. Ordinary `046B` and party/NPC append order remain separate and unchanged. Retained margin metadata uses stable reserved ranks 4–11 before party 12–31 and ordinary regular 32 onward.

The source-backed family distinction corrects an overly restrictive guard in the earlier standalone replay. **Derived A8–AF selects a special emitter only for party records**, at `01:D94D..D953`. The regular constructor instead branches only on base B0 at `DA92..DA97`; its emitter selection at `DB13..DB1C` depends solely on index 17. Consequently ordinary regular A8 artwork is accepted, including regular records below 17 and reserved records 17/18. Party derived A8 and either family's B0 constructor remain refused. The historical standalone receipt above is preserved, including its conservative A8 refusal; it does not define the final integrated regular-art contract.

`check_integrated_reserved.c` registers the private module's actual seven opcode observer callbacks and DMA notification callback, then replays their exact CPU/stack/direct-page seam contexts. This runs the callback bodies and the actual public `FoundationWideActorsPrepareLine` interface; the host harness does not execute guest constructors or the DMA engine. Every observer/notification call compares the full RAM, source PPU, CPU or DMA structures before and after to enforce read-only observation. The unchanged 544-byte original packet, staging completion and transfer-start producer identity remain required. A new byte-identical queued producer during a started transfer must not replace that transfer's epoch. Short transfers, packet mismatch and restore reset invalidate retained output.

The frozen receipt is `integrated-proof-frozen/report.json`: **53 host replays and 14 aggregate checks pass**, comprising 19 accepts and 34 refusals. Five genuine adjacent Likado producer/PPU pairs retain their actual one-member party and original regular cache, with all 544 staging bytes matching scanout. Reserved records 17/18 are inactive in all five genuine inputs. The other 48 cases mutate host copies only. They cover both visible, either visible, either culled, both culled, center anchors, reserved compaction, low-pose A8 descriptors and descriptor bounds, and malformed coordinates/words/size bits/cursors/masks/pointers/capture sequences. They also retain the inherited party, resource/layout, wrap, offset and packet/lifetime refusals. The matching late A8 capture accepts; a late A8 change with stale staging refuses on packet provenance rather than on an invented special-family classification.

The seven synthetic reserved patterns keep ordinary append end at slot 12; reserved output advances only `34/38`. Culled record 17 allows visible record 18 to compact into physical slots 4–7, while its margin metadata keeps its stable virtual ranks 8–11. Positive side metadata uses clean-ROM descriptors and the input's actual VRAM/CGRAM decode. A separate **synthetic opaque-control pixel** test copies the derived ranks into overlapping objects and calls the runtime's actual `PpuComposeExtraObjects`: reserved17 slot5 wins over reserved18 slot9 and party slot12 even when those objects arrive in reverse priority order; removing 17 lets 18 win. This qualifies the priority seam with host control colors, not natural special-art pixels or a rendered guest frame.

The checker hash-protects all read fixtures, ROM, private inputs, qualified authored/live actor sources and the frozen ordinary-party prototype before and after the run. It changes no qualified native/runtime module or installed build. Repeat with a fresh private output directory:

```powershell
python local/evidence/special-actor-prototype-20261009/check_integrated_reserved.py --out local/evidence/special-actor-prototype-20261009/integrated-proof-new
```

Frozen private C SHA-256: `57456b84c79601f1ce3756b3caea6eb18923f777e0502e70fdef886866ae2d88`; unchanged header: `9cef473607a2ffbf9534d33d841eb041c1ae41a069a30f7f0833e54b6daed763`. Harness C: `c1ec8be3414ba6e8ba3d4005b407e01396eba1c5584182e3635eeb7b7bf5b238`; checker: `5be61972941d399608cc66de71cf069dacf1a46bf6a95ccedf065c271984be1d`; private harness EXE: `9815c4745071b8d1ada0b04800b87a51c003f2ceb9ca4a04794c6c11b4537390`; frozen report: `53385e04b85da2acd2cb950d36bec1a2404ae229e8c7e2fe576b3b58ed31b370`.

Natural active reserved coverage remains **zero**. This private proof does not certify original guest observer routing, campaign activation, special-art pixels, GPU/audio/controller behavior, or B0/party-A8/variable/wrapping composites. Combined guest candidate testing and an original enabled reserved fixture remain separate next qualifications.

## Reusable authored canary and secondary-field linkage

The same replay is now preserved as authored `tools/foundation_reserved_actor_canary.c` and `tools/check_foundation_reserved_actors.py`. Neither embeds original ROM, graphics, OAM or saves. The canary includes the explicitly selected authored observer implementation; the checker independently links the explicitly selected field resolver. Both `--actor-source-dir` and `--field-source-dir` are required. The selected actor source must implement the ordinary-party/reserved contract; choosing an older source without that contract is not a valid positive qualification. The default external fixtures remain the five genuine adjacent pairs in `local/runs/actor-wide-20261009-133859/sweep-on/dump`; `--fixtures` and `--rom` may select explicit read-only inputs. The output must be a fresh directory under project `local/`.

The frozen authored-tool receipt `local/evidence/reserved-actors-authored-20261009-frozen/report.json` passes the same **53 replays and 14 gates** against actor C SHA `57456b84c79601f1ce3756b3caea6eb18923f777e0502e70fdef886866ae2d88` and secondary field C SHA `b58b866ebb82161a7ea6ecb3af0eb4402f69f8b910c420feb4dbfda2ee59d4ae`. All protected external inputs, selected source/header pairs, qualified authored/live actor sources, compiled helper sources and the historical party prototype present during the run match their before-run hashes. This verifies linkage with the new field resolver using the same Likado actor matrix; it does not add secondary-map natural actor coverage.

```powershell
python tools/check_foundation_reserved_actors.py --actor-source-dir local/evidence/special-actor-prototype-20261009/src --field-source-dir local/evidence/secondary-prototype-20261009/src --out local/evidence/reserved-actors-repeat
```

Authored canary SHA-256: `70b66d3d0cbf542a96c905b488a8aa7e914bd0352b6d1802ad3eef53c8f008ac`; checker: `ad76d92743082c45659202569f88930d5ad4d783025119e7f269b0600e495fe9`; frozen report: `2d245c67f0b05501c7506dbf748bc7d306f7e5c3346b8e7a02770added7cd679`; harness EXE: `6f11211c1d5d52287ab4fea5d214e145e6081a5a5ca5bff09505e3d03cdb2c99`. Earlier standalone and private integration receipts remain historical. Natural active reserved coverage remains zero, and all previously stated guest/campaign/pixel/controller/audio limits still apply.
