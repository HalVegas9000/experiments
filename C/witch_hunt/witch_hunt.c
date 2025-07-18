/*
** Program: witch_hunt.c
** Author: Hal Phillips with design input from Neil Ocampo
** Date: 10/28/2013
** Synopsis: A simple game to help an angry mob find a witch!
**
*/
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <termio.h>

#define REVEALED_DEFAULT 0

#define ROWS 25
#define COLS 45 
#define MOB_START 8
#define SCORE_START 0 
#define COMPLETED_START 0

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
   int witches_available;
   int witches_found;
   int witches_total;
}PLAYER;

struct termio set_tty;    /* assign structure to modify terminal*/
struct termio reset_tty;  /* assign structure to restore terminal */

/* function prototypes */
int print_title_page(PLAYER *p);
int populate_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p);
int print_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p);
int validate_action(ROWS_OF_COLS *f, PLAYER *p);
void reveal_forrest_by_torchlight(ROWS_OF_COLS *r, PLAYER *p);

int main(int argc, char *argv[])
{
   int forest[ROWS][COLS];
   int revealed[ROWS][COLS];
   char keystroke, c = '\0';
   int rtc = 0;

   ioctl(0, TCGETA, &set_tty); /* grab the current settings to set_tty */
   ioctl(0, TCGETA, &reset_tty);  /* save the original settings */
   set_tty.c_lflag &= ~ICANON; /* turn of carriage return requirement */
   set_tty.c_lflag &= ~ECHO;   /* turn of terminal keystroke echo */
   set_tty.c_cc[VMIN] = 1;     /* set minimum input buffer to 1 */

   ROWS_OF_COLS *p_forest = forest;
   ROWS_OF_COLS *p_revealed = revealed;
   PLAYER player;
   PLAYER *p_player = &player;

   player.mobsters = MOB_START;
   player.pitchforks = PITCHFORK_START;
   player.torches = TORCH_START;
   player.mushrooms = MUSHROOM_START;
   player.score = SCORE_START;
   player.witches_available = WITCH_START;
   player.witches_found = 0;
   player.witches_total = 0;

   populate_forest(p_forest, p_revealed, p_player);
   revealed[player.current_row][player.current_col] = 1;

   print_title_page(&player);
   system("clear");
   printf("%c[7mYou find yourself in the deep dark forest with %d witches...%c[0m\n",
      0x1B, player.witches_available, 0x1B);

   while(0 < player.mobsters)
   {
      player.score = (player.mobsters + player.pitchforks + player.mushrooms +
        (player.torches * 2) + (player.witches_total * 5));
     
      print_forest(p_forest, p_revealed, p_player);

      ioctl(0, TCSETAF, &set_tty);/* make the terminal changes */
      keystroke=getchar(); /* get a character from stdin */
      ioctl(0, TCSETAF, &reset_tty);  /* restore terminal settings */ 

      player.direction = keystroke;
      rtc = validate_action(p_forest, p_player);
      if (1 == rtc)
      {
         system("clear");
         printf("Invalid input, try again...\n");
         continue;
      }

      revealed[player.current_row][player.current_col] = 1;

      if (-1 == rtc && 0 < player.torches)
      {
         reveal_forrest_by_torchlight(p_revealed, p_player);
      }

      system("clear");
      switch (forest[player.current_row][player.current_col])
      {
         case RECRUIT :
            printf("%c[7mYay! You found a new mob member!%c[0m\n",0x1B,0x1B);
            player.mobsters++;
            break;
         case TORCH :
            printf("%c[7mYay! You found a torch!%c[0m\n",0x1B,0x1B);
            player.torches++;
            break;
         case PITCHFORK :
            printf("%c[7mYay! You found a pitchfork!%c[0m\n",0x1B,0x1B);
            player.pitchforks++;
            break;
         case MUSHROOM :
            printf("%c[7mYay! You found a magic mushroom!%c[0m\n",0x1B,0x1B);
            player.mushrooms++;
            break;
         case GOBLIN :
            if (0 < player.pitchforks)
            {
               printf("%c[7mYou found a goblin and stabbed it with a pitchfork!%c[0m\n",0x1B,0x1B);
               player.pitchforks--;
            }
            else
            {
               printf("%c[7mDang! You found a goblin and he ate a mob member!%c[0m\n",0x1B,0x1B);
               player.mobsters--;
            }
            break;
         case SWAMP :
            if (0 < player.mushrooms)
            {
               printf("%c[7mYou found the swamp and were saved by a magic mushroom!%c[0m\n",0x1B,0x1B);
               player.mushrooms--;
            }
            else
            {
               printf("%c[7mYou found the swamp and were bit by a snake! One of you died!%c[0m\n",0x1B,0x1B);
               player.mobsters--;
            }
            break;
         case TAINTED :
            printf("%c[7mYou found some tainted land! The witch turned one of you into a frog!%c[0m\n",0x1B,0x1B);
            player.mobsters--;
            break;
         case WITCH :
            printf("%c[7mHooray! You found a Witch!%c[0m\n",0x1B,0x1B);
            player.witches_found++;
            player.witches_total++;
            break;
         default :
            printf("You found an empty field, nothing to see here...\n");
      }

      if (player.witches_found == player.witches_available)
      {
         print_forest(p_forest, p_revealed, p_player);
         printf("%c[7mYou found the last witch! Press enter for MORE WITCHES!%c[0m\n",0x1B,0x1B);
         c=getchar(); /* get a character from stdin */
         player.witches_available++;
         player.witches_found = 0;
         player.mobsters = MOB_START;
         player.pitchforks = PITCHFORK_START;
         player.torches = TORCH_START;
         player.mushrooms = MUSHROOM_START;
         populate_forest(p_forest, p_revealed, p_player);
         revealed[player.current_row][player.current_col] = 1;
         system("clear");
         printf("%c[7mYou find yourself in the deep dark forest with %d witches...%c[0m\n",
            0x1B, player.witches_available, 0x1B);
      }
   }

   print_forest(p_forest, p_revealed, &player);

   {
      printf("%c[7mAlas, your mob was defeated and the village has been destroyed!%c[0m\n",0x1B,0x1B);
      printf("Your final score is %d.\n",player.score);
   }

   return(0);
}

