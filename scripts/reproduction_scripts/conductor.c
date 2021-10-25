#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>

#include "timeLib.h"
#include "treaceReader.h"

#define NTHREADS 2

int *ids;
pthread_mutex_t lock_loop;
pthread_mutex_t lock_sync;
pthread_cond_t cv;

void *initializeStressor (void *id){
    int t_id;
    struct timespec time;
    int c;
    
    t_id = *((int *) id);
    
    printf("ID %d LIVE.\n", t_id);


    while(1){
        pthread_cond_wait(&cv, &lock_loop);
        clock_gettime(CLOCK_REALTIME, &time);
        printf("\t ID: %d\t %s\n", t_id, stringifyTimespec(time));

    }   
}

// Reads Arguments received by the program, informing help messages, 
// defining input trace file.
void parseArguments(int argc, char *argv[], FILE **input){
    char c;
    *input = NULL;

    while ((c = getopt (argc, argv, "hi:")) != -1)
    switch (c){
        // Helper Argument.
        case 'h': 
            // Outputting help message.
            printf(
                "Program to reproduce  PAJE file trace that describes one virtual node of a cloud environment.\n\n"
                "Optional arguments:\n"
                "\t-h\tDisplay help Message.\n"
                "\t-i\tPath to input file (trace file).\n"
            );

            exit(0);
            break;
        
        // Defining input trace file. 
        case 'i':
            
            // Defining file descriptor to the output file. 
            *input = fopen(optarg,"r");

            // Checking if the operation was successful.
            if (*input == NULL) {
                fprintf(stderr, "ERROR: Error while oppening file '%s'.\n", optarg);
                exit(1);
            }
            break;

        // Unknow argument / not optinal argument not informed.  
        case '?':
            if (optopt == 'i')
                fprintf (stderr, "ERROR: Option '-i' requires an argument (path to PAJE trace file).\n");
            else if (isprint (optopt))
                fprintf (stderr, "ERROR: Unknown option '-%c'.\n", optopt);
            else
                fprintf (stderr, "ERROR: Unknown option character '\\x%x'.\n", optopt);
            exit(1);

        // Fallback.
        default:
            abort();
    }

    if (*input == NULL){
        fprintf (stderr, "ERROR: Virtual machine trace file must be informed (option '-i [path_to_trace_file]')");
        exit(1);
    }
}

int main(int argc, char *argv[]){
    struct timespec ts_sampling;

    double db_delay;
    double db_acc;
    struct timespec ts_interval;
    struct timespec ts_prev;

    pthread_t *stressors;

    double timestamp;
    unsigned int mem_bytes;
    float cpu_perc;
    FILE *f_trace;

    parseArguments(argc, argv, &f_trace);

    if(!preparePointerCPUMem(f_trace)){
        fprintf(stderr, "ERROR: CPU and/ or Memory Trace was not found.\n");
        fclose(f_trace);
        exit(1);
    }

    stressors = malloc (NTHREADS * sizeof(pthread_t));
    ids = malloc(NTHREADS * sizeof(int));
    
    pthread_mutex_init( &lock_loop, NULL);
    pthread_mutex_init( &lock_sync, NULL);
    pthread_cond_init( &cv, NULL);

    pthread_mutex_lock(&lock_sync);

    // Creating threads
    for(int i = 0; i < NTHREADS; i++){
        ids[i] = i;
        pthread_create(&stressors[i], NULL, initializeStressor, (void *)(ids + i));
    }

    db_delay = 0.5;

    // Initiating time control variables.
    db_acc = 0;                                     // The variable that accumulates error between sampling rounds.
    ts_interval = doubleToTimespec(&db_delay);      // The Timespec representation of delay between sampling intervals.

    // Initializing variable to calculate elapsed time.
    clock_gettime(CLOCK_REALTIME, &ts_prev);

    nanosleep(&ts_interval , &ts_interval);

    // Sampling current time.
    clock_gettime(CLOCK_REALTIME, &ts_sampling);

    while(followCPUMem(f_trace, &timestamp, &mem_bytes, &cpu_perc)){

        printf("%s\n", stringifyTimespec(ts_sampling));
        printf("%lf, %u, %f\n", timestamp, mem_bytes, cpu_perc);

        // Calculating new adusted interval.
        ts_interval = calculateNextInterval(ts_sampling, ts_prev, db_delay, &db_acc);

        // Updating value of previous time measured (ts_prev).
        ts_prev = ts_sampling;

        pthread_cond_broadcast(&cv);

        // Sleeping
        nanosleep(&ts_interval , &ts_interval);

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &ts_sampling);
    }

    for(int i = 0; i < NTHREADS; i++){
        pthread_kill(stressors[i], SIGTERM);   
        pthread_join(stressors[i], NULL);
    }

    fclose(f_trace);
    free(ids);
    free(stressors);
}