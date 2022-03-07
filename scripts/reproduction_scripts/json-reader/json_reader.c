#include <stdio.h>
#include <json-c/json.h>

void readEnvironments(char *envs_path){
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

    
    // Opening File, reading to 'buffer' and closing.
    fp_json = fopen(envs_path, "r");
    // Checking if the operation was successful.
    if (fp_json == NULL) {
        fprintf(stderr, "ERROR: Error while oppening environments file '%s'.\n", envs_path);
        exit(1);
    }

    // Finding 'fp_json' file size.
    fseek(fp_json, 0L, SEEK_END);
    file_size = ftell(fp_json); 
    rewind(fp_json);

    // Allocating reader buffer.
    buffer = (char *) malloc(file_size);

    fread(buffer, file_size, 1, fp_json);
    fclose(fp_json);

    // Parsing json content.
    parsed_json = json_tokener_parse(buffer);
    
    // Freeing buffer.
    free(buffer);

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
        printf("NODE: [%s] \n", json_object_get_string(hostname));

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

            printf("\tVM: [%s] <-> [%s]\n", json_object_get_string(vm_name), json_object_get_string(vm_ip));
        }
    }

    // Freeing root object 'parsed_json' memory;
    json_object_put(parsed_json);
}

int main(int argc, char **argv){

    readEnvironments("environments.json");
}

