#!/usr/bin/env bash
mkdir target
set -eu
lang_name=ja
model_dir=${lang_name}_ginza-$1
python -m ginza_util.edit_meta_json meta.json.ginza models/${model_dir}/meta.json
python -m spacy package ${@:2} -m models/${model_dir}/meta.json --force models/${model_dir} target/
set -e

cd target/${model_dir}/
python setup.py sdist
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/
rm -r target/${model_dir}
