#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}-${model_version}
corpus_dir=corpus/${model_name}
base_model_dir=models/${lang_name}_${model_name}
model_dir=${base_model_dir}-${model_version}
work_dir=temp/${lang_name}_${model_name}-${model_version}.`date +%Y%m%d%H%M`
python -m spacy train ${lang_name} ${work_dir} \
    ja_pud-ud-test.train.json \
    ja_pud-ud-test.test.json \
    -v ${base_model_dir} \
    -p tagger,parser,ner \
    -pt dep,tag \
    -et dep,tag \
    -ne 5 \
    -V ${model_version} \
    -VV
cp -r ${work_dir}/model-best ${model_dir}/
