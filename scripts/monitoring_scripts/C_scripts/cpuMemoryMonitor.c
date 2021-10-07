#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <libvirt/libvirt.h>
#include <ctype.h>

#include "cpuMemoryMonitor.h"
#include "timeLib.h"
#include "signals.h"

#define MAX_DELAY 5
#define MIN_DELAY 0.05
#define DEFAULT_DELAY 0.5

// Attempting to connect with virtual environment informed by 'connection'. 
virConnectPtr libvirtConnect(const char * connection){
    virConnectPtr conn;
    conn = virConnectOpen(connection);

    if (conn == NULL) {
        fprintf(stderr, "Failed to open connection to '%s'.\n", connection);
        exit(1);
    }

    return conn;
}

// Recovering all Active Domains from connection "conn".
TDomainsList getActiveDomains(virConnectPtr conn){
    TDomainsList domains;
    virDomainPtr *domains_pointers;
    int i;

    // Recovering the number of domains and their pointers.
    domains.number = virConnectListAllDomains(conn, &domains_pointers, VIR_CONNECT_LIST_DOMAINS_ACTIVE);

    if(domains.number < 0){
        fprintf(stderr, "Failed to recover Active Domains.\n");
        exit(1);
    }

    // Allocating domain structures and distributing domain pointer and name accordingly.
    domains.list = malloc(domains.number * sizeof(TDomain));
    for(i = 0; i< domains.number; i++){
        domains.list[i].pointer = domains_pointers[i];
        strcpy (domains.list[i].name, virDomainGetName(domains.list[i].pointer));
    }

    // Freeing list of pointers to domains.
    free(domains_pointers);

    return domains;
}

// Recover domain CPU usage since the last measurement.
void getDomainCPUUsage(TDomain *domain){
    virDomainInfo info;

    struct timespec t_current;
    struct timespec t_diff;

    double percCPU;
    double d_diff;

    // Recovering time of sampling and sampling infomations from domain.
    clock_gettime(CLOCK_REALTIME, &t_current);
    if(virDomainGetInfo(domain->pointer, &info) < 0){
        fprintf(stderr, "Failed to recover domain Information (%s).\n", domain->name);
        exit(1);
    }    

    // Recovering the difference between the last and current sampling timestamp and converting the difference to double.
    timespecElapsed(&t_diff, domain->cpu_Timestamp, t_current);
    d_diff = timespecToDouble(&t_diff);
    
    // Calculating new CPU usage percentage.
    percCPU = (((info.cpuTime - domain->cpuTime) * 1.0) / (d_diff * 10000000));

    // Storing data to the domain data.
    domain->cpuTime = info.cpuTime;
    domain->cpu_Timestamp = t_current;
    
    // Returning new CPU usage measurement in domain structure.
    domain->cpu_perc = percCPU;
}

void getDomainMemUsage(TDomain *domain){
    virDomainMemoryStatStruct mem_stats[VIR_DOMAIN_MEMORY_STAT_NR];
    int n_mem_stats;
    unsigned long long unused, actual, used;

    // Recover All Memory Stats for domain.
    n_mem_stats = virDomainMemoryStats(domain->pointer, mem_stats, VIR_DOMAIN_MEMORY_STAT_NR, 0);
    if(n_mem_stats < 0){
        fprintf(stderr, "Failed to recover domain Memory Stats (%s).\n", domain->name);
        exit(1);
    }    

    // Iterating throught all returned memory status, looking for current 
    // unused memory (tag  = VIR_DOMAIN_MEMORY_STAT_UNUSED) and total 
    // available memory by the domain perspective (tag =VIR_DOMAIN_MEMORY_STAT_AVAILABLE). 
    for(int j = 0; j <  n_mem_stats; j++){
        if (mem_stats[j].tag == VIR_DOMAIN_MEMORY_STAT_UNUSED)
            unused = mem_stats[j].val;
        if (mem_stats[j].tag == VIR_DOMAIN_MEMORY_STAT_AVAILABLE)
            actual = mem_stats[j].val;
    }

    // Calculating Used Memory (Available - (Used + Cached)).
    used = actual - unused;

    // Updating domain structure valuer for memory in yse (used + cached)
    domain->used_mem = used;
    domain->used_mem_perc = (used * 1.0 / actual) * 100;
}

// Setting Baloon Period dor domain represented by in 'domain'.
void setBalloonPeriod(TDomain *domain, int period){
    if(virDomainSetMemoryStatsPeriod(domain->pointer, period, VIR_DOMAIN_AFFECT_LIVE) < 0){
        fprintf(stderr, "Failed to set domain's Balloon period (%s).\n", domain->name);
        exit(1);
    }
}

