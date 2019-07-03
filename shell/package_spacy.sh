#!/usr/bin/env bash
mkdir target
set -eu
lang_name=ja
model_dir=${lang_name}_core_web_md-$1
python -m spacy package ${@:2} --force models/${model_dir} target/
set -e
cp -r ginza sudachipy sudachidict target/${model_dir}/
python -m ginza_util.edit_setup_init_spacy target/${model_dir}/setup.py
cd target/${model_dir}/
python setup.py sdist
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/
rm -r target/${model_dir}
