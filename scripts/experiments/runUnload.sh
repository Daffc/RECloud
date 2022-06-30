#/bash/bin

# RECOVERING VMS IPs to vms file
# cat /tmp/experiment_28-06-2022_15\:45\:42/environments.json  | json_pp | grep "virtual_machines" -A 10 | grep "ip" | cut -d : -f 2 | cut -d \" -f 2

LOG_OUTPUT="logUnload.txt";
RED='\033[0;31m';
NC='\033[0m';
EXPERIMENTS_DELAYS=(0.1 0.2 0.5 1 2);
EXPERIMENT_TIMES=$1;
EXPERIMENT_DURATION=$2;


# CHECKING IF EXISTS WITH ERROR, ENDING THE PROCESS.
function checkComandReturn() {
    if ! $*; then 
        printf "\n${RED}ERROR:${NC} While executing:\n";
        printf "\t$*\n";
        exit 1;
    fi
}

function CheckFile() {
    if [[ ! -f $* ]];then
        echo "File '$*' needs to be in current directory";
        exit 1;
    fi
}

function checkCreateFolders(){
    if [[ ! -d "results" ]];then
        mkdir results;
    fi

    EXP_DATE=UNLOAD_$(date +'%Y-%m-%d_%T');
    OUT_MAIN_FOLDER="results/$EXP_DATE";
    if [[ ! -d "$OUT_MAIN_FOLDER" ]]; then 
        mkdir "$OUT_MAIN_FOLDER";
    fi
    retval=$OUT_MAIN_FOLDER;

}

function createExperimentFolder(){
    if [[ ! -d "$1" ]]; then 
        mkdir "$1";
    fi
}
function checkArguments(){
    if ! [ "$2" -eq "$2" ] 2> /dev/null; then
        printf "\n${RED}ERROR:${NC} Invalid value for '$1'\n";
        exit 1;
    fi
}

main() {
    
    # CHECKING PROGRAM ARGUMENTS
    checkArguments EXPERIMENT_TIMES $EXPERIMENT_TIMES;
    checkArguments EXPERIMENT_DURATION $EXPERIMENT_DURATION;
    printf "*************************************************\n";
    printf "EXECUTING EXPERIMENTS FOR:\n";
    printf "\tEXPERIMENT_TIMES: $EXPERIMENT_TIMES\n";
    printf "\tEXPERIMENT_DURATION: $EXPERIMENT_DURATION\n";
    printf "\tEXPERIMENTS_DELAYS: ${EXPERIMENTS_DELAYS[*]}\n";
    printf "*************************************************\n";
    

    checkCreateFolders;
    OUT_MAIN_FOLDER=$retval;

    for delay in "${EXPERIMENTS_DELAYS[@]}"; do
        createExperimentFolder "$OUT_MAIN_FOLDER/$delay";
    done;

    echo "" > $LOG_OUTPUT;

    # CHECKING FILES
    CheckFile "credentials";
    CheckFile "nodos";
    CheckFile "vms";

    # GETTING CREDENTIALS
    printf "GETTING CREDENTIALS... ";
    USER=$(head -n 1 credentials);
    PASSWORD=$(tail -n 1 credentials);

    echo "[$USER] [$PASSWORD]";
    printf "OK\n";

    
    # SETTING CORES IN 'performance' MODE
    printf "SETTING NODES CORES IN PERFORMANCE STATE..."
    checkComandReturn parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g performance" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    checkComandReturn parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    printf "OK\n";

    # SETTING ALL VMS TO USE 1 VCORES
    printf "SETTING CORES TO ALL VMS... \n";
    printf "\tSHUTTING DOWN VMS... ";
    parallel-ssh -h nodos -i "VAR=\"\$(hostname)\"; virsh shutdown testvm\${VAR: -1}-1;" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    sleep 5;
    printf "OK\n";
    printf "\tCHANGING VMS CONFIGS AND BOOTING... ";
    checkComandReturn parallel-ssh -h nodos -i "VAR=\"\$(hostname)\"; echo $PASSWORD| sudo -S sed -i \"s/<vcpu placement='static'>2<\\/vcpu>/<vcpu placement='static'>1<\\/vcpu>/g\" /etc/libvirt/qemu/testvm\${VAR: -1}-1.xml;" >> $LOG_OUTPUT 2>> $LOG_OUTPUT; 
    checkComandReturn parallel-ssh -h nodos -i "VAR=\"\$(hostname)\"; echo $PASSWORD| sudo -S virsh define /etc/libvirt/qemu/testvm\${VAR: -1}-1.xml;" >> $LOG_OUTPUT 2>> $LOG_OUTPUT; 
    parallel-ssh -h nodos -i "VAR=\"\$(hostname)\"; virsh start testvm\${VAR: -1}-1;" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    sleep 5;
    checkComandReturn parallel-ssh -h nodos -i 'VAR="$(hostname)"; echo $VAR;  virsh vcpucount testvm${VAR: -1}-1' >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    printf "OK\n";
    printf "OK\n";

    printf "***** RUNNING EXPERIMENTS *****\n";
    checkComandReturn . ~/tg_scripts/venv/bin/activate >> $LOG_OUTPUT 2>> $LOG_OUTPUT;

    for delay in "${EXPERIMENTS_DELAYS[@]}"; do
        for (( t=1; t<=$EXPERIMENT_TIMES; t++ )); do
            printf "\tITERATION (DELAY:$delay\tITERATION:$t)\n";
            checkComandReturn ~/tg_scripts/scripts/monitoring_scripts/startAllMonitoring.py nodos "$OUT_MAIN_FOLDER/$delay" -d $delay -t $EXPERIMENT_DURATION >> $LOG_OUTPUT 2>> $LOG_OUTPUT <./credentials;
        done;
    done;
    printf "***** FINISHING EXPERIMENTS *****\n";

    # SETTING CORES IN 'ondemand' MODE
    printf "SETTING NODES CORES IN ONDEMAND STATE... ";
    checkComandReturn parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g ondemand" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    checkComandReturn parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> $LOG_OUTPUT 2>> $LOG_OUTPUT;
    printf "OK\n";

}
main

