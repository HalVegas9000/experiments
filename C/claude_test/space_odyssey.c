/* =====================================================================
   GALACTIC ODYSSEY - A Space Adventure
   Inspired by Star Trek, Star Wars, and classic text adventure games.

   You are Commander Alex Starfield. Your ship, the ISS Horizon, has
   crash-landed on Kelon-7. Repair your ship or find another escape
   before the Galactic Dominion forces arrive!

   Build:  gcc -o space_odyssey space_odyssey.c
   ===================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ---- Limits ---- */
#define MAX_ROOMS          11
#define MAX_ITEMS          13
#define MAX_ITEMS_PER_ROOM  6
#define MAX_INV            15
#define MAX_CMD           256
#define NUM_DIRS            6

/* ---- Directions ---- */
#define NORTH 0
#define SOUTH 1
#define EAST  2
#define WEST  3
#define UP    4
#define DOWN  5

/* ---- Room IDs ---- */
#define ROOM_BRIDGE      0
#define ROOM_ENGINE      1
#define ROOM_CARGO       2
#define ROOM_AIRLOCK     3
#define ROOM_CRASH_SITE  4
#define ROOM_FOREST      5
#define ROOM_RUINS       6
#define ROOM_CAVE        7
#define ROOM_CAVE_DEEP   8
#define ROOM_VILLAGE     9
#define ROOM_SHUTTLE    10

/* ---- Item IDs ---- */
#define ITEM_LASER        0
#define ITEM_COMMS        1
#define ITEM_POWER_CELL   2
#define ITEM_MEDKIT       3
#define ITEM_XTAL         4
#define ITEM_ENGINE_PART  5
#define ITEM_FUEL         6
#define ITEM_KEYCARD      7
#define ITEM_TORCH        8
#define ITEM_ROPE         9
#define ITEM_RATION      10
#define ITEM_ARTIFACT    11
#define ITEM_SCANNER     12

/* ---- NPC IDs ---- */
#define NPC_NONE    0
#define NPC_ELDER   1

/* ======================================================================
   STRUCTURES
   ====================================================================== */

typedef struct {
    const char *name;
    const char *short_desc;
    const char *description;
    int exits[NUM_DIRS];      /* -1 = no exit */
    int items[MAX_ITEMS_PER_ROOM];
    int num_items;
    int npc;
    int visited;
} Room;

typedef struct {
    const char *name;
    const char *description;
    const char *examine_text;
    int portable;
} Item;

typedef struct {
    int current_room;
    int inventory[MAX_INV];
    int num_inv;
    int health;

    /* Quest flags */
    int engine_repaired;
    int fuel_loaded;
    int talked_to_elder;
    int elder_gave_keycard;
    int soldiers_defeated;
    int soldiers_appeared;
    int cave_dark_warned;
    int turns;

    int game_over;
    int game_won;
} Player;

/* ======================================================================
   GLOBAL STATE
   ====================================================================== */

Room   rooms[MAX_ROOMS];
Item   items[MAX_ITEMS];
Player player;

/* ======================================================================
   FORWARD DECLARATIONS
   ====================================================================== */

void print_room(int full);
void check_events(void);
void go_direction(int dir);

/* ======================================================================
   UTILITY
   ====================================================================== */

void str_lower(char *s) {
    for (; *s; s++) *s = (char)tolower((unsigned char)*s);
}

int starts_with(const char *str, const char *prefix) {
    return strncmp(str, prefix, strlen(prefix)) == 0;
}

void print_line(void) {
    printf("---------------------------------------------------------------\n");
}

void print_dashes(void) {
    printf("===============================================================\n");
}

/* ======================================================================
   ITEM / INVENTORY HELPERS
   ====================================================================== */

/* Returns index within room's item list, or -1 */
int find_item_in_room(int room_id, int item_id) {
    Room *r = &rooms[room_id];
    int i;
    for (i = 0; i < r->num_items; i++)
        if (r->items[i] == item_id) return i;
    return -1;
}

/* Returns index within player inventory, or -1 */
int find_in_inv(int item_id) {
    int i;
    for (i = 0; i < player.num_inv; i++)
        if (player.inventory[i] == item_id) return i;
    return -1;
}

void remove_from_room(int room_id, int idx) {
    Room *r = &rooms[room_id];
    int i;
    for (i = idx; i < r->num_items - 1; i++)
        r->items[i] = r->items[i + 1];
    r->num_items--;
}

void remove_from_inv(int idx) {
    int i;
    for (i = idx; i < player.num_inv - 1; i++)
        player.inventory[i] = player.inventory[i + 1];
    player.num_inv--;
}

void add_to_room(int room_id, int item_id) {
    Room *r = &rooms[room_id];
    if (r->num_items < MAX_ITEMS_PER_ROOM)
        r->items[r->num_items++] = item_id;
}

/* Find item by partial name in room and/or inventory.
   Returns item_id or -1. */
int find_item_by_name(const char *name, int check_room, int check_inv) {
    char lower_name[MAX_CMD];
    char item_lower[64];
    int i;

    strncpy(lower_name, name, MAX_CMD - 1);
    lower_name[MAX_CMD - 1] = '\0';
    str_lower(lower_name);

    if (check_room) {
        Room *r = &rooms[player.current_room];
        for (i = 0; i < r->num_items; i++) {
            strncpy(item_lower, items[r->items[i]].name, 63);
            item_lower[63] = '\0';
            str_lower(item_lower);
            if (strstr(item_lower, lower_name)) return r->items[i];
        }
    }
    if (check_inv) {
        for (i = 0; i < player.num_inv; i++) {
            strncpy(item_lower, items[player.inventory[i]].name, 63);
            item_lower[63] = '\0';
            str_lower(item_lower);
            if (strstr(item_lower, lower_name)) return player.inventory[i];
        }
    }
    return -1;
}

/* ======================================================================
   DARK CHECK
   ====================================================================== */

int is_dark(void) {
    if (player.current_room == ROOM_CAVE ||
        player.current_room == ROOM_CAVE_DEEP) {
        if (find_in_inv(ITEM_TORCH) < 0) return 1;
    }
    return 0;
}

/* ======================================================================
   INITIALISATION
   ====================================================================== */

