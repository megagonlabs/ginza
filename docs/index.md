# GiNZAの公開ページ
![GiNZA logo](https://github.com/megagonlabs/ginza/releases/download/latest/GINZA_logo_4c_y.png)

[NLP2019論文](http://www.anlp.jp/proceedings/annual_meeting/2019/pdf_dir/F2-3.pdf),
[論文発表資料](https://www.slideshare.net/MegagonLabs/nlp2019-ginza-139011245)

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
$ pip install ginza-2.0.0.tar.gz
```
#### 2. ginzaコマンドの実行
コンソールで次のコマンドを実行して、日本語の文に続けてEnterを入力すると、conllu形式で解析結果が出力されます。
```bash
$ ginza
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
### version 2.0
#### ginza-2.0.0 (2019-07-08)
- `ginza` コマンドの追加
  - コンソールから `ginza` を実行してください
- パッケージ構成の変更
  - モジュール: `ginza`
  - 言語モデル: `ja_ginza`
  - `spacy.lang.ja` を `ginza` で置き換え
- `sudachipy` に関連するディレクトリの削除
  - SudachiPyと辞書はginzaと同時にpipでインストールされます
- ユーザ辞書が利用可能
  - 参照 [Customized dictionary - SudachiPy](https://github.com/WorksApplications/SudachiPy#customized-dictionary)
- トークン拡張フィールド
  - 追加
    - `token._.bunsetu_bi_label`, `token._.bunsetu_position_type`
  - 変更なし
    - `token._.inf`
  - 削除
    - `pos_detail` (同じ値が `token.tag_` に保存される)
### version 1.0
#### ja_ginza_nopn-1.0.2 (2019-04-07)
- conllu形式に合致するようcli出力のroot依存元インデックスを0に変更
#### ja_ginza_nopn-1.0.1 (2019-04-02)
- 新元号『令和』をsystem_core.dicに追加
#### ja_ginza_nopn-1.0.0 (2019-04-01)
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
