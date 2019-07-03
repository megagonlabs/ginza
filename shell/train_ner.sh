#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}-${model_version}
corpus_dir=corpus/kwdlc
model_dir=models/${lang_name}_${model_name}-${model_version}
python -m ginza_util.train_ner       -b ${model_dir} ${@:3} -e ${corpus_dir}/dev/ ${corpus_dir}/train/ &>> ${log}
python -m ginza_util.evaluate_ner    -b ${model_dir} ${@:3}                       ${corpus_dir}/test/  &>> ${log}
