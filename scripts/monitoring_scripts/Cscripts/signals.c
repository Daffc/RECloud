#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
 
// Detects aquisition of SIGTER or SIGINT.
volatile sig_atomic_t terminate = 0;

// Called when SIGTERM is received, setting terminate = 1, indicating that the process must terminate.
void terminateProcess(int signum)
{
    terminate = 1;
}
 
// Prepare program to handle SIGTERM signals, returning a pointer to a variable that indicates that the process must terminate (value = 1).
volatile sig_atomic_t * startGracefullExiting(){
    struct sigaction action;
    memset(&action, 0, sizeof(struct sigaction));

    // Defining Function that should be called when SIGINT and/or SIGTERM has been detected.
    action.sa_handler = terminateProcess;
    sigaction(SIGINT, &action, NULL);
    sigaction(SIGTERM, &action, NULL);

    return &terminate;
}