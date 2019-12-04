#! /usr/bin/python3

import psutil
import sys
import pprint

pp = pprint.PrettyPrinter()

procs = []

for proc in psutil.process_iter():
    try:
        pinfo = proc.as_dict(attrs=['name', 'num_ctx_switches'])
        reduced = {
            "name": pinfo["name"],
            "voluntary_ctx_switches":pinfo['num_ctx_switches'][0]
        }

        procs.append(reduced)
    except psutil.NoSuchProcess:
        pass

procs.sort(key=lambda x: x["voluntary_ctx_switches"], reverse=True)
# pp.pprint(procs[0:10])

for p in procs[0:10]:
    print(p)