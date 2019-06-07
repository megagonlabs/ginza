#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}-${model_version}
model_dir=models/${lang_name}_${model_name}-${model_version}
embed_corpus=corpus/${model_name}/embed
mkdir -p model_dir
python -m ginza_util.train_word2vec -n ${model_name} -v ${model_version} ${@:3} -o models/ ${embed_corus} &>> $log
