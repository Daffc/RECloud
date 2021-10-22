#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PajeSetVariable         "8"
#define PajeStartLink           "14"
#define PajeEndLink             "15"

// Updates 'file' pointer until it points to the first occurrence of 'PajeSet Variable', meaning, the first trace of the Memory and CPU tuple.
int preparePointerCPUMem(FILE *file){
    char code[3];

    char *line;
    size_t line_len;
    ssize_t read;

    line = NULL;
    
    // Looking for the line which initiates with 'PajeSetVariable' code.
    do{
        read = getline(&line, &line_len, file);
        sscanf(line, "%s", code);
    }
    while (strcmp(code, PajeSetVariable) != 0 && read != EOF);

    // Returning 'file' to the beginning of the line.
    fseek(file, -read, SEEK_CUR);
    
    // Freeing line;
    free(line);

    // If the end of file, return 0 (PajeSetVariable not found).
    if(read == EOF)
        return 0;
    
    // Else return that 'PajeSetVariable' was found.
    return 1;
}

// Receiving the 'file' pointer, read the next line, looking for code 'PajeSetVariable', if it matches, recovers timestamp, memory in bytes, and CPU usage.
int followCPUMem(FILE *file, double *timestamp, unsigned int *mem_bytes, float *cpu_perc){
    char *code;

    char *line;
    size_t line_len;
    ssize_t read;

    line = NULL;

    // Getting next line of the file.
    read = getline(&line, &line_len, file);
    
    // Recovering PAJE code of the line.
    code = strtok (line," ");

    // If code does not correspond to 'PajeSetVariable' (meaning CPU usage), return.
    if(strcmp(code, PajeSetVariable) != 0 || read == EOF){
        return 0;
    }

    
    *timestamp = strtod(strtok(NULL," "), NULL);        // Recovering timestamp of sampling.
    strtok(NULL," ");                                   // Skipping virtual machine's name. 
    strtok(NULL," ");                                   // Skipping 'MEM' label
    *mem_bytes = strtoul(strtok(NULL," "), NULL, 0);    // Recovering memory value for the timestamp.

    // Reading next line (CPU variable for same timestamp.)
    read = getline(&line, &line_len, file);
    strtok(line," ");                                   // Skipping 'PajeSetVariable' code.
    strtok(NULL," ");                                   // Skipping timestamp (same of previous MEM entry).
    strtok(NULL," ");                                   // Skipping vm name.
    strtok(NULL," ");                                   // Skipping 'CPU' labe
    *cpu_perc = strtof(strtok(NULL," "), NULL);         // Recovering CPU value for the timestamp.

    free(line);
    
    return 1;
}

int main(){
    FILE *f_trace;

    f_trace = fopen("/home/dac17/experiment/traces/21-10-2021_12:59/mojito1/testvm1-1.trace","r");

    if (f_trace == NULL){
        printf("ERRO DE LEITURA\n");
        exit(1);
    }

    if(!preparePointerCPUMem(f_trace)){
        fprintf(stderr, "ERROR: CPU and/ or Memory Trace was not found.\n");
    }

    double timestamp;
    unsigned int mem_bytes;
    float cpu_perc;

    while(followCPUMem(f_trace, &timestamp, &mem_bytes, &cpu_perc)){
        printf("%lf, %u, %f\n", timestamp, mem_bytes, cpu_perc);
    }

    fclose(f_trace);
}