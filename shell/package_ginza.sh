#!/usr/bin/env bash
mkdir target
set -eu
lang_name=ja
model_dir=${lang_name}_ginza-$1
target_dir=target/${lang_name}_ginza-$1
set -e
rm -rf ${target_dir}
set -eu
python -m spacy package ${@:2} --force models/${model_dir} target/

cp -r ${lang_name}_ginza/sudachidict/ ${target_dir}/${lang_name}_ginza/
rm ${target_dir}/${lang_name}_ginza/sudachidict/system.dic
touch ${target_dir}/${lang_name}_ginza/sudachidict/system.dic

python -m ginza_util.package_ginza_replacement ${target_dir}/setup.py
cd ${target_dir}/
python setup.py sdist bdist_wheel
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/
rm -r target/${model_dir}

cd ja_ginza
zip -r ../models/SudachiDict_core-20191224.zip sudachidict
cd ..

python setup.py sdist bdist_wheel
