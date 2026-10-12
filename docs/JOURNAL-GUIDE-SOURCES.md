# Journal guide content sources

Authored on 2026-10-12. The 42 cards in
`native/foundation/src/foundation_guide_data.h` summarize written walkthroughs
from the opening through the ending. They are concise navigation reminders,
not a complete dungeon map, item catalogue or battle strategy guide. Names
follow the English game and source spellings where practical. No source prose,
screenshots, maps or original game assets are reproduced.

This content is **written-guide advice**. It does not establish natural campaign
execution, a completed objective, an observed conversation or a durable journal
history. The owner and play testers will verify the campaign. Feature smoke
checks can qualify browsing and rendering without qualifying every direction.
The existing automatic current-state advice has its own original-source and
finite execution evidence, including
[the 0.3.8 bridge continuation](FOUNDATION-BRIDGE-ACCUMULATOR-2026-10-12.md).
These static cards do not widen those automatic predicates.

`part` is an editorial section numbered 1-14. It is **not** the original story
stage byte, a quest flag or a map coordinate. The header contains no state
mapping. Card numbers below are one-based; array indices are zero-based.
Browsing ahead reveals prerequisites and later objectives.

## RPGClassics source coverage

The [walkthrough index](https://tartarus.rpgclassics.com/secretstars/walk.shtml)
was read, and all fourteen actual part links were requested. Parts 1-10 returned
readable text. Parts 11-14 returned HTTP 404 when opened directly and through
their index links. They have **not been read**; fallback sources below supply
the late-game content. An HTTP-to-HTTPS retry for part 11 also returned 404.
Alternate host checks did not yield readable replacements.

| Editorial part | Cards | Exact RPGClassics page | Access |
| --- | --- | --- | --- |
| 1 | 01-03 | [Heart Island](https://tartarus.rpgclassics.com/secretstars/walk01.shtml) | Read |
| 2 | 04-06 | [Save the Children](https://tartarus.rpgclassics.com/secretstars/walk02.shtml) | Read |
| 3 | 07-09 | [The Farmer Baz](https://tartarus.rpgclassics.com/secretstars/walk03.shtml) | Read |
| 4 | 10-12 | [It's Not A Circus](https://tartarus.rpgclassics.com/secretstars/walk04.shtml) | Read |
| 5 | 13-14 | [Leona](https://tartarus.rpgclassics.com/secretstars/walk05.shtml) | Read |
| 6 | 15-18 | [The East Continent](https://tartarus.rpgclassics.com/secretstars/walk06.shtml) | Read |
| 7 | 19-22 | [Becoming Banalet](https://tartarus.rpgclassics.com/secretstars/walk07.shtml) | Read |
| 8 | 23-25 | [The Search for Dr. Ash](https://tartarus.rpgclassics.com/secretstars/walk08.shtml) | Read |
| 9 | 26-28 | [This Booth Out of Order](https://tartarus.rpgclassics.com/secretstars/walk09.shtml) | Read |
| 10 | 29-31 | [The Woman Warrior](https://tartarus.rpgclassics.com/secretstars/walk10.shtml) | Read |
| 11 | 32-33 | [Dr. Parakless](https://tartarus.rpgclassics.com/secretstars/walk11.shtml) | 404; fallback |
| 12 | 34 | [Nerves of Steel](https://tartarus.rpgclassics.com/secretstars/walk12.shtml) | 404; fallback |
| 13 | 35 | [Bris-dain for Godom](https://tartarus.rpgclassics.com/secretstars/walk13.shtml) | 404; fallback |
| 14 | 36-42 | [Kustera Power](https://tartarus.rpgclassics.com/secretstars/walk14.shtml) | 404; fallback |

Some index titles differ from the linked pages' headings; the exact URLs identify
the sources. Part 8's browser title incorrectly says part 7, but its text heading
says part 8. Editorial sections 11-14 retain the index's order, with additional
final-battle cards in section 14; they do not imply reading unavailable text.

## Readable late-game sources

| Cards | Source actually read | Relevant sections |
| --- | --- | --- |
| 32-34, 42 | [Igor M. Comba, RPG Gamers walkthrough](https://rpggamers.com/walkthrough/secret-of-the-stars) | Homncurse's secret; The final Battle |
| 35, 39-41 | [tankMage, RetroMaggedon walkthrough, June 2017](https://retromaggedon.com/index.php/tecmo-secret-of-the-stars-snes-walkthrough/) | Part 7: The Fall of Homncruse; Brisben; Gara's Lair; Godem's Lair; Homncruse's Lair; final rounds |
| 36-38 | [Steve Bergstrom / SCHALAAY, GameFAQs guide 8776](https://gamefaqs.gamespot.com/snes/588647-tecmo-secret-of-the-stars/faqs/8776) | Old Hill after Godem; Jeep Volcano; Dram; Booth |

These three pages returned actual readable text, including the final encounter
and ending. The final card deliberately avoids narrative ending details.
Directions to Donto differ between guides, so the card uses the agreed town
identity and mountain-ringed setting rather than choosing a disputed compass
bearing. Shrine metal names and party transfer use the readable GameFAQs guide.
The shrine card does not guess which chest or original flag owns a component.

[GameFAQs guide 43520](https://gamefaqs.gamespot.com/snes/588647-tecmo-secret-of-the-stars/faqs/43520)
was blocked in the parent assessment and is not a content source here. The
[Neoseeker 99000-b page](https://www.neoseeker.com/secret-of-the-stars/faqs/99000-b.html)
returned 403 on direct opening; its search excerpts were not used for authored
cards. The
[Neoseeker 134483-c mirror](https://www.neoseeker.com/secret-of-the-stars/faqs/134483-c.html)
also failed direct opening and is not claimed read.

## Content checks and limits

All 42 titles and their eight line slots are ASCII, each at most 28 characters.
Unused slots are empty strings. The structure stores only a title, eight lines
and the editorial part; there is no guest memory write, persistence or completion
inference. Source selection, current-stage suggestion and navigation are separate
integration work.

Conservative whitespace word counts include titles and every nonempty line:

| Editorial part | Words |
| --- | ---: |
| 1 | 89 |
| 2 | 101 |
| 3 | 104 |
| 4 | 98 |
| 5 | 68 |
| 6 | 135 |
| 7 | 135 |
| 8 | 103 |
| 9 | 102 |
| 10 | 98 |
| 11 | 64 |
| 12 | 35 |
| 13 | 33 |
| 14 | 161 |

Fallback card attribution is additionally limited per entire source page:
RPG Gamers 123 words, RetroMaggedon 104 words and GameFAQs 8776 66 words.
Each is below 180 words. Source identifiers and access
notes above are bibliographic metadata, not further walkthrough summaries.
The cards use independently phrased short instructions; none intentionally
quotes a source passage. No statistic table or detailed source maze solution
is copied. A source reference is not live gameplay verification, and no missing
RPGClassics ending page is represented as recovered.

## Automatic Current chapter cards — 0.4.7

The separate `foundation_current_data.h` now supplies25 independently phrased
route reminders keyed by original chapter0..24. It does not reuse Guide browsing
position. Original message selectors in the retained chapter-source assessment
establish broad chapter scope; the walkthrough references above supply directions.
Existing finer source-backed leads remain ahead of these cards. There are no
new quest-completion records, inferred acquisitions, flag meanings or map pins.

RPG Gamers and RetroMaggedon were reread for this continuation. GameFAQs8776
failed reopening; its previously documented reading remains historical attribution.
Later chapter cards are broad reminders; chapter24's fountain instruction is
conditional on Bosen's request. Owner/play testers verify campaign directions.
Focused staged checkpoints qualify visible operation, not natural acquisition.
The complete42-page Guide remains byte-identical.
