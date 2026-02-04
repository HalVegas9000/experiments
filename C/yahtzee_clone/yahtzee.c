#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <ctype.h>

#define NUM_DICE 5
#define NUM_ROUNDS 13
#define NUM_CATEGORIES 13

typedef enum {
    ONES = 0,
    TWOS,
    THREES,
    FOURS,
    FIVES,
    SIXES,
    THREE_OF_A_KIND,
    FOUR_OF_A_KIND,
    FULL_HOUSE,
    SMALL_STRAIGHT,
    LARGE_STRAIGHT,
    YAHTZEE,
    CHANCE
} Category;

typedef struct {
    int values[NUM_DICE];
    int held[NUM_DICE];
} DiceState;

typedef struct {
    int scores[NUM_CATEGORIES];
    int used[NUM_CATEGORIES];
} ScoreSheet;

typedef struct {
    char *name;
    int category;
} CategoryName;

CategoryName categoryNames[] = {
    {"Ones", ONES},
    {"Twos", TWOS},
    {"Threes", THREES},
    {"Fours", FOURS},
    {"Fives", FIVES},
    {"Sixes", SIXES},
    {"Three of a Kind", THREE_OF_A_KIND},
    {"Four of a Kind", FOUR_OF_A_KIND},
    {"Full House", FULL_HOUSE},
    {"Small Straight", SMALL_STRAIGHT},
    {"Large Straight", LARGE_STRAIGHT},
    {"Yahtzee", YAHTZEE},
    {"Chance", CHANCE}
};

// ASCII Dice display with borders
void displayDie(int value) {
    const char *dice[] = {
        // 0 (empty)
        "┌─────┐",
        "│     │",
        "│     │",
        "│     │",
        "└─────┘",
        // 1
        "┌─────┐",
        "│     │",
        "│  ●  │",
        "│     │",
        "└─────┘",
        // 2
        "┌─────┐",
        "│●    │",
        "│     │",
        "│    ●│",
        "└─────┘",
        // 3
        "┌─────┐",
        "│●    │",
        "│  ●  │",
        "│    ●│",
        "└─────┘",
        // 4
        "┌─────┐",
        "│●   ●│",
        "│     │",
        "│●   ●│",
        "└─────┘",
        // 5
        "┌─────┐",
        "│●   ●│",
        "│  ●  │",
        "│●   ●│",
        "└─────┘",
        // 6
        "┌─────┐",
        "│●   ●│",
        "│●   ●│",
        "│●   ●│",
        "└─────┘"
    };

    int index = value * 5;
    printf("     ");
    for (int i = 0; i < 5; i++) {
        printf("%s", dice[index + i]);
        if (i < 4) printf("\n     ");
    }
}

void displayDiceRow(int *values, int row) {
    for (int i = 0; i < NUM_DICE; i++) {
        int index = values[i] * 5 + row;
        const char *dice[] = {
            // 0 (empty)
            "┌─────┐",
            "│     │",
            "│     │",
            "│     │",
            "└─────┘",
            // 1
            "┌─────┐",
            "│     │",
            "│  ●  │",
            "│     │",
            "└─────┘",
            // 2
            "┌─────┐",
            "│●    │",
            "│     │",
            "│    ●│",
            "└─────┘",
            // 3
            "┌─────┐",
            "│●    │",
            "│  ●  │",
            "│    ●│",
            "└─────┘",
            // 4
            "┌─────┐",
            "│●   ●│",
            "│     │",
            "│●   ●│",
            "└─────┘",
            // 5
            "┌─────┐",
            "│●   ●│",
            "│  ●  │",
            "│●   ●│",
            "└─────┘",
            // 6
            "┌─────┐",
            "│●   ●│",
            "│●   ●│",
            "│●   ●│",
            "└─────┘"
        };
        
        printf("%s", dice[index]);
        if (i < NUM_DICE - 1) printf(" ");
    }
    printf("\n");
}

void displayDice(DiceState *dice) {
    printf("\n     Dice:\n");
    for (int row = 0; row < 5; row++) {
        printf("     ");
        displayDiceRow(dice->values, row);
    }
    printf("\n     Dice:  ");
    for (int i = 0; i < NUM_DICE; i++) {
        printf(" %d     ", i + 1);
    }
    printf("\n");
}

