#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>


#include "stressor.h"
#include "timeLib.h"

int *ids; // Used to store stressors threads ID.

void *initializeStressor (void *id){
    int t_id;
    struct timespec time;

    t_id = *((int *) id);
    
    printf("ID %d LIVE.\n", t_id);

    while(1){
        pthread_cond_wait(&cv, &lock_loop);
        clock_gettime(CLOCK_REALTIME, &time);
        printf("\t ID: %d\t %s\n", t_id, stringifyTimespec(time));
    }   
}

// Starts stressors as well as the controller metex and andition variable.
void startStressors(pthread_t *stressors, unsigned char n_stressors){
    extern pthread_mutex_t lock_loop; 
    extern pthread_cond_t cv;
    
    unsigned char i;

    // Allocating identification array.
    ids = malloc(n_stressors * sizeof(int));    
    
    // Initializing mutexes and conditional variables.
    pthread_mutex_init(&lock_loop, NULL);
    pthread_cond_init(&cv, NULL);                


    // Creating and starting threads.
    for(i = 0; i < n_stressors; i++){
        ids[i] = i;
        pthread_create(&stressors[i], NULL, initializeStressor, (void *)(ids + i));
    }
}


// Kill stressors processors and free allocated memory for their management.
void stopStressors(pthread_t *stressors, unsigned char n_stressors){
    
    // Killing stressors processes.
    for(int i = 0; i < n_stressors; i++){
        pthread_kill(stressors[i], SIGTERM);   
        pthread_join(stressors[i], NULL);
    }

    // Freeing identification array.
    free(ids);
}