int populate_forest(ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p)
{
   int i,j,k,row,col = 0;  
   int recruit_count = 0;
   int torch_count = 0;
   int pitchfork_count = 0;
   int mushroom_count = 0;
   int goblin_count = 0;
   int witch_row = 0;
   int witch_col = 0;
   time_t t;

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

   /* Add some random recruits */
   recruit_count = (rand() % RECRUIT_MOD) + RECRUIT_MIN;

   for (i = 0; i < recruit_count; i++)
   {
      f[(rand() % ROWS)][(rand() % COLS)] = RECRUIT;
   }

   /* Add some random goblins */
   goblin_count = (rand() % GOBLIN_MOD) + GOBLIN_MIN;

   for (i = 0; i < goblin_count; i++)
   {
      f[(rand() % ROWS)][(rand() % COLS)] = GOBLIN;
   }

   /* Add some random torches */
   torch_count = (rand() % TORCH_MOD) + TORCH_MIN;

   for (i = 0; i < torch_count; i++)
   {
      f[(rand() % ROWS)][(rand() % COLS)] = TORCH;
   }

   /* Add some random pitchforks */
   pitchfork_count = (rand() % PITCHFORK_MOD) + PITCHFORK_MIN;

   for (i = 0; i < pitchfork_count; i++)
   {
      f[(rand() % ROWS)][(rand() % COLS)] = PITCHFORK;
   }

   /* Add some random mushrooms */
   mushroom_count = (rand() % MUSHROOM_MOD) + MUSHROOM_MIN;

   for (i = 0; i < mushroom_count; i++)
   {
      f[(rand() % ROWS)][(rand() % COLS)] = MUSHROOM;
   }

   for (k = 0; k < p->witches_available; k++)
   {
   witch_row = rand() % ROWS;
   witch_col = rand() % COLS;

   /* Place witch within swamp and tainted land */

/*
   if(ROWS > witch_row+3 && 0 <= witch_col-2)
      f[witch_row+3][witch_col-2] = SWAMP;
   if(ROWS > witch_row+3 && 0 <= witch_col-1)
      f[witch_row+3][witch_col-1] = SWAMP;
   if(ROWS > witch_row+3 && 0 <= witch_col)
      f[witch_row+3][witch_col] = SWAMP;
   if(ROWS > witch_row+3 && 0 <= witch_col+1)
      f[witch_row+3][witch_col+1] = SWAMP;
   if(ROWS > witch_row+3 && 0 <= witch_col+2)
      f[witch_row+3][witch_col+2] = SWAMP;
*/


   /* top and bottom layers for a rounded look */
   for (col=-2; col<=2; col++)
   {
      if(ROWS > witch_row-3 && 0 <= witch_row-3 &&
         COLS > witch_col+col && 0 <= witch_col+col)
         f[witch_row-3][witch_col+col] = SWAMP;

      if(ROWS > witch_row+3 && 0 <= witch_row+3 &&
         COLS > witch_col+col && 0 <= witch_col+col)
         f[witch_row+3][witch_col+col] = SWAMP;
   }

   if(ROWS > witch_row+2 && 0 <= witch_col-3)
      f[witch_row+2][witch_col-3] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col-2)
      f[witch_row+2][witch_col-2] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col-1)
      f[witch_row+2][witch_col-1] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col)
      f[witch_row+2][witch_col] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col+1)
      f[witch_row+2][witch_col+1] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col+2)
      f[witch_row+2][witch_col+2] = SWAMP;
   if(ROWS > witch_row+2 && 0 <= witch_col+3)
      f[witch_row+2][witch_col+3] = SWAMP;

   if(ROWS > witch_row+1 && 0 <= witch_col-3)
      f[witch_row+1][witch_col-3] = SWAMP;
   if(ROWS > witch_row+1 && 0 <= witch_col-2)
      f[witch_row+1][witch_col-2] = SWAMP;
   if(ROWS > witch_row+1 && 0 <= witch_col-1)
      f[witch_row+1][witch_col-1] = TAINTED;
   if(ROWS > witch_row+1)
      f[witch_row+1][witch_col] = TAINTED;
   if(ROWS > witch_row+1 && COLS > witch_col+1)
      f[witch_row+1][witch_col+1] = TAINTED;
   if(ROWS > witch_row+1 && COLS > witch_col+2)
      f[witch_row+1][witch_col+2] = SWAMP;
   if(ROWS > witch_row+1 && COLS > witch_col+3)
      f[witch_row+1][witch_col+3] = SWAMP;

   if(0 <= witch_col-3)
      f[witch_row][witch_col-3] = SWAMP;
   if(0 <= witch_col-2)
      f[witch_row][witch_col-2] = SWAMP;
   if(0 <= witch_col-1)
      f[witch_row][witch_col-1] = TAINTED;
   f[witch_row][witch_col] = WITCH; /* The witch! */
   if(COLS > witch_col+1)
      f[witch_row][witch_col+1] = TAINTED;
   if(COLS > witch_col+2)
      f[witch_row][witch_col+2] = SWAMP;
   if(COLS > witch_col+3)
      f[witch_row][witch_col+3] = SWAMP;

   if(0 <= witch_row-1 && 0 <= witch_col-3)
      f[witch_row-1][witch_col-3] = SWAMP;
   if(0 <= witch_row-1 && 0 <= witch_col-2)
      f[witch_row-1][witch_col-2] = SWAMP;
   if(0 <= witch_row-1 && 0 <= witch_col-1)
      f[witch_row-1][witch_col-1] = TAINTED;
   if(0 <= witch_row-1)
      f[witch_row-1][witch_col] = TAINTED;
   if(0 <= witch_row-1 && COLS > witch_col+1)
      f[witch_row-1][witch_col+1] = TAINTED;
   if(0 <= witch_row-1 && COLS > witch_col+2)
      f[witch_row-1][witch_col+2] = SWAMP;
   if(0 <= witch_row-1 && COLS > witch_col+3)
      f[witch_row-1][witch_col+3] = SWAMP;

   if(0 <= witch_row-2 && 0 <= witch_col-3)
      f[witch_row-2][witch_col-3] = SWAMP;
   if(0 <= witch_row-2 && 0 <= witch_col-2)
      f[witch_row-2][witch_col-2] = SWAMP;
   if(0 <= witch_row-2 && 0 <= witch_col-1)
      f[witch_row-2][witch_col-1] = SWAMP;
   if(0 <= witch_row-2)
      f[witch_row-2][witch_col] = SWAMP;
   if(0 <= witch_row-2 && COLS > witch_col+1)
      f[witch_row-2][witch_col+1] = SWAMP;
   if(0 <= witch_row-2 && COLS > witch_col+2)
      f[witch_row-2][witch_col+2] = SWAMP;
   if(0 <= witch_row-2 && COLS > witch_col+3)
      f[witch_row-2][witch_col+3] = SWAMP;

   if(0 <= witch_row-3 && 0 <= witch_col-2)
      f[witch_row-3][witch_col-2] = SWAMP;
   if(0 <= witch_row-3 && 0 <= witch_col-1)
      f[witch_row-3][witch_col-1] = SWAMP;
   if(0 <= witch_row-3)
      f[witch_row-3][witch_col] = SWAMP;
   if(0 <= witch_row-3 && COLS > witch_col+1)
      f[witch_row-3][witch_col+1] = SWAMP;
   if(0 <= witch_row-3 && COLS > witch_col+2)
      f[witch_row-3][witch_col+2] = SWAMP;
   }

   p->current_row = rand() % ROWS;
   p->current_col = rand() % COLS;

   return(0);
}