void init_items(void) {
    items[ITEM_LASER].name         = "Laser Pistol";
    items[ITEM_LASER].description  = "A standard-issue plasma sidearm";
    items[ITEM_LASER].examine_text =
        "A sleek plasma-energy sidearm, standard issue for Galactic Fleet\n"
        "officers. It hums with stored energy and is ready to fire. You\n"
        "would feel a lot safer with this on your hip.";
    items[ITEM_LASER].portable = 1;

    items[ITEM_COMMS].name         = "Comms Unit";
    items[ITEM_COMMS].description  = "A personal subspace communicator";
    items[ITEM_COMMS].examine_text =
        "A handheld subspace communicator. Trying to hail the fleet yields\n"
        "only static this far out. But maybe it could still pick up a signal.";
    items[ITEM_COMMS].portable = 1;

    items[ITEM_POWER_CELL].name         = "Power Cell";
    items[ITEM_POWER_CELL].description  = "A high-capacity energy cell";
    items[ITEM_POWER_CELL].examine_text =
        "A chromium power cell capable of jump-starting a starship's primary\n"
        "systems. This is exactly what the engine room needs.";
    items[ITEM_POWER_CELL].portable = 1;

    items[ITEM_MEDKIT].name         = "Medkit";
    items[ITEM_MEDKIT].description  = "A field medical kit";
    items[ITEM_MEDKIT].examine_text =
        "Contains stims, wound sealant, and a neural stabilizer. Using it\n"
        "will restore your health to full.";
    items[ITEM_MEDKIT].portable = 1;

    items[ITEM_XTAL].name         = "Translation Crystal";
    items[ITEM_XTAL].description  = "A glowing language-matrix crystal";
    items[ITEM_XTAL].examine_text =
        "This crystal matrix, when held, allows comprehension of most known\n"
        "alien languages -- and lets them understand you in return. The native\n"
        "Kelonians would be able to speak with you if you carried this.";
    items[ITEM_XTAL].portable = 1;

    items[ITEM_ENGINE_PART].name         = "Engine Part";
    items[ITEM_ENGINE_PART].description  = "A quantum drive coupling";
    items[ITEM_ENGINE_PART].examine_text =
        "A quantum drive coupling -- the exact component your ship's FTL\n"
        "drive is missing. Combined with a power cell in the engine room,\n"
        "you could get the drive running again.";
    items[ITEM_ENGINE_PART].portable = 1;

    items[ITEM_FUEL].name         = "Fuel Canister";
    items[ITEM_FUEL].description  = "A sealed canister of hyperlite fuel";
    items[ITEM_FUEL].examine_text =
        "A pressurized canister of hyperlite fuel, enough to fill the ISS\n"
        "Horizon's launch tanks. The engine needs this to fly.";
    items[ITEM_FUEL].portable = 1;

    items[ITEM_KEYCARD].name         = "Keycard";
    items[ITEM_KEYCARD].description  = "A magnetic access card";
    items[ITEM_KEYCARD].examine_text =
        "An encoded magnetic keycard. The markings suggest it opens a secure\n"
        "facility. Your scanner picks up an energy signature to the north of\n"
        "the forest -- perhaps a hidden shuttle bay?";
    items[ITEM_KEYCARD].portable = 1;

    items[ITEM_TORCH].name         = "Plasma Torch";
    items[ITEM_TORCH].description  = "A compact plasma hand torch";
    items[ITEM_TORCH].examine_text =
        "A compact plasma torch that emits a bright, steady beam. Essential\n"
        "for exploring dark places -- like caves.";
    items[ITEM_TORCH].portable = 1;

    items[ITEM_ROPE].name         = "Carbon-Fibre Rope";
    items[ITEM_ROPE].description  = "A 30m coil of high-tensile rope";
    items[ITEM_ROPE].examine_text =
        "A 30-metre coil of high-tensile carbon-fibre rope. Useful for\n"
        "descending into deep shafts where climbing would be impossible.";
    items[ITEM_ROPE].portable = 1;

    items[ITEM_RATION].name         = "Food Ration";
    items[ITEM_RATION].description  = "A compressed nutrient ration pack";
    items[ITEM_RATION].examine_text =
        "Compressed nutrient bricks in a sealed pouch. Not exactly fine\n"
        "dining, but eating one restores 20 health points.";
    items[ITEM_RATION].portable = 1;

    items[ITEM_ARTIFACT].name         = "Ancient Artifact";
    items[ITEM_ARTIFACT].description  = "A strange glowing alien relic";
    items[ITEM_ARTIFACT].examine_text =
        "A dodecahedral object covered in luminescent runes, pulsing gently\n"
        "with inner light. It feels important. The Kelonian elder would\n"
        "probably value this greatly -- perhaps enough to trade for it.";
    items[ITEM_ARTIFACT].portable = 1;

    items[ITEM_SCANNER].name         = "Bio-Scanner";
    items[ITEM_SCANNER].description  = "A handheld biosignature scanner";
    items[ITEM_SCANNER].examine_text =
        "Detects life forms and energy signatures within 50 metres. Useful\n"
        "for finding hidden structures and tracking enemy movements.";
    items[ITEM_SCANNER].portable = 1;
}

