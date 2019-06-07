#!/usr/bin/env bash
set -eu
lang_name=ja
model_name=$1
model_version=$2
log=log/log.${model_name}-${model_version}
parser_corpus=corpus/${model_name}/parser
if [[ -f ${parser_corpus}/*/*PN* ]]; then
  echo "ERROR: PN file exists"
  exit 1
fi
ner_corpus=corpus/kwdlc
model_dir=models/${lang_name}_${model_name}-${model_version}
python -m ginza_util.train_parser    -b ${model_dir} ${@:3} -e ${parser_corpus}/dev/ ${parser_corpus}/train/ &>> $log
python -m ginza_util.evaluate_parser -b ${model_dir} ${@:3} -a ${parser_corpus}/test/ &>> $log
python -m ginza_util.train_ner       -b ${model_dir} ${@:3} -e ${ner_corpus}/dev/ ${ner_corpus}/train/ &>> $log
python -m ginza_util.evaluate_ner    -b ${model_dir} ${@:3} ${ner_corpus}/test/ &>> $log
./shell/package.sh ${model_name} ${model_version} &>> $log
