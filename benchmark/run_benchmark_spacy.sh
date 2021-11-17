#!/bin/bash
set -e
cat gsd/dev.txt gsd/test.txt | python benchmark.py -g ja_core_news_md ja_core_news_trf
cat gsd/dev.txt gsd/test.txt | python benchmark.py ja_core_news_md ja_core_news_trf
