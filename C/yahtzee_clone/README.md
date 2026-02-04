# Yahtzee Clone - Terminal Game

A terminal-based implementation of the classic Yahtzee dice game written in standard C.

## Features

- **ASCII Art Dice**: Each die displays with a bordered box containing visual pip representations
- **Full Yahtzee Gameplay**: All 13 scoring categories
- **Hold/Keep Dice**: Hold specific dice between rolls
- **Score Tracking**: Real-time score sheet display
- **13 Rounds**: Classic Yahtzee format with exactly 13 rounds

## Building

### Compile
```bash
make
```

### Run
```bash
make run
```

### Or directly
```bash
./yahtzee
```

### Clean
```bash
make clean
```

## How to Play

1. **Roll Phase**: At the start of each round, your dice are rolled automatically
2. **Hold Dice**: You get up to 3 rolls per round. After each roll (except the last), you can hold specific dice
   - When prompted, enter the die numbers (1-5) you want to hold, separated by spaces
   - Press Enter to skip holding
3. **Score Selection**: After your 3 rolls, choose which category to score your dice in
   - Available categories are displayed with their scoring values
   - Each category can only be used once per game
4. **13 Rounds**: Play all 13 rounds to complete your game
5. **Final Score**: Your total score is displayed at the end

## Scoring Categories

- **Ones through Sixes**: Sum of all dice matching that number
- **Three of a Kind**: Sum of all dice if 3+ match
- **Four of a Kind**: Sum of all dice if 4+ match
- **Full House**: 25 points for 3 of one number and 2 of another
- **Small Straight**: 30 points for 4 consecutive numbers
- **Large Straight**: 40 points for 5 consecutive numbers
- **Yahtzee**: 50 points for all 5 dice matching
- **Chance**: Sum of all dice (can be used anytime)

## Dice Display

Each die is displayed in an ASCII box showing the pip pattern:
```
┌─────┐
│  ●  │   <- One die (value 1)
│     │
│     │
└─────┘
```

## Requirements

- GCC compiler (or any standard C compiler)
- Linux/Unix terminal
- C99 standard support

## License

Free to use and modify.
