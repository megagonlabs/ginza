#!/usr/bin/env bash
set -eu
lang_name=ja_ginza
model_name=$1
model_version=$2
log=log.$1-$2
parser_corpus=nopn/sr
ner_corpus=kwdlc
model_dir=models/${lang_name}_${model_name}-${model_version}
python -m ja_ginza.train_parser    -b ${model_dir} ${@:3} -e ${parser_corpus}/dev/ ${parser_corpus}/train/ &>> $log
python -m ja_ginza.evaluate_parser -b ${model_dir} ${@:3} -a ${parser_corpus}/test/ &>> $log
python -m ja_ginza.train_ner       -b ${model_dir} ${@:3} -e ${ner_corpus}/dev/ ${ner_corpus}/train/ &>> $log
python -m ja_ginza.evaluate_ner    -b ${model_dir} ${@:3} ${ner_corpus}/test/ &>> $log
./shell/package.sh ${model_name} ${model_version} &>> $log
