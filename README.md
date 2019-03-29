# GiNZA NLP BETA
GiNZA - An Open Source NLP Library for Japanese Universal Dependencies using spaCy and SudachiPy

GiNZA is still beta version and pre-trained models are not included. We're almost ready to release a formal version with full features. Please keep waiting.

Please see [GiNZA NLP git repository](https://github.com/megagonlabs/ginza.git) too.

## License
GiNZA NLP Library is distributed under the MIT License

### spaCy
spaCy is the key framework of GiNZA.
[LICENSE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Sudachi and SudachiPy
SudachiPy gains much accuracy for Japanese Universal Dependency analysis tasks.
[LICENSE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt)

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
pip install ja_ginza_bccwj-x.x.x.tgz
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
### ja_ginza-0.5.2 (2019-03-22)
Second beta version
### ja_ginza-0.5.0 (2019-03-13)
First beta version

## Development Environment
### Set up
#### 1. Clone from github
```
git clone 'https://github.com/rit-git/ginza.git'
```
#### 2. Run setup.sh
```
./setup.sh
```
### Training
If you have embedding/, bccwj_ud/, and kwdlc/ in your project directory, run below.
```
shell/build.sh bccwj 0.5.3
```
After a while, you will find pip installable archive.
```
target/ja_ginza-0.5.3.tgz
```
