/*
** Program: witch_hunt_enhanced.c
** Original by: Hal Phillips with design input from Neil Ocampo (10/28/2013)
** Enhanced: 2026
** Synopsis: Enhanced version of the classic witch hunt game.
**           Same premise and mechanics as the original, but with:
**             - ANSI colors for the map and status bar
**             - Randomized flavor text so events don't get repetitive
**             - Difficulty scaling: more goblins each round
**             - Proximity hints when revealed tiles show swamp/tainted nearby
**             - High score tracking across rounds
**             - Bugfixes: bounds checks in validate_action, torch no longer
**               consumes the item at the player's current cell
*/
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <termio.h>

/* ---------- Sound effects ----------
** Uses the terminal BEL character (\a).  Make sure your terminal has the
** bell enabled (most do by default).  Each pattern is a short sequence of
** beeps with small delays so they feel distinct from one another.
*/
#define SND_ITEM     1   /* single positive beep -- found something good   */
#define SND_ATTACK   2   /* two sharp beeps        -- goblin encounter      */
#define SND_HURT     3   /* two slow beeps         -- lose a mob member     */
#define SND_WITCH    4   /* three quick beeps      -- witch captured!       */
#define SND_GAMEOVER 5   /* three slow beeps       -- mob wiped out         */

static void play_sound(int snd)
{
   switch (snd)
   {
      case SND_ITEM:
         printf("\a"); fflush(stdout);
         break;
      case SND_ATTACK:
         printf("\a"); fflush(stdout); usleep(80000);
         printf("\a"); fflush(stdout);
         break;
      case SND_HURT:
         printf("\a"); fflush(stdout); usleep(250000);
         printf("\a"); fflush(stdout);
         break;
      case SND_WITCH:
         printf("\a"); fflush(stdout); usleep(100000);
         printf("\a"); fflush(stdout); usleep(100000);
         printf("\a"); fflush(stdout);
         break;
      case SND_GAMEOVER:
         printf("\a"); fflush(stdout); usleep(400000);
         printf("\a"); fflush(stdout); usleep(400000);
         printf("\a"); fflush(stdout);
         break;
   }
}

/* ---------- ANSI color codes ---------- */
#define C_RESET    "\x1B[0m"
#define C_BOLD     "\x1B[1m"
#define C_DIM      "\x1B[2m"
#define C_REV      "\x1B[7m"
#define C_GREEN    "\x1B[32m"
#define C_BRED     "\x1B[1;31m"
#define C_BGREEN   "\x1B[1;32m"
#define C_BYELLOW  "\x1B[1;33m"
#define C_BBLUE    "\x1B[1;34m"
#define C_BMAGENTA "\x1B[1;35m"
#define C_BCYAN    "\x1B[1;36m"
#define C_BWHITE   "\x1B[1;37m"
#define C_MAGENTA  "\x1B[35m"

/* ---------- Game constants (unchanged from original) ---------- */
#define REVEALED_DEFAULT 0

#define ROWS 25
#define COLS 45
#define MOB_START 8
#define SCORE_START 0

#define FIELD 0

#define TORCH 1
#define TORCH_START 10
#define TORCH_MOD 10
#define TORCH_MIN 55

#define PITCHFORK 2
#define PITCHFORK_START 8
#define PITCHFORK_MOD 10
#define PITCHFORK_MIN 30

#define MUSHROOM 3
#define MUSHROOM_START 2
#define MUSHROOM_MOD 10
#define MUSHROOM_MIN 15

#define RECRUIT 5
#define RECRUIT_MOD 10
#define RECRUIT_MIN 30

#define GOBLIN 6
#define GOBLIN_MOD 10
#define GOBLIN_MIN 185

#define SWAMP 7
#define TAINTED 8

#define WITCH 9
#define WITCH_START 1

