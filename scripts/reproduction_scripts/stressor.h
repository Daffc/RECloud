#ifndef __STRESSOR__
    #define __STRESSOR__
    
    pthread_mutex_t lock_loop;
    pthread_mutex_t lock_sync;
    pthread_cond_t cv;

    void *initializeStressor (void *id);
#endif