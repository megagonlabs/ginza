#!/bin/bash

set -e

corpus_dir=$1
corpus_title=$2

for s in dev test train; do
for n in 1 10 -15; do

if ((n == -15)); then
   file_n_sents=random_sents
else
   file_n_sents=$n
fi

python ginza_util/conllu_to_json.py -n $n -r C -e -a $corpus_dir/$corpus_title-$s.ne.conllu > $corpus_dir/$corpus_title-$s.ne.rea.$file_n_sents.json

done
done
