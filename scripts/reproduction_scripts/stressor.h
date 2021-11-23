#ifndef __STRESSOR__
    #define __STRESSOR__
    
    pthread_mutex_t lock_loop;
    pthread_cond_t cv;

    // Main logic flux for stressor threads.
    void *initializeStressor(void *id);

    // Starts stressors as well as the controller metex and andition variable.
    void startStressors(pthread_t *stressors, unsigned char n_stressors);

    // Kill stressors processors and free allocated memory for their management.
    void stopStressors(pthread_t *stressors, unsigned char n_stressors);

#endif