int print_title_page(PLAYER *p)
{
   char c = '\0';
   system("clear");

   printf(" __      __  ______  ______  ____     __  __      \n");
   printf("/\\ \\  __/\\ \\/\\__  _\\/\\__  _\\/\\  _`\\  /\\ \\/\\ \\     \n");
   printf("\\ \\ \\/\\ \\ \\ \\/_/\\ \\/\\/_/\\ \\/\\ \\ \\/\\_\\\\ \\ \\_\\ \\    \n");
   printf(" \\ \\ \\ \\ \\ \\ \\ \\ \\ \\   \\ \\ \\ \\ \\ \\/_/_\\ \\  _  \\   \n");
   printf("  \\ \\ \\_/ \\_\\ \\ \\_\\ \\__ \\ \\ \\ \\ \\ \\_\\ \\\\ \\ \\ \\ \\  \n");
   printf("   \\ `\\___ ___/ /\\_____\\ \\ \\_\\ \\ \\____/ \\ \\_\\ \\_\\ \n");
   printf("    '\\/__//__/  \\/_____/  \\/_/  \\/___/   \\/_/\\/_/ \n");
   printf("            __  __  __  __  __  __  ______    \n");
   printf("           /\\ \\/\\ \\/\\ \\/\\ \\/\\ \\/\\ \\/\\__  _\\   \n");
   printf("           \\ \\ \\_\\ \\ \\ \\ \\ \\ \\ `\\\\ \\/_/\\ \\/   \n");
   printf("            \\ \\  _  \\ \\ \\ \\ \\ \\ , ` \\ \\ \\ \\   \n");
   printf("             \\ \\ \\ \\ \\ \\ \\_\\ \\ \\ \\`\\ \\ \\ \\ \\  \n");
   printf("              \\ \\_\\ \\_\\ \\_____\\ \\_\\ \\_\\ \\ \\_\\ \n");
   printf("               \\/_/\\/_/\\/_____/\\/_/\\/_/  \\/_/ \n");

   printf("\nWelcome to Witch Hunt by Hal Phillips!\n\n");
   printf("An evil witch is kidnapping villagers for her dark rituals!\n");
   printf("It's up to you to stop her!\n\n");

   printf("You have %d members in your angry mob.\n", p->mobsters);
   printf("You have %d pitchforks to defend yourself.\n", p->pitchforks);
   printf("You have %d torches to light your way.\n", p->torches);
   printf("You have %d magic mushrooms to cure poison.\n\n", p->mushrooms);

   printf("Beware of goblins(G). They will eat you if you have no pitchforks.\n");
   printf("The swamp(@) means witch is close, but beware of poisonous snakes.\n");
   printf("Tainted land(#) is the witch's home. Watch out! She will attack you!\n\n");

   printf("Look for new mob members(A) to join you...\n");
   printf("Look for additional pitchforks(Y) to fend off goblins...\n");
   printf("Look for additional torches(i) to help you see...\n");
   printf("Look for additional mushrooms(m) to cure poison...\n");
   printf("Please hit <enter> to begin");

   c=getchar(); /* get a character from stdin */

   return(0);
}

