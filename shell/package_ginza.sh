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

cd ${target_dir}/
python setup.py sdist bdist_wheel
cd ../../
mv target/${model_dir}/dist/${model_dir}.tar.gz target/
rm -r target/${model_dir}

dict_package=${lang_name}_ginza_dict
mkdir target/${dict_package}
cp -r ${dict_package} target/${dict_package}/
cp setup_dict.py target/${dict_package}/setup.py
cd target/${dict_package}/
rm ${dict_package}/sudachidict/system.dic
touch ${dict_package}/sudachidict/system.dic
python setup.py sdist bdist_wheel
cd ../../
mv target/${dict_package}/dist/${dict_package}*.tar.gz target/
rm -r target/${dict_package}

python setup.py sdist bdist_wheel
