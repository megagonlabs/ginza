# GiNZA NLP Library
![GiNZA logo](https://github.com/megagonlabs/ginza/releases/download/latest/GINZA_logo_4c_y.png)

An Open Source Japanese NLP Library, based on Universal Dependencies

***Please read [Important changes](#ginza-211) if you upgrade GiNZA to `v2.1.1`.***

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
We do not recommend to use Anaconda environment because the pip install step may not work properly.
(We'd like to support Anaconda in near future.)

Please also see the Development Environment section below.
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
$ pip install ginza-2.1.1.tar.gz
```

If you encountered some install problems related to Cython, please try to set the CFLAGS like below.
```bash
$ CFLAGS='-stdlib=libc++' pip install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
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
#### ginza-2.1.1
- 2019-10-03, Ametrine
- Important changes
  - `split_mode` has been set incorrectly to sudachipy.tokenizer from v2.0.0 (#43)
    - This bug caused `split_mode` incompatibility between the training phase and the `ginza` command.
    - `split_mode` was set to 'B' for training phase and python APIs, but 'C' for `ginza` command.
    - We fixed this bug by setting the default `split_mode` to 'C' entirely.
    - This fix may cause the word segmentation incompatibilities during upgrading GiNZA from v2.0.0 to v2.1.1.
- Performance improvements
  - Tokenizer
    - Use latest SudachiDict (SudachiDict_core-20190927.tar.gz) 
    - Use Cythonized SudachiPy (v0.4.0) 
  - Dependency parser
    - Apply `spacy pretrain` command to capture the language model from UD-Japanese BCCWJ, UD_Japanese-PUD and KWDLC.
    - Apply multitask objectives by using `-pt 'tag,dep'` option of `spacy train`
  - New model file
    - ja_ginza-2.1.1.tar.gz
#### ginza-2.0.0
- 2019-07-08
- Add `ginza` command
  - run `ginza` from the console
- Change package structure
  - module package as `ginza`
  - language model package as `ja_ginza`
  - `spacy.lang.ja` is overridden by `ginza`
- Remove `sudachipy` related directories
  - SudachiPy and its dictionary are installed via `pip` during `ginza` installation
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
#### ja_ginza_nopn-1.0.2
- 2019-04-07
- Set depending token index of root as 0 to meet with conllu format definitions
#### ja_ginza_nopn-1.0.1
- 2019-04-02
- Add new Japanese era 'reiwa' to system_core.dic.
#### ja_ginza_nopn-1.0.0
- 2019-04-01
- First release version

## Development Environment
### Development set up
#### 1. Clone from github
```bash
$ git clone 'https://github.com/megagonlabs/ginza.git'
```
#### 2. Run python setup.py
For normal environment:
```bash
$ python setup.sh develop
```
### Training
To be described
