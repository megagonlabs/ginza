#!/bin/bash
set -e
cat gsd/dev.txt gsd/test.txt | python benchmark.py -g
cat gsd/dev.txt gsd/test.txt | python benchmark.py
