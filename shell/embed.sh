#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}
base_model_dir=models/${lang_name}_${model_name}
embed_corpus=corpus/embed/${model_name}
mkdir -p base_model_dir
python -m ginza_util.train_word2vec -l ${lang_name} -n ${model_name} -v ${model_version} ${@:3} -o ${base_model_dir} ${embed_corpus} &>> ${log}