void init_rooms(void) {
    int i, d;
    for (i = 0; i < MAX_ROOMS; i++) {
        for (d = 0; d < NUM_DIRS; d++)
            rooms[i].exits[d] = -1;
        rooms[i].num_items = 0;
        rooms[i].npc       = NPC_NONE;
        rooms[i].visited   = 0;
    }

    /* --- BRIDGE --- */
    rooms[ROOM_BRIDGE].name       = "Bridge";
    rooms[ROOM_BRIDGE].short_desc = "the bridge of the ISS Horizon";
    rooms[ROOM_BRIDGE].description =
        "You stand on the bridge of the ISS Horizon, your downed starship.\n"
        "Sparks shower from torn conduits. The main viewscreen flickers,\n"
        "showing a canopy of alien trees and a violet sky. Emergency lights\n"
        "bathe everything in a deep crimson glow.\n"
        "  A corridor leads SOUTH to the engine room.\n"
        "  A hatch leads EAST to the cargo hold.\n"
        "  A passage leads WEST to the airlock.";
    rooms[ROOM_BRIDGE].exits[SOUTH] = ROOM_ENGINE;
    rooms[ROOM_BRIDGE].exits[EAST]  = ROOM_CARGO;
    rooms[ROOM_BRIDGE].exits[WEST]  = ROOM_AIRLOCK;
    rooms[ROOM_BRIDGE].items[0] = ITEM_LASER;
    rooms[ROOM_BRIDGE].items[1] = ITEM_COMMS;
    rooms[ROOM_BRIDGE].num_items = 2;

    /* --- ENGINE ROOM --- */
    rooms[ROOM_ENGINE].name       = "Engine Room";
    rooms[ROOM_ENGINE].short_desc = "the engine room";
    rooms[ROOM_ENGINE].description =
        "A cramped compartment thick with the smell of burnt circuits and\n"
        "ozone. The quantum drive sits cold and dark -- the coupling is\n"
        "missing and the fuel lines are dry. Warning indicators blink red\n"
        "on every panel. Without repairs this ship goes nowhere.\n"
        "  The bridge is to the NORTH.";
    rooms[ROOM_ENGINE].exits[NORTH] = ROOM_BRIDGE;

    /* --- CARGO HOLD --- */
    rooms[ROOM_CARGO].name       = "Cargo Hold";
    rooms[ROOM_CARGO].short_desc = "the cargo hold";
    rooms[ROOM_CARGO].description =
        "Cargo crates have shifted and toppled in the crash, scattering\n"
        "supplies across the deck. Dusty light filters through a cracked\n"
        "hull panel. Rummaging through the debris might turn up useful gear.\n"
        "  The bridge is to the WEST.";
    rooms[ROOM_CARGO].exits[WEST] = ROOM_BRIDGE;
    rooms[ROOM_CARGO].items[0] = ITEM_POWER_CELL;
    rooms[ROOM_CARGO].items[1] = ITEM_MEDKIT;
    rooms[ROOM_CARGO].items[2] = ITEM_TORCH;
    rooms[ROOM_CARGO].items[3] = ITEM_ROPE;
    rooms[ROOM_CARGO].items[4] = ITEM_RATION;
    rooms[ROOM_CARGO].num_items = 5;

    /* --- AIRLOCK --- */
    rooms[ROOM_AIRLOCK].name       = "Airlock";
    rooms[ROOM_AIRLOCK].short_desc = "the airlock chamber";
    rooms[ROOM_AIRLOCK].description =
        "A cylindrical decompression chamber. The inner door leads EAST\n"
        "back to the bridge. The outer hatch opens SOUTH to the planet\n"
        "surface. The atmospheric sensors read Kelon-7's air as breathable.\n"
        "The crash has left the outer hatch unsealed.";
    rooms[ROOM_AIRLOCK].exits[EAST]  = ROOM_BRIDGE;
    rooms[ROOM_AIRLOCK].exits[SOUTH] = ROOM_CRASH_SITE;

    /* --- CRASH SITE --- */
    rooms[ROOM_CRASH_SITE].name       = "Crash Site";
    rooms[ROOM_CRASH_SITE].short_desc = "the crash site";
    rooms[ROOM_CRASH_SITE].description =
        "You stand outside the downed ISS Horizon. The ship has gouged a\n"
        "long furrow through the alien jungle. Twisted metal and debris\n"
        "surround you. The air smells of ozone and exotic flora.\n"
        "  The airlock hatch is to the NORTH.\n"
        "  A dense alien forest lies to the SOUTH.";
    rooms[ROOM_CRASH_SITE].exits[NORTH] = ROOM_AIRLOCK;
    rooms[ROOM_CRASH_SITE].exits[SOUTH] = ROOM_FOREST;
    rooms[ROOM_CRASH_SITE].items[0] = ITEM_SCANNER;
    rooms[ROOM_CRASH_SITE].num_items = 1;

    /* --- ALIEN FOREST --- */
    rooms[ROOM_FOREST].name       = "Alien Forest";
    rooms[ROOM_FOREST].short_desc = "a dense alien forest";
    rooms[ROOM_FOREST].description =
        "Towering violet-leafed trees soar overhead, their roots writhing\n"
        "above loamy soil. Bioluminescent spores drift lazily through shafts\n"
        "of purple light. A rocky outcrop rises to the UP/north -- something\n"
        "about it feels unusual. Your scanner might reveal more.\n"
        "  The crash site is to the NORTH.\n"
        "  Ancient ruins are visible to the EAST.\n"
        "  A narrow path leads WEST toward what looks like a settlement.\n"
        "  A rocky outcrop (UP) looks climbable -- and oddly artificial.";
    rooms[ROOM_FOREST].exits[NORTH] = ROOM_CRASH_SITE;
    rooms[ROOM_FOREST].exits[EAST]  = ROOM_RUINS;
    rooms[ROOM_FOREST].exits[WEST]  = ROOM_VILLAGE;
    rooms[ROOM_FOREST].exits[UP]    = ROOM_SHUTTLE; /* needs keycard */

    /* --- ANCIENT RUINS --- */
    rooms[ROOM_RUINS].name       = "Ancient Ruins";
    rooms[ROOM_RUINS].short_desc = "ancient Kelonian ruins";
    rooms[ROOM_RUINS].description =
        "Crumbling stone structures rise from the undergrowth, blanketed in\n"
        "glowing runes. This was once a Kelonian temple. At the centre stands\n"
        "a stone altar bearing offerings and strange devices. A dark cave\n"
        "entrance descends to the NORTH.\n"
        "  The forest path leads WEST.";
    rooms[ROOM_RUINS].exits[WEST]  = ROOM_FOREST;
    rooms[ROOM_RUINS].exits[NORTH] = ROOM_CAVE;
    rooms[ROOM_RUINS].items[0] = ITEM_ENGINE_PART;
    rooms[ROOM_RUINS].items[1] = ITEM_XTAL;
    rooms[ROOM_RUINS].items[2] = ITEM_ARTIFACT;
    rooms[ROOM_RUINS].num_items = 3;

    /* --- CAVE --- */
    rooms[ROOM_CAVE].name       = "Cave";
    rooms[ROOM_CAVE].short_desc = "a dark cave";
    rooms[ROOM_CAVE].description =
        "A rough-hewn tunnel descends into solid rock beneath the ruins.\n"
        "With a light source you can make out dripping stalactites and the\n"
        "glint of mineral veins in the walls. A narrow shaft drops further\n"
        "DOWN into darkness. Something is stored down here.\n"
        "  The ruins are to the SOUTH.";
    rooms[ROOM_CAVE].exits[SOUTH] = ROOM_RUINS;
    rooms[ROOM_CAVE].exits[DOWN]  = ROOM_CAVE_DEEP;
    rooms[ROOM_CAVE].items[0] = ITEM_FUEL;
    rooms[ROOM_CAVE].num_items = 1;

    /* --- DEEP CAVE --- */
    rooms[ROOM_CAVE_DEEP].name       = "Deep Cave";
    rooms[ROOM_CAVE_DEEP].short_desc = "the depths of the cave";
    rooms[ROOM_CAVE_DEEP].description =
        "The cave widens into a vast underground chamber. Crystalline\n"
        "formations tower around you, glowing with prismatic inner light.\n"
        "The walls are carved with murals depicting the Kelonian people\n"
        "among the stars -- they were once a spacefaring civilisation.\n"
        "  The shaft leads back UP.";
    rooms[ROOM_CAVE_DEEP].exits[UP] = ROOM_CAVE;

    /* --- KELONIAN VILLAGE --- */
    rooms[ROOM_VILLAGE].name       = "Kelonian Village";
    rooms[ROOM_VILLAGE].short_desc = "a Kelonian village";
    rooms[ROOM_VILLAGE].description =
        "A cluster of elegant structures grown from living wood, threaded\n"
        "with glowing vines. Kelonian aliens -- tall, blue-skinned beings\n"
        "with large amber eyes -- watch you with wary curiosity.\n"
        "An Elder sits cross-legged before a communal fire. Beside them,\n"
        "a Trader tends a small market stall.\n"
        "  The forest path leads EAST.";
    rooms[ROOM_VILLAGE].exits[EAST] = ROOM_FOREST;
    rooms[ROOM_VILLAGE].npc = NPC_ELDER;

    /* --- SHUTTLE BAY --- */
    rooms[ROOM_SHUTTLE].name       = "Hidden Shuttle Bay";
    rooms[ROOM_SHUTTLE].short_desc = "a concealed shuttle bay";
    rooms[ROOM_SHUTTLE].description =
        "A bay carved into the rock face and hidden beneath the jungle\n"
        "canopy. Inside sits a sleek Kelonian escape shuttle -- compact but\n"
        "fully functional, its fuel cells reading green. The bay door leads\n"
        "SOUTH back into the forest.\n"
        "  Type LAUNCH to take the shuttle and escape!";
    rooms[ROOM_SHUTTLE].exits[SOUTH] = ROOM_FOREST;
}

