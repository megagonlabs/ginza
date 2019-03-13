#!/usr/bin/env bash
mkdir models
./shell/embed.sh $@
./shell/train.sh $@
