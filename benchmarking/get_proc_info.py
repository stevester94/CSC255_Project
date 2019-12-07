#! /usr/bin/python3

import psutil
import sys
import pprint
import time

pp = pprint.PrettyPrinter()

pids_first = {}
pids_last  = {}


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

def diff_and_sort_pids(first, last, duration):
    diffs = []

    for pid, val in last.items():
        try:
            diff = {}
            diff["name"] = val["name"]
            diff["voluntary_ctx_switches_difference_per_sec"] = (val["voluntary_ctx_switches"] - first[pid]["voluntary_ctx_switches"]) / duration

            diffs.append(diff)
        except:
            pass

    diffs.sort(key=lambda x: x["voluntary_ctx_switches_difference_per_sec"], reverse=True)

    return diffs[:5]


if __name__ == "__main__":

    if sys.argv[1] == "TEST": test()

    populate_pids_dict(pids_first)
    time.sleep(int(sys.argv[1]))
    populate_pids_dict(pids_last)

    # Get how many context switches ocurred for each pid

    muh_pids = diff_and_sort_pids(pids_first, pids_last)

# pp.pprint(procs[0:10])

    for p in muh_pids[0:10]:
        print(p)