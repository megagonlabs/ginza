#!/usr/bin/env bash
mkdir target
set -eu
lang_name=ja_ginza
model_dir=${lang_name}_$1-$2
python -m spacy package --force models/${model_dir} target/
set +e
mkdir -p target/${model_dir}/spacy/lang/
set -e
touch target/${model_dir}/spacy/__init__.py
touch target/${model_dir}/spacy/lang/__init__.py
cp -r ${lang_name} target/${model_dir}/spacy/lang/
cp -r sudachipy target/${model_dir}/
python -m edit_setup_init target/${model_dir}/setup.py
cd target/${model_dir}/
python setup.py sdist
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/${model_dir}.tgz
rm -r target/${model_dir}
