#!/usr/bin/env bash
set -eu
pip install -r requirements.txt
wget https://github.com/WorksApplications/Sudachi/releases/download/v0.1.1/sudachi-0.1.1-dictionary-core.zip -O dic.zip
unzip -o dic.zip
mv system_core.dic ja_ginza/resources/
rm dic.zip