/* Difficulty scaling per round (0-indexed round_idx = round - 1) */
#define DIFF_GOBLIN_PER_ROUND  8    /* extra goblins added each round */
#define DIFF_RECRUIT_PER_ROUND 3    /* fewer recruits each round      */
#define DIFF_MAX_GOBLINS       350  /* cap so game stays survivable   */
#define DIFF_MIN_RECRUITS      10   /* floor for recruits             */

typedef int ROWS_OF_COLS[COLS];

typedef struct
{
   int prev_row;
   int prev_col;
   int current_row;
   int current_col;
   int next_row;
   int next_col;
   char direction;
   int mobsters;
   int torches;
   int pitchforks;
   int mushrooms;
   int score;
   int high_score;
   int witches_available;
   int witches_found;
   int witches_total;
   int round;
} PLAYER;

struct termio set_tty;
struct termio reset_tty;

/* ---------- Flavor text arrays ---------- */
static const char *torch_msgs[] = {
   "You find a torch! Its warm glow pushes back the darkness.",
   "A torch! Someone dropped it fleeing a goblin. Their loss!",
   "You grab a torch wedged in a dead tree. The mob cheers!",
   "A flickering torch lies in the mud. You snatch it eagerly.",
   "You find a torch. The forest feels a little less menacing.",
};

static const char *pitchfork_msgs[] = {
   "You find a pitchfork! Now the goblins won't be so smug.",
   "A pitchfork! Perfect for goblin-poking.",
   "Someone left their pitchfork behind. You add it to the arsenal.",
   "You discover a pitchfork half-buried in the earth. Score!",
   "A sturdy pitchfork! The mob raises it triumphantly.",
};

static const char *mushroom_msgs[] = {
   "You find a magic mushroom! Keep it safe -- the swamp is treacherous.",
   "A glowing mushroom! The village herbalist would be proud.",
   "You spot a magic mushroom. Useful against swamp snakes!",
   "You find a peculiar mushroom. It smells faintly of magic.",
   "A magic mushroom! One of the mob pockets it carefully.",
};

static const char *torch_use_msgs[] = {
   "You hold a torch aloft. The shadows scatter around you!",
   "The torch blazes to life. The mob peers around eagerly.",
   "A torch is lit! The forest glows orange for a welcome moment.",
   "You ignite a torch. Eyes glint in the darkness just beyond its reach.",
   "The torch flares up. For a brief moment, the forest has no secrets.",
};

static const char *torch_empty_msgs[] = {
   "You reach for a torch -- but your pouch is empty!",
   "No torches left! The darkness presses in around you.",
   "Your last torch is long gone. The mob grumbles in the dark.",
   "Nothing to light. You'll have to find more torches.",
   "Empty handed. Someone should have grabbed more torches.",
};

static const char *recruit_msgs[] = {
   "A brave villager joins your mob! The more the merrier.",
   "A volunteer emerges from the shadows. Your mob grows!",
   "You find a lost farmhand eager to join the cause.",
   "A new recruit grabs a torch and falls in line.",
   "A burly blacksmith joins up. The mob is emboldened!",
};

static const char *goblin_kill_msgs[] = {
   "A goblin leaps out! You jab it with a pitchfork. It squeals and flees!",
   "Goblin attack! One well-placed pitchfork later, problem solved.",
   "The goblin snarls -- then sees the pitchfork. You stab it. It yelps!",
   "You stab the goblin before it can bite anyone. Crisis averted!",
   "A sneaky goblin! Good thing you had a pitchfork. It runs off wailing.",
};

static const char *goblin_eat_msgs[] = {
   "A goblin ambushes you! With no pitchforks, it drags off a mob member!",
   "Goblin attack! Without a weapon, one of you is gone. RIP.",
   "The goblin pounces! It carries off poor Gerald before anyone can stop it.",
   "No pitchforks! The goblin feasts. The mob mourns.",
   "A goblin snatches poor Agnes! The rest of the mob retreats a step.",
};

