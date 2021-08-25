# 開発者向けの情報

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
CUDA v11.0の場合は次のように指定します。
```console
$ pip install -U spacy[cuda110]
```

### 訓練の実行
GiNZAの解析モデル `ja_ginza` はspaCy標準コマンドを使用して学習を行っています。
```console
$ python -m spacy train ja ja_ginza-4.0.0 corpus/ja_ginza-ud-train.json corpus/ja_ginza-ud-dev.json -b ja_vectors_chive_mc90_35k/ -ovl 0.3 -n 100 -m meta.json.ginza -V 4.0.0
```

### トラブルシューティング

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

## ユーザ辞書の使用

GiNZAはTokenizer(形態素解析レイヤ)にSudachiPyを使用しています。
GiNZAでユーザ辞書を使用するにはSudachiPyの辞書設定ファイル `sudachi.json` の `userDict` フィールドに、
コンパイル済みのユーザ辞書ファイルのパスのリストを指定します。

SudachiPyのユーザ辞書ファイルのコンパイル方法についてはSudachiPyのGitHubリポジトリで公開されているドキュメントを参照してください。  
[SudachiPy - User defined Dictionary](https://github.com/WorksApplications/SudachiPy#user-defined-dictionary)  
[Sudachi ユーザー辞書作成方法](https://github.com/WorksApplications/Sudachi/blob/develop/docs/user_dict.md)
