# GiNZA NLP Library
An Open Source Japanese NLP Library, based on Universal Dependencies

## License
GiNZA NLP Library and GiNZA Japanese Universal Dependencies Models are distributed under
[The MIT License](https://github.com/megagonlabs/ginza/blob/master/LICENSE).
You must agree and follow The MIT License to use GiNZA NLP Library and GiNZA Japanese Universal Dependencies Models.

### spaCy
spaCy is the key framework of GiNZA.
[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Sudachi and SudachiPy
SudachiPy provides high accuracies for tokenization and pos tagging.
[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt),
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)

## Runtime Environment
This project is developed with Python>=3.6 and pip for it.

The footprint of this project is about 250MB.
Sudachi dictionary is 200MB.
The word embeddings from entire Japanese Wikipedia is 50MB.

(Please see Development Environment section located on bottom too)
### Runtime set up
#### 1. Install GiNZA NLP Library with Japanese Universal Dependencies Model
Run following line
```
pip install "https://github.com/megagonlabs/ginza/releases/download/v1.0.2/ja_ginza_nopn-1.0.2.tgz"
```
or download pip install archive from [release page](https://github.com/megagonlabs/ginza/releases) and
specify it as below.
```
pip install ja_ginza_nopn-1.0.2.tgz
```
#### 2. Test
Run following line and input some Japanese text + Enter, then you can see the parsed results with conllu format.
```
python -m spacy.lang.ja_ginza.cli
```
### Coding example
Following steps shows dependency parsing results with sentence boundary 'EOS'.
```
import spacy
nlp = spacy.load('ja_ginza_nopn')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.dep_, token.head.i)
    print('EOS')
```
### APIs
Please see [spaCy API documents](https://spacy.io/api/).
## Releases
### version 1.1
#### ja_ginza_nopn-1.1.0-alpha1 (2019-05-31)
- Add custom fields: Doc.\_.bunsetu_bi_label and Doc.\_.bunsetu_position_type
- Use new retokenize API (spaCy v2.1)
- Obsoleted: JapaneseCorrector.rewrite_ne_as_proper_noun
### version 1.0
#### ja_ginza_nopn-1.0.2 (2019-04-07)
- Set depending token index of root as 0 to meet with conllu format definitions
#### ja_ginza_nopn-1.0.1 (2019-04-02)
- Add new Japanese era 'reiwa' to system_core.dic.
#### ja_ginza_nopn-1.0.0 (2019-04-01)
- First release version

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
(We're preparing the descriptions of training environment. Coming soon.)
```
shell/build.sh nopn 1.0.2
```
You can speed up training and analyze process by adding -g option if GPUs available.

After a while, you will find pip installable archive.
```
target/ja_ginza_nopn-1.0.2.tgz
```
