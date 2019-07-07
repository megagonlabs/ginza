# GiNZA NLP Library
![GiNZA logo](images/GINZA_logo_4c_y.png)

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

(Please see Development Environment section located on bottom too)
### Runtime set up
#### 1. Install GiNZA NLP Library with Japanese Universal Dependencies Model
Run following line
```bash
$ pip install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
```
or download pip install archive from
[release page](https://github.com/megagonlabs/ginza/releases)
and run `pip install` with it.
```bash
$ pip install ginza-2.0.0.tar.gz
```
#### 2. Execute ginza from command line
Run `ginza` command from the console, then input some Japanese text.
After pressing enter key, you will get the parsed results with conllu format.
```bash
$ ginza
```
### Coding example
Following steps shows dependency parsing results with sentence boundary 'EOS'.
```python
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.i)
    print('EOS')
```
### APIs
Please see [spaCy API documents](https://spacy.io/api/).
## Releases
### version 2.0
#### ja_ginza-2.0.0 (2019-07-08)
- Add `ginza` command
  - run `ginza` from the console
- Change package structure
  - module package as `ginza`
  - language model package as `ja_ginza`
  - `spacy.lang.ja` is overridden by `ginza`
- Remove `sudachipy` related directories
  - SudachiPy and its dictionary are installed via `pip`
- User dictionary available
  - See [Customized dictionary - SudachiPy](https://github.com/WorksApplications/SudachiPy#customized-dictionary)
- Token extension fields
  - Added
    - `token._.bunsetu_bi_label`, `token._.bunsetu_position_type`
  - Remained
    - `token._.inf`
  - Removed
    - `pos_detail` (same value is set to `token.tag_`)
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
```bash
$ git clone --recursive 'https://github.com/megagonlabs/ginza.git'
```
#### 2. Run python setup.py
For normal environment:
```bash
$ python setup.sh develop
```
### Training
To be described
