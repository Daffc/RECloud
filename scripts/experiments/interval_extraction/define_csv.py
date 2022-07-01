#!/usr/bin/env python3.9
from glob import glob
from datetime import datetime
import time
import os
import csv
import argparse
from itertools import zip_longest


CPU_MEM_TIME_MASK = "%a %Y-%m-%d %H:%M:%S.%f"                     
CPU_MEM_START = " ********* Start Monitoring **********\n"
CPU_MEM_END = " ********* Stopping Monitoring **********\n"


def getIntervals(trace_f, colunm_name):
    results = []
    # CHECKING FIRST LINE
    line = trace_f.readline()
    line_cols = line.split(';')

    if(line_cols[1] != CPU_MEM_START):
        sys.exit(f"Wrong file format:'{trace_f.name}'.")

    # GETTING FIRST VALID LINE (TRACE)
    line = trace_f.readline()
    line_cols = line.split(';')
    prev_time = datetime.strptime(line_cols[0][0:30], CPU_MEM_TIME_MASK)

    for line in trace_f.readlines():
        line_cols = line.split(';')

        # Checking if it's 'trace_f' last line.
        if(line_cols[1] == CPU_MEM_END):
            break

        # Getting interval betwee samples and saving in 'results'
        curr_time = datetime.strptime(line_cols[0][0:30], CPU_MEM_TIME_MASK)
        interval_time = (curr_time - prev_time)
        prev_time = curr_time

        results.append(interval_time.total_seconds())

    return results


# Parsing program initialization arguments. 
def parsingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("root_folder", help="Path to source folder.")
    parser.add_argument("output_file", help="Name of output file.")
    args = parser.parse_args()

    return os.path.normpath(args.root_folder), args.output_file

if __name__ == '__main__':

    #  Recovering arguments
    root_folder, filename = parsingArguments()
    root_path = f'{root_folder}/*/'

    #  Recovering type of load folders path
    load_paths = glob(root_path, recursive = True)

    #  Initiating result dict
    results = {}

    # Looping over different load folders
    for l in load_paths:
        load = l.split("/")[-2].split('_')[0]
        experiment_paths = glob(f'{l}/*/', recursive = True)
        
        # Looping over different interval experiments
        for e in experiment_paths:
            experiment = e.split("/")[-2]
            cpu_mem_paths = glob(f'{e}/*/*/*.txt', recursive = True)
            colunm_name = f"{load}_{experiment}"
            results[colunm_name] = []

            # Looping complete experiments folder
            for trace_path in cpu_mem_paths:
                with open(trace_path, 'r') as trace_f:
                    experiment_result = getIntervals(trace_f, colunm_name)
                    results[colunm_name] = results[colunm_name] + experiment_result

    # Getting as result lists and setting as colnms.
    columns_data = zip_longest(*results.values())

    # Open output file and writing results.
    with open(f'{filename}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(results.keys())
        writer.writerows(columns_data)