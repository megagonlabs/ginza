from typing import Iterable, List

from spacy.language import Language
from spacy.tokens import Doc, Span, Token

__all__ = [
    "bunsetu_available",
    "bunsetu_span",
    "bunsetu_spans",
    "bunsetu_phrase_span",
    "bunsetu_phrase_spans",
    "bunsetu_head_list",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "bunsetu_position_types",
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


def bunsetu_available(span: Span):
    return "bunsetu_heads" in span.doc.user_data


def bunsetu_head_list(span: Span) -> Iterable[int]:
    doc = span.doc
    heads = doc.user_data["bunsetu_heads"]
    if isinstance(span, Doc):
        return heads
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
        if bunsetu_bi_list[idx] == "B" or token.doc[idx].is_sent_start:
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
        return bunsetu_bi
    else:
        start = span.start
        end = span.end
        return bunsetu_bi[start:end]


def bunsetu_position_types(span: Span) -> List[str]:
    doc = span.doc
    position_types = doc.user_data["bunsetu_position_types"]
    if isinstance(span, Doc):
        return position_types
    else:
        start = span.start
        end = span.end
        return position_types[start:end]


class BunsetuRecognizer:
    def __init__(self, nlp: Language, remain_bunsetu_suffix: bool = False) -> None:
        self.nlp = nlp
        self._remain_bunsetu_suffix = remain_bunsetu_suffix

    @property
    def remain_bunsetu_suffix(self) -> str:
        return self._remain_bunsetu_suffix

    @remain_bunsetu_suffix.setter
    def remain_bunsetu_suffix(self, remain: bool):
        self._remain_bunsetu_suffix = remain

    def __call__(self, doc: Doc) -> Doc:
        debug = False
        heads = [False] * len(doc)
        for t in doc:
            if t.dep_ == "ROOT":
                heads[t.i] = True
            elif t.dep_.endswith(BUNSETU_HEAD_SUFFIX):
                heads[t.i] = True
                if not self._remain_bunsetu_suffix:
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
            head = None
            outer = None
            for t in ent:
                if t.head.i == t.i or t.head.i < ent.start or ent.end <= t.head.i:
                    if not outer:
                        head = t
                        outer = t.head
                    elif outer.i != t.head.i:
                        break
            else:
                if head:
                    for t in ent:
                        if t.i != head.i:
                            heads[t.i] = False

        bunsetu_heads = tuple(idx for idx, is_head in enumerate(heads) if is_head)

        bunsetu_bi = ["I"] * len(doc)
        if bunsetu_bi:
            bunsetu_bi[0] = "B"
        for head_i, next_head_i in zip(bunsetu_heads[:-1], bunsetu_heads[1:]):
            l_head = doc[head_i]
            r_head = doc[next_head_i]
            if l_head.right_edge.i + 1 == r_head.left_edge.i or l_head.right_edge.i >= r_head.i:  # (l)(r) or (l (r))
                bunsetu_bi[r_head.left_edge.i] = "B"
            elif l_head.i <= r_head.left_edge.i:  # ((l) r)
                bunsetu_bi[l_head.right_edge.i + 1] = "B"
            else:  # ((l) (missed_tokens) (r))
                l_ancestors = set(t.i for t in l_head.ancestors)
                r_ancestors = set(t.i for t in r_head.ancestors)
                for m in doc[l_head.right_edge.i + 1: r_head.left_edge.i]:  # find closer branch
                    found = False
                    for m_ancestor in [m] + list(m.ancestors):
                        if m_ancestor.i in r_ancestors:
                            bunsetu_bi[m_ancestor.i] = "B"
                            found = True
                            break
                        elif m_ancestor.i in l_ancestors:
                            break
                    if found:
                        break
                else:
                    bunsetu_bi[l_head.right_edge.i + 1] = "B"

        doc.user_data["bunsetu_heads"] = bunsetu_heads
        doc.user_data["bunsetu_bi_labels"] = bunsetu_bi

        position_types = [None] * len(doc)
        for head in bunsetu_heads:
            phrase = bunsetu_phrase_span(doc[head])
            for t in phrase:
                if t.i == t.head.i:
                    position_types[t.i] = "ROOT"
                elif t.i == head:
                    position_types[t.i] = "NO_HEAD" if t.dep_ == "punct" else "SEM_HEAD"
                else:
                    position_types[t.i] = "CONT"
        first_func = True
        for t, bi, position_type in reversed(list(zip(doc, bunsetu_bi, position_types))):
            if bi:
                first_func = True
            if position_type is None:
                if t.pos_ in {'AUX', 'ADP', 'SCONJ', 'CCONJ', 'PART'}:
                    if first_func:
                        position_types[t.i] = "SYN_HEAD"
                        first_func = False
                    else:
                        position_types[t.i] = "FUNC"
                else:
                    position_types[t.i] = "CONT"
        doc.user_data["bunsetu_position_types"] = position_types
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