int print_forest (ROWS_OF_COLS *f, ROWS_OF_COLS *r, PLAYER *p)
{
   int i,j = 0;  
   
   printf("%c[0m",0x1B);
   for (i = 0; i < ROWS; i++)
   {
      for (j = 0; j < COLS; j++)
      {
         if(1 == r[i][j])
         {
            if (i == p->current_row && j == p->current_col)
            {
               printf("%c[7m",0x1B);
            }
                   
            switch (f[i][j])
            {
               case RECRUIT :
                  printf("A");
                  printf("%c[0m",0x1B);
                  break;
               case PITCHFORK :
                  printf("Y");
                  printf("%c[0m",0x1B);
                  break;
               case TORCH :
                  printf("i");
                  printf("%c[0m",0x1B);
                  break;
               case MUSHROOM :
                  printf("m");
                  printf("%c[0m",0x1B);
                  break;
               case GOBLIN :
                  printf("G");
                  printf("%c[0m",0x1B);
                  break;
               case SWAMP :
                  printf("@");
                  printf("%c[0m",0x1B);
                  break;
               case TAINTED :
                  printf("#");
                  printf("%c[0m",0x1B);
                  break;
               case WITCH :
                  printf("W");
                  printf("%c[0m",0x1B);
                  break;
               default :
                  printf(" ");
                  printf("%c[0m",0x1B);
            }
         }
         else
         {
            printf("+");
         }
      }
      printf("\n");
   }

   printf("Score: %d, Witches found: %d, Witches left: %d\n", 
      p->score, p->witches_found, p->witches_available - p->witches_found);
   printf("Resources: %d mobsters(A), %d torches(i), %d pitchforks(Y), %d mushrooms(m)\n", 
      p->mobsters, p->torches, p->pitchforks, p->mushrooms);
   printf("Actions: [w]up [s]down [a]left [d]right [t]light a torch\n");
 
   return(0);
}

