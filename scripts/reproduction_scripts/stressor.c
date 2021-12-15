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
    extern pthread_mutex_t lock_loop; 
    extern pthread_cond_t cv_loop;
    
    unsigned char i;

    // Initializing mutexe and conditional variables for main loop controll.
    pthread_mutex_init(&lock_loop, NULL);
    pthread_cond_init(&cv_loop, NULL); 

    // Initializing barrier for stressor threads initialization (stressor threads + main thread).
    pthread_barrier_init (&b_init_values, NULL, n_stressors + 1);

    // Allocating stressors data structure array.
    s_data_array = malloc(n_stressors * sizeof(TStressorsData));    
 
    // Defining values for 's_data_array', creating and starting for each stressor thread.
    for(i = 0; i < n_stressors; i++){
        s_data_array[i].id = i;
        s_data_array[i].p_mem_load = shared_mem_load_bytes_pointer;
        s_data_array[i].p_cpu_load = shared_cpu_dec_load;
        s_data_array[i].p_delay_interval = shared_delay_interval;
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

// -------------------- MAIN STRESSORS FUNCTIONS --------------------

void *startStressors (void *data){
    TStressorsData *stressor_data;
    struct timespec time;
    char *mem_stressor_alloc;
    
    long long prev_mem_load;

    extern pthread_mutex_t lock_loop;
    extern pthread_cond_t cv_loop;
    extern pthread_barrier_t b_init_values;



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

    // Waiting for other threads.
    pthread_barrier_wait(&b_init_values);

    while(1){
        pthread_cond_wait(&cv_loop, &lock_loop);
        clock_gettime(CLOCK_REALTIME, &time);
        printf("\tID: %u [%s]\n", stressor_data->id, stringifyTimespec(time));
        printf("\t\t MEMLOAD(B): %lld\n", *stressor_data->p_mem_load);
        printf("\t\t CPULOAD: %lf\n", *stressor_data->p_cpu_load);
        

        // Updating mem load.
        adjustingMemStressor(*(stressor_data->p_mem_load), &(prev_mem_load), &(mem_stressor_alloc));
    }   
}