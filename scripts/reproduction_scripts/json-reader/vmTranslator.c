#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <json-c/json.h>

#include "vmTranslator.h"

// Comparison function used by Quick Sort Algorithm (qsort) for Virtual Machines Data List ordering.
int cmpVmOrder(const void* a, const void* b){
    const char* aa = ((TVmData *) a)->name;
    const char* bb = ((TVmData *) b)->name;

    return strcmp(aa, bb);
}


// Comparison function used by Binary Search Algorithm (bsearch) to compare a string with b Virtual Machine Data name.
int cmpVmNameSearch(const void* a, const void* b){
    const char* aa = (char *) a;
    const char* bb = ((TVmData *) b)->name;

    return strcmp(aa, bb);
}


// Initializing Virtual Machines Data List.
TVmDataList * initializeVMDataList(){
    TVmDataList *vm_data_list;

    vm_data_list = malloc(sizeof(TVmDataList));
    vm_data_list->size = 0; 

    return  vm_data_list;
}

// Freeing Virtual Machines Data List.
void freeVMDataList(TVmDataList * vm_data_list){
    free(vm_data_list->items);
    free(vm_data_list);
}

// Inserting new Virtual Machine data into Virtual Machines Data List.
void insertVmData(TVmDataList * vm_data_list, TVmData *vm){

    // Oppening space for one more item.
    vm_data_list->items = realloc(vm_data_list->items, (vm_data_list->size + 1) * sizeof(TVmData));

    // Copying data to the new item.
    strcpy(vm_data_list->items[vm_data_list->size].name, vm->name);
    strcpy(vm_data_list->items[vm_data_list->size].ip, vm->ip);

    vm_data_list->size ++;
}

// Ordering items of Virtual Machines Data List by items name.
void orderVmDataList(TVmDataList * vm_data_list){
    qsort(vm_data_list->items, vm_data_list->size, sizeof(TVmData), cmpVmOrder);
}

// Prints Virtual Machines Data (debug).
void printVmData(TVmData * vm_data){
    size_t i;

    printf("%s <-> %s\n", vm_data->name, vm_data->ip);
}

// Prints Virtual Machines Data List (debug).
void printVmDataList(TVmDataList * vm_data_list){
    size_t i;

    for (i = 0; i < vm_data_list->size; i++)
    {
        printVmData(&vm_data_list->items[i]);
    }
}

// Reads JSON file located in "envs_path" and returns Virtual Machines Data List populated with virtual machines data.
TVmDataList * readEnvironmentsToVmDataList(char *envs_path){
    FILE    *fp_json;

    char    *buffer;

    unsigned int file_size;

    json_object * parsed_json,
                * hosts_array,
                * host,
                * hostname,
                * vm_array,
                * vm,
                * vm_name,
                * vm_ip;
    
    size_t  n_hosts,
            n_vms,
            i,
            j;

    
    TVmDataList * vm_data_list;
    TVmData vm_data;
    
    // Virtual Machines Data List
    vm_data_list = initializeVMDataList();

    // Opening File.
    fp_json = fopen(envs_path, "r");
    // Checking if the operation was successful.
    if (fp_json == NULL) {
        fprintf(stderr, "ERROR: Error while oppening environments file '%s'.\n", envs_path);
        exit(1);
    }

    // Finding 'fp_json' file size.
    fseek(fp_json, 0, SEEK_END);
    file_size = ftell(fp_json); 
    rewind(fp_json);

    // Allocating buffer.
    buffer = (char *) malloc(file_size);

    // Reading entire file to buffer and closing it.
    fread(buffer, file_size, 1, fp_json);
    fclose(fp_json);

    // Parsing json content.
    parsed_json = json_tokener_parse(buffer);
    
    // Freeing buffer.
    free(buffer);

    // Parsing 'hosts' from 'parsed_json'.
    if(!json_object_object_get_ex(parsed_json, "hosts", &hosts_array)){
        fprintf(stderr, "ERROR: Unable to find 'hosts' key in '%s'.\n", envs_path);
        exit(1);
    }
    n_hosts = json_object_array_length(hosts_array);

    // Looping through 'hosts_array'.
    for (i = 0; i < n_hosts; i++)
    {
        host = json_object_array_get_idx(hosts_array, i);

        if(!json_object_object_get_ex(host, "hostname", &hostname)){
            fprintf(stderr, "ERROR: Unable to find 'hostname' key in '%s'.\n", envs_path);
            exit(1);
        }

        // Retriving 'vm_array' from host.
        if(!json_object_object_get_ex(host, "virtual_machines", &vm_array)){
            fprintf(stderr, "ERROR: Unable to find 'virtual_machines' key in '%s'.\n", envs_path);
            exit(1);
        }
        n_vms = json_object_array_length(vm_array);

        // Looping through 'vm_array'.
        for (j = 0; j < n_vms; j++)
        {
            vm = json_object_array_get_idx(vm_array, j);

            // Retriving 'name' and 'ip' from vm.
            if(!json_object_object_get_ex(vm, "name", &vm_name)){
                fprintf(stderr, "ERROR: Unable to find 'name' key in '%s'.\n", envs_path);
                exit(1);
            }
            if(!json_object_object_get_ex(vm, "ip", &vm_ip)){
                fprintf(stderr, "ERROR: Unable to find 'name' key in '%s'.\n", envs_path);
                exit(1);
            }

            // Populating 'vm_data' with new found Virtual Machine Data and inserting it into vm_data_list.
            strcpy(vm_data.name, json_object_get_string(vm_name));
            strcpy(vm_data.ip, json_object_get_string(vm_ip));

            insertVmData(vm_data_list, &vm_data);
        }
    }

    // Freeing root object 'parsed_json' memory;
    json_object_put(parsed_json);

    return vm_data_list;
}

// Searches in Virtual Machines Data List the entry that contains key (name) returning the pointer to the found entry (TVmData *),  otherwise return NULL.
TVmData * searchVmDataEntry(TVmDataList * vm_data_list, char * key){
    TVmData *res_vm;

    // Searching for element in "vm_data_list" with key (name) equals to string pointed by "key". 
    res_vm = bsearch(key, vm_data_list->items, vm_data_list->size, sizeof(TVmData), cmpVmNameSearch);

    return res_vm;
}

int main(int argc, char **argv){

    // ----------------- DEBUG ---------------------

    TVmData *aux;

    TVmDataList *vm_data_list;

    // Allocating and populating Virtual Machine Data List.
    vm_data_list = readEnvironmentsToVmDataList("environments.json");

    // Odering Virtual Machine Data List. 
    orderVmDataList(vm_data_list);

    aux = searchVmDataEntry(vm_data_list, "testvm6-1");
    
    printf("------ SEARCH ------\n");
    printVmData(aux);

    freeVMDataList(vm_data_list);

    // ----------------- DEBUG ---------------------

}