#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/sysinfo.h>

#include "timeLib.h"
#include "treaceReader.h"
#include "stressor.h"
#include "memLib.h"

#define MAX_DELAY 5
#define MIN_DELAY 0.05


// Variables shared between conductor and stressors.
long long shared_mem_load_bytes;    // Variable that will store memory load, in bytes, that each stressor must onerate from the system.
double shared_cpu_dec_load;        // Variable that will store cpu percentage load, that each stressor must onerate from the system.
double db_delay;                    // Target delay between iterations (must be the same as the used to generate the reproduced trace).

// Reads Arguments received by the program, informing help messages, 
// defining input trace file.
void parseArguments(int argc, char *argv[], FILE **input, double *delay){
    char c;
    *input = NULL;
    *delay = 0.0;

    while ((c = getopt (argc, argv, "hi:d:")) != -1)
    switch (c){
        // Helper Argument.
        case 'h': 
            // Outputting help message.
            printf(
                "Program to reproduce  PAJE file trace that describes one virtual node of a cloud environment.\n\n"
                "Optional arguments:\n"
                "\t-h\tDisplay help Message.\n"
                "\t-i\tPath to input file (trace file).\n"
                "\t-d\tThe time interval between sampling the CPU and Moemory statistics in seconds (must be between %.2lfs and %ds).\n", MIN_DELAY, MAX_DELAY
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

        // Redefine delay between samples (default 0.5s).
        case 'd':
            // Converting value that follows '-d' to double, storing in *delay and, in case of error, print error and exists.
            if(sscanf(optarg, "%lf", delay) != 1){
                fprintf(stderr, "ERROR: value '%s' does not represents time in seconds (must be between %.2lfs and %ds).\n", optarg, MIN_DELAY, MAX_DELAY);
                exit(1);
            }
            else 
                if( (*delay < MIN_DELAY )|| (*delay > MAX_DELAY) ){
                    fprintf(stderr, "ERROR: value '%s' out of boundaries (must be between %.2lfs and %ds).\n", optarg, MIN_DELAY, MAX_DELAY);
                    exit(1);
                }

            break;

        // Unknow argument / not optinal argument not informed.  
        case '?':
            if (optopt == 'd')
                fprintf (stderr, "ERROR: Option '-d' requires an argument in seconds between %.2lfs and %ds.\n", MIN_DELAY, MAX_DELAY);
            if (optopt == 'i')
                fprintf (stderr, "ERROR: Option '-i' requires an argument (path to PAJE trace file).\n");
            else if (isprint (optopt))
                fprintf (stderr, "ERROR: Unknown option '-%c'.\n", optopt);
            else
                fprintf (stderr, "ERROR: Unknown option character '\\x%x'.\n", optopt);
            exit(1);

        // Fallback
        default:
            abort();
    }

    if (*input == NULL){
        fprintf (stderr, "ERROR: Virtual machine trace file must be informed (option '-i [path_to_trace_file]')\n");
        exit(1);
    }

    if (*delay == 0.0){
        fprintf (stderr, "ERROR: The delay between samples must be informed (option '-d [value between %d and %.2f.]')\n", MAX_DELAY, MIN_DELAY);
        exit(1);
    }
}

// Given next expected system memory load (trace_mem_kB) and available stressors (n_stressors), 
// calculates the memory value in Bytes that each stressor will have to occupy.
long long calculateSharedMemLoadBytes(unsigned long long trace_mem_kB, unsigned char n_stressors){
    long long int final_mem_load;
    unsigned long long env_mem_load;    // Total Memory load of the system.
    unsigned long long self_mem_load;   // Memory load (RSS) of conductor process and its children.
    unsigned long long sys_mem_load;    // System isolated memory load. 

    env_mem_load = getSysBusyMem();
    self_mem_load = getSelfMem();
    sys_mem_load = env_mem_load - self_mem_load;

    // Calculating new memory workload
    final_mem_load = trace_mem_kB - sys_mem_load;

    // Converting final_mem_load from KB to B.
    final_mem_load = final_mem_load * 1024;

    // Dividing load by the number of stressors.
    final_mem_load = final_mem_load / n_stressors;

    // Printing Memory debug if 'DEBUG_MEM' is defined in compilation time.
    #ifdef DEBUG_MEM
        printf("env_mem_load: %llu\tself_mem_load: %llu\ttrace_mem_kB: %llu\tsys_mem_load: %llu\n", env_mem_load, self_mem_load,trace_mem_kB, sys_mem_load);
        printf("final_mem_load(B): %lld\n", final_mem_load);
    #endif

    return final_mem_load;
}

// Given next expected system cpu load percentage (cpu_perc) and available stressors (n_stressors),
// returns double value (decimal) that each stressos will have to exert in CPU.
double calculateSharedCpuLoadDec(double cpu_perc, unsigned char n_stressors){
    double cpu_dec;

    // Dividing by number of stressors and percentile as to get decimal 
    // CPU comsiption representation for each stressor.
    cpu_dec = cpu_perc / (n_stressors * 100.0);

    // Preventing ocasional CPU consumption above 100% for each 
    // processor core (due to sampling accuracy in monitoring stage ).
    if(cpu_dec > 100.0){
        cpu_dec = 100.0;
    }

    return cpu_dec;
}


// Sends Signal to the reproduction manager process informing that reproduction process is read to start.
void sendReadySignal(){

    // TODO: 
    //      substitue 'printf()' function for proper signal sender processes that makes reproduction manager process aware of this process state.
    printf("***** Ready for Reproduction *****\n");
}

//  Defines the waiting for signal from reproduction manager process to start the reproduction scenario.
void waitStarReproductiontSignal(){

    // TODO: 
    //      substitue 'getchar()' function for proper external signal capture from reproduction manager process.
    getchar();
}


int main(int argc, char *argv[]){
    struct timespec ts_sampling;        // Stores current time after calculus and before sleep.

    double db_acc;                      // Accumulates the time error between iterations in order to dissipate it along the reproduction.
    struct timespec ts_interval;        // Actial time interval that will be applied to sleep function.
    struct timespec ts_prev;            // Current time of previour time sampling (ts_sampling).

    pthread_t *stressors;               // Pointer to array of descriptors of stressor threads.

    // External mutex for stressors controll.
    extern pthread_cond_t cv_loop;
    extern pthread_barrier_t b_init_values;

    TTraceEntry t_entry;                // Structure that stores information for trace entry according to Timestamp.

    FILE *f_trace;                      // The file descriptor of trace that will be read.

    // System information.
    unsigned char n_cpu_procs;          // Stores the number of physical cores of the system.


    // parsing program arguments.
    parseArguments(argc, argv, &f_trace, &db_delay);
    
    // Initiating time control variables.
    db_acc = 0;                                     // The variable that accumulates error between sampling rounds.
    ts_interval = doubleToTimespec(&db_delay);      // The Timespec representation of delay between sampling intervals.

    // Recovering number of "physical" cores from the system.
    n_cpu_procs = get_nprocs();  

    // Adjusting 'f_traces' pointer to the first CPU/MEM trace entry.
    if(!preparePointerCPUMem(f_trace)){
        fprintf(stderr, "ERROR: CPU and/or Memory Trace was not found.\n");
        fclose(f_trace);
        exit(1);
    }

    // Allocating Stressors and getting them ready to reproduction.
    stressors = malloc (n_cpu_procs * sizeof(pthread_t));

    // Setting environment to the same state as the first entry of the trace file.
    followCPUMem(f_trace, &t_entry);
    shared_mem_load_bytes = calculateSharedMemLoadBytes(t_entry.mem_kB, n_cpu_procs);
    shared_cpu_dec_load = calculateSharedCpuLoadDec(t_entry.cpu_perc, n_cpu_procs);
    initializeStressor(stressors, n_cpu_procs, &shared_mem_load_bytes, &shared_cpu_dec_load, &db_delay);

    // Waiting until all threads have properlly started and setted Memory and CPU initual values.
    pthread_barrier_wait(&b_init_values);
    
    // Sends signal to the reproduction manager that reproduction process is read to be started.
    sendReadySignal();

    // Wait for sinal to start reproduction.
    waitStarReproductiontSignal();

    // Initializing variable to calculate elapsed time.
    clock_gettime(CLOCK_REALTIME, &ts_sampling);

    // Defining a synthetic 'ts_prev' time spec value, in 'db_delay' seconds before 'ts_sampling'.
    ts_prev = timespecSubPositiveDouble(&ts_sampling, &db_delay);

        
    while(followCPUMem(f_trace, &t_entry)){

        printf("%s\n", stringifyTimespec(ts_sampling));
        printf("%lf, %llu, %f\n", t_entry.timestamp, t_entry.mem_kB, t_entry.cpu_perc);

        // Calculating new adusted interval.
        ts_interval = calculateNextInterval(ts_sampling, ts_prev, db_delay, &db_acc);

        // Updating value of previous time measured (ts_prev).
        ts_prev = ts_sampling;

        shared_mem_load_bytes = calculateSharedMemLoadBytes(t_entry.mem_kB, n_cpu_procs);
        shared_cpu_dec_load = calculateSharedCpuLoadDec(t_entry.cpu_perc, n_cpu_procs);

        pthread_cond_broadcast(&cv_loop);

        // Sleeping
        nanosleep(&ts_interval , &ts_interval);

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &ts_sampling);
    }

    // Killing stressors and freeing their management memory.
    stopStressors(stressors, n_cpu_procs);
    free(stressors);
    fclose(f_trace);
}