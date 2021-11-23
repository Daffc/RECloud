#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>


#include "stressor.h"
#include "timeLib.h"

// Array of 'TStressorsData' used as data argument for each stressor.
TStressorsData *s_data_array; 

void *initializeStressor (void *data){
    TStressorsData *stressor_data;
    struct timespec time;

    stressor_data = (TStressorsData *) data;
    
    printf("ID %d LIVE.\n", stressor_data->id);

    while(1){
        pthread_cond_wait(&cv, &lock_loop);
        clock_gettime(CLOCK_REALTIME, &time);
        printf("\tID: %u \t MEMLOAD: %llu\t %s\n", stressor_data->id, *stressor_data->p_mem_load, stringifyTimespec(time));
    }   
}

// Starts stressors as well as the controller metex and andition variable, pointing 'p_mem_load' from each 'TStressorsData' structure to 'shared_mem_load_bytes_pointer'.
void startStressors(pthread_t *stressors, unsigned char n_stressors, unsigned long long *shared_mem_load_bytes_pointer){
    extern pthread_mutex_t lock_loop; 
    extern pthread_cond_t cv;
    
    unsigned char i;

    // Initializing mutexes and conditional variables.
    pthread_mutex_init(&lock_loop, NULL);
    pthread_cond_init(&cv, NULL); 

    // Allocating stressors data structure array.
    s_data_array = malloc(n_stressors * sizeof(TStressorsData));    
 
    // Defining values for 's_data_array', creating and starting for each stressor thread.
    for(i = 0; i < n_stressors; i++){
        s_data_array[i].id = i;
        s_data_array[i].p_mem_load = shared_mem_load_bytes_pointer;
        pthread_create(&stressors[i], NULL, initializeStressor, (void *)(s_data_array + i));
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
    // free(s_data_array);
}