static const char *swamp_save_msgs[] = {
   "You wade into the swamp. A snake lunges -- but the magic mushroom cures it!",
   "Swamp snake! You chew a mushroom and feel fine instantly. Close call.",
   "Poisonous bite! Good thing you had a mushroom. You feel better already.",
   "The swamp snake strikes! Your mushroom cures the bite. The mob sighs.",
   "Snake bite from the murk! Your mushroom saves the day. Phew!",
};

static const char *swamp_hurt_msgs[] = {
   "You enter the swamp and a snake bites one of you! You had no mushrooms.",
   "A serpent strikes from the murk! No mushrooms to save him. He is lost.",
   "The swamp claims a victim! Out of mushrooms. One of you didn't make it.",
   "Swamp snakes! Without mushrooms, poor Harold is gone. The mob grieves.",
   "A snake bite in the mire! No mushrooms left. One of you collapses.",
};

static const char *tainted_msgs[] = {
   "Tainted land! The witch's dark magic turns one mob member into a frog!",
   "Cursed ground! One of the mob sprouts webbed feet and hops away. Poof!",
   "The witch's aura hangs heavy here. One villager is turned into a newt!",
   "Dark earth seeps into poor Thomas's boots. He... ribbits. And hops off.",
   "Dark magic! One mob member vanishes in a puff of green smoke. Frog.",
};

static const char *witch_found_msgs[] = {
   "HOORAY! You found the witch! The mob erupts in righteous fury!",
   "There she is! The witch cackles and is captured! The village is safer!",
   "The witch is cornered! She shrieks as the mob closes in. CAUGHT!",
   "You found her! She tries a spell but your torches break her concentration!",
   "The witch is found! The mob drags her off to face justice!",
};

static const char *field_msgs[] = {
   "You find an empty field, nothing to see here...",
   "Just trees and shadows. Nothing interesting.",
   "An empty clearing. The mob shuffles onward.",
   "Nothing here but moonlight and mud.",
   "Empty. The mob presses forward into the dark.",
};

#define NMSG(arr) (int)(sizeof(arr)/sizeof(arr[0]))

/* ---------- Function prototypes ---------- */
int print_title_page(PLAYER *p);
int populate_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p);
int print_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p);
int validate_action(ROWS_OF_COLS *f, PLAYER *p);
void reveal_forrest_by_torchlight(ROWS_OF_COLS *r, PLAYER *p);
void print_danger_hint(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p);

static const char *pick_msg(const char **msgs, int count)
{
   return msgs[rand() % count];
}

