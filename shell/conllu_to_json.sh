#!/usr/bin/env bash
set -eu
model_name=$1
log=log/log.convert_${model_name}
corpus_dir=corpus/${model_name}
if [[ -f ${corpus_dir}/*/*PN* ]]; then
  echo "ERROR: PN file exists"
  exit 1
fi
for t in train dev test
do
  python -m ginza_util.conllu_to_json ${corpus_dir}/${t}/ > ${corpus_dir}/${t}.json 2>> ${log}
done
