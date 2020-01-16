![GiNZA logo](https://github.com/megagonlabs/ginza/releases/download/latest/GINZA_logo_4c_y.png)
# GiNZAの公開ページ

## What's new in v3.1!
- `$ pip install ginza` 実行時に一部の環境(pipenvを含む)で形態素辞書が正しく展開されない問題に対処するためのオプションを追加しました
  - `ginza` コマンドが `ValueError: cannot mmap an empty file` で異常終了する場合は `$ ginza -i` を一度だけ実行して辞書ファイルを初期化してください
- ja_ginza_dict(形態素解析辞書)パッケージをPyPI経由で配布するよう変更しました

## What's new in v3.0!
- `$ pip install ginza` でGiNZAをインストールできるようになりました
- 形態素解析のみを高速に実行する `ginzame` コマンドを追加しました
- 固有表現抽出モデルが改良されました
- `sudachipy`コマンドの実行にはSudachi辞書を別途インストールする必要があります

***GiNZAをアップグレードする際は必ず [重要な変更](#ginza-300) の記述をご確認ください。***

## 発表資料
- NLP2020論文 (coming soon)
- [Universal Dependencies Symposium 2019@国語研での発表スライド](https://www.slideshare.net/MegagonLabs/ginza-cabocha-udpipe-stanford-nlp)
- [NLP2019論文](http://www.anlp.jp/proceedings/annual_meeting/2019/pdf_dir/F2-3.pdf)
([発表スライド](https://www.slideshare.net/MegagonLabs/nlp2019-ginza-139011245))

## ライセンス
GiNZA NLPライブラリおよびGiNZA日本語Universal Dependenciesモデルは
[The MIT License](https://github.com/megagonlabs/ginza/blob/master/LICENSE)のもとで公開されています。
利用にはThe MIT Licenseに合意し、規約を遵守する必要があります。

### spaCy
GiNZAはspaCyをNLP Frameworkとして使用しています。

[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### SudachiおよびSudachiPy
GiNZAはトークン化（形態素解析）処理にSudachiPyを使用することで、高い解析精度を得ています。

[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt),
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)

## 訓練コーパス

### UD Japanese BCCWJ v2.4
GiNZA v3 の依存構造解析モデルは
[UD Japanese BCCWJ](https://github.com/UniversalDependencies/UD_Japanese-BCCWJ) v2.4
([Omura and Asahara:2018](https://www.aclweb.org/anthology/W18-6014/))
から新聞系文書を除外して学習しています。
本モデルは国立国語研究所とMegagon Labsの共同研究成果です。

### GSK2014-A (2019) BCCWJ版
GiNZA v3 の固有表現抽出モデルは
[GSK2014-A](https://www.gsk.or.jp/catalog/gsk2014-a/) (2019) BCCWJ版
([橋本・乾・村上:2008](https://www.anlp.jp/proceedings/annual_meeting/2010/pdf_dir/C4-4.pdf))
から新聞系文書を除外して学習しています。
固有表現抽出ラベル体系は[関根の拡張固有表現階層](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html、
および、[OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf)
を独自に拡張したものを併用しています。
本モデルは国立国語研究所とMegagon Labsの共同研究成果です。

## 実行環境
このプロジェクトは Python 3.6以上（および対応するpip）で動作検証を行っています。
Anaconda環境等ではpipによるインストールが正常に行えない場合があります。
(Anaconda環境は将来のバージョンでサポートする予定です)

[(開発環境についての詳細はこちら)](#development-environment)
### 実行環境のセットアップ
#### 1. GiNZA NLPライブラリと日本語Universal Dependenciesモデルのインストール
最新版をインストールするにはコンソールで次のコマンドを実行します。
```bash
$ pip install -U ginza
```
pipインストールアーカイブを[リリースページからダウンロード](https://github.com/megagonlabs/ginza/releases)して、
次のように直接指定することもできます。
```bash
$ pip install -U ginza-3.1.0.tar.gz
```
インストールの後、`ginza` コマンド実行時に `ValueError: cannot mmap an empty file` が表示されて `ginza` が異常終了する場合は、
```bash
$ ginza -i
```
を一度だけ実行して辞書ファイルを初期化してください。

Google Colab 環境ではインストール後にパッケージ情報の再読込が必要な場合があります。詳細はリンクの記事をご確認下さい。
```python
import pkg_resources, imp
imp.reload(pkg_resources)
```
[【GiNZA】GoogleColabで日本語NLPライブラリGiNZAがloadできない](https://www.sololance.tokyo/2019/10/colab-load-ginza.html)

インストール時にCythonに関するエラーが発生した場合は、次のように環境変数CFLAGSを設定してください。
```bash
$ CFLAGS='-stdlib=libc++' pip install ginza
```
#### 2. ginzaコマンドの実行
コンソールで次のコマンドを実行して、日本語の文に続けてEnterを入力すると、[CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式で解析結果が出力されます。
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
`ginzame`コマンドでオープンソース形態素解析エンジン [MeCab](https://taku910.github.io/mecab/) の`mecab`コマンドに近い形式で解析結果を出力することができます。
`ginzame`コマンドは形態素解析処理のみをマルチプロセスで高速に実行します。
このコマンドと`mecab`の出力形式の相違点として、 
最終フィールド（発音）が常に`*`となることに注意して下さい。
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
日本語係り受け解析器 [CaboCha](https://taku910.github.io/cabocha/) の`cabocha -f1`のラティス形式に近い解析結果を出力する場合は
`ginza -f 1` または `ginza -f cabocha` を実行して下さい。
このオプションと`cabocha -f1`の出力形式の相違点として、 
スラッシュ記号`/`に続く`func_index`フィールドが常に自立語の終了位置（機能語があればその開始位置に一致）を示すこと、
機能語認定基準が一部異なること、
に注意して下さい。
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
### マルチプロセス実行 (Experimental)
GiNZA v3.0 で追加された `-p NUM_PROCESS` オプションで解析処理のマルチプロセス実行が可能になります。
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
基本的な解析APIは[spaCy API documents](https://spacy.io/api/)を参照してください。
その他、詳細についてはドキュメントが整備されるまでお手数ですがソースコードをご確認ください。

## [リリース履歴](https://github.com/megagonlabs/ginza/releases)
### version 3.x
#### ginza-3.1.0
- 2020-01-16
- 重要な変更
  - 形態素辞書パッケージ(ja_ginza_dict)の配布元をPyPIに変更
- API Changes
  - commands
    - `ginza` and `ginzame`
      - add `-i` option to initialize the files of `ja_ginza_dict`
#### ginza-3.0.0
- 2020-01-15
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
#### 1. githubからsubmodulesを含めてclone
```bash
$ git clone 'https://github.com/megagonlabs/ginza.git'
```
#### 2. ./setup.sh の実行
通常の開発環境はこちらを実行。
```bash
$ python setup.sh develop
```
### 訓練の実行
記述予定
