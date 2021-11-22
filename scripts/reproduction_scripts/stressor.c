#include <pthread.h>
#include <stdio.h>
#include <time.h>

#include "stressor.h"
#include "timeLib.h"

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