void init_player(void) {
    player.current_room    = ROOM_BRIDGE;
    player.num_inv         = 0;
    player.health          = 100;
    player.engine_repaired = 0;
    player.fuel_loaded     = 0;
    player.talked_to_elder = 0;
    player.elder_gave_keycard = 0;
    player.soldiers_defeated  = 0;
    player.soldiers_appeared  = 0;
    player.cave_dark_warned   = 0;
    player.turns   = 0;
    player.game_over = 0;
    player.game_won  = 0;
}

/* ======================================================================
   DISPLAY
   ====================================================================== */

void print_title(void) {
    print_dashes();
    printf("                 *** GALACTIC ODYSSEY ***\n");
    printf("            A Space Adventure in the Outer Rim\n");
    print_dashes();
    printf("\n");
    printf("You are Commander Alex Starfield. Your ship, the ISS Horizon,\n");
    printf("has crash-landed on Kelon-7 -- a remote jungle world on the\n");
    printf("outer rim. Your distress beacon activated on impact.\n\n");
    printf("Bad news: the Galactic Dominion intercepted it. Their forces\n");
    printf("will reach your position in roughly 25 turns.\n\n");
    printf("You must repair the Horizon and launch, or find another escape\n");
    printf("before they arrive. Good luck, Commander.\n\n");
    printf("Type HELP for a list of commands.\n");
    print_dashes();
    printf("\n");
}

void print_help(void) {
    print_line();
    printf("NAVIGATION:\n");
    printf("  go [direction]  / [n/s/e/w/u/d]  - Move in a direction\n");
    printf("  look            (l)               - Describe current location\n");
    printf("\nACTIONS:\n");
    printf("  take [item]     / get [item]      - Pick up an item\n");
    printf("  drop [item]                       - Drop an item\n");
    printf("  examine [item]  (x [item])        - Examine an item\n");
    printf("  use [item]                        - Use an item\n");
    printf("  use [item] on [target]            - Use item on something\n");
    printf("  attack                            - Attack an enemy\n");
    printf("  talk                              - Talk to a nearby character\n");
    printf("  trade                             - Trade with a merchant\n");
    printf("  launch                            - Launch ship or shuttle\n");
    printf("\nINFO:\n");
    printf("  inventory       (i)               - List what you are carrying\n");
    printf("  status                            - Health and quest progress\n");
    printf("  help            (?)               - Show this help\n");
    printf("  quit            (q)               - Quit the game\n");
    print_line();
}

void print_room(int full) {
    Room *r = &rooms[player.current_room];
    const char *dir_names[] = {"north", "south", "east", "west", "up", "down"};
    int d, i, found;

    print_line();
    printf("[ %s ]\n", r->name);

    if (is_dark()) {
        printf("\nIt is pitch black. You cannot see a thing.\n");
        if (!player.cave_dark_warned) {
            printf("(You need a light source to explore here safely.)\n");
            player.cave_dark_warned = 1;
        }
        print_line();
        return;
    }

    if (full || !r->visited) {
        printf("\n%s\n", r->description);
    } else {
        printf("(Familiar territory. Type LOOK for the full description.)\n");
    }

    /* Items on floor */
    if (r->num_items > 0) {
        printf("\nYou see: ");
        for (i = 0; i < r->num_items; i++) {
            printf("%s", items[r->items[i]].name);
            if (i < r->num_items - 1) printf(", ");
        }
        printf(".\n");
    }

    /* NPCs */
    if (player.current_room == ROOM_VILLAGE) {
        printf("\nThe Kelonian Elder is here. (Type TALK)\n");
        if (player.talked_to_elder && !player.elder_gave_keycard &&
            find_in_inv(ITEM_KEYCARD) < 0) {
            printf("The Kelonian Trader is nearby. (Type TRADE)\n");
        }
    }

    /* Soldiers */
    if (player.current_room == ROOM_CRASH_SITE &&
        player.soldiers_appeared && !player.soldiers_defeated) {
        printf("\n!! TWO GALACTIC DOMINION SOLDIERS are here, weapons drawn !!\n");
    }

    /* Exits */
    printf("\nExits: ");
    found = 0;
    for (d = 0; d < NUM_DIRS; d++) {
        if (r->exits[d] >= 0) {
            printf("%s ", dir_names[d]);
            found = 1;
        }
    }
    if (!found) printf("none");
    printf("\n");

    print_line();
    r->visited = 1;
}

void print_inventory(void) {
    int i;
    print_line();
    printf("INVENTORY:\n");
    if (player.num_inv == 0) {
        printf("  You are carrying nothing.\n");
    } else {
        for (i = 0; i < player.num_inv; i++) {
            printf("  - %-20s %s\n",
                   items[player.inventory[i]].name,
                   items[player.inventory[i]].description);
        }
    }
    printf("\nHealth: %d / 100\n", player.health);
    print_line();
}

void print_status(void) {
    print_line();
    printf("STATUS -- Commander Alex Starfield\n");
    printf("Health : %d / 100\n", player.health);
    printf("Turns  : %d  (Dominion arrives ~turn 25)\n", player.turns);
    printf("\nQUEST PROGRESS:\n");
    printf("  Engine coupling installed : %s\n",
           player.engine_repaired ? "YES" : "no");
    printf("  Fuel tanks loaded         : %s\n",
           player.fuel_loaded ? "YES" : "no");
    if (player.engine_repaired && player.fuel_loaded)
        printf("  >> The ISS Horizon is ready! Go to the BRIDGE and LAUNCH.\n");
    print_line();
}

/* ======================================================================
   MOVEMENT
   ====================================================================== */

