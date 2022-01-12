CC := gcc
LDLIBS := -pthread -lm

.DEFAULT_GOAL := all
.PHONY := install all clean purge

EXEC :=  conductor

conductor: conductor.c timeLib.c treaceReader.c stressor.c memLib.c

debugall: CFLAGS := -Wall -Wextra -fsanitize=leak,address -g -D DEBUG_MEM -D DEBUG_CPU
debugall: all

debugmem: CFLAGS := -D DEBUG_MEM
debugmem: all

debugcpu: CFLAGS := -D DEBUG_CPU
debugcpu: all

all: conductor

clean:
	-rm -f *.o 
	-rm -f *~

purge: clean
	-rm -f $(EXEC)
