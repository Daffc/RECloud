#ifndef __MEM_LIB__
    #define __MEM_LIB__

    #define VM_NAME_SIZE 21
    #define IPV4_MAX_SIZE 16

    typedef struct t_VmData{
        char    name[VM_NAME_SIZE],
                ip[IPV4_MAX_SIZE];
    }TVmData;

    typedef struct t_VmDataList{
        int size;
        TVmData *items;
    }TVmDataList;

    // Comparison function used by Quick Sort Algorithm (qsort) for Virtual Machines Data List ordering.
    int cmpVmOrder(const void* a, const void* b);

    // Comparison function used by Binary Search Algorithm (bsearch) to compare a string with b Virtual Machine Data name.
    int cmpVmNameSearch(const void* a, const void* b);

    // Initializing Virtual Machines Data List.
    TVmDataList * initializeVMDataList();

    // Freeing Virtual Machines Data List.
    void freeVMDataList(TVmDataList * vm_data_list);

    // Inserting new Virtual Machine data into Virtual Machines Data List.
    void insertVmData(TVmDataList * vm_data_list, TVmData *vm);

    // Ordering items of Virtual Machines Data List by items name.
    void orderVmDataList(TVmDataList * vm_data_list);

    // Prints Virtual Machines Data (debug).
    void printVmData(TVmData * vm_data);

    // Prints Virtual Machines Data List (debug).
    void printVmDataList(TVmDataList * vm_data_list);

    // Reads JSON file located in "envs_path" and returns Virtual Machines Data List populated with virtual machines data.
    TVmDataList * readEnvironmentsToVmDataList(char *envs_path);

    // Searches in Virtual Machines Data List the entry that contains key (name) returning the pointer to the found entry (TVmData *),  otherwise return NULL.
    TVmData * searchVmDataEntry(TVmDataList * vm_data_list, char * key);

#endif