/* ============================== main ============================== */
int main(int argc, char *argv[])
{
   int forest[ROWS][COLS];
   int revealed[ROWS][COLS];
   char keystroke, c = '\0';
   int rtc = 0;

   ioctl(0, TCGETA, &set_tty);
   ioctl(0, TCGETA, &reset_tty);
   set_tty.c_lflag &= ~ICANON;
   set_tty.c_lflag &= ~ECHO;
   set_tty.c_cc[VMIN] = 1;

   ROWS_OF_COLS *p_forest = forest;
   ROWS_OF_COLS *p_revealed = revealed;
   PLAYER player;
   PLAYER *p_player = &player;

   player.mobsters = MOB_START;
   player.pitchforks = PITCHFORK_START;
   player.torches = TORCH_START;
   player.mushrooms = MUSHROOM_START;
   player.score = SCORE_START;
   player.high_score = 0;
   player.witches_available = WITCH_START;
   player.witches_found = 0;
   player.witches_total = 0;
   player.round = 1;

   populate_forest(p_forest, p_revealed, p_player);
   revealed[player.current_row][player.current_col] = 1;

   print_title_page(&player);
   system("clear");
   printf(C_BMAGENTA C_REV " You find yourself in the deep dark forest with %d witch%s... " C_RESET "\n",
      player.witches_available, player.witches_available == 1 ? "" : "es");

   while (0 < player.mobsters)
   {
      player.score = (player.mobsters + player.pitchforks + player.mushrooms +
         (player.torches * 2) + (player.witches_total * 5));
      if (player.score > player.high_score)
         player.high_score = player.score;

      print_forest(p_forest, p_revealed, p_player);

      ioctl(0, TCSETAF, &set_tty);
      keystroke = getchar();
      ioctl(0, TCSETAF, &reset_tty);

      if ('q' == keystroke || 'Q' == keystroke)
         break;

      player.direction = keystroke;
      rtc = validate_action(p_forest, p_player);
      if (1 == rtc)
      {
         system("clear");
         printf(C_BYELLOW "Invalid input, try again...\n" C_RESET);
         continue;
      }

      revealed[player.current_row][player.current_col] = 1;

      system("clear");

      if (-1 == rtc)
      {
         /* Torch action: always print a message so the map doesn't shift */
         if (0 < player.torches)
         {
            reveal_forrest_by_torchlight(p_revealed, p_player);
            printf(C_BYELLOW C_REV " %s " C_RESET "\n",
               pick_msg(torch_use_msgs, NMSG(torch_use_msgs)));
            play_sound(SND_ITEM);
         }
         else
         {
            printf(C_BYELLOW C_REV " %s " C_RESET "\n",
               pick_msg(torch_empty_msgs, NMSG(torch_empty_msgs)));
         }
      }
      else if (0 == rtc)
      {
         int show_hint = 1;  /* suppressed for tiles that already imply danger */

         switch (forest[player.current_row][player.current_col])
         {
            case RECRUIT:
               printf(C_BBLUE C_REV " %s " C_RESET "\n",
                  pick_msg(recruit_msgs, NMSG(recruit_msgs)));
               player.mobsters++;
               play_sound(SND_ITEM);
               break;
            case TORCH:
               printf(C_BYELLOW C_REV " %s " C_RESET "\n",
                  pick_msg(torch_msgs, NMSG(torch_msgs)));
               player.torches++;
               play_sound(SND_ITEM);
               break;
            case PITCHFORK:
               printf(C_BCYAN C_REV " %s " C_RESET "\n",
                  pick_msg(pitchfork_msgs, NMSG(pitchfork_msgs)));
               player.pitchforks++;
               play_sound(SND_ITEM);
               break;
            case MUSHROOM:
               printf(C_BGREEN C_REV " %s " C_RESET "\n",
                  pick_msg(mushroom_msgs, NMSG(mushroom_msgs)));
               player.mushrooms++;
               play_sound(SND_ITEM);
               break;
            case GOBLIN:
               if (0 < player.pitchforks)
               {
                  printf(C_BRED C_REV " %s " C_RESET "\n",
                     pick_msg(goblin_kill_msgs, NMSG(goblin_kill_msgs)));
                  player.pitchforks--;
                  play_sound(SND_ATTACK);
               }
               else
               {
                  printf(C_BRED C_REV " %s " C_RESET "\n",
                     pick_msg(goblin_eat_msgs, NMSG(goblin_eat_msgs)));
                  player.mobsters--;
                  play_sound(SND_HURT);
               }
               break;
            case SWAMP:
               if (0 < player.mushrooms)
               {
                  printf(C_BGREEN C_REV " %s " C_RESET "\n",
                     pick_msg(swamp_save_msgs, NMSG(swamp_save_msgs)));
                  player.mushrooms--;
                  play_sound(SND_ITEM);
               }
               else
               {
                  printf(C_GREEN C_REV " %s " C_RESET "\n",
                     pick_msg(swamp_hurt_msgs, NMSG(swamp_hurt_msgs)));
                  player.mobsters--;
                  play_sound(SND_HURT);
               }
               show_hint = 0;  /* swamp message already tells the player they're close */
               break;
            case TAINTED:
               printf(C_MAGENTA C_REV " %s " C_RESET "\n",
                  pick_msg(tainted_msgs, NMSG(tainted_msgs)));
               player.mobsters--;
               play_sound(SND_HURT);
               show_hint = 0;  /* tainted message already tells the player they're in the lair */
               break;
            case WITCH:
               printf(C_BMAGENTA C_REV " %s " C_RESET "\n",
                  pick_msg(witch_found_msgs, NMSG(witch_found_msgs)));
               player.witches_found++;
               player.witches_total++;
               play_sound(SND_WITCH);
               show_hint = 0;
               break;
            default:
               printf("%s\n", pick_msg(field_msgs, NMSG(field_msgs)));
         }

         /* Show a proximity hint only when the tile event doesn't already
            tell the player they are near the witch's lair */
         if (show_hint)
            print_danger_hint(p_forest, p_revealed, p_player);
      }

      if (player.witches_found == player.witches_available)
      {
         print_forest(p_forest, p_revealed, p_player);
         printf(C_BMAGENTA C_REV " You found the last witch! Press enter for MORE WITCHES! " C_RESET "\n");
         c = getchar();
         player.witches_available++;
         player.round++;
         player.witches_found = 0;
         player.mobsters = MOB_START;
         player.pitchforks = PITCHFORK_START;
         player.torches = TORCH_START;
         player.mushrooms = MUSHROOM_START;
         populate_forest(p_forest, p_revealed, p_player);
         revealed[player.current_row][player.current_col] = 1;
         system("clear");
         printf(C_BMAGENTA C_REV " Round %d! You find yourself in the forest with %d witches... " C_RESET "\n",
            player.round, player.witches_available);
         printf(C_BRED "The forest grows darker. More goblins lurk in the shadows...\n" C_RESET);
      }
   }

   print_forest(p_forest, p_revealed, &player);
   if (0 < player.mobsters)
      printf(C_BYELLOW C_REV " The mob disperses into the night. Better luck next time! " C_RESET "\n");
   else
   {
      play_sound(SND_GAMEOVER);
      printf(C_BRED C_REV " Alas, your mob was defeated and the village has been destroyed! " C_RESET "\n");
   }
   printf("Final score: " C_BWHITE "%d" C_RESET "   Best this session: " C_BYELLOW "%d" C_RESET "\n",
      player.score, player.high_score);

   return 0;
}

