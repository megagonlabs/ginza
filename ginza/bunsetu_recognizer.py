from typing import Iterable, List

from spacy.language import Language
from spacy.tokens import Doc, Span, Token

__all__ = [
    "bunsetu_span",
    "bunsetu_spans",
    "bunsetu_phrase_span",
    "bunsetu_phrase_spans",
    "bunsetu_head_list",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "BunsetuRecognizer",
    "append_bunsetu_head_dep_suffix",
    "BUNSETU_HEAD_SUFFIX",
    "PHRASE_RELATIONS",
    "POS_PHRASE_MAP",
]


BUNSETU_HEAD_SUFFIX = "_bunsetu"

PHRASE_RELATIONS = ("compound", "nummod", "nmod")

POS_PHRASE_MAP = {
    "NOUN": "NP",
    "NUM": "NP",
    "PRON": "NP",
    "PROPN": "NP",

    "VERB": "VP",

    "ADJ": "ADJP",

    "ADV": "ADVP",

    "CCONJ": "CCONJP",
}


def bunsetu_head_list(span: Span) -> Iterable[int]:
    doc = span.doc
    heads = doc.user_data["bunsetu_heads"]
    if isinstance(span, Doc):
        start = 0
        end = len(span)
    else:
        start = span.start
        end = span.end
    return [i - start for i in heads if start <= i < end]


def bunsetu_head_tokens(span: Span) -> Iterable[Token]:
    doc = span.doc
    heads = doc.user_data["bunsetu_heads"]
    if isinstance(span, Doc):
        start = 0
        end = len(span)
    else:
        start = span.start
        end = span.end
    return [span[i - start] for i in heads if start <= i < end]


def bunsetu_spans(span: Span) -> Iterable[Span]:
    return [
        bunsetu_span(head) for head in bunsetu_head_tokens(span)
    ]


def bunsetu_span(token: Token) -> Span:
    bunsetu_bi_list = bunsetu_bi_labels(token.doc)
    start = token.i
    end = start + 1
    for idx in range(start, 0, -1):
        if bunsetu_bi_list[idx] == "B":
            start = idx
            break
    else:
        start = 0
    doc_len = len(token.doc)
    for idx in range(end, doc_len):
        if bunsetu_bi_list[idx] == "B":
            end = idx
            break
    else:
        end = doc_len

    doc = token.doc
    return Span(doc, start=start, end=end, label=POS_PHRASE_MAP.get(doc[start:end].root.pos_, ""))


def bunsetu_phrase_spans(span: Span, phrase_relations: Iterable[str] = PHRASE_RELATIONS) -> Iterable[Span]:
    return [
        bunsetu_phrase_span(head, phrase_relations) for head in bunsetu_head_tokens(span)
    ]


def bunsetu_phrase_span(token: Token, phrase_relations: Iterable[str] = PHRASE_RELATIONS) -> Span:
    def _traverse(head, _bunsetu, result):
        for t in head.children:
            if _bunsetu.start <= t.i < _bunsetu.end:
                if t.dep_ in phrase_relations:
                    _traverse(t, _bunsetu, result)
        result.append(head.i)
    bunsetu = bunsetu_span(token)
    phrase_tokens = []
    _traverse(bunsetu.root, bunsetu, phrase_tokens)
    start = min(phrase_tokens)
    end = max(phrase_tokens) + 1
    return Span(token.doc, start=start, end=end, label=bunsetu.label_)


def bunsetu_bi_labels(span: Span) -> List[str]:
    doc = span.doc
    bunsetu_bi = doc.user_data["bunsetu_bi_labels"]
    if isinstance(span, Doc):
        start = 0
        end = len(span)
    else:
        start = span.start
        end = span.end
    return bunsetu_bi[start:end]


class BunsetuRecognizer:
    def __init__(self, nlp: Language, **_cfg) -> None:
        self.nlp = nlp

    def __call__(self, doc: Doc, debug: bool = False) -> Doc:
        heads = [False] * len(doc)
        for t in doc:
            if t.dep_ == "ROOT":
                heads[t.i] = True
            elif t.dep_.endswith(BUNSETU_HEAD_SUFFIX):
                heads[t.i] = True
                t.dep_ = t.dep_[:-len(BUNSETU_HEAD_SUFFIX)]
        for t in doc:  # recovering uncovered subtrees
            if heads[t.i]:
                while t.head.i < t.i and not heads[t.head.i]:
                    heads[t.head.i] = t.head.pos_ not in {"PUNCT"}
                    if debug and heads[t.head.i]:
                        print("========= A", t.i + 1, t.orth_, "=========")
                        print(list((t.i + 1, t.orth_, t.head.i + 1) for t, is_head in zip(doc, heads) if is_head))
                    t = t.head
                heads[t.head.i] = True

        for ent in doc.ents:  # removing head inside ents
            head = ent.root
            if head is not None:
                for t in ent:
                    if t.i != head.i:
                        heads[t.i] = False

        """
        for t in doc:
            if heads[t.i]:
                continue
            if t.i < t.head.i:
                for idx in range(t.i + 1, t.head.i):
                    if heads[idx]:
                        heads[t.i] = t.pos_ not in {"PUNCT"}
                        if debug and heads[t.i]:
                            print("========= B", t.i + 1, t.orth_, "=========")
                            print(list((t.i + 1, t.orth_, t.head.i + 1) for t, is_head in zip(doc, heads) if is_head))
                        break
            else:
                for idx in range(t.head.i + 1, t.i):
                    if heads[idx]:
                        heads[t.i] = t.pos_ not in {"PUNCT"}
                        if debug and heads[t.i]:
                            print("========= C", t.i + 1, t.orth_, "=========")
                            print(list((t.i + 1, t.orth_, t.head.i + 1) for t, is_head in zip(doc, heads) if is_head))
                        break
        """
        bunsetu_heads = tuple(idx for idx, is_head in enumerate(heads) if is_head)

        bunsetu_bi = ["I"] * len(doc)
        next_start = 0
        for head_i in bunsetu_heads:
            t = doc[head_i]
            if next_start < len(bunsetu_bi):
                bunsetu_bi[next_start] = "B"
            right = t
            for sub in t.rights:
                if heads[sub.i]:
                    right = right.right_edge
                    break
                right = sub
            next_start = right.i + 1

        doc.user_data["bunsetu_heads"] = bunsetu_heads
        doc.user_data["bunsetu_bi_labels"] = bunsetu_bi
        return doc


def append_bunsetu_head_dep_suffix(tokens: List[Token], suffix: str = BUNSETU_HEAD_SUFFIX) -> None:
    if not suffix:
        return
    for token in tokens:
        if token.dep_.lower() == "root":
            return
        if token.head.i < tokens[0].i or tokens[-1].i < token.head.i:
            token.dep_ += suffix
            return
