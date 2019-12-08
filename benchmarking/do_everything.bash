#! /usr/bin/bash

./auto_test.py

cp results/*client* ../../results/client/
cp results/*server* ../../results/server/

./summarizer.py ../../results/client/ ../../results/client_results.json
./summarizer.py ../../results/server/ ../../results/server_results.json