void go_direction(int dir) {
    const char *dir_names[] = {"north","south","east","west","up","down"};
    int dest;

    /* Special: UP from FOREST = hidden shuttle bay (needs keycard) */
    if (player.current_room == ROOM_FOREST && dir == UP) {
        if (find_in_inv(ITEM_KEYCARD) >= 0) {
            printf("You press the keycard against a concealed panel set into the\n");
            printf("rock face. A section slides aside with a hiss of compressed\n");
            printf("air, revealing the hidden bay entrance.\n");
            player.current_room = ROOM_SHUTTLE;
            print_room(1);
        } else {
            printf("You scramble up the rocky outcrop. It looks and feels\n");
            printf("artificial -- smooth panels disguised as stone. Your scanner\n");
            printf("confirms a power signature and a concealed door, but you need\n");
            printf("an access card to open it.\n");
        }
        return;
    }

    /* Special: down from CAVE = requires torch + rope */
    if (player.current_room == ROOM_CAVE && dir == DOWN) {
        if (is_dark()) {
            printf("You can feel the shaft at your feet, but you cannot see to\n");
            printf("descend safely in the dark. You need a light source first.\n");
            return;
        }
        if (find_in_inv(ITEM_ROPE) >= 0) {
            printf("You anchor the rope to a stalactite and lower yourself into\n");
            printf("the shaft. The crystal-covered walls glow as you descend.\n");
            player.current_room = ROOM_CAVE_DEEP;
            print_room(1);
        } else {
            printf("The shaft drops away steeply. The walls are smooth and slick\n");
            printf("-- you cannot climb down without a rope.\n");
        }
        return;
    }

    /* Cave navigation without light */
    if (is_dark() && dir != SOUTH) {
        printf("You stumble blindly in the darkness and nearly pitch over the\n");
        printf("edge of something! You need a light source to move safely.\n");
        return;
    }

    dest = rooms[player.current_room].exits[dir];
    if (dest < 0) {
        printf("You cannot go %s from here.\n", dir_names[dir]);
        return;
    }

    /* Soldiers block southward exit at crash site */
    if (player.current_room == ROOM_CRASH_SITE &&
        player.soldiers_appeared && !player.soldiers_defeated && dir == SOUTH) {
        printf("The soldiers open fire as you try to run! You take a hit!\n");
        player.health -= 25;
        printf("Health: %d / 100\n", player.health);
        if (player.health <= 0) {
            printf("\nYou collapse under enemy fire. The mission is over.\n");
            player.game_over = 1;
            return;
        }
        printf("Wounded, you push past them into the forest.\n");
        player.current_room = dest;
        print_room(1);
        return;
    }

    player.current_room = dest;
    print_room(1);
}

/* ======================================================================
   TAKE / DROP
   ====================================================================== */

void take_item(const char *item_name) {
    int item_id, idx;

    if (is_dark()) {
        printf("It is too dark to find anything!\n");
        return;
    }
    if (player.num_inv >= MAX_INV) {
        printf("You cannot carry any more items.\n");
        return;
    }
    item_id = find_item_by_name(item_name, 1, 0);
    if (item_id < 0) {
        printf("You do not see any '%s' here.\n", item_name);
        return;
    }
    if (!items[item_id].portable) {
        printf("You cannot pick that up.\n");
        return;
    }
    idx = find_item_in_room(player.current_room, item_id);
    remove_from_room(player.current_room, idx);
    player.inventory[player.num_inv++] = item_id;
    printf("You pick up the %s.\n", items[item_id].name);
}

void drop_item(const char *item_name) {
    int item_id, idx;
    item_id = find_item_by_name(item_name, 0, 1);
    if (item_id < 0) {
        printf("You are not carrying any '%s'.\n", item_name);
        return;
    }
    idx = find_in_inv(item_id);
    remove_from_inv(idx);
    add_to_room(player.current_room, item_id);
    printf("You set down the %s.\n", items[item_id].name);
}

/* ======================================================================
   EXAMINE
   ====================================================================== */

void examine_item(const char *item_name) {
    char lower[MAX_CMD];
    int item_id;

    strncpy(lower, item_name, MAX_CMD - 1);
    lower[MAX_CMD - 1] = '\0';
    str_lower(lower);

    if (strlen(lower) == 0 || strcmp(lower, "room") == 0 ||
        strcmp(lower, "around") == 0) {
        print_room(1);
        return;
    }

    if (is_dark()) {
        printf("It is too dark to examine anything here.\n");
        return;
    }

    item_id = find_item_by_name(item_name, 1, 1);
    if (item_id < 0) {
        /* Examine scenery descriptions */
        if (strstr(lower, "altar") && player.current_room == ROOM_RUINS) {
            printf("The altar is carved from a single block of dark stone and\n");
            printf("covered in glowing runes. Objects have been placed on it as\n");
            printf("offerings -- including some that look distinctly useful.\n");
            return;
        }
        if (strstr(lower, "ship") || strstr(lower, "horizon")) {
            printf("The ISS Horizon will never fly again in one piece. But the\n");
            printf("engine might still be repaired for a last launch -- if you\n");
            printf("can find the right parts.\n");
            return;
        }
        if ((strstr(lower, "rune") || strstr(lower, "mural")) &&
            (player.current_room == ROOM_RUINS || player.current_room == ROOM_CAVE_DEEP)) {
            printf("The runes appear to be a pictographic language. They seem to\n");
            printf("tell the story of a great civilisation that once traversed\n");
            printf("the stars -- before retreating to this world long ago.\n");
            return;
        }
        printf("You do not see any '%s' to examine.\n", item_name);
        return;
    }
    printf("%s\n", items[item_id].examine_text);
}

/* ======================================================================
   USE ITEM
   ====================================================================== */

