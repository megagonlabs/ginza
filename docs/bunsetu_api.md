# 文節APIの解説

## GiNZAの解析モデルと文節単位の解析API

GiNZA独自の文節解析モデルにより、Universal Dependenciesの枠組みの中で日本語に特徴的な文節構造を考慮することができます。

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

#### 表1 GiNZAの文節APIの一覧

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
| Clause | | |
| | clauses()                | 節単位に分割されたトークン列。(experimental) |
| | clause_head()            | トークンが属する節のヘッドとなるトークン。(experimental) |
| | clause_head_i()          | トークンが属する節のヘッドとなるトークン番号。(experimental) |

## 解説資料

詳細な解説はこちらの記事をご覧ください。

- [GiNZA version 4.0: 多言語依存構造解析技術への文節APIの統合 - Megagon Labs Blog](https://www.megagon.ai/jp/blog/ginza-version-4-0/)
- [GiNZA - Universal Dependenciesによる実用的日本語解析 - 自然言語処理 Volume 27 Number 3](https://www.jstage.jst.go.jp/article/jnlp/27/3/27_695/_article/-char/ja/)
