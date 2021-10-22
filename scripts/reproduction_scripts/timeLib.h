#include <time.h>

#ifndef __TIMELIB__
#define __TIMELIB__

    #define BILLION 1000000000

    // Returns pointer to human-readable string of "timestamp".
    char * stringifyTimespec(struct timespec timestamp);

    // Calculates time enlapse between from timespec 'x' to 'y', storing difference in 'result', and returning singal of operation.
    int timespecElapsed (struct timespec *result, struct timespec x, struct timespec  y);

    // Receive a timespec 't_time' and returns correspondent double value.
    double timespecToDouble(struct timespec *t_time);

    // Receive a double '*d_time' and returns the correspondent timespec.
    struct timespec doubleToTimespec(double *d_time);

    // Calculates the difference between measures time samplings (ts_actual to ts_prev), 
    // retuning new adjusted time interval according to the desired interval in 'db_delay', and accumulated error in 'db_acc'. 
    struct timespec calculateNextInterval(struct timespec ts_actual, struct timespec ts_prev, double db_delay, double *db_acc);

#endif