/* ============================== populate_forest ============================== */
int populate_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p)
{
   int i, j, k, col = 0;
   int witch_row = 0;
   int witch_col = 0;
   time_t t;

   /* Difficulty scaling */
   int round_idx  = p->round - 1;
   int goblin_min = GOBLIN_MIN + (round_idx * DIFF_GOBLIN_PER_ROUND);
   int recruit_min = RECRUIT_MIN - (round_idx * DIFF_RECRUIT_PER_ROUND);
   if (goblin_min  > DIFF_MAX_GOBLINS)  goblin_min  = DIFF_MAX_GOBLINS;
   if (recruit_min < DIFF_MIN_RECRUITS) recruit_min = DIFF_MIN_RECRUITS;

   /* Initialize forest */
   for (i = 0; i < ROWS; i++)
   {
      for (j = 0; j < COLS; j++)
      {
         f[i][j] = 0;
         r[i][j] = REVEALED_DEFAULT;
      }
   }

   srand((unsigned) time(&t));

   /* Add recruits (fewer each round) */
   int recruit_count = (rand() % RECRUIT_MOD) + recruit_min;
   for (i = 0; i < recruit_count; i++)
      f[(rand() % ROWS)][(rand() % COLS)] = RECRUIT;

   /* Add goblins (more each round) */
   int goblin_count = (rand() % GOBLIN_MOD) + goblin_min;
   for (i = 0; i < goblin_count; i++)
      f[(rand() % ROWS)][(rand() % COLS)] = GOBLIN;

   /* Add torches */
   int torch_count = (rand() % TORCH_MOD) + TORCH_MIN;
   for (i = 0; i < torch_count; i++)
      f[(rand() % ROWS)][(rand() % COLS)] = TORCH;

   /* Add pitchforks */
   int pitchfork_count = (rand() % PITCHFORK_MOD) + PITCHFORK_MIN;
   for (i = 0; i < pitchfork_count; i++)
      f[(rand() % ROWS)][(rand() % COLS)] = PITCHFORK;

   /* Add mushrooms */
   int mushroom_count = (rand() % MUSHROOM_MOD) + MUSHROOM_MIN;
   for (i = 0; i < mushroom_count; i++)
      f[(rand() % ROWS)][(rand() % COLS)] = MUSHROOM;

   /* Place witches, each surrounded by a ring of swamp then tainted land */
   for (k = 0; k < p->witches_available; k++)
   {
      witch_row = rand() % ROWS;
      witch_col = rand() % COLS;

      /* Outer oval: rows ±3, cols -2..+2 (all swamp) */
      for (col = -2; col <= 2; col++)
      {
         if (witch_row-3 >= 0 && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row-3][witch_col+col] = SWAMP;
         if (witch_row+3 < ROWS && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row+3][witch_col+col] = SWAMP;
      }

      /* Rows ±2, full width (all swamp) */
      for (col = -3; col <= 3; col++)
      {
         if (witch_row+2 < ROWS && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row+2][witch_col+col] = SWAMP;
         if (witch_row-2 >= 0 && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row-2][witch_col+col] = SWAMP;
      }

      /* Rows ±1: outer cols = swamp, inner 3 = tainted */
      for (col = -3; col <= 3; col++)
      {
         int tile = (col >= -1 && col <= 1) ? TAINTED : SWAMP;
         if (witch_row+1 < ROWS && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row+1][witch_col+col] = tile;
         if (witch_row-1 >= 0 && witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row-1][witch_col+col] = tile;
      }

      /* Witch row: outer = swamp, adjacent = tainted, center = witch */
      for (col = -3; col <= 3; col++)
      {
         if (col == 0) continue;
         int tile = (col == -1 || col == 1) ? TAINTED : SWAMP;
         if (witch_col+col >= 0 && witch_col+col < COLS)
            f[witch_row][witch_col+col] = tile;
      }
      f[witch_row][witch_col] = WITCH;
   }

   p->current_row = rand() % ROWS;
   p->current_col = rand() % COLS;

   return 0;
}

