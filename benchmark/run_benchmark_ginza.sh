#!/bin/bash
cat gsd/dev.txt gsd/test.txt | python benchmark.py -g ja_ginza ja_ginza_electra
cat gsd/dev.txt gsd/test.txt | python benchmark.py ja_ginza ja_ginza_electra
