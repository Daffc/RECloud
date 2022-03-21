#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef __TRACE_READER__
    #define __TRACE_READER__

    #define PAJESETVARIABLE         "8"
    #define PAJESTARTLINK           "14"
    #define PAJEENDLINK             "15"

    // Store trace information for one entry at 'timestamp' time.
    typedef struct T_TraceEntry{
        double timestamp;               // Timestamp of current trace entry.
        unsigned long long mem_kB;      // Memory in kB for trace entry. 
        float cpu_perc;                 // CPU usage percentage for in kB for trace entry
    }TTraceEntry;


    // Updates 'file' pointer until it points to the first occurrence of 'PajeSet Variable', meaning, the first trace of the Memory and CPU tuple.
    int preparePointerCPUMem(FILE *file);

    // Receiving the 'file' pointer, read the next line, looking for code 'PajeSetVariable', if it matches, recovers timestamp, memory in bytes, and CPU usage.
    int followCPUMem(FILE *file, TTraceEntry *t_entry, struct timespec *ts_init);

#endif

