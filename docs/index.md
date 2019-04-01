# GiNZAの公開ページ

[NLP2019論文](http://www.anlp.jp/proceedings/annual_meeting/2019/pdf_dir/F2-3.pdf),
[論文発表資料](https://www.slideshare.net/MegagonLabs/nlp2019-ginza-138927873)

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
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE-2.0.txt)

## 実行環境
このプロジェクトは Python 3.7 および、対応する pip 環境で動作検証を行っています。

プロジェクトが専有する容量はおよそ250MBです。
そのうち、Sudachi辞書が200MB、日本語Wikipedia全体から得た単語分散表現が50MBを占めます。

[(開発環境についての詳細はこちら)](#development-environment)
### 実行環境のセットアップ
#### 1. GiNZA NLPライブラリと日本語Universal Dependenciesモデルのインストール
最新版をインストールするにはコンソールで次のコマンドを実行します。
```
pip install ginza
```
pipインストールアーカイブを[リリースページからダウンロード](https://github.com/megagonlabs/ginza/releases)して、
次のように直接指定することもできます。
```
pip install ja_ginza_nopn-1.0.0.tar.gz
```
#### 2. 試し方
コンソールで次のコマンドを実行して、日本語の文に続けてEnterを入力すると、conll形式で解析結果が出力されます。
```
python -m spacy.lang.ja_ginza.cli
```
### コーディング例
次のコードは文単位で依存構造解析結果を出力します。
```
import spacy
nlp = spacy.load('ja_ginza')
doc = nlp('依存構造解析の実験を行っています。')
for sent in doc.sents:
    for token in sent:
        print(token.i, token.orth_, token.lemma_, token.pos_, token.dep_, token.head.i)
    print('EOS')
```
### API
詳細は[spaCy API documents](https://spacy.io/api/)を参照してください。
## リリース履歴
### version 1.0
#### ja_ginza_nopn-1.0.0 (2019-04-01)
初回リリース

## 開発環境
### 開発環境のセットアップ
#### 1. githubからsubmodulesを含めてclone
```
git clone --recursive 'https://github.com/megagonlabs/ginza.git'
```
#### 2. ./setup.sh の実行
通常の開発環境はこちらを実行。
```
./setup.sh
```
GPU環境(cuda92)はこちらを実行。
```
./setup_cuda92.sh
```
### 訓練の実行
nopn_embedding/, nopn/, kwdlc/ のそれぞれのディレクトを用意して次のコマンドを実行。
```
shell/build.sh nopn 1.0.1
```
GPU環境の場合は-gオプションを追加することで訓練と解析を高速化できます。

訓練が終了すると次のpipインストールアーカイブが作成されます。
```
target/ja_ginza_nopn-1.0.1.tgz
```