void use_item(const char *cmd) {
    char item_name[MAX_CMD];
    char target_name[MAX_CMD];
    char temp[MAX_CMD];
    char *on_pos;
    int item_id, idx;

    strncpy(temp, cmd, MAX_CMD - 1);
    temp[MAX_CMD - 1] = '\0';

    on_pos = strstr(temp, " on ");
    if (on_pos) {
        *on_pos = '\0';
        strncpy(item_name,   temp,      MAX_CMD - 1);
        strncpy(target_name, on_pos + 4, MAX_CMD - 1);
    } else {
        strncpy(item_name,  temp, MAX_CMD - 1);
        target_name[0] = '\0';
    }

    item_id = find_item_by_name(item_name, 0, 1);
    if (item_id < 0) {
        /* Maybe it's in the room */
        item_id = find_item_by_name(item_name, 1, 0);
        if (item_id < 0) {
            printf("You are not carrying any '%s'.\n", item_name);
            return;
        }
        printf("You will need to pick that up first.\n");
        return;
    }

    /* ---- MED KIT ---- */
    if (item_id == ITEM_MEDKIT) {
        if (player.health >= 100) {
            printf("You are already at full health. Save it for when you need it.\n");
            return;
        }
        player.health = 100;
        idx = find_in_inv(ITEM_MEDKIT);
        remove_from_inv(idx);
        printf("You inject the stims and seal your wounds. Health fully restored.\n");
        return;
    }

    /* ---- FOOD RATION ---- */
    if (item_id == ITEM_RATION) {
        if (player.health >= 100) {
            printf("You are not hungry enough to force that down right now.\n");
            return;
        }
        player.health = (player.health + 20 > 100) ? 100 : player.health + 20;
        idx = find_in_inv(ITEM_RATION);
        remove_from_inv(idx);
        printf("You chew the nutrient brick. It tastes terrible, but you feel\n");
        printf("a little stronger. Health: %d / 100\n", player.health);
        return;
    }

    /* ---- PLASMA TORCH ---- */
    if (item_id == ITEM_TORCH) {
        if (player.current_room == ROOM_CAVE ||
            player.current_room == ROOM_CAVE_DEEP) {
            printf("The torch blazes to life, illuminating the cave!\n");
            print_room(1);
        } else {
            printf("The torch fills the area with brilliant light, though it\n");
            printf("is already bright enough here.\n");
        }
        return;
    }

    /* ---- BIO-SCANNER ---- */
    if (item_id == ITEM_SCANNER) {
        if (player.current_room == ROOM_CRASH_SITE) {
            if (player.soldiers_appeared)
                printf("The scanner shows two human biosignatures at your location.\n");
            else
                printf("The scanner detects two human biosignatures approaching from\n"
                       "the east. ETA: approximately %d turns.\n",
                       25 - player.turns);
        } else if (player.current_room == ROOM_FOREST) {
            printf("The scanner picks up a concentrated power signature to the\n");
            printf("north -- consistent with a sealed, pressurised structure.\n");
            printf("There is definitely something hidden in that rock face.\n");
        } else if (player.current_room == ROOM_CAVE) {
            printf("The scanner detects a large open cavity below the shaft.\n");
            printf("Crystalline formations. No hostile life signs.\n");
        } else {
            printf("The scanner reads normal background biosignatures for Kelon-7.\n");
        }
        return;
    }

    /* ---- COMMUNICATOR ---- */
    if (item_id == ITEM_COMMS) {
        printf("You activate the communicator. Static hisses.\n");
        printf("\"...this is... ISS Horizon... mayday... does anyone copy?...\"\n");
        printf("A faint voice cuts through: \"...Commander...Dominion forces...\n");
        printf("...sector seven...intercept course...you have very little\n");
        printf("...time...good luck...\"\n");
        printf("Then nothing. You are very much on your own.\n");
        return;
    }

    /* ---- ENGINE PART ---- */
    if (item_id == ITEM_ENGINE_PART) {
        if (player.current_room != ROOM_ENGINE) {
            printf("There is nothing to install that on here.\n");
            return;
        }
        if (player.engine_repaired) {
            printf("The engine is already running.\n");
            return;
        }
        if (find_in_inv(ITEM_POWER_CELL) >= 0) {
            printf("You slot the quantum drive coupling into its housing and\n");
            printf("charge it with the power cell. The quantum drive spins up\n");
            printf("with a rising whine -- and ROARS to life!\n");
            printf(">> Engine repaired! You still need fuel to launch.\n");
            player.engine_repaired = 1;
            idx = find_in_inv(ITEM_ENGINE_PART); remove_from_inv(idx);
            idx = find_in_inv(ITEM_POWER_CELL);  remove_from_inv(idx);
        } else {
            printf("You install the coupling, but the drive fails to initialise\n");
            printf("without power. You need a power cell to go with it.\n");
        }
        return;
    }

    /* ---- POWER CELL ---- */
    if (item_id == ITEM_POWER_CELL) {
        if (player.current_room != ROOM_ENGINE) {
            printf("There is nothing useful to power here.\n");
            return;
        }
        if (player.engine_repaired) {
            printf("The engine is already running.\n");
            return;
        }
        if (find_in_inv(ITEM_ENGINE_PART) >= 0) {
            printf("You slot the quantum drive coupling into its housing and\n");
            printf("charge it with the power cell. The quantum drive ROARS!\n");
            printf(">> Engine repaired! You still need fuel to launch.\n");
            player.engine_repaired = 1;
            idx = find_in_inv(ITEM_ENGINE_PART); remove_from_inv(idx);
            idx = find_in_inv(ITEM_POWER_CELL);  remove_from_inv(idx);
        } else {
            printf("The cell alone cannot fix the engine. You also need the\n");
            printf("quantum drive coupling (the Engine Part).\n");
        }
        return;
    }

    /* ---- FUEL CANISTER ---- */
    if (item_id == ITEM_FUEL) {
        if (player.current_room != ROOM_ENGINE) {
            printf("The fuel lines are in the engine room. Go there first.\n");
            return;
        }
        if (!player.engine_repaired) {
            printf("The fuel lines are torn and useless right now. Repair the\n");
            printf("engine first, then load fuel.\n");
            return;
        }
        if (player.fuel_loaded) {
            printf("The fuel tanks are already full.\n");
            return;
        }
        printf("You connect the canister to the fuel manifold and transfer\n");
        printf("the hyperlite fuel. Tank gauges climb to maximum -- full!\n");
        printf(">> Fuel loaded! Go to the BRIDGE and type LAUNCH!\n");
        player.fuel_loaded = 1;
        idx = find_in_inv(ITEM_FUEL);
        remove_from_inv(idx);
        return;
    }

    /* ---- KEYCARD ---- */
    if (item_id == ITEM_KEYCARD) {
        if (player.current_room == ROOM_FOREST) {
            printf("You hold the keycard against the rock face. A concealed\n");
            printf("panel beeps and a section of stone slides aside revealing\n");
            printf("a stairway cut into the rock. You can now go UP.\n");
        } else {
            printf("The keycard does not appear useful here.\n");
        }
        return;
    }

    /* ---- ARTIFACT ---- */
    if (item_id == ITEM_ARTIFACT) {
        if (player.current_room == ROOM_VILLAGE) {
            printf("You hold the artifact toward the Elder. Their amber eyes\n");
            printf("widen. They rise slowly and accept it with both hands,\n");
            printf("pressing something cool into yours in return.\n");
            printf("\"Sacred relic of the Ancients,\" the Elder says (the crystal\n");
            printf("translates seamlessly). \"In exchange -- a gift. This keycard\n");
            printf("opens our emergency shelter to the north of the great trees.\n");
            printf("Go with honour, sky-traveller.\"\n");
            idx = find_in_inv(ITEM_ARTIFACT);
            remove_from_inv(idx);
            if (find_in_inv(ITEM_KEYCARD) < 0) {
                player.inventory[player.num_inv++] = ITEM_KEYCARD;
                printf("You receive the Keycard.\n");
            }
            player.elder_gave_keycard = 1;
        } else {
            printf("The artifact pulses gently. Beautiful and mysterious.\n");
            printf("The Kelonian Elder in the village might recognise it.\n");
        }
        return;
    }

    /* ---- TRANSLATION CRYSTAL ---- */
    if (item_id == ITEM_XTAL) {
        if (player.current_room == ROOM_VILLAGE) {
            printf("You hold the crystal. The clicking tonal speech of the\n");
            printf("Kelonians resolves instantly into clear language!\n");
            printf("Try talking to the Elder now.\n");
        } else {
            printf("The crystal pulses with soft light. You sense it would be\n");
            printf("invaluable among alien speakers.\n");
        }
        return;
    }

    /* ---- ROPE ---- */
    if (item_id == ITEM_ROPE) {
        if (player.current_room == ROOM_CAVE) {
            printf("You anchor the rope to a stalactite near the shaft. You\n");
            printf("can now descend (go DOWN) into the deep cave.\n");
        } else {
            printf("There is nothing useful to anchor the rope to here.\n");
        }
        return;
    }

    /* ---- LASER PISTOL ---- */
    if (item_id == ITEM_LASER) {
        printf("The pistol hums with charged plasma. Conserve your shots\n");
        printf("for when you really need them.\n");
        return;
    }

    printf("You try using the %s but nothing interesting happens.\n",
           items[item_id].name);
}

