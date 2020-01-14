#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
pretrain_model=$3
log=log/log.${model_name}-${model_version}
corpus_dir=corpus/${model_name}
base_model_dir=models/${lang_name}_${model_name}
model_dir=${base_model_dir}-${model_version}
work_dir=temp/${lang_name}_${model_name}-${model_version}.`date +%Y%m%d%H%M`
python -m spacy train ${lang_name} ${work_dir} \
    ${corpus_dir}/train.json \
    ${corpus_dir}/dev.json \
    -v ${base_model_dir} \
    -t2v ${pretrain_model} \
    -G \
    -p 'parser,ner' \
    -pt dep \
    -et dep \
    -ovl 0.2 \
    -n 100 \
    -ne 10 \
    -m ./meta.json.ginza \
    -V ${model_version}
cp -r ${work_dir}/model-best ${model_dir}/
