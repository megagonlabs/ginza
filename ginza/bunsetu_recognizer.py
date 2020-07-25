# encoding: utf8

__all__ = [
    "BUNSETU_HEAD_SUFFIX",
    "PHRASE_RELATIONS",
    "POS_PHRASE_MAP",
    "bunsetu_heads",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "bunsetu_bounds",
    "bunsetu_tokens",
    "bunsetu_phrase",
    "bunsetu_phrase_tokens",
    "BunsetuRecognizer",
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


def bunsetu_heads(span):
    doc = span.doc
    heads = doc.user_data.get("bunsetu_heads", None)
    if heads is None or span is doc:
        return heads
    else:
        return [i - span.start for i in heads if span.start <= i < span.end]


def bunsetu_head_tokens(doc):
    return [
        doc[i] for i in bunsetu_heads(doc)
    ]


def bunsetu_bi_labels(span):
    doc = span.doc
    bunsetu_bi = doc.user_data.get("bunsetu_bi_labels", None)
    if bunsetu_bi is None or span is doc:
        return bunsetu_bi
    else:
        return bunsetu_bi[span.start:span.end]


def bunsetu_bounds(bunsetu_head_token):
    bunsetu_bi_list = bunsetu_bi_labels(bunsetu_head_token.doc)
    begin = bunsetu_head_token.i
    end = begin + 1
    for idx in range(begin, 0, -1):
        if bunsetu_bi_list[idx] == "B":
            begin = idx
            break
    else:
        begin = 0
    doc_len = len(bunsetu_head_token.doc)
    for idx in range(end, doc_len):
        if bunsetu_bi_list[idx] == "B":
            end = idx
            break
    else:
        end = doc_len
    return begin, end


def bunsetu_tokens(bunsetu_head_token):
    doc = bunsetu_head_token.doc
    begin, end = bunsetu_bounds(bunsetu_head_token)
    return doc[begin:end]


def bunsetu_phrase(bunsetu_head_token, phrase_relations=PHRASE_RELATIONS):
    def _yield(token, result):
        for t in token.children:
            if t.i not in bunsetu_head_list:
                if t.dep_ in phrase_relations:
                    _yield(t, result)
        result.append(token.i)
    bunsetu_head_list = bunsetu_heads(bunsetu_head_token.doc)
    phrase_tokens = []
    _yield(bunsetu_head_token, phrase_tokens)
    return min(phrase_tokens), max(phrase_tokens) + 1, POS_PHRASE_MAP.get(bunsetu_head_token.pos_, None)


def bunsetu_phrase_tokens(bunsetu_head_token, phrase_relations=PHRASE_RELATIONS):
    doc = bunsetu_head_token.doc
    begin, end, _ = bunsetu_phrase(bunsetu_head_token, phrase_relations=phrase_relations)
    return doc[begin:end]


class BunsetuRecognizer:
    def __init__(self, nlp, **cfg):
        self.nlp = nlp

    def __call__(self, doc, debug=False):
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
        bunsetu_head_list = tuple(idx for idx, is_head in enumerate(heads) if is_head)

        bunsetu_bi = ["I"] * len(doc)
        next_begin = 0
        for head_i in bunsetu_head_list:
            t = doc[head_i]
            if next_begin < len(bunsetu_bi):
                bunsetu_bi[next_begin] = "B"
            right = t
            for sub in t.rights:
                if heads[sub.i]:
                    right = right.right_edge
                    break
                right = sub
            next_begin = right.i + 1

        doc.user_data["bunsetu_heads"] = bunsetu_head_list
        doc.user_data["bunsetu_bi_labels"] = bunsetu_bi

        return doc


def add_head_dep_suffix(tokens, suffix="_bunsetu"):
    if not suffix:
        return
    for token in tokens:
        if token.dep_.lower() == "root":
            return
        if token.head.i < tokens[0].i or tokens[-1].i < token.head.i:
            token.dep_ += suffix
            return
