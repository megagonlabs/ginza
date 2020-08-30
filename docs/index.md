![GiNZA logo](https://github.com/megagonlabs/ginza/raw/static/docs/images/GiNZA_logo_4c_y.png)
# GiNZAの公開ページ
[![Tweet](https://abs.twimg.com/favicons/favicon.ico)](https://twitter.com/intent/tweet?text=GiNZA%20-%20Japanese%20NLP%20Library%20https%3A%2F%2Fmegagonlabs.github.io%2Fginza%2F)
&emsp;
[![Downloads](https://pepy.tech/badge/ginza/week)](https://pepy.tech/project/ginza/week)

***GiNZAをアップグレードする際は [重要な変更](#ginza-400) の記述をご確認ください。***
## Breaking Changes in v4.0
- 解析モデルを`spaCy v2.3`の`spacy.lang.ja`に変更
  - SudachiPy辞書をPyPI(SudachiDict-core)の公式パッケージに変更
  - `Token.lemma_`に設定する値をSudachiPyの`Morpheme.dictionary_form()`に変更
- コマンドラインツール起動オプションおよび出力(標準conllu形式)のmiscフィールドの変更
  - use_sentence_separator(-s)オプションの廃止
  - NE(OntoNotes)のBIラベル直後のセパレータをハイフン(B-GPE)に変更
  - Reading(読み), Inf(活用), ENE(拡張固有表現)のサブフィールドを追加
- トークン拡張フィールド(`Token._.*`)を廃止
  - `Doc.user_data`に対応するエントリを追加
- Pipelineの構成を変更
  - BunsetuRecognizer・CompoundSplitterを追加しJapaneseCorrectorを廃止
- 文節単位で解析を行うAPIを追加
  - `from ginza import *`
- 学習コーパスをUD_JAPANESE-BCCWJ v2.6にアップグレード
  - 解析精度と一貫性が向上
- 単語ベクトルをchiVe mc90(うち頻度上位35,000語)に変更

## GiNZA v4の解析モデルと文節単位の解析API
新しいGiNZAの解析モデルにより、Universal Dependenciesの枠組みの中で日本語に特徴的な文節構造を考慮することができます。

![bunsetu_heads](https://github.com/megagonlabs/ginza/raw/static/docs/images/bunsetu_heads.png)

またGiNZA v4で追加された解析APIを用いることで、文節やその主辞を単位とした分析がこれまでよりずっと容易になります。
```python
from ginza import *
import spacy
nlp = spacy.load("ja_ginza")  # GiNZAモデルの読み込み

from collections import defaultdict
frames = defaultdict(lambda: 0)  # 依存関係の出現頻度を格納
sentences = set()  # 重複文検出用のset

with open("sentences.txt", "r") as fin:  # 解析対象のテキストファイルから
  for line in fin:  # 一行ごとに
    try:
      doc = nlp(line.rstrip())  # 解析を実行し
    except:
      continue
    for sent in doc.sents:  # 文単位でループ
      if sent.text in sentences:
        continue  # 重複文はスキップ
      sentences.add(sent.text)
      for t in bunsetu_head_tokens(sent):  # 文節主辞トークンのうち
        if t.pos_ not in {"ADJ", "VERB"}:
          continue  # 述語以外はスキップ
        v = phrase(lemma_)(t)  # 述語とその格要素(主語・目的語相当)の句を集める
        dep_phrases = sub_phrases(t, phrase(lemma_), is_not_stop)
        subj = [phrase for dep, phrase in dep_phrases if dep in {"nsubj"}]
        obj  = [phrase for dep, phrase in dep_phrases if dep in {"obj", "iobj"}]
        for s in subj:
          for o in obj:
            frames[(s, o, v)] += 1  # 格要素と述語の組み合わせをカウント

for frame, count in sorted(frames.items(), key=lambda t: -t[1]):
  print(count, *frame, sep="\t")  # 出現頻度の高い順に表示
```

#### 表1 GiNZA v4で追加された文節APIの一覧

| category | func or variable | description |
| --- | --- | --- |
| Span-based | | |
| | bunsetu_spans()           | 文節SpanのIterable。 |
| | bunsetu_phrase_spans()    | 文節主辞SpanのIterable。 |
| | bunsetu_span()            | トークンが属する文節のSpan。 |
| | bunsetu_phrase_span()     | トークンが属する文節の主辞Span。 |
| Construction | | |
| | bunsetu()                 | 文節中のトークン列を指定された形に整形して返す。 |
| | phrase()                  | 文節主辞中のトークン列を指定された形に整形して<br>返す。 |
| | sub_phrases()             | 従属文節を指定された形に整形して返す。 |
| | phrases()                 | スパンに含まれる文節を指定された形に整形して<br>返す。 |
| Utility | | |
| | traverse()                | 構文木を指定された方法で巡回し指定された形に<br>整形して返す。 |
| | default_join_func()       | デフォルトのトークン列の結合方法。 |
| | SEP                       | デフォルトのトークン区切り文字。 |
| Token-based | | |
| | bunsetu_head_list()       | DocやSpanに含まれる文節のヘッドトークンの<br>インデックスのリスト。 |
| | bunsetu_head_tokens()     | DocやSpanに含まれる文節のヘッドトークンの<br>リスト。 |
| | bunsetu_bi_labels()       | DocやSpanに含まれるトークンが文節開始位置<br>にある場合は"B"、それ以外は"I"とするリスト。 |
| | bunsetu_position_types()  | DocやSpanに含まれるトークンを{"ROOT",<br>"SEM_HEAD", "SYN_HEAD", "NO_HEAD",<br>"FUNC", "CONT"}に分類したリスト。 |
| | is_bunsetu_head()         | トークンが文節のヘッドの場合はTrue、<br>それ以外はFalse。 |
| | bunsetu_bi_label()        | トークンが文節開始位置にある場合は"B"、<br>それ以外は"I"。 |
| | bunsetu_position_type()   | トークンを{"ROOT", "SEM_HEAD",<br>"SYN_HEAD", "NO_HEAD", "FUNC",<br>"CONT"}に分類。 |
| Proxy | | |
| | *                         | spacy.tokens.Tokenクラスのプロパティと<br>同名・同機能の関数群。 |
| Subtoken | | |
| | sub_tokens()              | トークンの分割情報。 |
| | set_split_mode()          | デフォルトの分割モードの変更。 |

## 発表資料
- 言語処理学会論文誌 委嘱記事 Volume 27 Number 3 (coming soon)
- [Universal Dependencies Symposium 2019 発表スライド](https://www.slideshare.net/MegagonLabs/ginza-cabocha-udpipe-stanford-nlp)

## ライセンス
GiNZA NLPライブラリおよびGiNZA日本語Universal Dependenciesモデルは
[The MIT License](https://github.com/megagonlabs/ginza/blob/master/LICENSE)のもとで公開されています。
利用にはThe MIT Licenseに合意し、規約を遵守する必要があります。

### spaCy
GiNZAはspaCyをNLP Frameworkとして使用しています。

[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Sudachi/SudachiPy - SudachiDict - chiVe
GiNZAはトークン化（形態素解析）処理にSudachiPyを使用することで、高い解析精度を得ています。

[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt),
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)

[SudachiDict LEGAL PAGE](https://github.com/WorksApplications/SudachiDict/blob/develop/LEGAL)

[chiVe LICENSE PAGE](https://github.com/WorksApplications/chiVe/blob/master/LICENSE)

## 訓練コーパス

### UD Japanese BCCWJ v2.6
GiNZA v4 の依存構造解析モデルは
[UD Japanese BCCWJ](https://github.com/UniversalDependencies/UD_Japanese-BCCWJ) v2.6
([Omura and Asahara:2018](https://www.aclweb.org/anthology/W18-6014/))
から新聞系文書を除外して学習しています。
本モデルは国立国語研究所とMegagon Labsの共同研究成果です。

### GSK2014-A (2019) BCCWJ版
GiNZA v4 の固有表現抽出モデルは
[GSK2014-A](https://www.gsk.or.jp/catalog/gsk2014-a/) (2019) BCCWJ版
([橋本・乾・村上(2008)](https://www.anlp.jp/proceedings/annual_meeting/2010/pdf_dir/C4-4.pdf))
から新聞系文書を除外して学習しています。
固有表現抽出ラベル体系は[関根の拡張固有表現階層](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)、
および、[OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf)
を独自に拡張したものを併用しています。
本モデルは国立国語研究所とMegagon Labsの共同研究成果です。

## 実行環境
このプロジェクトは Python 3.6以上（および対応するpip）で動作検証を行っています。

[(開発環境についての詳細はこちら)](#development-environment)
### 実行環境のセットアップ
#### 1. GiNZA NLPライブラリと日本語Universal Dependenciesモデルのインストール
最新版をインストールするにはコンソールで次のコマンドを実行します。
```console
$ pip install -U ginza
```

Google Colab 環境ではインストール後にパッケージ情報の再読込が必要な場合があります。詳細はリンクの記事をご確認下さい。
```python
import pkg_resources, imp
imp.reload(pkg_resources)
```
[【GiNZA】GoogleColabで日本語NLPライブラリGiNZAがloadできない](https://www.sololance.tokyo/2019/10/colab-load-ginza.html)

インストール時にCythonに関するエラーが発生した場合は、次のように環境変数CFLAGSを設定してください。
```console
$ CFLAGS='-stdlib=libc++' pip install ginza
```

#### 2. ginzaコマンドの実行
コンソールで次のコマンドを実行して、日本語の文に続けてEnterを入力すると、[CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式で解析結果が出力されます。
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
7	し	する	AUX	動詞-非自立可能	_	6	advcl	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Inf=サ行変格,連用形-一般|Reading=シ
8	ましょう	ます	AUX	助動詞	_	6	aux	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=SYN_HEAD|Inf=助動詞-マス,意志推量形|Reading=マショウ
9	。	。	PUNCT	補助記号-句点	_	6	punct	_	SpaceAfter=No|BunsetuBILabel=I|BunsetuPositionType=CONT|Reading=。

```
`ginzame`コマンドでオープンソース形態素解析エンジン [MeCab](https://taku910.github.io/mecab/) の`mecab`コマンドに近い形式で解析結果を出力することができます。
`ginzame`コマンドは形態素解析処理のみをマルチプロセスで高速に実行します。
このコマンドと`mecab`の出力形式の相違点として、 
最終フィールド（発音）が常に`*`となることに注意して下さい。
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
### マルチプロセス実行 (Experimental)
`-p NUM_PROCESS` オプションで解析処理のマルチプロセス実行が可能になります。
`NUM_PROCESS`には並列実行するプロセス数を整数で指定します。
0以下の値は`実行環境のCPUコア数＋NUM_PROCESS`を指定したのと等価になります。

`ginza -f mecab`とそのエイリアスである`ginzame`以外で`-p NUM_PROCESS`オプションを使用する場合は、
実行環境の空きメモリ容量が十分あることを事前に確認してください。
マルチプロセス実行では1プロセスあたり約130MBのメモリが必要です。(今後のリリースで改善予定)

### コーディング例
次のコードは文単位で依存構造解析結果を出力します。
```python
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('銀座でランチをご一緒しましょう。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.i)
    print('EOS')
```

### API
基本的な解析APIは [spaCy API documents](https://spacy.io/api/) を参照してください。
その他、詳細についてはドキュメントが整備されるまでお手数ですがソースコードをご確認ください。

### ユーザ辞書の使用
GiNZAはTokenizer(形態素解析レイヤ)にSudachiPyを使用しています。
GiNZAでユーザ辞書を使用するにはSudachiPyの辞書設定ファイル `sudachi.json` の `userDict` フィールドに、
コンパイル済みのユーザ辞書ファイルのパスのリストを指定します。

SudachiPyのユーザ辞書ファイルのコンパイル方法についてはSudachiPyのGitHubリポジトリで公開されているドキュメントを参照してください。  
[SudachiPy - User defined Dictionary](https://github.com/WorksApplications/SudachiPy#user-defined-dictionary)  
[Sudachi ユーザー辞書作成方法](https://github.com/WorksApplications/Sudachi/blob/develop/docs/user_dict.md)

## [リリース履歴](https://github.com/megagonlabs/ginza/releases)
### version 4.x

#### ginza-4.0.1
- 2020-08-30
- Debug
  - Add type arguments for singledispatch register annotations (for Python 3.6)

#### ginza-4.0.0
- 2020-08-16, Chrysoberyl
- 重要な変更
  - 解析モデルを`spaCy v2.3`の`spacy.lang.ja`に変更
    - `Token.lemma_`に設定される値をSudachiPyの`Morpheme.dictionary_form()`に変更
  - SudachiPy辞書をPyPI(SudachiDict-core)の公式パッケージに変更
    - 旧バージョンでインストールされる`ja_ginza_dict`パッケージはアンインストール可能
  - コマンドラインツール起動オプションおよび出力(標準conllu形式)のmiscフィールドの変更
    - use_sentence_separator(-s)オプションの廃止
    - NE(OntoNotes)のBIラベル直後のセパレータをハイフン(B-GPE)に変更
    - Reading(読み), Inf(活用), ENE(拡張固有表現)のサブフィールドを追加
  - トークン拡張フィールド(`Token._.*`)を廃止し`Doc.user_data[]`のエントリとアクセサを追加
    - inflections (`ginza.inflection(Token)`)
    - reading_forms (`ginza.reading_form(Token)`)
    - bunsetu_bi_labels (`ginza.bunsetu_bi_label(Token)`)
    - bunsetu_position_types (`ginza.bunsetu_position_type(Token)`)
    - bunsetu_heads (`ginza.is_bunsetu_head(Token)`)
  - Pipelineの構成を変更
    - JapaneseCorrectorを廃止
      - 可能性品詞の曖昧性解消およびトークン結合処理はspaCy標準機能を利用するよう変更
    - CompoundSplitterを追加
      - `spacy.lang.ja`で登録されるSudachi辞書の分割情報(`Doc.user_data["sub_tokens"]`)を参照してTokenを分割
      - `ginza.set_split_mode(Language, str)`の第2引数にA, B, Cのいずれかを指定(デフォルト=C)
    - BunsetuRecognizerを追加
      - ja_ginzaモデルで得られる文節主辞ラベルを用いて`Doc.user_data[]`に`bunsetu_bi_labels`,`bunsetu_position_types`,`bunsetu_heads`を追加
  - 学習コーパスをUD_JAPANESE-BCCWJ v2.6にアップグレード
    - 解析精度と一貫性が向上
  - 単語ベクトルをchiVe mc90(うち頻度上位35,000語)に変更
    - ベクトル次元数=300
- API Changes
  - 文節単位で解析を行うAPIを追加(`from ginza import *`)
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
    - The values of ``Token._.sudachi`` field would	be set after calling ``SudachipyTokenizer.set_enable_ex_sudachi(True)``, to avoid pickling errors

```python
import spacy
import pickle
nlp = spacy.load('ja_ginza')
doc1 = nlp('この例は正しくserializeされます。')
doc1.to_bytes()
with open('sample1.pickle', 'wb') as f:
    pickle.dump(doc1, f)

nlp.tokenizer.set_enable_ex_sudachi(True)
doc2 = nlp('この例ではserialize時にエラーが発生します。')
doc2.to_bytes()
with open('sample2.pickle', 'wb') as f:
    pickle.dump(doc2, f)
```

#### ginza-3.1.0
- 2020-01-16
- 重要な変更
  - 形態素辞書パッケージ(ja_ginza_dict)の配布元をPyPIに変更
- API Changes
  - commands
    - `ginza` and `ginzame`
      - add `-i` option to initialize the files of `ja_ginza_dict`

#### ginza-3.0.0
- 2020-01-15, Benitoite
- 重要な変更
  - パッケージの配布元をPyPIに変更
    - `pip install ginza` を実行するだけで解析モデルを含めてインストールが完結
    - 解析モデルの`ja_ginza`もPyPIから配布 (`ja_ginza.setup.py`実行中に形態素解析辞書もダウンロード)
  - 解析モデルの改良
    - 固有表現抽出モデルの訓練コーパスを GSK2014-A (2019) BCCWJ版(新聞系文書を除外)に変更
      - 固有表現抽出精度が再現性・適合性の両面で大きく向上
      - `token.ent_type_`を[関根の拡張固有表現階層](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)のラベルに変更
        - `ginza`コマンド出力の最終フィールドに`ENE7`属性を追加
      - [OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf)体系の固有表現ラベルを`token._.ne`に移動
        - OntoNotes5体系には`PHONE`, `EMAIL`, `URL`, `PET_NAME`のラベルを追加
    - `spacy pretrain`のエポック数を100回以上とすることで依存構造解析精度が向上
      - `spacy train`コマンドで依存構造解析と固有表現抽出をマルチタスク学習することでさらに精度が向上
    - 形態素解析辞書を`SudachiDict_core-20191224`にアップグレード
  - `ginzame`コマンドの追加
    - `sudachipy`のみをマルチプロセスで高速に実行し結果を`mecab`形式で出力
    - 形態素解析辞書を独自にインストールする形に変更したため`sudachipy`コマンドの実行にはSudachi辞書のインストールが別途必要
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
- 機能改良
  - JapaneseCorrectorで`as_*`形式の依存構造を完全にマージ可能になった
- 不具合改修
  - コマンドラインツールが特定の状況で異常終了していた

#### ginza-2.2.0
- 2019-10-04, Ametrine
- 重要な変更
  - sudachipy.tokenizerの`split_mode`が正しく設定されない不具合(v2.0.0でデグレード)を改修 (#43)
    - この不具合により学習時と`ginza`コマンドによる解析時で`split_mode`が異なる状態となっていました。
    - v2.0.0で`split_mode`は学習時およびAPIでは'B'に、`ginza`コマンド実行時は'C'にセットされていました。
    - 今回の改修でデフォルトの`split_mode`は'C'に統一されました。
    - この改修によりGiNZAをv2.0.0からv2.2.0にアップグレードする際にトークン区切り基準が変化します。
- 機能追加
  - `ginza` コマンドの出力形式を指定する`-f`, `--output-format` オプションを追加
    - `-f 0` or `-f conllu` : [CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式
    - `-f 1` or `-f cabocha`: [cabocha](https://taku910.github.io/cabocha/) -f1 互換形式
  - カスタムトークンフィールドの追加:
    - `bunsetu_index` : 文節番号 (0起番)
    - `reading`: 読み (発音フィールドには未対応)
    - `sudachi`: SudachiPyのmorphemeインスタンスまたはmorphemeのリスト(JapaneseCorrectorが複数トークンをまとめ上げた場合はリストとなる)
- 性能改良
  - Tokenizer
    - 最新のSudachiDictを使用(SudachiDict_core-20190927.tar.gz) 
    - SudachiPyをCythonで高速化されたバージョンにアップグレード(v0.4.0) 
  - Dependency parser
    - `spacy pretrain`コマンドを用いてUD-Japanese BCCWJ, UD_Japanese-PUD, KWDLCから言語モデルを学習。
    - `spacy train`コマンド実行時にマルチタスク学習のために`-pt 'tag,dep'`オプションを指定 
  - New model file
    - ja_ginza-2.2.0.tar.gz

#### ginza-2.0.0
- 2019-07-08
- `ginza` コマンドの追加
  - コンソールから `ginza` を実行してください
- パッケージ構成の変更
  - モジュール: `ginza`
  - 言語モデル: `ja_ginza`
  - `spacy.lang.ja` を `ginza` で置き換え
- `sudachipy` に関連するディレクトリの削除
  - SudachiPyと辞書は`ginza`と同時に`pip`でインストールされます
- ユーザ辞書が利用可能
  - 参照 [Customized dictionary - SudachiPy](https://github.com/WorksApplications/SudachiPy#customized-dictionary)
- トークン拡張フィールド
  - 追加
    - `token._.bunsetu_bi_label`, `token._.bunsetu_position_type`
  - 変更なし
    - `token._.inf`
  - 削除
    - `pos_detail` (同じ値が `token.tag_` に保存される)

### version 1.x
#### ja_ginza_nopn-1.0.2
- 2019-04-07
- conllu形式に合致するようcli出力のroot依存元インデックスを0に変更

#### ja_ginza_nopn-1.0.1
- 2019-04-02
- 新元号『令和』をsystem_core.dicに追加

#### ja_ginza_nopn-1.0.0
- 2019-04-01
- 初回リリース

## 開発環境
### 開発環境のセットアップ
#### 1. githubからclone
```console
$ git clone 'https://github.com/megagonlabs/ginza.git'
```

#### 2. pip install および setup.sh の実行
```console
$ pip install -U -r requirements.txt
$ python setup.py develop
```

#### 3. GPU用ライブラリのセットアップ (Optional)
CUDA v10.1の場合は次のように指定します。
```console
$ pip install -U thinc[cuda101]
```

### 訓練の実行
GiNZAの解析モデル `ja_ginza` はspaCy標準コマンドを使用して学習を行っています。
```console
$ python -m spacy train ja ja_ginza-4.0.0 corpus/ja_ginza-ud-train.json corpus/ja_ginza-ud-dev.json -b ja_vectors_chive_mc90_35k/ -ovl 0.3 -n 100 -m meta.json.ginza -V 4.0.0
```