// Reads Arguments received by the program, informing help messages, 
// defining the output of the program and/or redefining the desired delay between samples.
void parseArguments(int argc, char *argv[], FILE **output, double *delay){
    char c;
    
    // Defining variables with default values.
    *delay = DEFAULT_DELAY;
    *output = stdout;

    while ((c = getopt (argc, argv, "ho:d:")) != -1)
    switch (c){
        // Helper Argument.
        case 'h': 
            // Outputting help message.
            printf(
                "Program to collect CPU and Memory data from Virtual Machines. Displayed data will follow the schema for each time interval:\n"
                "\tTIMESTAMP; [VM0]; [VM1]; [VM2] ...\n"
                "Each [VMN] entry will have the following Information:\n"
                "\tVM-NAME VM-MEM-ABS VM-MEM-PERC VM-CPU-PERC.\n\n"
                "Optional arguments:\n"
                "\t-h\tDisplay help Message.\n"
                "\t-o\tPath to output file. If not informed, data will be displayed in stdout.\n"
                "\t-d\tThe time interval between sampling the statistics in seconds (must bee between %d and %.2f, default is %.1f).\n",
                MAX_DELAY,
                MIN_DELAY,
                DEFAULT_DELAY
            );

            exit(0);
            break;

        // Redefine delay between samples (default 0.5s).
        case 'd':
            // Converting value that follows '-d' to double, storing in *delay and, in case of error, print error and exists.
            if(sscanf(optarg, "%lf", delay) != 1){
                fprintf(stderr, "ERROR: value '%s' does not represents time in seconds (must be between %d and %.2lf).\n", optarg, MAX_DELAY, MIN_DELAY);
                exit(1);
            }
            else 
                if( (*delay < MIN_DELAY )|| (*delay > MAX_DELAY) ){
                    fprintf(stderr, "ERROR: value '%s' out of boundaries (must be between %d and %.2lf).\n", optarg, MAX_DELAY, MIN_DELAY);
                    exit(1);
                }

            break;
        
        // Redefnine output of program to a file. 
        case 'o':
            
            // Defining file descriptor to the output file. 
            *output = fopen(optarg,"w");

            // Checking if the operation was successful.
            if (*output == NULL) {
                fprintf(stderr, "ERROR: Error while oppening file '%s'.\n", optarg);
                exit(1);
            }
            break;

        // Unknow argument / not optinal argument not informed.  
        case '?':
            if (optopt == 'd')
                fprintf (stderr, "ERROR: Option '-d' requires an argument in seconds between %d and %.2f (default is 0.5).\n", MAX_DELAY, MIN_DELAY);
            else if (optopt == 'o')
                fprintf (stderr, "ERROR: Option '-o' requires an argument path to output file.\n");
            else if (isprint (optopt))
                fprintf (stderr, "ERROR: Unknown option '-%c'.\n", optopt);
            else
                fprintf (stderr, "ERROR: Unknown option character '\\x%x'.\n", optopt);
            exit(1);

        // Fallback.
        default:
            abort();
    }

}
int main(int argc, char *argv[])
{
    struct timespec ts_sampling;
    virConnectPtr conn;
    TDomainsList domains;
    volatile sig_atomic_t * terminate;
    FILE * output;

    double db_delay;
    double db_acc;
    struct timespec ts_interval;
    struct timespec ts_prev;

    // Parsing Arguments (Defining interval between samples in 'delay' and output file descriptor in 'output').
    parseArguments(argc, argv, &output, &db_delay);

    // Initiating time control variables.
    db_acc = 0;                                 // The variable that accumulates error between sampling rounds.
    ts_interval = doubleToTimespec(&db_delay);     // The Timespec representation of delay between sampling intervals.

    // Establishing connection with qemu.
    conn = libvirtConnect("qemu:///system");
    
    // Recovering domains number and pointers to structure 'domains'.
    domains = getActiveDomains(conn);

    // Preparing Domains and gatterind ilitializin information.
    for(int i = 0; i < domains.number; i ++){
        setBalloonPeriod(&(domains.list[i]), 1);    // Setting Balloon Period (Memory Monitoring)
        getDomainCPUUsage(&(domains.list[i]));      // Recover initial CPU measurements (cpuTime, and cpu_Timestamp).
    }

    // Recover pointer to SIGTER signal handler.
    terminate =  startGracefullExiting();

    // Initializing variable to calculate elapsed time.
    clock_gettime(CLOCK_REALTIME, &ts_prev);
    nanosleep(&ts_interval , &ts_interval);

    // Stops loop when receive SIGTER.
    while(!(*terminate)){

        // Sampling current time.
        clock_gettime(CLOCK_REALTIME, &ts_sampling);

        // Recovering Domains Information.
        for(int i = 0; i < domains.number; i ++){
            getDomainCPUUsage(&(domains.list[i]));
            getDomainMemUsage(&(domains.list[i]));
        }

        // Printing sampling time.
        fprintf(output, "%s", stringifyTimespec(ts_sampling));
        
        // For all domains, dusplay statistics.
        for(int i = 0; i < domains.number; i ++){
            fprintf(output, "; %s", domains.list[i].name);               // Domain name.
            fprintf(output, " %llu", domains.list[i].used_mem);          // Domain used memory (used + cached in KB).
            fprintf(output, " %3.2f", domains.list[i].used_mem_perc);    // Domain used memory percentage (used + cached).
            fprintf(output, " %3.2f", domains.list[i].cpu_perc);         // Domain used memory percentage.
        }
        fprintf(output,"\n");

        // Calculating new adusted interval.
        ts_interval = calculateNextInterval(ts_sampling, ts_prev, db_delay, &db_acc);

        // Updating value of previous time measured (ts_prev).
        ts_prev = ts_sampling;
        
        // Sleeping
        nanosleep(&ts_interval , &ts_interval);
    }

    // Deactivatind Balloon for all domains.
    for(int i = 0; i < domains.number; i ++){
        setBalloonPeriod(&(domains.list[i]), 0);
    }

    // Freeing domains pointers and structures.
    for(int i = 0; i < domains.number; i ++){
        virDomainFree(domains.list[i].pointer);
    }
    free(domains.list);

    // Closing connection with the virtualizer.
    virConnectClose(conn);

    // Closing file descriptor of output.
    fclose(output);
}