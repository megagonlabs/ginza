#!/bin/bash
seet -e
mkdir -p gsd
for t in train dev test ; do
  curl "https://raw.githubusercontent.com/megagonlabs/UD_Japanese-GSD/c614040872a74587912a15ef4637eabc0dc29a60/ja_gsd-ud-${t}.ne.conllu?raw=true" | grep "# text = " | sed 's/# text = //' > gsd/${t}.txt
done
echo
echo '=== CUDA Related Installation Steps ==='
echo 'The pytorch should be installed with cuda support. See https://pytorch.org/get-started/previous-versions/#linux-and-windows-1'
echo 'Also you need to install spacy with appropriate cuda specifier as `pip install -U spacy[cudaXXX]`. See https://spacy.io/usage#gpu'
echo 'And then, install GiNZA as `pip install -U ginza ja-ginza ja-ginza-electra`.'
