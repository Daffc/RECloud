#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>


#include "stressor.h"
#include "timeLib.h"
#include "memLib.h"

// Array of 'TStressorsData' used as data argument for each stressor.
TStressorsData *s_data_array; 


// -------------------- EXTERNAL FUNCTIONS --------------------

// Starts stressors as well as the controller mutex  and andition variable, pointing 'p_mem_load', 'p_cpu_load', 'p_delay_interval' 
// from each 'TStressorsData' structure to 'shared_mem_load_bytes_pointer', 'shared_cpu_dec_load' and 'shared_delay_interval', respectively. 
void initializeStressor(pthread_t *stressors, unsigned char n_stressors, long long *shared_mem_load_bytes_pointer, double *shared_cpu_dec_load, double *shared_delay_interval){
    
    extern pthread_barrier_t b_init_values;
    extern pthread_mutex_t *wait_mutexes;
    extern pthread_mutex_t *start_mutexes;
    
    unsigned char i;

    // Initializing mutexes for main stressor loop controll.
    wait_mutexes = (pthread_mutex_t *) malloc(n_stressors * sizeof(pthread_mutex_t));
    start_mutexes = (pthread_mutex_t *) malloc(n_stressors * sizeof(pthread_mutex_t));

    // Initializing barrier for stressor threads initialization (stressor threads + main thread).
    pthread_barrier_init(&b_init_values, NULL, n_stressors + 1);

    // Allocating stressors data structure array.
    s_data_array = malloc(n_stressors * sizeof(TStressorsData));    
 
    // Defining values for 's_data_array', creating and starting for each stressor thread.
    for(i = 0; i < n_stressors; i++){
        s_data_array[i].id = i;
        s_data_array[i].p_mem_load = shared_mem_load_bytes_pointer;
        s_data_array[i].p_cpu_load = shared_cpu_dec_load;
        s_data_array[i].p_delay_interval = shared_delay_interval;

        pthread_mutex_init(&wait_mutexes[i], NULL);
        pthread_mutex_init(&start_mutexes[i], NULL);
        pthread_mutex_lock(&start_mutexes[i]);
        s_data_array[i].p_m_wait = &wait_mutexes[i];
        s_data_array[i].p_m_start = &start_mutexes[i];

        pthread_create(&stressors[i], NULL, startStressors, (void *)(s_data_array + i));
    }
}


// Kill stressors processors and free allocated memory for their management.
void stopStressors(pthread_t *stressors, unsigned char n_stressors){
    
    // Killing stressors processes.
    for(int i = 0; i < n_stressors; i++){
        pthread_kill(stressors[i], SIGTERM);   
        pthread_join(stressors[i], NULL);
    }

    // Freeing stressors data array.
    free(s_data_array);
}


// -------------------- INTERNAL FUNCTIONS --------------------

void adjustingMemStressor(long long new_mem_stress, long long *prev_mem_stress, char ** mem_stressor_alloc){

    // printf("\t\tadjustingMemStressor\tnew_mem_stress: %lld\tprev_mem_stress %lld\n", new_mem_stress, *prev_mem_stress);
    // Checking if it is needed to memoy onerate the system (new_mem_stress is positive).
    if(new_mem_stress > 0){

        // Adjusting memory allocation.
        *mem_stressor_alloc = (char*) realloc(*mem_stressor_alloc, new_mem_stress);

        // If the total needed memory has increased, occupy the allocated space.
        if(new_mem_stress > *prev_mem_stress){
            touchNewAddresses(*mem_stressor_alloc, new_mem_stress, *prev_mem_stress);     
        }
        // Updating 'prev_mem_stress' for next iteration.
        *prev_mem_stress = new_mem_stress;
    }
    // If system is alread to load compared to the mem sample (new_mem_stress is negative, occupy minimum space as possible).
    else{
        // Adjusting memory allocation.
        *mem_stressor_alloc = (char*) realloc(*mem_stressor_alloc, 1);
        *prev_mem_stress = 1;
    }
}

