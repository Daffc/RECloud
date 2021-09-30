#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void print_time(struct timespec timestamp){
    time_t now = timestamp.tv_sec;
    struct tm ts;
    char buf[100];
    // Format time, "ddd yyyy-mm-dd hh:mm:ss"
    ts = *localtime(&now);
    strftime(buf, sizeof(buf), "%a %Y-%m-%d %H:%M:%S", &ts);
    printf("%s.%09ld\n", buf, timestamp.tv_nsec);
}