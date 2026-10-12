#ifndef FOUNDATION_GUIDE_DATA_H
#define FOUNDATION_GUIDE_DATA_H

/* Authored, manually browsable walkthrough notes. These are written-guide
 * directions, not observed events, completion history or quest flags.
 * part is an editorial walkthrough section, not the original story byte.
 * Sources and inaccessible source links: docs/JOURNAL-GUIDE-SOURCES.md. */
typedef struct FoundationGuidePage {
    const char *title;
    const char *lines[8];
    unsigned part;
} FoundationGuidePage;

static const FoundationGuidePage foundation_guide_pages[] = {
    /* 01-03: Heart Island */
    { "Find David", {
        "Leave Ray's house.", "Likado lies to the east.",
        "David: southeast house.", "Ask about the StarCrest.",
        "Rest in beds; save often.", "Prepare healing supplies.", "", ""
    }, 1 },
    { "The first StarCrest", {
        "After speaking to David,", "explore the mountain cave.",
        "Stand on its central tile.", "Ray gains magic; David",
        "forms the Kustera party.", "SWAP changes active party.",
        "Keep both groups equipped.", ""
    }, 1 },
    { "Jeep Volcano", {
        "Go northeast on Heart Isle.", "Kustera open green gates;",
        "Aqutallion open yellow.", "Climb the volcanic path.",
        "Rest before Dr. Gari.", "Defeat him; Bosen takes you",
        "to Old Hill's new refuge.", ""
    }, 1 },
    /* 04-06: Save the Children */
    { "Winds and Beegees", {
        "Head west to Winds.", "Visit the southeast house.",
        "Send its children to safety.", "Continue south to Beegees.",
        "Defeat the church's Badmen.", "Speak to priest and Tina.",
        "Tina joins Aqutallion.", ""
    }, 2 },
    { "Badbad and the Dog-Pill", {
        "Take the cave south from", "Beegees to Badbad's house.",
        "Climb to his upstairs room.", "After victory, check below",
        "his chair for the Dog-Pill.", "Bring it to Beegees' priest.",
        "Ryu can now join Kustera.", ""
    }, 2 },
    { "Rescue the lab children", {
        "Visit Beegees' mayor in", "the southwest house.",
        "Follow the route to Ringo.", "Aqutallion use yellow gate",
        "and the upper catwalks.", "Defeat Bingo and Leach.",
        "Old Hill needs settlers.", ""
    }, 2 },
    /* 07-09: The Farmer Baz */
    { "Builder and hidden tunnel", {
        "Northwest of Winds, ask", "Bun's master for a builder.",
        "Then visit Giant.", "Follow its eastern trees",
        "north to Morgan's hole.", "After Decatas refuses you,",
        "ask Morgan; bring 100 gold.", ""
    }, 3 },
    { "Free farmer Baz", {
        "Visit Dynamite upstairs", "in Decatas' laboratory.",
        "Take the Graviton to Giant.", "Find Baz in the big house.",
        "Use Graviton during battle", "to shrink his captor.",
        "Rescue Baz for Old Hill.", ""
    }, 3 },
    { "A ticket and a lion", {
        "Return to Decatas and vote.", "The new mayor gives Ticket.",
        "Enter the circus maze.", "Use stairs, not the exit.",
        "Cross rafters to meet Cody.", "After the circus vanishes,",
        "ask the priest what next.", ""
    }, 3 },
    /* 10-12: The bridge and Bonzley */
    { "Lower Victory Bridge", {
        "The bridge south of Winds", "needs Morgan's WIN-KEY.",
        "In Giant, walk through", "his room's right-hand wall.",
        "Take the key to WIN-Shrine.", "Use the device at the top.",
        "Cross toward Bonzley.", ""
    }, 4 },
    { "Kaja's missing mustache", {
        "Kaja blocks the route.", "Search Sidon Forest to",
        "the southwest, by ponds.", "Defeat Scratcher and bring",
        "its mustache back to Kaja.", "Use his bed to restore MP.",
        "Continue to Alpin Shrine.", ""
    }, 4 },
    { "Bring Cody home", {
        "Through Alpin's cave,", "defeat Garados.",
        "Bring golden Cody to Kaja.", "Visit Shark by the cove",
        "on the southern coast.", "Then return to Old Hill's",
        "shrine to restore Cody.", ""
    }, 4 },
    /* 13-14: Leona */
    { "Find Leona in Decatas", {
        "Ask the town gossip.", "Visit the middle apartment",
        "in the poorer district.", "After Leona is taken,",
        "question the local hoods", "and the gossip again.", "", ""
    }, 5 },
    { "Open the hidden route", {
        "Search down and right for", "a man concealed by a wall.",
        "Buy his TimeBomb: 100 gold.", "Use it at the dented wall.",
        "Enter the house; use its bed", "to reach the basement.",
        "Rescue Leona; seek Brasca.", ""
    }, 5 },
    /* 15-18: East continent */
    { "Open the eastern road", {
        "At Old Hill, speak to Baz.", "Use Morgan's new tunnel.",
        "Travel east to Box Town.", "Buy Gloves; equip Ray.",
        "Challenge the tent's leader", "with the Aqutallion party.",
        "Continue south to Sleepers.", ""
    }, 6 },
    { "Karappon and storage", {
        "Defeat Arthur in Sleepers.", "Go south to Karappon.",
        "Speak to Arithree after", "beating Andy and Arthur.",
        "They clear the south rock.", "Old Hill's warehouse lets",
        "the parties exchange items.", ""
    }, 6 },
    { "Escape Lagoon's mirage", {
        "Continue through Codo to", "Lagoon in Zoo Desert.",
        "After the trap, walk south", "to a mirage; do not enter.",
        "Walk east to the next town", "and enter to escape.",
        "Seek Brasca southeast.", ""
    }, 6 },
    { "Brasca's lava passages", {
        "Aqutallion enter the well.", "Cast STEP against lava harm.",
        "Use east-room switch first,", "then the center and west.",
        "Cross the raised lower lava", "to Bowy; defeat Dram.",
        "Dan completes Aqutallion.", ""
    }, 6 },
    /* 19-22: Banalet trials */
    { "Repair the ship", {
        "Return to damaged Old Hill.", "Speak with Dynamite and Bun.",
        "Search behind the tarp in", "the architect's old house.",
        "Bring Gold Nail to Dynamite.", "With all five Aqutallion,",
        "Shark can join Kustera.", ""
    }, 7 },
    { "Fire and Water trials", {
        "Use Star Shrines' left tile.", "Ray: north of Beegees.",
        "Tina: west over WIN-Bridge,", "around the north mountain.",
        "Each must fight alone.", "Heal before entering.",
        "Winning grants Banalet rank.", ""
    }, 7 },
    { "Cody's Wind trial", {
        "Stock healing food for Cody.", "From Karappon head south;",
        "at the T junction go west.", "Use the shrine's left tile.",
        "Defeat both air spirits.", "Banalet allies can combine",
        "compatible magic via COMBI.", ""
    }, 7 },
    { "Leona's Earth trial", {
        "Sail north from Giant to", "the frozen island.",
        "Round its northeast corner;", "go west to the Star Shrine.",
        "STEP protects on snow.", "Bring Leona healing food.",
        "Finish all four trials.", ""
    }, 7 },
    /* 23-25: Orbs and Dr. Ash */
    { "MoreEyes and the Blue Orb", {
        "After attaining Aqutallion,", "visit MoreEyes' shrine.",
        "Ghost Cave is on the island", "directly north of MoreEyes.",
        "Defeat Undead; recover Moai.", "Return it to the shrine.",
        "Murray joins; take Blue Orb.", ""
    }, 8 },
    { "Edon and the Red Orb", {
        "Sail to Jabon Island.", "Ask Edon's castle leader",
        "on its upper floor.", "Go southwest to Onsaka.",
        "Challenge Jubei inside", "the largest house.",
        "Return to Edon for Red Orb.", ""
    }, 8 },
    { "Fuel for the rocket", {
        "Carry both orbs to the cove", "southwest of Bonzley.",
        "Defeat Clarken for Tacosmin.", "Bring fuel to the rocket",
        "below Decatas' laboratory.", "After landing, drop through",
        "the corner hole to meet Ash.", ""
    }, 8 },
    /* 26-28: Booth */
    { "Across the upper continent", {
        "Prepare in Elekees; Evelyn", "can join the Kustera party.",
        "Follow the eastern coast,", "then its southern paths",
        "to Alazina.", "Booth's Castle lies south.",
        "Old Hill is rebuilding too.", ""
    }, 9 },
    { "Booth's two-tier castle", {
        "White tiles change tiers.", "Use them to change floors.",
        "Some paths run underneath", "the visible upper walkway.",
        "Keep exploring both tiers.", "Collect Fire Sword en route",
        "for fire Unity attacks.", ""
    }, 9 },
    { "Booth and the waterfall", {
        "Reach Booth on floor four.", "MIRROR helps against spells;",
        "SLOW does not affect him.", "After victory, go down one",
        "floor before casting FLEE.", "Report to Ash for Niagaran.",
        "Only Aqutallion can use it.", ""
    }, 9 },
    /* 29-31: Amaboss and Gara */
    { "Enter Amaboss", {
        "Sail north of Elekees,", "up the waterfall; go east.",
        "Buy three BunnySuits in", "Dengers for Ray, Cody, Dan.",
        "Equip them; travel west to", "Amaboss. Accept Daisy's task",
        "Beth and Kathy join Kustera.", ""
    }, 10 },
    { "The way to Gara", {
        "Take Amaboss castle's", "lower-left basement stairs.",
        "Aqutallion cross the cave.", "Use the water switch.",
        "In Gara's castle, follow", "balconies between towers.",
        "Gara waits on floor eight.", ""
    }, 10 },
    { "After Gara's defeat", {
        "Keep healing through Gara's", "powerful elemental attacks.",
        "Ash rescues you afterward.", "His next lead is Parakless",
        "in Hidon, below the clouds.", "Use the new flying transport",
        "to reach the lower world.", ""
    }, 10 },
    /* 32-35: Fallback-written late-game sources; see sources document. */
    { "Parakless in Misty Pass", {
        "From Hidon, take the cave", "north of town.",
        "Aqutallion climb Misty Pass.", "Read the laboratory message.",
        "Use its switch; explore", "the shrine's star tiles.",
        "Bosen directs you to Donto.", ""
    }, 11 },
    { "Donto's work whistle", {
        "Find mountain-ringed Donto.", "Speak with its residents.",
        "Revisit the worker in the", "northwestern house.",
        "When the whistle sounds,", "follow workers into the lab.",
        "Its pad leads to Steeler.", ""
    }, 11 },
    { "Disable Steeler Lab", {
        "Explore pits and warp pads", "to reach the engine room.",
        "Stop all four outer units,", "then the central machine.",
        "Return to Old Hill; speak", "to Decatas' visiting mayor.",
        "Prepare before that meeting.", ""
    }, 12 },
    { "Brisben and Godem", {
        "Fly west from Brasca to", "Brisben's island shrine.",
        "Use its star tile.", "Northwest stairs lead onward",
        "to the route across the hub.", "Beat Godem; take Aqutalium.",
        "Return to Old Hill.", ""
    }, 13 },
    /* 36-42: Both parties and the ending */
    { "Four Kustera components", {
        "Explore four Star Shrines", "as Kustera: Iridium, Ultrium",
        "Eledium, Organium.", "Warehouse them; Aqutallion",
        "must withdraw them.", "", "", ""
    }, 14 },
    { "Launch the Algos", {
        "Ask Dynamite; take all four", "components plus Aqutalium",
        "to the shrine's secret room.", "Activate the console.",
        "Equip both parties for Jeep.", "", "", ""
    }, 14 },
    { "Jeep: Dram and Booth", {
        "Kustera: silver doors.", "Aqutallion: gold doors.",
        "Switches aid the other team.", "Aqutallion fight Bio Dram,",
        "then Booth; take CureCane.", "", "", ""
    }, 14 },
    { "Jeep: Gara and Godem", {
        "Alternate parties to open", "Gara's maze switches.",
        "Beat Bio Gara, then Godem.", "All four victories open",
        "the central final route.", "", "", ""
    }, 14 },
    { "The first final encounter", {
        "Central tile: follow ladders", "around pits to the throne.",
        "First Homncruse fight:", "accept the story defeat.",
        "Then follow Bosen's lead.", "", "", ""
    }, 14 },
    { "Return to Red Fountain", {
        "UFO back to Heart Island.", "Revisit the first shrine.",
        "Beyond its star tile:", "MetlSwrd and LightOrb.",
        "Restock; face Homncruse.", "", "", ""
    }, 14 },
    { "The battle and the ending", {
        "Use LightOrb; Ray: MetlSwrd.", "Keep everyone healed.",
        "Restore MP as needed.", "Defeat both final forms.",
        "Watch Old Hill's ending.", "", "", ""
    }, 14 }
};

