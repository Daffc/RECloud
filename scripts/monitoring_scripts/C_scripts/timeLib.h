#include <libvirt/libvirt.h>
#include <time.h>

#ifndef __TIMELIB__
#define __TIMELIB__

    // Prints the human-readable value of "timestamp".
    void print_time(struct timespec timestamp);

#endif