int validate_action(ROWS_OF_COLS *f, PLAYER *p)
{
   int rtc = 1;

   p->next_row = p->current_row;
   p->next_col = p->current_col;
   p->prev_row = p->current_row;
   p->prev_col = p->current_col;

   switch(p->direction)
   {
      case 'w' :
         p->next_row--;
         if (ROWS > p->next_row)
         {
            p->current_row = p->next_row;
            rtc = 0;
         }
         break;
      case 's' :
         p->next_row++;
         if (0 <= p->next_row)
         {
            p->current_row = p->next_row;
            rtc = 0;
         }
         break;
      case 'a' :
         p->next_col--;
         if (0 <= p->next_col)
         {
            p->current_col = p->next_col;
            rtc = 0;
         }
         break;
      case 'd' :
         p->next_col++;
         if (COLS > p->next_col)
         {
            p->current_col = p->next_col;
            rtc = 0;
         }
         break;
      case 't' :
         rtc = -1;
         break;
      default :
         rtc = 1;
   }
   if (1 > rtc)
   {
      f[p->prev_row][p->prev_col] = FIELD;
   }
   return(rtc);
}

void reveal_forrest_by_torchlight(ROWS_OF_COLS *r, PLAYER *p)
{
   int row = 0;
   int col = 0;

   /* top and bottom layers for a rounded look */
   for (col=-1; col<=1; col++)
   {
      if(ROWS > p->current_row-2 && 0 <= p->current_row-2 &&
         COLS > p->current_col+col && 0 <= p->current_col+col)
         r[p->current_row-2][p->current_col+col] = 1;

      if(ROWS > p->current_row+2 && 0 <= p->current_row+2 &&
         COLS > p->current_col+col && 0 <= p->current_col+col)
         r[p->current_row+2][p->current_col+col] = 1;
   }

   /* middle layers */
   for (row=-1; row<=1; row++)
   {
      for (col=-2; col<=2; col++)
      {
         if(ROWS > p->current_row+row && 0 <= p->current_row+row &&
            COLS > p->current_col+col && 0 <= p->current_col+col)
            r[p->current_row+row][p->current_col+col] = 1;
      }
   }


   p->torches--;

   return;
}
