#!/usr/bin/env bash
mkdir target
set -eu
lang_name=ja
model_dir=${lang_name}_$1-$2
python -m spacy package --force models/${model_dir} target/
set -e
cp -r ginza sudachipy target/${model_dir}/
python -m edit_setup_init target/${model_dir}/setup.py
cd target/${model_dir}/
python setup.py sdist
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/
rm -r target/${model_dir}