/* ============================== print_title_page ============================== */
int print_title_page(PLAYER *p)
{
   char c = '\0';
   system("clear");

   printf(C_BYELLOW);
   printf(" __      __  ______  ______  ____     __  __      \n");
   printf("/\\ \\  __/\\ \\/\\__  _\\/\\__  _\\/\\  _`\\  /\\ \\/\\ \\     \n");
   printf("\\ \\ \\/\\ \\ \\ \\/_/\\ \\/\\/_/\\ \\/\\ \\ \\/\\_\\\\ \\ \\_\\ \\    \n");
   printf(" \\ \\ \\ \\ \\ \\ \\ \\ \\ \\   \\ \\ \\ \\ \\ \\/_/_\\ \\  _  \\   \n");
   printf("  \\ \\ \\_/ \\_\\ \\ \\_\\ \\__ \\ \\ \\ \\ \\ \\_\\ \\\\ \\ \\ \\ \\  \n");
   printf("   \\ `\\___ ___/ /\\_____\\ \\ \\_\\ \\ \\____/ \\ \\_\\ \\_\\ \n");
   printf("    '\\/__//__/  \\/_____/  \\/_/  \\/___/   \\/_/\\/_/ \n");
   printf(C_BMAGENTA);
   printf("            __  __  __  __  __  __  ______    \n");
   printf("           /\\ \\/\\ \\/\\ \\/\\ \\/\\ \\/\\ \\/\\__  _\\   \n");
   printf("           \\ \\ \\_\\ \\ \\ \\ \\ \\ \\ `\\\\ \\/_/\\ \\/   \n");
   printf("            \\ \\  _  \\ \\ \\ \\ \\ \\ , ` \\ \\ \\ \\   \n");
   printf("             \\ \\ \\ \\ \\ \\ \\_\\ \\ \\ \\`\\ \\ \\ \\ \\  \n");
   printf("              \\ \\_\\ \\_\\ \\_____\\ \\_\\ \\_\\ \\ \\_\\ \n");
   printf("               \\/_/\\/_/\\/_____/\\/_/\\/_/  \\/_/ \n");
   printf(C_RESET);

   printf("\nWelcome to " C_BWHITE "Witch Hunt" C_RESET " by Hal Phillips!\n\n");
   printf("An evil witch is kidnapping villagers for her dark rituals!\n");
   printf("It's up to you to stop her!\n\n");

   printf("You have " C_BBLUE "%d" C_RESET " members in your angry mob.\n", p->mobsters);
   printf("You have " C_BCYAN "%d" C_RESET " pitchforks to defend yourself.\n", p->pitchforks);
   printf("You have " C_BYELLOW "%d" C_RESET " torches to light your way.\n", p->torches);
   printf("You have " C_BGREEN "%d" C_RESET " magic mushrooms to cure poison.\n\n", p->mushrooms);

   printf("Beware of " C_BRED "goblins(G)" C_RESET ". They eat a mob member if you have no pitchforks.\n");
   printf("The " C_GREEN "swamp(@)" C_RESET " means the witch is close, but beware of poisonous snakes.\n");
   printf(C_MAGENTA "Tainted land(#)" C_RESET " is the witch's home turf. She will attack you!\n\n");

   printf("Look for new " C_BBLUE "mob members(A)" C_RESET " to join you...\n");
   printf("Look for additional " C_BCYAN "pitchforks(Y)" C_RESET " to fend off goblins...\n");
   printf("Look for additional " C_BYELLOW "torches(i)" C_RESET " to help you see...\n");
   printf("Look for additional " C_BGREEN "mushrooms(m)" C_RESET " to cure swamp poison...\n\n");

   printf(C_BRED "Each round, the witch summons more goblins. Stay sharp!\n" C_RESET "\n");
   printf("Please hit <enter> to begin");

   c = getchar();
   return 0;
}

