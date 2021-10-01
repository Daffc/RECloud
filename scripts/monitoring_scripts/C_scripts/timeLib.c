#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "timeLib.h"

// Returns pointer to human-readable string of "timestamp".
char * stringifyTimespec(struct timespec timestamp){
    time_t now = timestamp.tv_sec;
    struct tm ts;
    static char buf[100];

    ts = *localtime(&now);
    strftime(buf, sizeof(buf), "%a %Y-%m-%d %H:%M:%S", &ts);
    sprintf(buf + strlen (buf), ".%lu", timestamp.tv_nsec);

    return buf;
}

// Calculates time enlapse between from timespec 'x' to 'y', storing difference in 'result', and returning singal of operation.
int timespec_enlapse (struct timespec *result, struct timespec x, struct timespec  y){
  
    struct timespec * big;
    struct timespec * sml;

    int nsec;
    unsigned long long a, b;
    int signal;


    // Checking which of the values to the largest by adjusting the "big" and "sml" pointers and the "signal" return sign.
    a = (x.tv_sec * BILLION) + x.tv_nsec;
    b = (y.tv_sec * BILLION) + y.tv_nsec;

    if(a < b){
        big = &y;
        sml = &x; 
        signal = 1;
    }
    else{
        big = &x;
        sml = &y;
        signal = -1;
    }

    // Adjusting nanoseconds to execute the subtraction.
    if (big->tv_nsec < sml->tv_nsec) {
        nsec = (sml->tv_nsec - big->tv_nsec) / BILLION + 1;
        sml->tv_nsec -= BILLION * nsec;
        sml->tv_sec += nsec;
    }
    if (big->tv_nsec - sml->tv_nsec > BILLION) {
        nsec = (big->tv_nsec - sml->tv_nsec) / BILLION;
        sml->tv_nsec += BILLION * nsec;
        sml->tv_sec -= nsec;
    }

    result->tv_sec = big->tv_sec - sml->tv_sec;
    result->tv_nsec = big->tv_nsec - sml->tv_nsec;

    /* Return signal of the elapsed time. */
    return signal;
}


// Receiver a timespec 't_time' and returns correspondent double value.
double timespecToDouble(struct timespec *t_time){
    double d_time;

    d_time = t_time->tv_sec + (t_time->tv_nsec * 1.0 / BILLION);
    return d_time;
}