/* ======================================================================
   COMBAT
   ====================================================================== */

void attack_enemy(void) {
    if (player.current_room == ROOM_CRASH_SITE &&
        player.soldiers_appeared && !player.soldiers_defeated) {
        if (find_in_inv(ITEM_LASER) >= 0) {
            printf("You draw your laser pistol and take aim.\n");
            printf("ZAP! ZAP! Two clean shots -- both soldiers drop.\n");
            printf("The Dominion advance team will not be a problem anymore.\n");
            player.soldiers_defeated = 1;
        } else {
            printf("You charge the soldiers unarmed! A terrible idea.\n");
            printf("They overpower you and throw you to the ground.\n");
            player.health -= 35;
            printf("Health: %d / 100\n", player.health);
            if (player.health <= 0) {
                printf("\nYou are beaten unconscious in the wreckage of your ship.\n");
                printf("Game over.\n");
                player.game_over = 1;
            } else {
                printf("You stagger back. Find a weapon before trying that again!\n");
            }
        }
        return;
    }
    printf("There is nothing to attack here.\n");
}

/* ======================================================================
   TALK
   ====================================================================== */

void talk_npc(void) {
    if (player.current_room != ROOM_VILLAGE) {
        printf("There is no one here to talk to.\n");
        return;
    }

    printf("You approach the Kelonian Elder.\n");

    if (find_in_inv(ITEM_XTAL) < 0) {
        printf("The Elder speaks in a rapid sequence of clicks and rising tones.\n");
        printf("You cannot understand a word. You need a translation device.\n");
        return;
    }

    player.talked_to_elder = 1;

    if (player.elder_gave_keycard) {
        printf("The Elder nods serenely. \"The bay is yours, star-wanderer.\n");
        printf("May your journey carry you safely through the dark.\"\n");
        return;
    }

    if (find_in_inv(ITEM_ARTIFACT) >= 0) {
        printf("\"Sky-traveller,\" the Elder says through your crystal,\n");
        printf("\"you carry a relic of the Ancients. Return it to us and\n");
        printf("we will give you passage through our hidden escape bay.\"\n");
        printf("(USE the ARTIFACT while here to make the trade.)\n");
        return;
    }

    printf("\"Sky-traveller. Your vessel has carved a wound in our jungle.\n");
    printf("Yet we sense no malice in you. Know this: to the north of the\n");
    printf("great trees there is a hidden bay built by our ancestors. The\n");
    printf("keycard is held by Zeth, our trader.\"\n");
    printf("The Trader catches your eye and holds up a keycard with a grin.\n");
    printf("\"One food ration,\" the Trader says. \"Fair price.\"\n");
    printf("(Type TRADE to exchange a ration for the keycard.)\n");
}

/* ======================================================================
   TRADE
   ====================================================================== */

void trade(void) {
    if (player.current_room != ROOM_VILLAGE) {
        printf("There is no one here to trade with.\n");
        return;
    }
    if (!player.talked_to_elder) {
        printf("You should speak to the Elder first.\n");
        return;
    }
    if (player.elder_gave_keycard || find_in_inv(ITEM_KEYCARD) >= 0) {
        printf("You already have the keycard.\n");
        return;
    }
    if (find_in_inv(ITEM_RATION) >= 0) {
        int idx;
        printf("You hold out the ration pack. The Trader snatches it eagerly\n");
        printf("and drops the keycard into your palm. \"Good trade!\"\n");
        idx = find_in_inv(ITEM_RATION);
        remove_from_inv(idx);
        player.inventory[player.num_inv++] = ITEM_KEYCARD;
        printf("You receive the Keycard.\n");
    } else {
        printf("You have nothing to trade. The Trader wants a food ration.\n");
    }
}

/* ======================================================================
   LAUNCH
   ====================================================================== */

void launch_ship(void) {
    /* Shuttle bay escape */
    if (player.current_room == ROOM_SHUTTLE) {
        printf("\nYou seal the shuttle hatch and strap into the pilot seat.\n");
        printf("Systems check: all green. Fuel cells: full.\n");
        printf("Engaging launch sequence...\n\n");
        print_dashes();
        printf("  THRUSTERS IGNITE. The shuttle blasts from the hidden bay\n");
        printf("  and tears through the jungle canopy in seconds.\n\n");
        printf("  Kelon-7 shrinks to a violet marble below you.\n");
        printf("  Through the viewscreen you see the Dominion fleet closing --\n");
        printf("  but you are already calculating your hyperspace jump.\n\n");
        printf("  JUMP ENGAGED.\n\n");
        printf("  CONGRATULATIONS, COMMANDER STARFIELD!\n");
        printf("  You escaped Kelon-7 aboard the Kelonian shuttle!\n");
        printf("  Turns taken: %d\n", player.turns);
        print_dashes();
        player.game_won = 1;
        return;
    }

    /* ISS Horizon launch from bridge */
    if (player.current_room != ROOM_BRIDGE) {
        printf("You need to be on the Bridge to launch the ISS Horizon.\n");
        return;
    }
    if (!player.engine_repaired) {
        printf("The engine is not repaired. Install the Engine Part and Power\n");
        printf("Cell in the engine room first.\n");
        return;
    }
    if (!player.fuel_loaded) {
        printf("The fuel tanks are empty. Bring the Fuel Canister from the\n");
        printf("cave and use it in the engine room.\n");
        return;
    }

    printf("\nYou take your seat at the helm and run the pre-launch checklist.\n");
    printf("Engine: online. Fuel: nominal. Hull integrity: marginal but\n");
    printf("sufficient. Thrusters: ready.\n\n");
    printf("Here goes everything.\n\n");
    print_dashes();
    printf("  3 ... 2 ... 1 ... IGNITION!\n\n");
    printf("  The ISS Horizon SCREAMS. The jungle tears apart around the\n");
    printf("  ship as the thrusters burn white-hot. Warning lights flash --\n");
    printf("  Dominion ships are sweeping into sensor range.\n\n");
    printf("  Too late for them.\n\n");
    printf("  You punch the FTL drive. The stars smear into streaks of light.\n");
    printf("  Kelon-7 -- and the Galactic Dominion -- are gone.\n\n");
    printf("  CONGRATULATIONS, COMMANDER STARFIELD!\n");
    printf("  You repaired and launched the ISS Horizon!\n");
    printf("  Turns taken: %d\n", player.turns);
    print_dashes();
    player.game_won = 1;
}

