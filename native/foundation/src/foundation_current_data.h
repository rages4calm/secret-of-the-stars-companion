#ifndef FOUNDATION_CURRENT_DATA_H
#define FOUNDATION_CURRENT_DATA_H
#include <stddef.h>
#include <stdint.h>

/* Automatic route reminders indexed by ORIGINAL chapter5372, not Guide part
 * or browsing position. Original selectors establish chapter scope; written
 * walkthroughs supply directions. Existing finer source-backed leads take
 * priority. Nothing here establishes completion, inventory or destination.
 * Sources: docs/JOURNAL-GUIDE-SOURCES.md and Current continuation source notes. */
typedef struct FoundationCurrentAdvice {
    const char *objective[2];
    const char *route[2];
} FoundationCurrentAdvice;

static const FoundationCurrentAdvice foundation_current_advice[] = {
    {{"Find David in Likado.", "Ask about the StarCrest."},
     {"Leave home; travel east.", "David: southeast house."}},
    {{"Gather Aqutallion allies.", "Search Winds and Beegees."},
     {"Winds: southeast house.", "Beegees: visit the church."}},
    {{"Help Beegees' townspeople.", "Recover the Dog Pill."},
     {"Badbad's house: south cave.", "Bring pill to the priest."}},
    {{"Rescue the Ringo children.", "Ask Beegees' mayor."},
     {"Mayor: southwest house.", "Use yellow gate at the lab."}},
    {{"Find help for Old Hill.", "Seek builders and Morgan."},
     {"Bun's master: near Winds.", "Giant: eastern tree path."}},
    {{"Free Baz from Golan.", "Ask Dynamite for a weapon."},
     {"Decatas: upstairs lab.", "Take Graviton to Giant."}},
    {{"Grow Old Hill; seek Cody.", "Ask about Decatas' circus."},
     {"Visit the voting clerk.", "Mayor offers a ticket lead."}},
    {{"Find the route to Bonzley.", "Ask Morgan about WIN-KEY."},
     {"Giant: hidden room wall.", "WIN-Shrine: bridge device."}},
    {{"Help Kaja open the route.", "Seek Sidon Forest's clue."},
     {"Kaja asks for a moustache.", "Check the southern forest."}},
    {{"Seek Garados in Bonzley.", "Follow the Alpin cave."},
     {"Prepare before Garados.", "Take golden Cody to Kaja."}},
    {{"Bring golden Cody home.", "Ask Kaja how to restore him."},
     {"Visit Shark by the coast.", "Return to Old Hill's shrine."}},
    {{"Find Leona in Decatas.", "Ask the town gossip."},
     {"Check the poor apartments.", "If taken, ask local hoods."}},
    {{"Seek the eastern road.", "Ask Baz about the tunnel."},
     {"Box Town: give Ray Gloves.", "Visit Sleepers and Karappon."}},
    {{"Escape Lagoon's mirage.", "Seek Brasca afterward."},
     {"South mirage: do not enter.", "East mirage: enter the town."}},
    {{"Find Brasca's hidden route.", "Prepare for lava passages."},
     {"Aqutallion: enter the well.", "STEP helps against lava."}},
    {{"Reach Bowy through Brasca.", "Face Dram; look for Dan."},
     {"Switches: east/center/west.", "Cross the lower lava route."}},
    {{"Repair Old Hill's ship.", "Prepare the Banalet trials."},
     {"Ask Bun and Dynamite.", "Gold Nail: behind the tarp."}},
    {{"Seek both orbs and fuel.", "Follow MoreEyes and Edon."},
     {"Take orbs to Bonzley's cove.", "Fuel: Decatas' lab rocket."}},
    {{"Seek Booth's castle.", "Ask Ash about the waterfall."},
     {"Explore both castle tiers.", "After Booth, report to Ash."}},
    {{"Seek Amaboss and Gara.", "BunnySuits help gain entry."},
     {"Amaboss: basement cave.", "Gara: balconies link towers."}},
    {{"Find Parakless and his lead.", "Travel from Hidon to Donto."},
     {"Misty Pass: lab and shrine.", "Donto: follow work whistle."}},
    {{"Disable Steeler's machinery.", "Explore its pits and pads."},
     {"Stop four units, then core.", "Old Hill: ask for new clues."}},
    {{"Seek Godem beyond Brisben.", "Prepare before leaving town."},
     {"Brisben shrine: star tile.", "Bring Aqutalium home."}},
    {{"Prepare the Algos launch.", "Kustera: four shrine metals."},
     {"Warehouse: transfer metals.", "Dynamite: shrine console."}},
    {{"Explore Jeep as both teams.", "Switches help both teams."},
     {"Gold/silver doors: use SWAP.", "If Bosen asks: Red Fountain."}}
};

/* Fresh current state only. Idle original field ownership is required, and
 * unknown party/chapter or an active dialogue/event yields no chapter card.
 * This reader does not mutate RAM or keep a host-side progression cache. */
static inline const FoundationCurrentAdvice *FoundationJournalChapterAdvice(
        const uint8_t *ram, size_t size) {
    if (!ram || size < 0x53b3 || ram[0x20] != 1 ||
        (ram[0x4b6] != 0 && ram[0x4b6] != 0x80) || ram[0x5372] > 24 ||
        ram[0x434] || ram[0x435] || ram[0x532] ||
        ram[0x1410] || ram[0x1411] || ram[0x1415] ||
        ram[0x1416] || ram[0x1417]) return NULL;
    return &foundation_current_advice[ram[0x5372]];
}

_Static_assert(sizeof(foundation_current_advice) / sizeof(foundation_current_advice[0]) == 25,
               "Every original chapter0..24 has route advice");
#endif
