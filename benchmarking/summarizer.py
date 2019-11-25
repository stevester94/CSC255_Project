#! /usr/bin/python3

import copy
import paramiko
import pprint
import time
import socket
import os
import json
import results_processor
import sys 
from os import listdir
from os.path import isfile, join

pp = pprint.PrettyPrinter()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: <path with JSON> <output name | PRINT >" )
        print("Will scan directory for json test results and build a summary")
        print("Passing PRINT as second arg will only print the summaries")
        sys.exit(1)
    
    path = sys.argv[1]
    out  = sys.argv[2]

    
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]

    result_files = [f for f in onlyfiles if ".json" in f]

    print(result_files)


    summaries = []
    for f in result_files:
        name = f[:-5]
        print(name)

        results = results_processor.get_summary(path+"/"+f)
        results["Test Name"] = name
        summaries.append(results)

    pp.pprint(summaries)

    if out != "PRINT":
        with open(out, "w") as out_file:
            out_file.write(json.dumps(summaries, indent=4))