/* ============================== print_forest ============================== */
int print_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p)
{
   int i, j = 0;

   printf(C_RESET);
   for (i = 0; i < ROWS; i++)
   {
      for (j = 0; j < COLS; j++)
      {
         if (1 == r[i][j])
         {
            int is_player = (i == p->current_row && j == p->current_col);
            const char *pre  = is_player ? C_REV : "";
            const char *post = C_RESET;

            switch (f[i][j])
            {
               case RECRUIT:
                  printf("%s" C_BBLUE "A%s", pre, post); break;
               case PITCHFORK:
                  printf("%s" C_BCYAN "Y%s", pre, post); break;
               case TORCH:
                  printf("%s" C_BYELLOW "i%s", pre, post); break;
               case MUSHROOM:
                  printf("%s" C_BGREEN "m%s", pre, post); break;
               case GOBLIN:
                  printf("%s" C_BRED "G%s", pre, post); break;
               case SWAMP:
                  printf("%s" C_GREEN "@%s", pre, post); break;
               case TAINTED:
                  printf("%s" C_MAGENTA "#%s", pre, post); break;
               case WITCH:
                  printf("%s" C_BMAGENTA "W%s", pre, post); break;
               default:
                  /* Empty field: show mob marker if player is here */
                  printf("%s%s%s", pre, is_player ? C_BWHITE "M" : " ", post);
                  break;
            }
         }
         else
         {
            printf(C_DIM "+" C_RESET);
         }
      }
      printf("\n");
   }

   printf(C_BWHITE "Score: %d" C_RESET
          "  " C_BYELLOW "Best: %d" C_RESET
          "  " C_BMAGENTA "Round: %d" C_RESET
          "  Witches found: " C_BGREEN "%d" C_RESET
          "  Witches left: " C_BRED "%d\n" C_RESET,
      p->score, p->high_score, p->round,
      p->witches_found, p->witches_available - p->witches_found);

   printf("Mob: " C_BBLUE "%d(A)" C_RESET
          "  Torches: " C_BYELLOW "%d(i)" C_RESET
          "  Pitchforks: " C_BCYAN "%d(Y)" C_RESET
          "  Mushrooms: " C_BGREEN "%d(m)\n" C_RESET,
      p->mobsters, p->torches, p->pitchforks, p->mushrooms);

   printf("Move: [w]up [s]down [a]left [d]right  [t]light a torch  [q]quit\n");

   return 0;
}

