#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#ifndef __SIGNALS__
#define __SIGNALS__

    // Starts monitoring for SIGINT and SIGTERM, returning a pointer to volatile sig_atomic_t, 
    // pointing to a variable witch value will be equal to 1 after the program receives SIGTERM, 
    // otherwise, it will equal 0;
    volatile sig_atomic_t * startGracefullExiting();
    
#endif