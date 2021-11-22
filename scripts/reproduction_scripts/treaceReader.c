#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "treaceReader.h" 

// Updates 'file' pointer until it points to the first occurrence of 'PajeSet Variable', meaning, the first trace of the Memory and CPU tuple.
int preparePointerCPUMem(FILE *file){
    char *code;

    char *line;
    size_t line_len;
    ssize_t read;

    line = NULL;

    
    // Looking for the line which initiates with 'PAJESETVARIABLE' code.
    do{
        read = getline(&line, &line_len, file);
        code = strtok(line," ");  
    }
    while (strcmp(code, PAJESETVARIABLE) != 0 && read != EOF);

    // Freeing line;
    free(line);

    // If the end of file, return 0 (PAJESETVARIABLE not found).
    if(read == EOF){
        return 0;
    }

    // Returning 'file' to the beginning of the line.
    fseek(file, -read, SEEK_CUR);
    
    // Else return that 'PAJESETVARIABLE' was found.
    return 1;
}

// Receiving the 'file' pointer, read the next line, looking for code 'PAJESETVARIABLE', if it matches, recovers timestamp, memory in bytes, and CPU usage.
int followCPUMem(FILE *file, TTraceEntry *t_entry){
    char *code;

    char *line;
    size_t line_len;
    ssize_t read;

    line = NULL;

    // Getting next line of the file.
    read = getline(&line, &line_len, file);
    
    // Recovering PAJE code of the line.
    code = strtok (line," ");

    // If code does not correspond to 'PAJESETVARIABLE' (meaning CPU usage), return.
    if(strcmp(code, PAJESETVARIABLE) != 0 || read == EOF){
        free(line);
        return 0;
    }

    
    t_entry->timestamp = strtod(strtok(NULL," "), NULL);    // Recovering timestamp of sampling.
    strtok(NULL," ");                                       // Skipping virtual machine's name. 
    strtok(NULL," ");                                       // Skipping 'MEM' label
    t_entry->mem_kB = strtoul(strtok(NULL," "), NULL, 0);   // Recovering memory value (kilobytes) for the timestamp.

    // Reading next line (CPU variable for same timestamp.)
    read = getline(&line, &line_len, file);
    strtok(line," ");                                       // Skipping 'PAJESETVARIABLE' code.
    strtok(NULL," ");                                       // Skipping timestamp (same of previous MEM entry).
    strtok(NULL," ");                                       // Skipping vm name.
    strtok(NULL," ");                                       // Skipping 'CPU' labe
    t_entry->cpu_perc = strtof(strtok(NULL," "), NULL);     // Recovering CPU value for the timestamp.

    free(line);
    
    return 1;
}