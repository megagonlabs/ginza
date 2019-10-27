# GiNZA NLP Library
![GiNZA logo](https://github.com/megagonlabs/ginza/releases/download/latest/GINZA_logo_4c_y.png)

An Open Source Japanese NLP Library, based on Universal Dependencies

***Please read the [Important changes](#ginza-220) before you upgrade GiNZA.***

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
This project is developed with Python>=3.6 and pip>=18 for it.
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
$ pip install ginza-2.2.1.tar.gz
```

If you encountered install error with the message like below, please upgrade `pip`.

```
Could not find a version that satisfies the requirement ja_ginza@ http://github.com/ ...  
```

```bash
$ pip install --upgrade pip
```

For Google Colab, you need to reload the package info. 
```python
import pkg_resources, imp
imp.reload(pkg_resources)
```

If you encountered some install problems related to Cython, please try to set the CFLAGS like below.
```bash
$ CFLAGS='-stdlib=libc++' pip install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
```
#### 2. Execute ginza from command line
Run `ginza` command from the console, then input some Japanese text.
After pressing enter key, you will get the parsed results with [CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) format.
```bash
$ ginza
銀座七丁目はお洒落だ。
# text = 銀座七丁目はお洒落だ。
1	銀座	銀座	PROPN	名詞-固有名詞-地名-一般	_	3	compound	_	BunsetuBILabel=B|BunsetuPositionType=CONT|SpaceAfter=No|NP_B|NE=LOC_B
2	七	7	NUM	名詞-数詞	NumType=Card	3	nummod	_	BunsetuBILabel=I|BunsetuPositionType=CONT|SpaceAfter=No|NE=LOC_I
3	丁目	丁目	NOUN	名詞-普通名詞-助数詞可能	_	5	nsubj	_	BunsetuBILabel=I|BunsetuPositionType=SEM_HEAD|SpaceAfter=No|NP_B|NE=LOC_I
4	は	は	ADP	助詞-係助詞	_	3	case	_	BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|SpaceAfter=No
5	お洒落	御洒落	ADJ	名詞-普通名詞-サ変形状詞可能	_	0	root	_	BunsetuBILabel=B|BunsetuPositionType=ROOT|SpaceAfter=No
6	だ	だ	AUX	助動詞	_	5	cop	_	BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|SpaceAfter=No
7	。	。	PUNCT	補助記号-句点	_	5	punct	_	BunsetuBILabel=I|BunsetuPositionType=CONT|SpaceAfter=No

```
If you want to use [`cabocha -f1`](https://taku910.github.io/cabocha/) (lattice style) like output, add `-f 1` or `-f cabocha` option to `ginza` command.
This option's format is almost same as `cabocha -f1` but the `func_index` field (after the slash) is slightly different.
Our `func_index` field indicates the boundary where the `自立語` ends in each `文節` (and the `機能語` might start from there).
And the functional token filter is also slightly different between `cabocha -f1` and ' `ginza -f cabocha`.
```bash
$ ginza -f 1
銀座七丁目はお洒落だ。
* 0 1D 2/3 0.000000
銀座	名詞,固有名詞,地名,一般,*,*,銀座,ギンザ,	B-LOC
七	名詞,数詞,*,*,*,*,7,ナナ,	I-LOC
丁目	名詞,普通名詞,助数詞可能,*,*,*,丁目,チョウメ,	I-LOC
は	助詞,係助詞,*,*,*,*,は,ハ,	O
* 1 -1D 0/1 0.000000
お洒落	名詞,普通名詞,サ変形状詞可能,*,*,*,御洒落,オシャレ,	O
だ	助動詞,*,*,*,助動詞-ダ,終止形-一般,だ,ダ,	O
。	補助記号,句点,*,*,*,*,。,。,	O
EOS
```
If you need only the tokenization results, please consider to use `sudachipy` command to speed up. Please see [SudachiPy](https://github.com/WorksApplications/SudachiPy/) for details. The SudachiPy is the tokenizer of GiNZA.
```bash
$ sudachipy
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
### version 2.x
### version 2.x
#### ginza-2.2.1
- 2019-10-28
- Improvements
  - JapaneseCorrector can merge the `as_*` type dependencies completely
- Bug fixes
  - command line tool failed at the specific situations

#### ginza-2.2.0
- 2019-10-04, Ametrine
- Important changes
  - `split_mode` has been set incorrectly to sudachipy.tokenizer from v2.0.0 (#43)
    - This bug caused `split_mode` incompatibility between the training phase and the `ginza` command.
    - `split_mode` was set to 'B' for training phase and python APIs, but 'C' for `ginza` command.
    - We fixed this bug by setting the default `split_mode` to 'C' entirely.
    - This fix may cause the word segmentation incompatibilities during upgrading GiNZA from v2.0.0 to v2.2.0.
- New features
  - Add `-f` and `--output-format` option to `ginza` command:
    - `-f 0` or `-f conllu` : [CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) format
    - `-f 1` or `-f cabocha`: [cabocha](https://taku910.github.io/cabocha/) -f1 compatible format
  - Add custom token fields:
    - `bunsetu_index` : bunsetu index starting from 0
    - `reading`: reading of token (not a pronunciation)
    - `sudachi`: SudachiPy's morpheme instance (or its list when then tokens are gathered by JapaneseCorrector)
- Performance improvements
  - Tokenizer
    - Use latest SudachiDict (SudachiDict_core-20190927.tar.gz) 
    - Use Cythonized SudachiPy (v0.4.0) 
  - Dependency parser
    - Apply `spacy pretrain` command to capture the language model from UD-Japanese BCCWJ, UD_Japanese-PUD and KWDLC.
    - Apply multitask objectives by using `-pt 'tag,dep'` option of `spacy train`
  - New model file
    - ja_ginza-2.2.0.tar.gz

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

### version 1.x
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
