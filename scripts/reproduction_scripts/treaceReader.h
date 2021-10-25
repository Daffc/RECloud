#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PAJESETVARIABLE         "8"
#define PAJESTARTLINK           "14"
#define PAJEENDLINK             "15"

// Updates 'file' pointer until it points to the first occurrence of 'PajeSet Variable', meaning, the first trace of the Memory and CPU tuple.
int preparePointerCPUMem(FILE *file);

// Receiving the 'file' pointer, read the next line, looking for code 'PajeSetVariable', if it matches, recovers timestamp, memory in bytes, and CPU usage.
int followCPUMem(FILE *file, double *timestamp, unsigned int *mem_bytes, float *cpu_perc);