void displayHeldDice(DiceState *dice) {
    printf("     Held:  ");
    for (int i = 0; i < NUM_DICE; i++) {
        if (dice->held[i]) {
            printf("[H]   ");
        } else {
            printf(" -    ");
        }
    }
    printf("\n\n");
}

void rollDice(DiceState *dice) {
    for (int i = 0; i < NUM_DICE; i++) {
        if (!dice->held[i]) {
            dice->values[i] = (rand() % 6) + 1;
        }
    }
}

int countValue(int *dice, int value) {
    int count = 0;
    for (int i = 0; i < NUM_DICE; i++) {
        if (dice[i] == value) count++;
    }
    return count;
}

int countOfAKind(int *dice, int kind) {
    for (int value = 6; value >= 1; value--) {
        if (countValue(dice, value) >= kind) {
            return value;
        }
    }
    return 0;
}

int calculateScore(DiceState *dice, Category category) {
    int total = 0;

    switch (category) {
        case ONES:
        case TWOS:
        case THREES:
        case FOURS:
        case FIVES:
        case SIXES: {
            int target = category + 1;
            for (int i = 0; i < NUM_DICE; i++) {
                if (dice->values[i] == target) total += target;
            }
            break;
        }
        case THREE_OF_A_KIND: {
            if (countOfAKind(dice->values, 3)) {
                for (int i = 0; i < NUM_DICE; i++) {
                    total += dice->values[i];
                }
            }
            break;
        }
        case FOUR_OF_A_KIND: {
            if (countOfAKind(dice->values, 4)) {
                for (int i = 0; i < NUM_DICE; i++) {
                    total += dice->values[i];
                }
            }
            break;
        }
        case FULL_HOUSE: {
            int counts[7] = {0};
            for (int i = 0; i < NUM_DICE; i++) {
                counts[dice->values[i]]++;
            }
            int has3 = 0, has2 = 0;
            for (int i = 1; i <= 6; i++) {
                if (counts[i] == 3) has3 = 1;
                if (counts[i] == 2) has2 = 1;
            }
            if (has3 && has2) total = 25;
            break;
        }
        case SMALL_STRAIGHT: {
            int sorted[NUM_DICE];
            for (int i = 0; i < NUM_DICE; i++) sorted[i] = dice->values[i];
            for (int i = 0; i < NUM_DICE; i++) {
                for (int j = i + 1; j < NUM_DICE; j++) {
                    if (sorted[i] > sorted[j]) {
                        int temp = sorted[i];
                        sorted[i] = sorted[j];
                        sorted[j] = temp;
                    }
                }
            }
            if ((sorted[0] == 1 && sorted[1] == 2 && sorted[2] == 3 && sorted[3] == 4) ||
                (sorted[1] == 2 && sorted[2] == 3 && sorted[3] == 4 && sorted[4] == 5) ||
                (sorted[2] == 3 && sorted[3] == 4 && sorted[4] == 5 && sorted[4] == 6)) {
                total = 30;
            }
            break;
        }
        case LARGE_STRAIGHT: {
            int sorted[NUM_DICE];
            for (int i = 0; i < NUM_DICE; i++) sorted[i] = dice->values[i];
            for (int i = 0; i < NUM_DICE; i++) {
                for (int j = i + 1; j < NUM_DICE; j++) {
                    if (sorted[i] > sorted[j]) {
                        int temp = sorted[i];
                        sorted[i] = sorted[j];
                        sorted[j] = temp;
                    }
                }
            }
            if ((sorted[0] == 1 && sorted[1] == 2 && sorted[2] == 3 && 
                 sorted[3] == 4 && sorted[4] == 5) ||
                (sorted[0] == 2 && sorted[1] == 3 && sorted[2] == 4 && 
                 sorted[3] == 5 && sorted[4] == 6)) {
                total = 40;
            }
            break;
        }
        case YAHTZEE: {
            if (countValue(dice->values, dice->values[0]) == 5) {
                total = 50;
            }
            break;
        }
        case CHANCE: {
            for (int i = 0; i < NUM_DICE; i++) {
                total += dice->values[i];
            }
            break;
        }
    }

    return total;
}

