# GiNZA NLP BETA
GiNZA - An Open Source NLP Library for Japanese Universal Dependencies using spaCy and SudachiPy

GiNZA is still beta version and pre-trained models are not included. We're almost ready to release a formal version with full features. Please keep waiting.

Please see [GiNZA NLP git repository](https://github.com/rit-git/ginza.git) too.

## Runtime Environment
This project is developed with python 3.6.8 (not python 3.7) and pip for it.

The footprint of this project is about 250MB.
Sudachi dictionary is 200MB.
The word embeddings from entire Japanese Wikipedia is 50MB.

(Please see Development Environment section located on bottom too)
### Runtime set up
#### 1. Download GiNZA pip archive
Coming soon!
#### 2. Install
```
pip install ja_ginza-x.x.x.tgz
```
And then, you can delete downloaded archive.
#### 3. Test
Run following line and input some Japanese text + Enter, then you can see the parsed results.
```
python -m spacy.lang.ja_ginza.cli
```
### Simple example
Following steps shows dependency parsing results with sentence boundary 'EOS'.
```
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.pos_, token.dep_, token.head.i)
    print('EOS')
```
### APIs
Please see [spaCy API documents](https://spacy.io/api/).
## Releases
### ja_ginza-0.5.0 (2019-03-13)
First beta version

## Development Environment
### Set up
#### 1. Clone from github
```
git clone 'https://github.com/rit-git/ginza.git'
```
#### 2. Download system.dic.tgz
Download the latest core-dictionary archive from below link and extract dic file as 'system.dic' on project root.

[Sudachi Release Page](https://github.com/WorksApplications/Sudachi/releases/download/v0.1.1/)
#### 3. Run setup.sh
```
./setup.sh
```
### Training
If you have embedding_corpus/ and ud_japanese/ in your project directory, run below.
```
shell/build.sh ginza 0.5.1 embedding_corpus/ ud_japanese/

```
After a while, you will find pip installable archive.
```
target/ja_ginza-0.5.1.tgz
```
