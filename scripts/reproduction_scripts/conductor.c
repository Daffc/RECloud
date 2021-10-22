#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <ctype.h>
#include <pthread.h>
#include <unistd.h>

#include "timeLib.h"

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

        // for(int i = 0; i < 500000000; i++){
        //     c = i;
        // }
    }   
}

int main(int argc, char *argv[]){
    struct timespec ts_sampling;

    double db_delay;
    double db_acc;
    struct timespec ts_interval;
    struct timespec ts_prev;

    pthread_t *stressors;


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

    int c = 0;

    // Sampling current time.
    clock_gettime(CLOCK_REALTIME, &ts_sampling);

    while(c < 5){
        c++;

        printf("%s\n", stringifyTimespec(ts_sampling));

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
        pthread_cancel(stressors[i]);   
    }

    free(stressors);
}