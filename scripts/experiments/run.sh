#/bash/bin

# RECOVERING VMS IPs to vms file
# cat /tmp/experiment_28-06-2022_15\:45\:42/environments.json  | json_pp | grep "virtual_machines" -A 10 | grep "ip" | cut -d : -f 2 | cut -d \" -f 2

printf "GETTING CREDENTIALS... "
if [[ ! -f "credentials" ]];then
    echo "necessário definir arquieo 'credentials"
fi

# GETTING CREDENTIALS

USER=$(head -n 1 credentials) 
USER=$(tail -n 1 credentials)
printf "OK\n" 

# DEFININDO CORES EM MODO 'performance'
printf "SETTING NODES IN PERFORMANCE..."
parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g performance" >> log.txt 2>> log.txt ;
parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> log.txt 2>> log.txt ;
printf "OK\n" 

printf "DEFINING OUTPUT FOLDERS..."
if [[ ! -d "results" ]];then
    mkdir results;
fi
EXP_DATE=$(date +'%Y-%m-%d_%T');
OUT_FOLDER="results/$EXP_DATE";
if [[ ! -d "$OUT_FOLDER" ]]; then 
    mkdir "$OUT_FOLDER";
fi
printf "OK\n"

printf "***** RUNNING EXPERIMENTS *****\n"
. ~/tg_scripts/venv/bin/activate;
for i in {1..3}; do
    INTERVAL=0.5;
    DURATION=5;
    printf "ITERATION $i - (INTERVAL:$INTERVAL\tDURATION:$DURATION)\n"
    ~/tg_scripts/scripts/monitoring_scripts/startAllMonitoring.py nodos $OUT_FOLDER -d $INTERVAL -t $DURATION < ./credentials >> log.txt 2>> log.txt;
done;
printf "***** FINISHING EXPERIMENTS *****\n"

# DEFININDO CORES EM MODO 'performance'
printf "SETTING NODES IN PERFORMANCE... "
parallel-ssh -h nodos -i "echo $PASSWORD| sudo -S  cpupower frequency-set -g ondemand" >> log.txt 2>> log.txt ;
parallel-ssh -h nodos -i "cpufreq-info |  grep 'frequency is'" >> log.txt 2>> log.txt ;
printf "OK\n" 


