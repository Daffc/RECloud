#!/bin/bash

PREFIX=$1
EXPERIMENT_TIMES=$2
HOSTFILE=$3
NVMS=$4
PROGRAMS=("ep.A.$NVMS" "cg.A.$NVMS" "dt.W.x BH")
PERF_EVENTS="-e task-clock,cpu-clock,context-switches,cpu-migrations"

function checkCreateFolders(){
    if [[ ! -d "results" ]];then
        mkdir results;
    fi

    EXP_DATE="$1_$(date +'%Y-%m-%d_%T')";
    OUT_MAIN_FOLDER="results/$EXP_DATE";
    if [[ ! -d "$OUT_MAIN_FOLDER" ]]; then 
        mkdir "$OUT_MAIN_FOLDER";
    fi
    retval=$OUT_MAIN_FOLDER;
}

main(){
	checkCreateFolders $PREFIX
	OUT_MAIN_FOLDER=$retval

	for program in "${PROGRAMS[@]}"; do
        	p_name=$(echo $program | awk '{print $1}')
		echo "" > $OUT_MAIN_FOLDER/$p_name;
        done;

	for (( t=1; t<=$EXPERIMENT_TIMES; t++ )); do	
		printf "$t - \n"
		for program in "${PROGRAMS[@]}"; do
			p_name=$(echo $program | awk '{print $1}')
			printf "\t$p_name\n"
			perf stat --append -o $OUT_MAIN_FOLDER/$p_name $PERF_EVENTS mpirun -n $NVMS -hostfile $HOSTFILE ./bin/$program  1>/dev/null;
		done;
	done;
		
}
main
