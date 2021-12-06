# コマンドラインツールの解説

## ginza

`ginza`コマンドはコマンドライン引数で指定されたファイル(指定されない場合は標準入力)から一行を単位としてテキストを読み込み、解析結果を標準出力に[CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式で出力します。
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

## ginzame

`ginzame`コマンドでオープンソース形態素解析エンジン [MeCab](https://taku910.github.io/mecab/) の`mecab`コマンドに近い形式で解析結果を出力することができます。
`ginzame`コマンドは形態素解析処理のみをマルチプロセスで高速に実行します。
このコマンドと`mecab`の出力形式の相違点として、最終フィールド（発音）が常に`*`となること、
ginza の split_mode はデフォルトが `C` なので unidic 相当の単語分割を得るためには `-s A` を指定する必要があることに注意して下さい。
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

## OPTIONS
`ginza`コマンドでは以下のオプションを指定することができます。
`ginzame`コマンドでは `--split-mode` `--hash-comment` `output-path` `--use-normalized-form` `--parallel` オプションが利用可能です。

- `--model-path <string>`, `-b <string>`
    `spacy.language.Language` 形式の学習済みモデルが保存されたディレクトリを指定します。
    `--ensure-model` オプションと同時に指定することはできません。
- `--ensure-model <string>`, `-m <string>`
    ginza および spaCy が公開している学習済みモデル名を指定します。`--model-path` オプションと同時に指定することはできません。次の値のいずれかを指定できます。
        - `ja_ginza`, `ja_ginza_electra`
        - [spaCy Models & Languages](https://spacy.io/usage/models)で公開されている日本語以外を含む全ての言語のモデル (例: en_core_web_md)
    使用するモデルに応じて、事前に `pip install ja-ginza-electra` のようにパッケージをダウンロードする必要があります。
    `--model-path`, `--ensure-model` のどちらも指定されない場合には `ja_ginza_electra`、`ja_ginza` の順の優先度でロード可能なモデルを利用します。
- `--split-mode <string>`, `-s <string>`
     複合名詞の分割モードを指定します。モードは [sudachi](https://github.com/WorksApplications/Sudachi#the-modes-of-splitting) に準拠し、`A`、`B`、`C`のいずれかを指定できます。`ginza`コマンドのデフォルト値は `C`、`ginzame`コマンドのデフォルト値はMeCab UniDicに近い `A` です。
     `A`が分割が最も短く複合名詞が UniDic 短単位まで分割され、 `C` では固有名詞が抽出されます。`B` は二つの中間の単位に分割されます。
- `--hash-comment <string>`, `-c <string>`
    行頭が `#` から始まる行を解析対象とするかのモードを指定します。次の値のいずれかを指定できます。
        - `print`
            解析対象とはしないが、解析結果には入力をそのまま出力します。
        - `skip`
            解析対象とせず、解析結果にも出力しません。
        - `analyze`
            `#` から始まる行についても解析を行い、結果を出力します。ただし`-f json`が指定されている場合は `-c`の指定に依らず常に`analyze`が適用されます。
    デフォルト値は `print` です。
- `--output-path <string>`, `-o <string>`
    解析結果を出力するファイルのパスを指定します。指定しない場合には標準出力に解析結果が出力されます。
- `--output-format <string>`, `-f <string>`
    [解析結果のフォーマット](#出力形式の指定)を指定します。次の値のいずれかを指定できます。
        - `0`, `conllu`
        - `1`, `cabocha`
        - `2`, `mecab`
        - `3`, `json`
    デフォルト値は `conllu` です。
- `--require-gpu <int>`, `-g <int>`
    引数で指定されたgpu_idのGPUを使用して解析を行います。引数に-1を指定(デフォルト)するとCPUを使用します。ただし、[spaCyおよびcupyの制約](https://github.com/explosion/spaCy/issues/5507)から、`--require-gpu`は`--parallel`と同時に指定できません。
- `--use-normalized-form`, `-n`
    `-f conllu`のlemmaフィールドに [sudachi](https://github.com/WorksApplications/Sudachi#normalized-form) を使用するためのブールスイッチ。
- `--disable-sentencizer`, `-d`
    `ja_ginza`、 `ja_ginza_electra` モデル利用時に[disable_sentencizer](https://github.com/megagonlabs/ginza/blob/develop/ginza/disable_sentencizer.py)を有効化するブールスイッチ。
- `--parallel <int>`, `-p <int>`
    並列実行するプロセス数を指定します。0 を指定すると cpu コア数分のプロセスを起動します。デフォルト値は1です。

## 出力形式の指定

### JSON

spaCyの学習用JSON形式での出力は`ginza -f 3` または `ginza -f json`を実行してください。
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

### CaboCha

日本語係り受け解析器 [CaboCha](https://taku910.github.io/cabocha/) の`cabocha -f1`のラティス形式に近い解析結果を出力する場合は
`ginza -f 1` または `ginza -f cabocha` を実行して下さい。
このオプションと`cabocha -f1`の出力形式の相違点として、
スラッシュ記号`/`に続く`func_index`フィールドが常に自立語の終了位置（機能語があればその開始位置に一致）を示すこと、
機能語認定基準が一部異なること、
に注意して下さい。
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

## マルチプロセス実行 (Experimental)

`-p NUM_PROCESS` オプションで解析処理のマルチプロセス実行が可能になります。
`NUM_PROCESS`には並列実行するプロセス数を整数で指定します。
0以下の値は`実行環境のCPUコア数＋NUM_PROCESS`を指定したのと等価になります。

`ginza -f mecab`とそのエイリアスである`ginzame`以外で`-p NUM_PROCESS`オプションを使用する場合は、
実行環境の空きメモリ容量が十分あることを事前に確認してください。
マルチプロセス実行では1プロセスあたり`ja_ginza`で数百MB、`ja_ginza_electra`で数GBのメモリが必要です。
