#include <libvirt/libvirt.h>
#include <time.h>

#ifndef __TIMELIB__
#define __TIMELIB__

    #define BILLION 1000000000

    // Returns pointer to human-readable string of "timestamp".
    char * stringifyTimespec(struct timespec timestamp);

    // Calculates time enlapse between from timespec 'x' to 'y', storing difference in 'result', and returning singal of operation.
    int timespec_enlapse (struct timespec *result, struct timespec x, struct timespec  y);

    // Receiver a timespec 't_time' and returns correspondent double value.
    double timespecToDouble(struct timespec *t_time);

#endif