#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

#include "timeLib.h"

// Returns pointer to human-readable string of "timestamp".
char * stringifyTimespec(struct timespec timestamp){
    time_t now = timestamp.tv_sec;
    struct tm ts;
    static char buf[100];

    ts = *localtime(&now);
    strftime(buf, sizeof(buf), "%a %Y-%m-%d %H:%M:%S", &ts);
    sprintf(buf + strlen (buf), ".%09lu", timestamp.tv_nsec);

    return buf;
}

// Calculates time enlapse from timespec 'x' to 'y', storing difference in 'result', and returning singal of operation.
int timespecElapsed (struct timespec *result, struct timespec x, struct timespec  y){
  
    struct timespec * big;
    struct timespec * sml;

    int nsec;
    unsigned long long x_, y_;
    int signal;


    // Checking which of the values to the largest by adjusting the "big" and "sml" pointers and the "signal" return sign.
    x_ = (x.tv_sec * BILLION) + x.tv_nsec;
    y_ = (y.tv_sec * BILLION) + y.tv_nsec;

    if(x_ < y_){
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


// Receive a timespec 't_time' and returns correspondent double value.
double timespecToDouble(struct timespec *t_time){
    double d_time;

    d_time = t_time->tv_sec + (t_time->tv_nsec * 1.0 / BILLION);
    return d_time;
}

// Receive a double '*d_time' and returns the correspondent timespec.
struct timespec doubleToTimespec(double *d_time){
    struct timespec t_time;

    t_time.tv_sec = (int) *d_time;
    t_time.tv_nsec = (*d_time - (t_time.tv_sec)) * BILLION;

    return t_time;
}

// Calculates the difference between measures time samplings (ts_actual to ts_prev), 
// retuning new adjusted time interval according to the desired interval in 'db_delay', and accumulated error in 'db_acc'. 
struct timespec calculateNextInterval(struct timespec ts_actual, struct timespec ts_prev, double db_delay, double *db_acc){

    int err_signal;
    double db_err;
    double db_interval;

    struct timespec diff;
    struct timespec err;

    // Calculating elapsed time from 'ts_prev' to 'ts_actual', storing result in 'diff'.
    timespecElapsed(&diff, ts_prev, ts_actual);

    // Calculating elapsed time from 'diff' to 'db_delay', storing result in 'err' and returning signal of operation to 'err_signal' (1 to positive and -1 to negative).
    err_signal = timespecElapsed(&err, diff, doubleToTimespec(&db_delay));

    // Recovering double representation of 'db_err'.
    db_err = timespecToDouble(&err);
    // Adjusting signal of the value according to 'err_signal'.
    db_err *= err_signal; 

    // Adding error to the error accumulator.
    *db_acc += db_err;

    // Applying accumulated error to the desired interval, defining the new time interval.
    db_interval = db_delay + (*db_acc);

    // Converting new time interval from double to timespec and returning.
    return doubleToTimespec(&db_interval);
}

// Given a pointer to timespec 'ts_base' and positive double value 'db_value' 
// (Representing seconds in integer part and nanoseconds in float part), 
// returns new timespec resulting from the sum of the two previous values. 
struct timespec timespecAddPositiveDouble(struct timespec *ts_base, double *db_value){
    struct timespec result;
    long    nsec;
    long    trunc_value;

    // Checking if 'db_value' represents a negative value.
    if(*db_value < 0){
        fprintf(stderr, "ERROR: Negative double value in 'timespecAddPositiveDouble' function. '%lf'.\n", *db_value);
        exit(1);
    }

    trunc_value = trunc(*db_value);

    result.tv_sec = ts_base->tv_sec;
    nsec = ts_base->tv_nsec + ((*(db_value) - trunc_value) * BILLION);

    // If 'nsec'  is greater than BILLION, add on second to the result and adjust 'nsec'.
    if(nsec > BILLION){
        result.tv_sec += 1;
        nsec -= BILLION;
    }

    result.tv_sec += trunc_value;   // Adding seconds from 'db_value'
    result.tv_nsec = nsec;          // Defining final nanoseconds value.

    return result;
}

// Given a pointer to timespec 'ts_base' and positive double value 'db_value' 
// (Representing seconds in integer part and nanoseconds in float part), 
// returns new timespec resulting from the subtraction of the two previous values.
struct timespec timespecSubPositiveDouble(struct timespec *ts_base, double *db_value){
        struct  timespec result;
        long    nsec;
        long    trunc_value;

        // Checking if 'db_value' represents a negative value.
        if(*db_value < 0){
            fprintf(stderr, "ERROR: Negative double value in 'timespecSubPositiveDouble' function. '%lf'.\n", *db_value);
            exit(1);
        }

        trunc_value = trunc(*db_value);

        result.tv_sec = ts_base->tv_sec;
        nsec = ts_base->tv_nsec - ((*(db_value) - trunc_value) * BILLION);
        if(nsec < 0){
            result.tv_sec -= 1;
            nsec = nsec + BILLION;
        }

        result.tv_sec -= trunc_value;
        result.tv_nsec = nsec;

        return result;
}


