#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#include "networkLib.h"

//MAYBE OPTIONAL LIBS
#include "timeLib.h"


void resetQueue(TMessageQueue * m_queue){
    m_queue->front = - 1;
    m_queue->rear = - 1;
}

TMessageQueue * initializeTMessageQueue(unsigned size){
    TMessageQueue *m_queue;

    m_queue = (TMessageQueue *) malloc (sizeof(TMessageQueue));
    m_queue->messages = (TMessage *) malloc (size * sizeof(TMessage));
    m_queue->size = size;
    resetQueue(m_queue);

    return m_queue;
}


void freeTMessageQueue(TMessageQueue *m_queue){
    free(m_queue->messages);
    free(m_queue);
}

void enqueueMessage(TMessageQueue *m_queue, TMessage * message){
    
    m_queue->rear++;

    if( m_queue->rear >= m_queue->size ){
        fprintf(stderr, "ERROR: Message Queue is full (rear: %ld and size: %u).\n", m_queue->rear, m_queue->size);
        exit(1);
    }
    if(m_queue->front == -1){
        m_queue->front = 0;
    }

    strcpy(m_queue->messages[m_queue->rear].ip, message->ip);
    m_queue->messages[m_queue->rear].size = message->size;
    m_queue->messages[m_queue->rear].timestamp = message->timestamp;

}

TMessage * dequeueMessage(TMessageQueue * m_queue){
    
    TMessage *p_message;
    // Check if the queue is empt, returnin NULL pointer.
    if(m_queue->front == -1 || m_queue->front > m_queue->rear){
        return NULL;
    }

    p_message = &(m_queue->messages[m_queue->front]);
    m_queue->front++;

    return p_message;
}

void printTMessage(TMessage * message){
    printf("\t\t%s: %u - %s\n", message->ip, message->size, stringifyTimespec(message->timestamp));
}
    
void printTMessageQueue(TMessageQueue *m_queue){

    size_t i;

    printf("Message Queue:\n");
    printf("\tsize %u\n", m_queue->size);
    printf("\tfront %ld\n", m_queue->front);
    printf("\trear %ld\n", m_queue->rear);
    for (i = 0; i < m_queue->size; i++)
    {
        printTMessage(&m_queue->messages[i]);
    }
}

int main(){

    TMessageQueue *m_queue;
    TMessage message;
    TMessage *p_message;
    unsigned size = 10;

    m_queue = initializeTMessageQueue(size);

    for (size_t i = 0; i < size/2; i++)
    {
        strcpy(message.ip, "255.255.255.255");
        message.size = i;
        clock_gettime(CLOCK_REALTIME, &(message.timestamp));
 
        enqueueMessage(m_queue, &message);
    }
    printTMessageQueue(m_queue);


    printf("\t\t--------------------------\n");
    for (size_t i = 0; i < 3; i++)
    {
        p_message = dequeueMessage(m_queue);

        if(p_message){
            printTMessage(p_message);        
        }
        else{
            printf("\t\t!!! EMPT !!!\n");
        }
    }
    printf("\t\t--------------------------\n");


    for (size_t i = 0; i < size/2; i++)
    {
        strcpy(message.ip, "255.255.255.255");
        message.size = i;
        clock_gettime(CLOCK_REALTIME, &(message.timestamp));
 
        enqueueMessage(m_queue, &message);
    }
    printTMessageQueue(m_queue);

    printf("\t\t--------------------------\n");
    for (size_t i = 0; i < 10; i++)
    {
        p_message = dequeueMessage(m_queue);

        if(p_message){
            printTMessage(p_message);        
        }
        else{
            printf("\t\t!!! EMPT !!!\n");
        }
    }
    printf("\t\t--------------------------\n");

    freeTMessageQueue(m_queue);
    
}