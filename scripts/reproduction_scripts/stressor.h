#ifndef __STRESSOR__
    #define __STRESSOR__
    
    pthread_mutex_t lock_loop;
    pthread_cond_t cv_loop;
    pthread_barrier_t b_init_values;

    // Used as data argument for each stressor in 'pthread_create'.
    typedef struct t_stressorsData{
        unsigned char id;
        long long *p_mem_load;
        double *p_cpu_load;
        double *p_delay_interval;
    } TStressorsData;

    // Main logic flux for stressor threads.
    void *startStressors(void *id);

    // Starts stressors as well as the controller mutex  and andition variable, pointing 'p_mem_load', 'p_cpu_load', 'p_delay_interval' 
    // from each 'TStressorsData' structure to 'shared_mem_load_bytes_pointer', 'shared_cpu_dec_load' and 'shared_delay_interval', respectively.
    void initializeStressor(pthread_t *stressors, unsigned char n_stressors, long long *shared_mem_load_bytes_pointer, double *shared_cpu_perc__load, double *shared_delay_interval);

    // Kill stressors processors and free allocated memory for their management.
    void stopStressors(pthread_t *stressors, unsigned char n_stressors);

#endif