/* ============================== validate_action ============================== */
int validate_action(ROWS_OF_COLS *f, PLAYER *p)
{
   int rtc = 1;

   p->next_row = p->current_row;
   p->next_col = p->current_col;
   p->prev_row = p->current_row;
   p->prev_col = p->current_col;

   switch (p->direction)
   {
      case 'w':
         p->next_row--;
         if (p->next_row >= 0)           /* fixed: was ROWS > next_row */
         {
            p->current_row = p->next_row;
            rtc = 0;
         }
         break;
      case 's':
         p->next_row++;
         if (p->next_row < ROWS)         /* fixed: was 0 <= next_row   */
         {
            p->current_row = p->next_row;
            rtc = 0;
         }
         break;
      case 'a':
         p->next_col--;
         if (p->next_col >= 0)
         {
            p->current_col = p->next_col;
            rtc = 0;
         }
         break;
      case 'd':
         p->next_col++;
         if (p->next_col < COLS)
         {
            p->current_col = p->next_col;
            rtc = 0;
         }
         break;
      case 't':
         rtc = -1;
         break;
      default:
         rtc = 1;
   }

   /* Only consume the previous cell when the player actually moved.
      The original cleared the cell for torch (rtc==-1) too, which was
      a bug that could destroy items at the player's feet. */
   if (0 == rtc)
   {
      f[p->prev_row][p->prev_col] = FIELD;
   }

   return rtc;
}

/* ============================== reveal_forrest_by_torchlight ============================== */
void reveal_forrest_by_torchlight(ROWS_OF_COLS *r, PLAYER *p)
{
   int row, col;

   /* top and bottom layers for a rounded look */
   for (col = -1; col <= 1; col++)
   {
      if (p->current_row-2 >= 0 && p->current_row-2 < ROWS &&
          p->current_col+col >= 0 && p->current_col+col < COLS)
         r[p->current_row-2][p->current_col+col] = 1;

      if (p->current_row+2 >= 0 && p->current_row+2 < ROWS &&
          p->current_col+col >= 0 && p->current_col+col < COLS)
         r[p->current_row+2][p->current_col+col] = 1;
   }

   /* middle layers */
   for (row = -1; row <= 1; row++)
   {
      for (col = -2; col <= 2; col++)
      {
         if (p->current_row+row >= 0 && p->current_row+row < ROWS &&
             p->current_col+col >= 0 && p->current_col+col < COLS)
            r[p->current_row+row][p->current_col+col] = 1;
      }
   }

   p->torches--;
}

/* ============================== print_danger_hint ============================== */
/*
** Scans revealed tiles within 3 steps of the player.
** If tainted land is visible, the witch is very close.
** If swamp is visible, the witch's lair may be nearby.
** Only revealed tiles count -- rewards strategic torch usage.
*/
void print_danger_hint(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p)
{
   int dr, dc;
   int swamp_near   = 0;
   int tainted_near = 0;

   for (dr = -3; dr <= 3; dr++)
   {
      for (dc = -3; dc <= 3; dc++)
      {
         int nr = p->current_row + dr;
         int nc = p->current_col + dc;
         /* Skip the player's own tile and out-of-bounds */
         if (dr == 0 && dc == 0) continue;
         if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) continue;
         if (r[nr][nc] != 1) continue;

         if (f[nr][nc] == TAINTED) tainted_near++;
         else if (f[nr][nc] == SWAMP) swamp_near++;
      }
   }

   if (tainted_near > 0)
      printf(C_BMAGENTA "The air crackles with dark magic. The witch is VERY close!\n" C_RESET);
   else if (swamp_near > 0)
      printf(C_GREEN "You smell something foul on the wind. A witch may be nearby.\n" C_RESET);
}