void displayScoreSheet(ScoreSheet *sheet) {
    printf("\n╔════════════════════════╦═════════╗\n");
    printf("║ Category               ║ Score   ║\n");
    printf("╠════════════════════════╬═════════╣\n");

    for (int i = 0; i < NUM_CATEGORIES; i++) {
        printf("║ %d.  %-18s ║", i + 1, categoryNames[i].name);
        if (sheet->used[i]) {
            printf(" %3d     ║\n", sheet->scores[i]);
        } else {
            printf("   -    ║\n");
        }
    }

    int total = 0;
    for (int i = 0; i < NUM_CATEGORIES; i++) {
        if (sheet->used[i]) total += sheet->scores[i];
    }

    printf("╠════════════════════════╬═════════╣\n");
    printf("║ TOTAL                  ║ %3d    ║\n", total);
    printf("╚════════════════════════╩═════════╝\n\n");
}

void clearScreen() {
    printf("\033[2J\033[H");
}

void playGame() {
    clearScreen();
    printf("╔══════════════════════════╗\n");
    printf("║     YAHTZEE GAME         ║\n");
    printf("╚══════════════════════════╝\n\n");

    DiceState dice;
    ScoreSheet sheet;
    memset(&sheet, 0, sizeof(sheet));

    for (int round = 0; round < NUM_ROUNDS; round++) {
        clearScreen();
        printf("╔══════════════════════════╗\n");
        printf("║     YAHTZEE GAME         ║\n");
        printf("║   Round %2d of %2d        ║\n", round + 1, NUM_ROUNDS);
        printf("╚══════════════════════════╝\n");

        memset(&dice.held, 0, sizeof(dice.held));

        // Three rolls per round
        for (int roll = 0; roll < 3; roll++) {
            rollDice(&dice);
            clearScreen();
            printf("╔══════════════════════════╗\n");
            printf("║     YAHTZEE GAME         ║\n");
            printf("║   Round %2d of %2d        ║\n", round + 1, NUM_ROUNDS);
            printf("╚══════════════════════════╝\n");

            displayDice(&dice);
            displayHeldDice(&dice);
            displayScoreSheet(&sheet);

            if (roll < 2) {
                printf("Roll %d/3 complete.\n", roll + 1);
                printf("Hold dice? Enter die numbers to hold (1-5) or press Enter to skip: ");
                char input[20];
                fgets(input, sizeof(input), stdin);

                // Reset held dice
                memset(&dice.held, 0, sizeof(dice.held));

                // Parse input
                for (int i = 0; input[i]; i++) {
                    if (isdigit(input[i])) {
                        int dieNum = input[i] - '0';
                        if (dieNum >= 1 && dieNum <= 5) {
                            dice.held[dieNum - 1] = 1;
                        }
                    }
                }
            }
        }

        // Score selection
        clearScreen();
        printf("╔══════════════════════════╗\n");
        printf("║     YAHTZEE GAME         ║\n");
        printf("║   Round %2d of %2d        ║\n", round + 1, NUM_ROUNDS);
        printf("╚══════════════════════════╝\n");

        displayDice(&dice);
        displayHeldDice(&dice);
        displayScoreSheet(&sheet);

        printf("Available categories:\n");
        for (int i = 0; i < NUM_CATEGORIES; i++) {
            if (!sheet.used[i]) {
                int score = calculateScore(&dice, i);
                printf("%2d. %-18s - Score: %d\n", i + 1, categoryNames[i].name, score);
            }
        }

        printf("\nSelect category (1-%d): ", NUM_CATEGORIES);
        int choice;
        scanf("%d", &choice);
        getchar();

        choice--;
        if (choice >= 0 && choice < NUM_CATEGORIES && !sheet.used[choice]) {
            sheet.scores[choice] = calculateScore(&dice, choice);
            sheet.used[choice] = 1;
        }
    }

    clearScreen();
    printf("╔══════════════════════════╗\n");
    printf("║    GAME OVER!            ║\n");
    printf("╚══════════════════════════╝\n");
    displayScoreSheet(&sheet);

    int total = 0;
    for (int i = 0; i < NUM_CATEGORIES; i++) {
        if (sheet.used[i]) total += sheet.scores[i];
    }
    printf("FINAL SCORE: %d\n\n", total);
}

int main() {
    srand(time(NULL));

    playGame();

    return 0;
}
