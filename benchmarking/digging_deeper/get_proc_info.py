#! /usr/bin/python3

import psutil
import sys
import pprint
import time

pp = pprint.PrettyPrinter()

pids_first = {}
pids_last  = {}

diffs = []

def populate_pids_dict(d):
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'num_ctx_switches'])
            reduced = {
                "name": pinfo["name"],
                "voluntary_ctx_switches":pinfo['num_ctx_switches'][0]
            }

            d[pinfo["pid"]] = reduced
        except psutil.NoSuchProcess:
            pass


def test():
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict()
            if "openvpn" in pinfo["name"]:
                pp.pprint(pinfo)    
        except:
            pass
    sys.exit(0)

if __name__ == "__main__":

    if sys.argv[1] == "TEST": test()

    populate_pids_dict(pids_first)
    time.sleep(int(sys.argv[1]))
    populate_pids_dict(pids_last)

    # Get how many context switches ocurred for each pid
    for pid, val in pids_last.items():
        try:
            diff = {}
            diff["name"] = val["name"]
            diff["voluntary_ctx_switches_difference_per_sec"] = (val["voluntary_ctx_switches"] - pids_first[pid]["voluntary_ctx_switches"]) / int(sys.argv[1])

            diffs.append(diff)
        except:
            pass

diffs.sort(key=lambda x: x["voluntary_ctx_switches_difference_per_sec"], reverse=True)
# pp.pprint(procs[0:10])

for p in diffs[0:10]:
    print(p)