/* ======================================================================
   EVENTS  (called once per turn)
   ====================================================================== */

void check_events(void) {
    /* Soldiers arrive after turn 15 */
    if (!player.soldiers_appeared && player.turns >= 15) {
        player.soldiers_appeared = 1;
        if (player.current_room == ROOM_CRASH_SITE) {
            printf("\n!! ALERT: A Dominion patrol has found the crash site!\n");
            printf("   Two soldiers emerge from the treeline, rifles raised!\n");
        } else {
            printf("\n>> SCANNER ALERT: Dominion biosignatures detected near\n");
            printf("   the crash site. They have found the Horizon!\n");
        }
    }

    /* Ominous final warning */
    if (player.turns == 22 && !player.game_won) {
        printf("\n>> SCANNER: Multiple Dominion warships entering low orbit.\n");
        printf("   Ground forces inbound. Hurry, Commander!\n");
    }

    if (player.health <= 0 && !player.game_over) {
        printf("\nYour wounds are too severe. You collapse on alien soil.\n");
        printf("The Dominion will find only your remains.\n");
        player.game_over = 1;
    }
}

/* ======================================================================
   COMMAND PROCESSING
   ====================================================================== */

void process_command(char *raw_cmd) {
    char cmd[MAX_CMD];
    char *start;
    char *end;

    strncpy(cmd, raw_cmd, MAX_CMD - 1);
    cmd[MAX_CMD - 1] = '\0';
    str_lower(cmd);

    /* Trim whitespace */
    start = cmd;
    while (*start == ' ') start++;
    end = start + strlen(start) - 1;
    while (end > start && (*end == ' ' || *end == '\n' || *end == '\r'))
        *end-- = '\0';

    if (strlen(start) == 0) return;

    player.turns++;

    /* --- MOVEMENT --- */
    if (!strcmp(start,"n")||!strcmp(start,"north")||!strcmp(start,"go north"))
        { go_direction(NORTH); }
    else if (!strcmp(start,"s")||!strcmp(start,"south")||!strcmp(start,"go south"))
        { go_direction(SOUTH); }
    else if (!strcmp(start,"e")||!strcmp(start,"east")||!strcmp(start,"go east"))
        { go_direction(EAST); }
    else if (!strcmp(start,"w")||!strcmp(start,"west")||!strcmp(start,"go west"))
        { go_direction(WEST); }
    else if (!strcmp(start,"u")||!strcmp(start,"up")||!strcmp(start,"go up"))
        { go_direction(UP); }
    else if (!strcmp(start,"d")||!strcmp(start,"down")||!strcmp(start,"go down"))
        { go_direction(DOWN); }

    /* --- LOOK --- */
    else if (!strcmp(start,"l")||!strcmp(start,"look")||
             starts_with(start,"look around"))
        { print_room(1); }

    /* --- INVENTORY --- */
    else if (!strcmp(start,"i")||!strcmp(start,"inv")||
             !strcmp(start,"inventory"))
        { print_inventory(); }

    /* --- STATUS --- */
    else if (!strcmp(start,"status")||!strcmp(start,"stat"))
        { print_status(); }

    /* --- HELP --- */
    else if (!strcmp(start,"help")||!strcmp(start,"?")||!strcmp(start,"h"))
        { print_help(); }

    /* --- QUIT --- */
    else if (!strcmp(start,"quit")||!strcmp(start,"q")||!strcmp(start,"exit")) {
        printf("Farewell, Commander. The stars await another day.\n");
        player.game_over = 1;
        return; /* skip check_events */
    }

    /* --- TAKE --- */
    else if (starts_with(start,"take ")||starts_with(start,"get ")||
             starts_with(start,"pick up ")) {
        const char *arg;
        if (starts_with(start,"take "))      arg = start + 5;
        else if (starts_with(start,"get "))  arg = start + 4;
        else                                 arg = start + 8;
        take_item(arg);
    }

    /* --- DROP --- */
    else if (starts_with(start,"drop "))
        { drop_item(start + 5); }

    /* --- EXAMINE --- */
    else if (starts_with(start,"examine ")||starts_with(start,"x ")||
             starts_with(start,"ex ")||starts_with(start,"look at ")||
             !strcmp(start,"examine")||!strcmp(start,"x")) {
        const char *arg;
        if (starts_with(start,"examine "))      arg = start + 8;
        else if (starts_with(start,"look at ")) arg = start + 8;
        else if (starts_with(start,"x "))       arg = start + 2;
        else if (starts_with(start,"ex "))      arg = start + 3;
        else                                    arg = "room";
        examine_item(arg);
    }

    /* --- USE --- */
    else if (starts_with(start,"use "))
        { use_item(start + 4); }

    /* --- ATTACK --- */
    else if (!strcmp(start,"attack")||!strcmp(start,"fight")||
             !strcmp(start,"shoot")||starts_with(start,"attack ")||
             starts_with(start,"shoot ")||starts_with(start,"fight "))
        { attack_enemy(); }

    /* --- TALK --- */
    else if (!strcmp(start,"talk")||starts_with(start,"talk to ")||
             !strcmp(start,"speak")||starts_with(start,"speak to ")||
             starts_with(start,"talk with "))
        { talk_npc(); }

    /* --- TRADE --- */
    else if (!strcmp(start,"trade")||starts_with(start,"trade ")||
             !strcmp(start,"buy")||starts_with(start,"buy "))
        { trade(); }

    /* --- LAUNCH --- */
    else if (!strcmp(start,"launch")||!strcmp(start,"launch ship")||
             !strcmp(start,"launch shuttle")||!strcmp(start,"fly")||
             !strcmp(start,"takeoff")||!strcmp(start,"take off"))
        { launch_ship(); }

    /* --- UNKNOWN --- */
    else {
        printf("You ponder the command '%s' for a moment, then give up.\n", start);
        printf("Type HELP for a list of commands.\n");
    }

    if (!player.game_over && !player.game_won)
        check_events();
}

/* ======================================================================
   MAIN
   ====================================================================== */

int main(void) {
    char input[MAX_CMD];

    init_items();
    init_rooms();
    init_player();

    print_title();
    print_room(1);

    while (!player.game_over && !player.game_won) {
        printf("\n> ");
        fflush(stdout);

        if (!fgets(input, MAX_CMD, stdin)) break;

        /* Strip newline */
        {
            size_t len = strlen(input);
            if (len > 0 && input[len - 1] == '\n') input[len - 1] = '\0';
        }

        process_command(input);
    }

    return 0;
}
