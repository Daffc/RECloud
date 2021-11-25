CC := gcc
LDLIBS := -pthread -lm

.DEFAULT_GOAL := all
.PHONY := install all clean purge

EXEC :=  conductor

conductor: conductor.c timeLib.c treaceReader.c stressor.c memLib.c

debug: CFLAGS := -Wall -Wextra -fsanitize=leak,address -g
debug: all

all: conductor

clean:
	-rm -f *.o 
	-rm -f *~

purge: clean
	-rm -f $(EXEC)
