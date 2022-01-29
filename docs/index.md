![GiNZA logo](https://github.com/megagonlabs/ginza/raw/static/docs/images/GiNZA_logo_4c_y.png)

# GiNZAの公開ページ

[![Tweet](https://abs.twimg.com/favicons/favicon.ico)](https://twitter.com/intent/tweet?text=GiNZA%20-%20Japanese%20NLP%20Library%20https%3A%2F%2Fmegagonlabs.github.io%2Fginza%2F)
&emsp;
[![Downloads](https://pepy.tech/badge/ginza/week)](https://pepy.tech/project/ginza)

## What's new!

- `spaCy v3.2`と`Sudachi.rs(SudachiPy v0.6.2)`に対応した`GiNZA v5.1`をリリース
  - バッチ解析処理をGPU環境で50〜60%・CPU環境で10〜40%高速化
  - ginzaコマンドの並列実行オプション(`ginza -p {n_process}`および`ginzame`)の処理効率を向上
- ginzaコマンドで日本語以外を含む全てのspaCyモデルが利用可能に
  - `ginza -m en_core_web_md` の形でモデル名を指定することで[CoNLL-U](https://universaldependencies.org/format.html#syntactic-annotation)出力ツールとして利用可能
- [ginzaコマンドの解説ページ](https://megagonlabs.github.io/ginza/command_line_tool.html)の記述を拡充
  - `ginza`コマンドで使用するGPUのgpu_idを`ginza -g 1`の形で指定可能に

***GiNZAをアップグレードする際は下記の互換性情報を確認してください。***

## GiNZA v5.1 互換性情報
- `ginza --require_gpu`および`ginza -g`オプションが引数にgpu_idを取るようになりました
  - gpu_idに-1を指定(デフォルト)するとCPUのみを使用します
- v5.0以前の`ja_ginza`および`ja_ginza_electra`パケージはGiNZA v5.1で使用できません（旧バージョン向けパッケージは事前にアンインストールが必要です）
  - `pip uninstall ginza ; pip uninstall ja_ginza ; pip uninstall ja_ginza_electra`
- transformersモデルの追加に伴いGiNZA v5.1インストール時は`ginza`パッケージとともに解析モデルパッケージを明示的に指定する必要があります
  - 解析精度重視モデル (メモリ容量16GB以上を推奨)
    - `pip install -U ginza ja_ginza_electra`
  - 実行速度重視モデル
    - `pip install -U ginza ja_ginza`
- トークンの活用/読み/正規形の保存先がTokenクラスのフィールドに変更されました。
  - `doc.user_data[“reading_forms”][token.i]` -> `token.morph.get(“Reading”)`
  - `doc.user_data[“inflections”][token.i]` -> `token.morph.get(“Inflection”)`
  - `force_using_normalized_form_as_lemma(True)` -> `token.norm_`
- 併せて[GiNZA v5.0.0 重要な変更](#ginza-500)についても確認してください

## GiNZA v5 新機能

### Transformersモデルによる解析精度の向上

GiNZA v5の解析精度は以前のバージョンから飛躍的な向上を遂げました。精度向上の主たる貢献はTransformers事前学習モデルの導入にあります。次の図は、UD_Japanese-BCCWJ r2.8における、従来型モデルの`ja_ginza`と、Transformers事前学習モデルを用いた`ja_ginza_electra`の、依存関係ラベリングおよび単語依存構造解析の学習曲線です。

![LAS](https://github.com/megagonlabs/ginza/raw/static/docs/images/v5_las_graph.svg)
![UAS](https://github.com/megagonlabs/ginza/raw/static/docs/images/v5_uas_graph.svg)

次の表はUD_Japanese-BCCWJ r2.8で5万ステップ学習した時点でのテストセットでの依存関係ラベリング精度(LAS:Labeled Attachment Score)、単語依存構造解析精度(UAS:Unlabeled Attachment Score)、UD品詞推定精度(UPOS)、拡張固有表現抽出精度(ENE)の比較です。

| Model | LAS | UAS | UPOS | ENE |
| --- | --- | --- | --- | --- |
| ja_ginza_electra | 92.3 | 93.7 | 98.1 | 61.3 |
| ja_ginza (v5)    | 89.2 | 91.1 | 97.0 | 53.9 |
| ja_ginza (v4相当) | 89.0 | 91.0 | 95.1 | 53.1 |

`ja_ginza_electra`は`ja_ginza`に対して、5万ステップ学習時の依存関係ラベリング・単語依存構造解析の誤りを、以前のバージョンと比較して25%以上低減できました。

また従来型モデルの`ja_ginza`においても、処理パイプラインに`morphologizer`を追加することにより、以前のバージョンと比較してUD品詞推定の誤りを4割低減できました。

[関根の拡張固有表現階層](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)を用いた拡張固有表現抽出精度(ENE)においても`ja_ginza_electra`は大幅な精度向上が得られています。GiNZAは関根の拡張固有表現階層にもとづく固有表現抽出結果を、spaCyで標準的に用いられる[OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf)にマッピング(変換表を適用)して出力しています。OntoNotes5は関根の拡張固有表現階層よりカテゴリ数が非常に少ない(粗い)ため、拡張固有表現をOntoNotes5体系にマッピングした場合の固有表現抽出精度は、拡張固有表現での数値より一般に高くなります。

※各モデルの学習と解析精度評価にはUD_Japanese-BCCWJ r2.8から新聞記事系のテキストを除外したものをSudachi辞書mode C(長単位)で再解析(retokenize)した上で、文節主辞情報を依存関係ラベルに組み合わせた状態のコーパスを用いています。

## 実行環境

GiNZAは Python 3.6以上（および対応するpip）で動作検証を行っています。
GiNZAをインストールする前に予めPython実行環境を構築してください。

### 実行環境のセットアップ

#### 1. GiNZA + Transformersモデル

※Transformersモデルの実行には16GB以上のメモリ容量が必要です。メモリ容量が不足する場合は後述の従来型モデルをお試しください。

旧バージョンのGiNZAをインストールしている場合は次のコマンドでアンインストールします。
```console
$ pip uninstall ginza ja_ginza_electra
```

旧バージョンの`ja_ginza`をインストールしている場合は次のコマンドでアンインストールします。
```console
$ pip uninstall ja_ginza
```

旧バージョンの`j_ginza_electra`をインストールしている場合は次のコマンドでアンインストールします。
```console
$ pip uninstall ja_ginza_electra
```

次のコマンドを実行して最新のGiNZAおよびTransformersモデルをインストールします。
```console
$ pip install -U ginza ja_ginza_electra
```

上記コマンドでインストールされる`ja_ginza_electra`パッケージには大容量モデルファイルは含まれていません。大容量モデルファイルは初回実行時に自動的にダウンロードされて、以降の実行時にはローカルにキャッシュされたファイルが使用されます。

大容量モデルファイルを含めたインストールを行うには、次のようにGitHubのリリースアーカイブを指定します。
```console
$ pip install -U ginza https://github.com/megagonlabs/ginza/releases/download/latest/ja_ginza_electra-latest-with-model.tar.gz
```

GPUを利用してtransformersモデルを高速に実行するには、実行環境のCUDAバージョンを指定してspacyを上書きインストールします。

CUDA 11.0を使用する場合:
```console
pip install -U "spacy[cuda110]"
```

あわせてpytorchもCUDAと整合したバージョンをインストールする必要があります。

#### 2. GiNZA + 従来型モデル

旧バージョンのGiNZAおよび`ja_ginza`をインストールしている場合は次のコマンドでアンインストールを実行します。
```console
$ pip uninstall ginza _ginza
```

次のコマンドを実行して最新のGiNZAと従来型モデルをインストールします。
```console
$ pip install -U ginza ja_ginza
```

### ginzaコマンドによる解析処理の実行

`ginza`コマンドを実行して、日本語の文に続けてEnterを入力すると、[CoNLL-U Syntactic Annotation](https://universaldependencies.org/format.html#syntactic-annotation) 形式で解析結果が出力されます。
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
実行環境に`ja_ginza_electra`と`ja_ginza`の両方のモデルがインストールされている場合、`ginza`コマンドは`ja_ginza_electra`を優先して使用します。同じ状況で`ja_ginza`を使用するには`ginza -m`オプションでモデル名を指定します。
```console
# ginza -m ja_ginza
```

また、spaCyが提供している[様々な言語の解析モデル](https://spacy.io/usage/models)の名称を`-m`オプションに指定することで、そのモデルのダウンロードと解析をまとめて実行することができます。
```console
# ginza -m en_core_web_trf
```

### Pythonコードによる解析処理の実行

次のコードは、Transformersモデルによる依存構造解析結果を文単位で出力します。
従来型モデルを用いる場合は`ja_ginza_electra`を`ja_ginza`に置き換えます。
```python
import spacy
nlp = spacy.load('ja_ginza_electra')
doc = nlp('銀座でランチをご一緒しましょう。')
for sent in doc.sents:
    for token in sent:
        print(
            token.i,
            token.orth_,
            token.lemma_,
            token.norm_,
            token.morph.get("Reading"),
            token.pos_,
            token.morph.get("Inflection"),
            token.tag_,
            token.dep_,
            token.head.i,
        )
    print('EOS')
```

## 解説資料

### マニュアル

- [コマンドラインツールの解説](./command_line_tool.md)
- [文節APIの解説](./bunsetu_api.md)
- [開発者向けの情報](./developer_reference.md)

### 講演資料

- [日本語Universal Dependenciesのための学習済みTransformersモデル公開に向けて](https://docs.google.com/presentation/d/1vJ-CeOwq0SG7KvjizjFOTh4A3-_nhY0b57NuKs-mow0/edit) - 第3回 Universal Dependencies 公開研究会 (2021.06)
- [Japanese Language Analysis by GPU Ready Open Source NLP Frameworks](https://storage.googleapis.com/megagon-publications/GPU_Technology_Conference_2020/Japanese-Language-Analysis-by-GPU-Ready-Open-Source-NLP-Frameworks_Hiroshi-Matsuda.pdf) - NVIDIA GPU Technology Conference 2020 (2020.10)
- [GiNZAで始める日本語依存構造解析 〜CaboCha, UDPipe, Stanford NLPとの比較〜](https://www.slideshare.net/MegagonLabs/ginza-cabocha-udpipe-stanford-nlp) - Universal Dependencies Symposium (2019.09)

### 論文

- [GiNZA - Universal Dependenciesによる実用的日本語解析](https://www.jstage.jst.go.jp/article/jnlp/27/3/27_695/_pdf) - 自然言語処理 Volume 27 Number 3 (2020.09)
- [UD Japanese GSD の再整備と固有表現情報付与](https://anlp.jp/proceedings/annual_meeting/2020/pdf_dir/P1-34.pdf) - 言語処理学会第26回年次大会 (2020.03)
- [短単位品詞の用法曖昧性解決と依存関係ラベリングの同時学習](https://www.anlp.jp/proceedings/annual_meeting/2019/pdf_dir/F2-3.pdf) - 言語処理学会第25回年次大会 (2019.03)

### 解説記事

- [GiNZA Version 4.0: Improving Syntactic Structure Analysis Through Japanese Bunsetsu-Phrase Extraction API Integration](https://megagon.ai/blog/ginza-version-4-0-improving-syntactic-structure-analysis-through-japanese-bunsetsu-phrase-extraction-api-integration/) - Megagon Labs Blog (2021.03)
- [GiNZA version 4.0: 多言語依存構造解析技術への文節APIの統合](https://www.megagon.ai/jp/blog/ginza-version-4-0/) - Megagon Labs Blog (2020.09)
- [GiNZA: 日本語自然言語処理オープンソースライブラリ](https://www.megagon.ai/jp/projects/ginza-install-a-japanese-nlp-library-in-one-step/) - Megagon Labs (2019)

## ライセンス
GiNZA NLPライブラリおよびGiNZA日本語Universal Dependenciesモデルは
[The MIT License](https://github.com/megagonlabs/ginza/blob/master/LICENSE)のもとで公開されています。
利用にはThe MIT Licenseに合意し、規約を遵守する必要があります。

### Explosion/ spaCy
GiNZAはspaCyをNLP Frameworkとして使用しています。

[spaCy LICENSE PAGE](https://github.com/explosion/spaCy/blob/master/LICENSE)

### Works Applications Enterprise / Sudachi/SudachiPy - SudachiDict - chiVe
GiNZAはトークン化（形態素解析）処理にSudachiPyを、単語ベクトル表現にchiVeを使用することで、高い解析精度を得ています。

[Sudachi LICENSE PAGE](https://github.com/WorksApplications/Sudachi/blob/develop/LICENSE-2.0.txt),
[SudachiPy LICENSE PAGE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE),
[SudachiDict LEGAL PAGE](https://github.com/WorksApplications/SudachiDict/blob/develop/LEGAL),
[chiVe LICENSE PAGE](https://github.com/WorksApplications/chiVe/blob/master/LICENSE)

### Hugging Face / transformers
GiNZA v5 Transformersモデル(ja_ginza_electra)はHugging Face社が提供するtransformersを事前学習フレームワークに用いています。

[transformers LICENSE PAGE](https://github.com/huggingface/transformers/blob/master/LICENSE)

## 訓練コーパス

### UD Japanese BCCWJ r2.8
GiNZA v5の依存構造解析モデルは
[UD Japanese BCCWJ](https://github.com/UniversalDependencies/UD_Japanese-BCCWJ) r2.8
([Omura and Asahara:2018](https://www.aclweb.org/anthology/W18-6014/))
から新聞系文書を除外して学習しています。
GiNZA v5の依存構造解析モデルは国立国語研究所とMegagon Labsの共同研究成果です。

### GSK2014-A (2019) BCCWJ版
GiNZA v5の固有表現抽出モデルは
[GSK2014-A](https://www.gsk.or.jp/catalog/gsk2014-a/) (2019) BCCWJ版
([橋本・乾・村上(2008)](https://www.anlp.jp/proceedings/annual_meeting/2010/pdf_dir/C4-4.pdf))
から新聞系文書を除外して学習しています。
固有表現抽出ラベル体系は[関根の拡張固有表現階層](http://liat-aip.sakura.ne.jp/ene/ene8/definition_jp/html/enedetail.html)、
および、[OntoNotes5](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf)
を独自に拡張したものを併用しています。
GiNZA v5の固有表現抽出モデルは国立国語研究所とMegagon Labsの共同研究成果です。

### mC4
GiNZA v5 Transformersモデル(ja_ginza_electra)は、[mC4](https://huggingface.co/datasets/mc4)から抽出した日本語20億文以上を用いて事前学習した[transformers-ud-japanese-electra-base-discriminator](https://huggingface.co/megagonlabs/transformers-ud-japanese-electra-base-discriminator)を使用しています。
mC4はODC-BYライセンスの規約に基づいて事前学習データとして利用しています。

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



## [リリース履歴](https://github.com/megagonlabs/ginza/releases)

### version 5.x

#### ginza-5.1.0
- 2021-12-10, Euclase
- 重要な変更
  - spaCy v3.2 および Sudachi.rs(SudachiPy v0.6.2) に対応
  - トークンの活用・読み・正規形の保存先をTokenクラスのフィールドに変更 #208 #209
    - `doc.user_data[“reading_forms”][token.i]` -> `token.morph.get(“Reading”)`
    - `doc.user_data[“inflections”][token.i]` -> `token.morph.get(“Inflection”)`
    - `force_using_normalized_form_as_lemma(True)` -> `token.norm_`
  - ginzaコマンドで日本語以外を含む全てのspaCyモデルが利用可能に #217
    - `ginza -m en_core_web_md` の形でモデル名を指定することでモデルのダウンロードと解析をまとめて実行 #219
  - `ginza --require_gpu`および`ginza -g`オプションがgpu_idを引数を取る形に変更
    - -1を指定(デフォルト)するとCPUのみを使用
  - ginza -f json で -c オプションの指定に関わらず#で始まるはもすべて解析対象とする #215
- Improvements
  - バッチ解析処理をGPU環境で50〜60%・CPU環境で10〜40%高速化
  - ginzaコマンドの並列実行オプション(`ginza -p {n_process}`および`ginzame`)の処理効率を向上 #204
  - [ginzaコマンドの解説ページ](https://megagonlabs.github.io/ginza/command_line_tool.html)の記述を拡充 #201
  - add tests #198 #210 #214
  - add benchmark #207 #220

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
- 重要な変更
  - プラットフォームをspaCy v3に変更
  - transformersモデルを採用して飛躍的に精度を向上した解析モデルパッケージ`ja-ginza-electra`をリリースしました。
  - 従来型の解析モデルパッケージ`ja-ginza`のpiplelineに`morphologizer`を追加し、UD品詞解析精度を向上しました。
  - transformersモデルの追加に伴いGiNZA v5インストール時は`ginza`パッケージとともに解析モデルパッケージを明示的に指定する必要があります
    - 解析精度重視モデル (メモリ容量16GB以上を推奨)
      - `pip install -U ginza ja-ginza-electra`
    - 実行速度重視モデル
      - `pip install -U ginza ja-ginza`
  - `CompoundSplitter`および`BunsetuRecognizer`の名称を`compound_splitter`および`bunsetu_recognizer`に変更しました
  - 併せてspaCy v3の[Backwards Incompatibilities](https://spacy.io/usage/v3#incompat)も確認してください
- Improvements
  - Add command line options
    - `Token.lemma_`にSudachiPyのnormalized_formを強制的にセットするオプション`-n`を追加しました。
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
