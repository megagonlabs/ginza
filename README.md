# GiNZA
GiNZA - An Open Source Japanese NLP Library based on Universal Dependencies

[git repository](https://github.com/megagonlabs/ginza.git)

## License
GiNZA NLP Library is distributed under [The MIT License](https://github.com/megagonlabs/LICENSE)

### spaCy
spaCy is the key framework of GiNZA.
[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Sudachi and SudachiPy
SudachiPy provides high accuracies for tokenization and pos tagging.
[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt)
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt)

## Runtime Environment
This project is developed with ython 3.7 and pip for it.

The footprint of this project is about 250MB.
Sudachi dictionary is 200MB.
The word embeddings from entire Japanese Wikipedia is 50MB.

(Please see Development Environment section located on bottom too)
### Runtime set up
#### 1. Install GiNZA
Run following line
```
pip install ginza
```
or download pip install archive and specify it as below.
```
pip install ja_ginza_nopn-1.0.0.tar.gz
```
#### 2. Test
Run following line and input some Japanese text + Enter, then you can see the parsed results with conll format.
```
python -m spacy.lang.ja_ginza.cli
```
### Coding example
Following steps shows dependency parsing results with sentence boundary 'EOS'.
```
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.dep_, token.head.i)
    print('EOS')
```
### APIs
Please see [spaCy API documents](https://spacy.io/api/).
## Releases
### ja_ginza_nopn-1.0.0 (2019-04-01)
First release version

## Development Environment
### Development set up
#### 1. Clone from github
```
git clone --recursive 'https://github.com/megagonlabs/ginza.git'
```
#### 2. Run ./setup.sh
For normal environment:
```
./setup.sh
```
For GPU environment(cuda92):
```
./setup_cuda92.sh
```
### Training
Prepare nopn_embedding/, nopn/, and kwdlc/ in your project directory, then run below.
```
shell/build.sh nopn 1.0.1
```
You can speed up training and analyze process by adding -g option if GPUs available.

After a while, you will find pip installable archive.
```
target/ja_ginza_nopn-1.0.1.tgz
```