#define FOUNDATION_GUIDE_PAGE_COUNT \
    (sizeof(foundation_guide_pages) / sizeof(foundation_guide_pages[0]))

/* Optional player-chosen town for each page. These are original 04:C200
 * name identities, never coordinates or an inferred next event. Unmapped
 * shrines, castles, upper-world locations and Kaja-House stay unavailable.
 * The map resolves only a unique currently accepted world0 town point. */
static const int foundation_guide_towns[] = {
    18, -1, -1, 17, 1, 1, 2, 2, 3, -1, -1, 0, 3, -1,
    5, 7, 21, 9, 0, -1, -1, -1, -1, 11, 3, -1, -1, -1,
    -1, -1, 15, 15, 14, 0, -1, -1, -1, -1, -1, -1, -1, -1
};
_Static_assert(sizeof(foundation_guide_towns)/sizeof(foundation_guide_towns[0]) ==
    FOUNDATION_GUIDE_PAGE_COUNT, "Every guide page has an explicit town choice");
static inline int FoundationGuideTownName(unsigned page) {
    return page < FOUNDATION_GUIDE_PAGE_COUNT ? foundation_guide_towns[page] : -1;
}
static inline const char *FoundationGuideTownLabel(unsigned page) {
    switch (FoundationGuideTownName(page)) {
    case 0: return "OLD HILL";
    case 1: return "BEEGEES";
    case 2: return "GIANT";
    case 3: return "DECATAS";
    case 5: return "BOX TOWN";
    case 7: return "KARAPPON";
    case 9: return "BRASCA";
    case 11: return "EDON";
    case 14: return "DONTO";
    case 15: return "HIDON";
    case 17: return "WINDS";
    case 18: return "LIKADO";
    case 21: return "LAGOON";
    default: return "";
    }
}

#endif
