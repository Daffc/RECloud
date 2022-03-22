#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#include "networkLib.h"

//MAYBE OPTIONAL LIBS
#include "timeLib.h"


TMessageQueue * initializeTMessageQueue(unsigned size){
    TMessageQueue *m_queue;

    m_queue = (TMessageQueue *) malloc (sizeof(TMessageQueue));
    m_queue->messages = (TMessage *) malloc (size * sizeof(TMessage));
    m_queue->size = size;
    m_queue->front = 0;
    m_queue->rear= 0;

    return m_queue;
}


void freeTMessageQueue(TMessageQueue *m_queue){
    free(m_queue->messages);
    free(m_queue);
}

int main(){

    TMessageQueue *m_queue;

    unsigned size = 10;

    m_queue = initializeTMessageQueue(size);

    for (size_t i = 0; i < size; i++)
    {
        strcpy(m_queue->messages[i].ip, "255.255.255.255");
        m_queue->messages[i].size = i;
        clock_gettime(CLOCK_REALTIME, &(m_queue->messages[i].timestamp));
    }

    for (size_t i = 0; i < size; i++)
    {
        printf("[%ld]\t%s: %u - %s\n", i, m_queue->messages[i].ip, m_queue->messages[i].size, stringifyTimespec(m_queue->messages[i].timestamp));
    }

    freeTMessageQueue(m_queue);
    
}