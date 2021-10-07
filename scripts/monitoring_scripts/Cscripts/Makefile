CC := gcc
LDLIBS := -lvirt

.DEFAULT_GOAL := all
.PHONY := install all clean purge

EXEC :=  cpuMemMonitor

cpuMemMonitor: cpuMemMonitor.c timeLib.c signals.c

all: cpuMemMonitor

clean:
	-rm -f *.o 
	-rm -f *~

purge: clean
	-rm -f $(EXEC)
