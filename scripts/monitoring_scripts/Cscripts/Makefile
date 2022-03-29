CC := gcc
LDLIBS := -lvirt -lm

.DEFAULT_GOAL := all
.PHONY := install all clean purge

EXEC :=  cpuMemMonitor

cpuMemMonitor: cpuMemMonitor.c timeLib.c signals.c

debug: CFLAGS := -Wall -Wextra -fsanitize=leak,address -g
debug: all

all: cpuMemMonitor

clean:
	-rm -f *.o 
	-rm -f *~

purge: clean
	-rm -f $(EXEC)
