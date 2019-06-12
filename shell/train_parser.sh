#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}-${model_version}
corpus_dir=corpus/${model_name}
base_model_dir=models/${lang_name}_${model_name}
model_dir=${base_model_dir}-${model_version}
python -m spacy train ${lang_name} ${lang_name}_${model_name} \
    ${corpus_dir}/train.json \
    ${corpus_dir}/dev.json \
    -b ${base_model_dir} \
    -p tagger,parser \
    -pt dep,tag \
    -ne 5 \
    -V ${model_version} \
    -VV &>> ${log}
cp -r ${lang_name}_${model_name}/model-best ${model_dir}/

python -m ginza_util.evaluate_parser -b ${model_dir} ${@:3} -a ${corpus_dir}/test/ &>> ${log}
