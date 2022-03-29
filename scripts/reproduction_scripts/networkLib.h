#include <time.h>

#ifndef __NETWORK_LIB__
    #define __NETWORK_LIB__

    #define IPV4_MAX_SIZE 16

    typedef struct t_Message{
        char            ip[IPV4_MAX_SIZE];
        unsigned        size;
        struct timespec timestamp; 

    }TMessage;

    typedef struct t_Message_Queue{
        TMessage        *messages;
        unsigned        size;
        long            front,
                        rear;
    }TMessageQueue;

#endif