void adjustingCPUStressor( double cpu_load, double total_interval, double mem_interval){

    double busy_cpu_interval;
    struct timespec ts_start_cpu;
    struct timespec ts_end_cpu;
    struct timespec ts_actual;
    struct timespec ts_cpu_busy;

    float p;
    int i;

    // Calculating remainding time to apply CPU stress (after memory stress alread aplyed).
    busy_cpu_interval = (total_interval * cpu_load) - mem_interval;

    // Check if there isn't time to CPU reproduction, returning if true.
    if(busy_cpu_interval <= 0)
        return;

    // Calculating end time in order to execute 'busy_cpu_interval'
    // CPU stress interval to reach 'cpu_load' percentage.
    clock_gettime(CLOCK_REALTIME, &ts_start_cpu);
    ts_end_cpu = timespecAddPositiveDouble(&ts_start_cpu, &busy_cpu_interval);
    clock_gettime(CLOCK_REALTIME, &ts_actual);

    // Busy waiting in order to apply 'cpu_load' stress (while current time < 'ts_end_cpu').
    while (timespecElapsed(&ts_cpu_busy, ts_actual, ts_end_cpu) != -1){
        p += 1.0;
        i += 1;

        clock_gettime(CLOCK_REALTIME, &ts_actual);
    }

    // Printing CPU debug if 'DEBUG_CPU' is defined in compilation time.
    #ifdef DEBUG_CPU
        printf("\t\t\ttotal_interval: %lf\n", total_interval);
        printf("\t\t\tmem_interval: %lf\n", mem_interval);
        printf("\t\t\tbusy_cpu_interval: %lf\n", busy_cpu_interval);
        printf("\t\t\tts_start_cpu: %s\n", stringifyTimespec(ts_start_cpu));
        printf("\t\t\tts_end_cpu: %s\n", stringifyTimespec(ts_end_cpu));
        printf("\t\t\tts_actual: %s\n", stringifyTimespec(ts_actual));
    #endif

}

// -------------------- MAIN STRESSORS FUNCTIONS --------------------

void *startStressors (void *data){
    TStressorsData *stressor_data;
    struct timespec time;
    char *mem_stressor_alloc;
    
    long long prev_mem_load;

    extern pthread_barrier_t b_init_values;    

    struct timespec ts_start_mem;
    struct timespec ts_end_mem;
    struct timespec ts_mem_interval;

    // Parsing data argument pointer to TStressor structure.
    stressor_data = (TStressorsData *) data;

    

    // Starting memStressor allocation.
    mem_stressor_alloc = malloc(1);
    prev_mem_load = 1;
    // Updating mem load.

    clock_gettime(CLOCK_REALTIME, &time);
    printf("\tID: %u [%s]\n", stressor_data->id, stringifyTimespec(time));
    printf("\t\t MEMLOAD(B): %lld\n", *stressor_data->p_mem_load);
    printf("\t\t CPULOAD: %lf\n", *stressor_data->p_cpu_load);
    printf("\t\t DELAY: %lf\n", *stressor_data->p_delay_interval);

    // Presetting environment with memory stress.
    adjustingMemStressor(*(stressor_data->p_mem_load), &(prev_mem_load), &(mem_stressor_alloc));

    // Sincronizing all threads (stressors and conductor).
    pthread_barrier_wait(&b_init_values);   

    while(1){
        // Wating conductor thread mutex unlock to execute new stress load.
        pthread_mutex_lock(stressor_data->p_m_start);
        
        clock_gettime(CLOCK_REALTIME, &time);
        printf("\tID: %u [%s]\n", stressor_data->id, stringifyTimespec(time));
        printf("\t\tMEMLOAD(B): %lld\n", *stressor_data->p_mem_load);
        printf("\t\tCPULOAD: %lf\n", *stressor_data->p_cpu_load);
        
        // Updating Memory stress.
        clock_gettime(CLOCK_REALTIME, &ts_start_mem);
        adjustingMemStressor(*(stressor_data->p_mem_load), &(prev_mem_load), &(mem_stressor_alloc));
        clock_gettime(CLOCK_REALTIME, &ts_end_mem);

        // Calculating enlapsed time dedicated to memory stress.
        timespecElapsed(&ts_mem_interval, ts_start_mem, ts_end_mem);
        // Applying CPU stress.
        adjustingCPUStressor(*(stressor_data->p_cpu_load), *(stressor_data->p_delay_interval), timespecToDouble(&ts_mem_interval));
        
        
        // Freeing conductor thread to call for new round of stress.
        pthread_mutex_unlock(stressor_data->p_m_wait);
    }  
}