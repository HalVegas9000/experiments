CC = gcc
CFLAGS = -std=c99 -Wall -Wextra
TARGET = yahtzee
SRC = yahtzee.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean
