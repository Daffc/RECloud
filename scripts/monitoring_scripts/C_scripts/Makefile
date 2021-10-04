CC := gcc
LDLIBS := -lvirt

.DEFAULT_GOAL := all
.PHONY := install all clean purge

EXEC :=  cpuMemoryMonitor

cpuMemoryMonitor: cpuMemoryMonitor.c timeLib.c signals.c

all: cpuMemoryMonitor

clean:
	-rm -f *.o 
	-rm -f *~

purge: clean
	-rm -f $(EXEC)
