![GiNZA logo](https://github.com/megagonlabs/ginza/releases/download/latest/GINZA_logo_4c_y.png)
# GiNZAの公開ページ

***GiNZA 'v2.2.0'をインストールする前に [重要な変更](#ginza-211) の記述をご確認ください。***

## 発表資料
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

## 実行環境
このプロジェクトは Python 3.6以上（および対応するpip）で動作検証を行っています。
Anaconda環境ではpipによるインストールが正常に行えない場合があります。
(Anaconda環境は将来のバージョンでサポートする予定です)

[(開発環境についての詳細はこちら)](#development-environment)
### 実行環境のセットアップ
#### 1. GiNZA NLPライブラリと日本語Universal Dependenciesモデルのインストール
最新版をインストールするにはコンソールで次のコマンドを実行します。
```bash
$ pip install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
```
pipインストールアーカイブを[リリースページからダウンロード](https://github.com/megagonlabs/ginza/releases)して、
次のように直接指定することもできます。
```bash
$ pip install ginza-2.2.0.tar.gz
```

インストール時に次のようなエラーメッセージが表示される場合は、`pip`をupgradeする必要があります。

```
Could not find a version that satisfies the requirement ja_ginza@ http://github.com/ ...  
```

```bash
$ pip install --upgrade pip
```

Google Colab 環境ではインストール後にパッケージ情報の再読込が必要です。詳細はリンクの記事をご確認下さい。
```python
import pkg_resources, imp
imp.reload(pkg_resources)
```
[【GiNZA】GoogleColabで日本語NLPライブラリGiNZAがloadできない](https://www.sololance.tokyo/2019/10/colab-load-ginza.html)

インストール時にCythonに関するエラーが発生した場合は、次のように環境変数CFLAGSを設定してください。
```bash
$ CFLAGS='-stdlib=libc++' pip install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
```
#### 2. ginzaコマンドの実行
コンソールで次のコマンドを実行して、日本語の文に続けてEnterを入力すると、[CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式で解析結果が出力されます。
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
日本語係り受け解析器 [CaboCha](https://taku910.github.io/cabocha/) 互換(`cabocha -f1`)のラティス形式で解析結果を出力する場合は
`-f 1` または `-f cabocha` オプションを追加して下さい。
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
※ GiNZAは依存構造解析(または係り受け解析)のためのライブラリです。
高速に形態素解析だけを実行するには、GiNZAと同時にインストールされる [SudachiPy](https://github.com/WorksApplications/SudachiPy/) または `sudachipy`コマンドを使用して下さい。
```bash
$ sudachipy
```
### コーディング例
次のコードは文単位で依存構造解析結果を出力します。
```python
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.i)
    print('EOS')
```
### API
詳細は[spaCy API documents](https://spacy.io/api/)を参照してください。
## [リリース履歴](https://github.com/megagonlabs/ginza/releases)
### version 2.x
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
