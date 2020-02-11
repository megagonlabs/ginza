# GiNZA NLP Library
![GiNZA logo](https://github.com/megagonlabs/ginza/raw/static/docs/images/GiNZA_logo_4c_y.png)

An Open Source Japanese NLP Library, based on Universal Dependencies

***Please read the [Important changes](#ginza-300) before you upgrade GiNZA.***

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

## Training Data-sets

### UD Japanese BCCWJ v2.4
The parsing model of GiNZA v3 is trained on a part of
[UD Japanese BCCWJ](https://github.com/UniversalDependencies/UD_Japanese-BCCWJ) v2.4
([Omura and Asahara:2018](https://www.aclweb.org/anthology/W18-6014/)).
This model is developed by National Institute for Japanese Language and Linguistics, and Megagon Labs.

### GSK2014-A (2019) BCCWJ edition
The named entity recognition model of GiNZA v3 is trained on a part of
[GSK2014-A](https://www.gsk.or.jp/catalog/gsk2014-a/) (2019) BCCWJ edition
([Hashimoto, Inui, and Murakami:2008](https://www.anlp.jp/proceedings/annual_meeting/2010/pdf_dir/C4-4.pdf)).
We use two of the named entity label systems, both
[Sekine's Extended Named Entity Hierarchy](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)
and extended [OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf).
This model is developed by National Institute for Japanese Language and Linguistics, and Megagon Labs.


## Runtime Environment
This project is developed with Python>=3.6 and pip for it.
We do not recommend to use Anaconda environment because the pip install step may not work properly.
(We'd like to support Anaconda in near future.)

Please also see the Development Environment section below.
### Runtime set up
#### 1. Install GiNZA NLP Library with Japanese Universal Dependencies Model
Run following line
```bash
$ pip install -U ginza
```
or download pip install archive from
[release page](https://github.com/megagonlabs/ginza/releases)
and run `pip install` with it.
```bash
$ pip install ginza-3.1.2.tar.gz
```
If you found a error message, `ValueError: cannot mmap an empty file` from `ginza` command,
please execute following step once to initialize `ja_ginza_dict` package.
```bash
$ ginza -i
```

For Google Colab, you need to reload the package info. 
```python
import pkg_resources, imp
imp.reload(pkg_resources)
```

If you encountered some install problems related to Cython, please try to set the CFLAGS like below.
```bash
$ CFLAGS='-stdlib=libc++' pip install ginza
```

#### 2. Execute ginza from command line
Run `ginza` command from the console, then input some Japanese text.
After pressing enter key, you will get the parsed results with [CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) format.
```bash
$ ginza
銀座でランチをご一緒しましょう。
# text = 銀座でランチをご一緒しましょう。
1	銀座	銀座	PROPN	名詞-固有名詞-地名-一般	_	6	compound	_	BunsetuBILabel=B|BunsetuPositionType=SEM_HEAD|SpaceAfter=No|NP_B|ENE7=B_City|NE=B_GPE
2	で	で	ADP	助詞-格助詞	_	1	case	_	BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|SpaceAfter=No
3	ランチ	ランチ	NOUN	名詞-普通名詞-一般	_	6	obj	_	BunsetuBILabel=B|BunsetuPositionType=SEM_HEAD|SpaceAfter=No|NP_B
4	を	を	ADP	助詞-格助詞	_	3	case	_	BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|SpaceAfter=No
5	ご	御	NOUN	接頭辞	_	6	compound	_	BunsetuBILabel=B|BunsetuPositionType=CONT|SpaceAfter=No|NP_B
6	一緒	一緒	VERB	名詞-普通名詞-サ変可能	_	0	root	_	BunsetuBILabel=I|BunsetuPositionType=ROOT|SpaceAfter=No
7	し	為る	AUX	動詞-非自立可能	_	6	aux	_	BunsetuBILabel=I|BunsetuPositionType=FUNC|SpaceAfter=No
8	ましょう	ます	AUX	助動詞	_	6	aux	_	BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|SpaceAfter=No
9	。	。	PUNCT	補助記号-句点	_	6	punct	_	BunsetuBILabel=I|BunsetuPositionType=CONT|SpaceAfter=No

```
`ginzame` command provides tokenization function like [MeCab](https://taku910.github.io/mecab/).
The output format of `ginzame` is almost same as `mecab`, but the last `pronounciation` field is always '*'.
```bash
$ ginzame
銀座でランチをご一緒しましょう。
銀座	名詞,固有名詞,地名,一般,*,*,銀座,ギンザ,*
で	助詞,格助詞,*,*,*,*,で,デ,*
ランチ	名詞,普通名詞,一般,*,*,*,ランチ,ランチ,*
を	助詞,格助詞,*,*,*,*,を,ヲ,*
ご	接頭辞,*,*,*,*,*,御,ゴ,*
一緒	名詞,普通名詞,サ変可能,*,*,*,一緒,イッショ,*
し	動詞,非自立可能,*,*,サ行変格,連用形-一般,為る,シ,*
ましょう	助動詞,*,*,*,助動詞-マス,意志推量形,ます,マショウ,*
。	補助記号,句点,*,*,*,*,。,。,*
EOS

```
If you want to use [`cabocha -f1`](https://taku910.github.io/cabocha/) (lattice style) like output, add `-f 1` or `-f cabocha` option to `ginza` command.
This option's format is almost same as `cabocha -f1` but the `func_index` field (after the slash) is slightly different.
Our `func_index` field indicates the boundary where the `自立語` ends in each `文節` (and the `機能語` might start from there).
And the functional token filter is also slightly different between `cabocha -f1` and ' `ginza -f cabocha`.
```bash
$ ginza -f 1
銀座でランチをご一緒しましょう。
* 0 2D 0/1 0.000000
銀座	名詞,固有名詞,地名,一般,*,*,銀座,ギンザ,*	B-City
で	助詞,格助詞,*,*,*,*,で,デ,*	O
* 1 2D 0/1 0.000000
ランチ	名詞,普通名詞,一般,*,*,*,ランチ,ランチ,*	O
を	助詞,格助詞,*,*,*,*,を,ヲ,*	O
* 2 -1D 0/2 0.000000
ご	接頭辞,*,*,*,*,*,御,ゴ,*	O
一緒	名詞,普通名詞,サ変可能,*,*,*,一緒,イッショ,*	O
し	動詞,非自立可能,*,*,サ行変格,連用形-一般,為る,シ,*	O
ましょう	助動詞,*,*,*,助動詞-マス,意志推量形,ます,マショウ,*	O
。	補助記号,句点,*,*,*,*,。,。,*	O
EOS

```
### Multi-processing (Experimental)
We added `-p NUM_PROCESS` option from GiNZA v3.0.
Please specify the number of analyzing processes to `NUM_PROCESS`.
You might want to use all the cpu cores for GiNZA, then execute `ginza -p 0`.
The memory requirement is about 130MB/process (to be improved).

### Coding example
Following steps shows dependency parsing results with sentence boundary 'EOS'.
```python
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('銀座でランチをご一緒しましょう。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.i)
    print('EOS')
```

### APIs
Please see [spaCy API documents](https://spacy.io/api/) for general analyzing functions.
Or please refer the source codes of GiNZA on github until we'd write the documents.

### User Dictionary
The user dictionary files should be set to `userDict` field of `sudachi.json` in the installed package directory of`ja_ginza_dict` package.
The `sudachi.json` is located at below path.  
`${python_library_path}/ja_ginza_dict/sudachidict/sudachi.json`

Please read the official documents to compile user dictionaries with `sudachipy` command.  
[SudachiPy - User defined Dictionary](https://github.com/WorksApplications/SudachiPy#user-defined-dictionary)  
[Sudachi ユーザー辞書作成方法 (Japanese Only)](https://github.com/WorksApplications/Sudachi/blob/develop/docs/user_dict.md)

## Releases
### version 3.x

#### ginza-3.1.2
- 2020-02-12
- Debug
  - Fix: degrade of cabocha mode

#### ginza-3.1.1
- 2020-01-19
- API Changes
  - Extension fields
    - The values of Token._.sudachi field would be set after calling SudachipyTokenizer.enable_ex_sudachi(True), to avoid serializtion errors
```
import spacy
import pickle
nlp = spacy.load('ja_ginza')
doc1 = nlp('This example will be serialized correctly.')
doc1.to_bytes()
with open('sample1.pickle', 'wb') as f:
    pickle.dump(doc1, f)

nlp.tokenizer.set_enable_ex_sudachi(True)
doc2 = nlp('This example will cause a serialization error.')
doc2.to_bytes()
with open('sample2.pickle', 'wb') as f:
    pickle.dump(doc2, f)
```

#### ginza-3.1.0
- 2020-01-16
- Important changes
  - Distribute `ja_ginza_dict` from PyPI
- API Changes
  - commands
    - `ginza` and `ginzame`
      - add `-i` option to initialize the files of `ja_ginza_dict`

#### ginza-3.0.0
- 2020-01-15
- Important changes
  - Distribute `ginza` and `ja_ginza` from PyPI
    - Simple installation; `pip install ginza`, and run `ginza`
    - The model package, `ja_ginza`, is also available from PyPI.
  - Model improvements
    - Change NER training data-set to GSK2014-A (2019) BCCWJ edition
      - Improved accuracy of NER
      - `token.ent_type_` value is changed to [Sekine's Extended Named Entity Hierarchy](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)
        - Add `ENE7` attribute to the last field of the output of `ginza`
      - Move [OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf) -based label to `token._.ne`
        - We extended the OntoNotes5 named entity labels with `PHONE`, `EMAIL`, `URL`, and `PET_NAME`
    - Overall accuracy is improved by executing `spacy pretrain` over 100 epochs
      - Multi-task learning of `spacy train` effectively working on UD Japanese BCCWJ
    - The newest `SudachiDict_core-20191224`
  - `ginzame`
    - Execute `sudachipy` by `multiprocessing.Pool` and output results with `mecab` like format
    - Now `sudachipy` command requires additional SudachiDict package installation
- Breaking API Changes
  - commands
    - `ginza` (`ginza.command_line.main_ginza`)
      - change option `mode` to `sudachipy_mode`
      - drop options: `disable_pipes` and `recreate_corrector`
      - add options: `hash_comment`, `parallel`, `files`
      - add `mecab` to the choices for the argument of `-f` option
      - add `parallel NUM_PROCESS` option (EXPERIMENTAL)
      - add `ENE7` attribute to conllu miscellaneous field
        - `ginza.ent_type_mapping.ENE_NE_MAPPING` is used to convert `ENE7` label to `NE`
    - add `ginzame` (`ginza.command_line.main_ginzame`)
      - a multi-process tokenizer providing `mecab` like output format
  - spaCy field extensions
    - add `token._.ne` for ner label
  - `ginza/sudachipy_tokenizer.py`
    - change `SudachiTokenizer` to `SudachipyTokenizer`
    - use `SUDACHI_DEFAULT_SPLIT_MODE` instead of `SUDACHI_DEFAULT_SPLITMODE` or `SUDACHI_DEFAULT_MODE`
- Dependencies
  - upgrade `spacy` to v2.2.3
  - upgrade `sudachipy` to v0.4.2

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

### 3. Set up system.dic
Copy `system.dic` from installed package directory of `ja_ginza_dict` to `./ja_ginza_dict/sudachidict/`.

### Training models
The script below is used to train `ja_ginza` models.
[shell/train_pipeline.sh](https://github.com/megagonlabs/ginza/blob/develop/shell/train_pipeline.sh)
