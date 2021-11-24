#ifndef __STRESSOR__
    #define __STRESSOR__
    
    pthread_mutex_t lock_loop;
    pthread_cond_t cv;

    // Used as data argument for each stressor in 'pthread_create'.
    typedef struct t_stressorsData{
        unsigned char id;
        long long *p_mem_load;
    } TStressorsData;

    // Main logic flux for stressor threads.
    void *startStressors(void *id);

    // Starts stressors as well as the controller metex and andition variable.
    void initializeStressor(pthread_t *stressors, unsigned char n_stressors, long long *memLoadBytes);

    // Kill stressors processors and free allocated memory for their management.
    void stopStressors(pthread_t *stressors, unsigned char n_stressors);

#endif