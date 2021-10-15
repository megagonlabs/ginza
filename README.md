![GiNZA logo](https://github.com/megagonlabs/ginza/raw/static/docs/images/GiNZA_logo_4c_y.png)

# GiNZA NLP Library
[![Tweet](https://abs.twimg.com/favicons/favicon.ico)](https://twitter.com/intent/tweet?text=GiNZA%20-%20Japanese%20NLP%20Library%20https%3A%2F%2Fgithub.com%2Fmegagonlabs%2Fginza)
&emsp;
[![Downloads](https://pepy.tech/badge/ginza/week)](https://pepy.tech/project/ginza)

An Open Source Japanese NLP Library, based on Universal Dependencies

***Please read the [Important changes](#ginza-500) before you upgrade GiNZA.***

[日本語ページはこちら](https://megagonlabs.github.io/ginza/)

## License
GiNZA NLP Library and GiNZA Japanese Universal Dependencies Models are distributed under the
[MIT License](https://github.com/megagonlabs/ginza/blob/master/LICENSE).
You must agree and follow the MIT License to use GiNZA NLP Library and GiNZA Japanese Universal Dependencies Models.

### Explosion / spaCy
spaCy is the key framework of GiNZA.

[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Works Applications Enterprise / Sudachi/SudachiPy - SudachiDict - chiVe
SudachiPy provides high accuracies for tokenization and pos tagging.

[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt),
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE),
[SudachiDict LEGAL PAGE](https://github.com/WorksApplications/SudachiDict/blob/develop/LEGAL),
[chiVe LICENSE PAGE](https://github.com/WorksApplications/chiVe/blob/master/LICENSE)

### Hugging Face / transformers
The GiNZA v5 Transformers model (ja_ginza_electra) is trained by using Hugging Face Transformers as a framework for pretrained models.

[transformers LICENSE PAGE](https://github.com/huggingface/transformers/blob/master/LICENSE)

## Training Datasets

### UD Japanese BCCWJ v2.6
The parsing model of GiNZA v4 is trained on a part of
[UD Japanese BCCWJ](https://github.com/UniversalDependencies/UD_Japanese-BCCWJ) v2.6
([Omura and Asahara:2018](https://www.aclweb.org/anthology/W18-6014/)).
This model is developed by National Institute for Japanese Language and Linguistics, and Megagon Labs.

### GSK2014-A (2019) BCCWJ edition
The named entity recognition model of GiNZA v4 is trained on a part of
[GSK2014-A](https://www.gsk.or.jp/catalog/gsk2014-a/) (2019) BCCWJ edition
([Hashimoto, Inui, and Murakami:2008](https://www.anlp.jp/proceedings/annual_meeting/2010/pdf_dir/C4-4.pdf)).
We use two of the named entity label systems, both
[Sekine's Extended Named Entity Hierarchy](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)
and extended [OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf).
This model is developed by National Institute for Japanese Language and Linguistics, and Megagon Labs.

### mC4
The GiNZA v5 Transformers model (ja-ginza-electra) is trained by using [transformers-ud-japanese-electra-base-discriminator](https://huggingface.co/megagonlabs/transformers-ud-japanese-electra-base-discriminator) which is pretrained on more than 200 million Japanese sentences extracted from [mC4](https://huggingface.co/datasets/mc4).

Contains information from mC4 which is made available under the ODC Attribution License.
```
@article{2019t5,
    author = {Colin Raffel and Noam Shazeer and Adam Roberts and Katherine Lee and Sharan Narang and Michael Matena and Yanqi Zhou and Wei Li and Peter J. Liu},
    title = {Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer},
    journal = {arXiv e-prints},
    year = {2019},
    archivePrefix = {arXiv},
    eprint = {1910.10683},
}
```

## Runtime Environment
This project is developed with Python>=3.6 and pip for it.
We do not recommend to use Anaconda environment because the pip install step may not work properly.

Please also see the Development Environment section below.
### Runtime set up

#### 1. Install GiNZA NLP Library with Transformer-based Model
Uninstall previous version:
```console
$ pip uninstall ginza ja-ginza
```
Then, install the latest version of `ginza` and `ja-ginza-electra`:
```console
$ pip install -U ginza ja-ginza-electra
```

The package of `ja-ginza-electra` does not include `pytorch_model.bin` due to PyPI's archive size restrictions.
This large model file will be automatically downloaded at the first run time, and the locally cached file will be used for subsequent runs.

If you need to install `ja-ginza-electra` along with `pytorch_model.bin` at the install time, you can specify direct link for GitHub release archive as follows:
```console
$ pip install -U ginza https://github.com/megagonlabs/ginza/releases/download/latest/ja_ginza_electra-latest-with-model.tar.gz
```

If you hope to accelarate the transformers-based models by using GPUs with CUDA support, you can install `spacy` by specifying the CUDA version as follows:
```console
pip install -U "spacy[cuda110]"
```

#### 2. Install GiNZA NLP Library with Standard Model
Uninstall previous version:
```console
$ pip uninstall ginza ja-ginza
```
Then, install the latest version of `ginza` and `ja-ginza`:
```console
$ pip install -U ginza ja-ginza
```

### Execute ginza command
Run `ginza` command from the console, then input some Japanese text.
After pressing enter key, you will get the parsed results with [CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) format.
```console
$ ginza
銀座でランチをご一緒しましょう。
# text = 銀座でランチをご一緒しましょう。
1	銀座	銀座	PROPN	名詞-固有名詞-地名-一般	_	6	obl	_	SpaceAfter=No|BunsetuBILabel=B|BunsetuPositionType=SEM_HEAD|NP_B|Reading=ギンザ|NE=B-GPE|ENE=B-City
2	で	で	ADP	助詞-格助詞	_	1	case	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Reading=デ
3	ランチ	ランチ	NOUN	名詞-普通名詞-一般	_	6	obj	_	SpaceAfter=No|BunsetuBILabel=B|BunsetuPositionType=SEM_HEAD|NP_B|Reading=ランチ
4	を	を	ADP	助詞-格助詞	_	3	case	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Reading=ヲ
5	ご	ご	NOUN	接頭辞	_	6	compound	_	SpaceAfter=No|BunsetuBILabel=B|BunsetuPositionType=CONT|Reading=ゴ
6	一緒	一緒	VERB	名詞-普通名詞-サ変可能	_	0	root	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=ROOT|Reading=イッショ
7	し	する	AUX	動詞-非自立可能	_	6	aux	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Inf=サ行変格,連用形-一般|Reading=シ
8	ましょう	ます	AUX	助動詞	_	6	aux	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Inf=助動詞-マス,意志推量形|Reading=マショウ
9	。	。	PUNCT	補助記号-句点	_	6	punct	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=CONT|Reading=。

```
`ginzame` command provides tokenization function like [MeCab](https://taku910.github.io/mecab/).
The output format of `ginzame` is almost same as `mecab`, but the last `pronunciation` field is always '*'.
```console
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
The format of spaCy's JSON is available by specifying `-f 3` or `-f json` for `ginza` command.
```console
$ ginza -f json
銀座でランチをご一緒しましょう。
[
 {
  "paragraphs": [
   {
    "raw": "銀座でランチをご一緒しましょう。",
    "sentences": [
     {
      "tokens": [
       {"id": 1, "orth": "銀座", "tag": "名詞-固有名詞-地名-一般", "pos": "PROPN", "lemma": "銀座", "head": 5, "dep": "obl", "ner": "B-City"},
       {"id": 2, "orth": "で", "tag": "助詞-格助詞", "pos": "ADP", "lemma": "で", "head": -1, "dep": "case", "ner": "O"},
       {"id": 3, "orth": "ランチ", "tag": "名詞-普通名詞-一般", "pos": "NOUN", "lemma": "ランチ", "head": 3, "dep": "obj", "ner": "O"},
       {"id": 4, "orth": "を", "tag": "助詞-格助詞", "pos": "ADP", "lemma": "を", "head": -1, "dep": "case", "ner": "O"},
       {"id": 5, "orth": "ご", "tag": "接頭辞", "pos": "NOUN", "lemma": "ご", "head": 1, "dep": "compound", "ner": "O"},
       {"id": 6, "orth": "一緒", "tag": "名詞-普通名詞-サ変可能", "pos": "VERB", "lemma": "一緒", "head": 0, "dep": "ROOT", "ner": "O"},
       {"id": 7, "orth": "し", "tag": "動詞-非自立可能", "pos": "AUX", "lemma": "する", "head": -1, "dep": "advcl", "ner": "O"},
       {"id": 8, "orth": "ましょう", "tag": "助動詞", "pos": "AUX", "lemma": "ます", "head": -2, "dep": "aux", "ner": "O"},
       {"id": 9, "orth": "。", "tag": "補助記号-句点", "pos": "PUNCT", "lemma": "。", "head": -3, "dep": "punct", "ner": "O"}
      ]
     }
    ]
   }
  ]
 }
]
```
If you want to use [`cabocha -f1`](https://taku910.github.io/cabocha/) (lattice style) like output, add `-f 1` or `-f cabocha` option to `ginza` command.
This option's format is almost same as `cabocha -f1` but the `func_index` field (after the slash) is slightly different.
Our `func_index` field indicates the boundary where the `自立語` ends in each `文節` (and the `機能語` might start from there).
And the functional token filter is also slightly different between `cabocha -f1` and ' `ginza -f cabocha`.
```console
$ ginza -f cabocha
銀座でランチをご一緒しましょう。
* 0 2D 0/1 0.000000
銀座	名詞,固有名詞,地名,一般,,銀座,ギンザ,*	B-City
で	助詞,格助詞,*,*,,で,デ,*	O
* 1 2D 0/1 0.000000
ランチ	名詞,普通名詞,一般,*,,ランチ,ランチ,*	O
を	助詞,格助詞,*,*,,を,ヲ,*	O
* 2 -1D 0/2 0.000000
ご	接頭辞,*,*,*,,ご,ゴ,*	O
一緒	名詞,普通名詞,サ変可能,*,,一緒,イッショ,*	O
し	動詞,非自立可能,*,*,サ行変格,連用形-一般,する,シ,*	O
ましょう	助動詞,*,*,*,助動詞-マス,意志推量形,ます,マショウ,*	O
。	補助記号,句点,*,*,,。,。,*	O
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
nlp = spacy.load('ja_ginza_electra')
doc = nlp('銀座でランチをご一緒しましょう。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.i)
    print('EOS')
```

### User Dictionary
The user dictionary files should be set to `userDict` field of `sudachi.json` in the installed package directory of`ja_ginza_dict` package.

Please read the official documents to compile user dictionaries with `sudachipy` command.  
[SudachiPy - User defined Dictionary](https://github.com/WorksApplications/SudachiPy#user-defined-dictionary)  
[Sudachi User Dictionary Construction (Japanese Only)](https://github.com/WorksApplications/Sudachi/blob/develop/docs/user_dict.md)

## Releases

### version 5.x

#### ginza-5.0.3
- 2021-10-15
- Bug fix
  - `Bunsetu span should not cross the sentence boundary` #195

#### ginza-5.0.2
- 2021-09-06
- Bug fix
  - `Command Line -s option and set_split_mode() not working in v5.0.x` #185

#### ginza-5.0.1
- 2021-08-26
- Bug fix
  - `ginzame not woriking in ginza ver. 5` #179
  - `Command Line -d option not working in v5.0.0` #178
- Improvement
  - accept `ja-ginza` and `ja-ginza-electra` for `-m` option of `ginza` command

#### ginza-5.0.0
- 2021-08-26, Demantoid
- Important changes
  - Upgrade spaCy to v3
    - Release transformer-based `ja-ginza-electra` model
    - Improve UPOS accuracy of the standard `ja-ginza` model by adding `morphologizer` to the tail of spaCy pipleline
  - Need to insrtall analysis model along with `ginza` package
    - High accuracy model (>=16GB memory needed)
      - `pip install -U ginza ja-ginza-electra`
    - Speed oriented model
      - `pip install -U ginza ja-ginza`
  - Change component names of `CompoundSplitter` and `BunsetuRecognizer` to `compound_splitter` and `bunsetu_recognizer` respectively
  - Also see [spaCy v3 Backwards Incompatibilities](https://spacy.io/usage/v3#incompat)
- Improvements
  - Add command line options
    - `-n`
      - Force using SudachiPy's `normalized_form` as `Token.lemma_`
    - `-m (ja_ginza|ja_ginza_electra)`
      - Select model package
  - Revise ENE category name
    - `Degital_Game` to `Digital_Game`

### version 4.x

#### ginza-4.0.6
- 2021-06-01
- Bug fix
  - Issue #160: IndexError: list assignment index out of range for empty string

#### ginza-4.0.5
- 2020-10-01
- Improvements
  - Add `-d` option, which disables spaCy's sentence separator, to `ginza` command line tool

#### ginza-4.0.4
- 2020-09-11
- Improvements
  - `ginza` command line tool works correctly without BunsetuRecognizer in the pipeline

#### ginza-4.0.3
- 2020-09-10
- Improve bunsetu head identification accuracy over inconsistent deps in ent spans

#### ginza-4.0.2
- 2020-09-04
- Improvements
  - Serialization of `CompoundSplitter` for `nlp.to_disk()`
  - Bunsetu span detection accuracy

#### ginza-4.0.1
- 2020-08-30
- Debug
  - Add type arguments for singledispatch register annotations (for Python 3.6)

#### ginza-4.0.0
- 2020-08-16, Chrysoberyl
- Important changes
  - Replace Japanese model with `spacy.lang.ja` of spaCy v2.3
    - Replace values of `Token.lemma_` with the output of SudachiPy's `Morpheme.dictionary_form()`
  - Replace ja_ginza_dict with official SudachiDict-core package
    - You can delete`ja_ginza_dict` package safety
  - Change options and misc field contents of output of command line tool
    - delete use_sentence_separator(-s)
    - NE(OntoNotes) BI labels as `B-GPE`
    - Add subfields: Reading, Inf(inflection) and ENE(Extended NE)
  - Obsolete `Token._.*` and add some entries for `Doc.user_data[]` and accessors
    - inflections (`ginza.inflection(Token)`)
    - reading_forms (`ginza.reading_form(Token)`)
    - bunsetu_bi_labels (`ginza.bunsetu_bi_label(Token)`)
    - bunsetu_position_types (`ginza.bunsetu_position_type(Token)`)
    - bunsetu_heads (`ginza.is_bunsetu_head(Token)`)
  - Change pipeline architecture
    - JapaneseCorrector was obsoleted
    - Add CompoundSplitter and BunsetuRecognizer
  - Upgrade UD_JAPANESE-BCCWJ to v2.6
  - Change word2vec to chiVe mc90
- API Changes
  - Add bunsetu-unit APIs (`from ginza import *`)
    - bunsetu(Token)
    - phrase(Token)
    - sub_phrases(Token)
    - phrases(Span)
    - bunsetu_spans(Span)
    - bunsetu_phrase_spans(Span)
    - bunsetu_head_list(Span)
    - bunsetu_head_tokens(Span)
    - bunsetu_bi_labels(Span)
    - bunsetu_position_types(Span)


### version 3.x

#### ginza-3.1.2
- 2020-02-12
- Debug
  - Fix: degrade of cabocha mode

#### ginza-3.1.1
- 2020-01-19
- API Changes
  - Extension fields
    - The values of ``Token._.sudachi`` field would be set after calling ``SudachipyTokenizer.set_enable_ex_sudachi(True)``, to avoid serializtion errors
```python
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
- 2020-01-15, Benitoite
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
```console
$ git clone 'https://github.com/megagonlabs/ginza.git'
```

#### 2. Run python setup.py
For normal environment:
```console
$ python setup.py develop
```

### 3. Set up system.dic
Copy `system.dic` from installed package directory of `ja_ginza_dict` to `./ja_ginza_dict/sudachidict/`.

### Training models
The analysis model of GiNZA is trained by `spacy train` command.
```console
$ python -m spacy train ja ja_ginza-4.0.0 corpus/ja_ginza-ud-train.json corpus/ja_ginza-ud-dev.json -b ja_vectors_chive_mc90_35k/ -ovl 0.3 -n 100 -m meta.json.ginza -V 4.0.0
```
