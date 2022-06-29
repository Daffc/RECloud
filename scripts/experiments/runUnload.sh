#/bash/bin

# RECOVERING VMS IPs to vms file
# cat /tmp/experiment_28-06-2022_15\:45\:42/environments.json  | json_pp | grep "virtual_machines" -A 10 | grep "ip" | cut -d : -f 2 | cut -d \" -f 2

RED='\033[0;31m'
NC='\033[0m' # No Color
EXPERIMENTS_DELAYS=(0.1 0.2 0.5 1 2)
EXPERIMENT_TIMES=$1
EXPERIMENT_DURATION=$2


# CHECKING IF EXISTS WITH ERROR, ENDING THE PROCESS.
function checkComandReturn() {
    if ! $*; then 
        printf "\n${RED}ERROR:${NC} While executing:\n"
        printf "\t$*\n"
        exit
    fi
}

function CheckFile() {
    if [[ ! -f $* ]];then
        echo "File '$*' needs to be in current directory" 
        exit 
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
    retval=$OUT_MAIN_FOLDER

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
    

    checkCreateFolders
    OUT_MAIN_FOLDER=$retval

    for delay in "${EXPERIMENTS_DELAYS[@]}"; do
        createExperimentFolder "$OUT_MAIN_FOLDER/$delay"
    done;

    echo "" > logUnload.txt;

    # CHECKING FILES
    CheckFile "credentials"
    CheckFile "nodos"
    CheckFile "vms"

    # GETTING CREDENTIALS
    printf "GETTING CREDENTIALS... "
    USER=$(head -n 1 credentials) 
    PASSWORD=$(tail -n 1 credentials)

    echo "[$USER] [$PASSWORD]"
    printf "OK\n" 

    
    # SETTING CORES IN 'performance' MODE
    printf "SETTING NODES IN PERFORMANCE..."
    checkComandReturn parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g performance" >> logUnload.txt 2>> logUnload.txt;
    checkComandReturn parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> logUnload.txt 2>> logUnload.txt;
    printf "OK\n" 


    printf "***** RUNNING EXPERIMENTS *****\n"
    checkComandReturn . ~/tg_scripts/venv/bin/activate >> logUnload.txt 2>> logUnload.txt;

    for delay in "${EXPERIMENTS_DELAYS[@]}"; do
        for (( t=1; t<=$EXPERIMENT_TIMES; t++ )); do
            printf "\tITERATION (DELAY:$delay\tITERATION:$t)\n"
            checkComandReturn ~/tg_scripts/scripts/monitoring_scripts/startAllMonitoring.py nodos "$OUT_MAIN_FOLDER/$delay" -d $delay -t $EXPERIMENT_DURATION >> logUnload.txt 2>> logUnload.txt <./credentials;
        done;
    done;
    printf "***** FINISHING EXPERIMENTS *****\n"

    # SETTING CORES IN 'ondemand' MODE
    printf "SETTING NODES IN ONDEMAND... "
    checkComandReturn parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g ondemand" >> logUnload.txt 2>> logUnload.txt;
    checkComandReturn parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> logUnload.txt 2>> logUnload.txt;
    printf "OK\n" 

}
main

