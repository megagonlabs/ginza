# encoding: utf8
from collections import OrderedDict

import srsly

from spacy import util
from spacy.language import Language
from spacy.lang.ja import resolve_pos

__all__ = [
    "CompoundSplitter",
    "tag_to_pos",
]


TAG_DEP_MAP = {
    "ADJ": "amod",
    "ADP": "case",
    "NUM": "nummod",
    "PART": "mark",
    "PUNCT": "punct",
}


def tag_dep_map(tag):
    return TAG_DEP_MAP.get(tag, "compound")


def tag_to_pos(sub_tokens, next_token_tag):
    pos_list = []
    next_pos = None
    for t1, t2 in zip(sub_tokens[:-1], sub_tokens[1:]):
        if next_pos:
            pos = next_pos
            next_pos = None
        else:
            pos, next_pos = resolve_pos(t1.surface, t1.tag, t2.tag)
        pos_list.append(pos)
    if next_pos:
        pos = next_pos
    else:
        pos, next_pos = resolve_pos(sub_tokens[-1].surface, sub_tokens[-1].tag, next_token_tag)
    pos_list.append(pos)
    return pos_list


def _replace_list_entries(lst, index, inserting_list):
    return lst[:index] + inserting_list + lst[index + 1:]


class CompoundSplitter:
    def __init__(self, nlp, split_mode=None):
        self.nlp = nlp
        self.split_mode = split_mode

    def __call__(self, doc):
        if self._split_mode is None:
            return doc
        elif self._split_mode == "C":
            del doc.user_data["sub_tokens"]
            return doc
        elif self._split_mode == "B":
            sub_tokens_index = 1
        elif self._split_mode == "A":
            sub_tokens_index = 0
        else:
            raise Exception("invalid split_mode: " + self._split_mode)

        sub_tokens_list = [
            sub_tokens[sub_tokens_index] if sub_tokens else None for sub_tokens in doc.user_data["sub_tokens"]
        ]

        for token_i, sub_tokens in reversed(tuple(zip(range(len(doc)), sub_tokens_list))):
            token = doc[token_i]
            token_ent_type = token.ent_type

            # edit token.dep_
            if token.head.i == token.i:
                dep = "ROOT"
            else:
                dep = token.dep_

            compounds = dep in {"compound", "nummod", "punct"}

            # retokenize
            if sub_tokens_index is not None and sub_tokens:
                deps = [tag_dep_map(dtoken.tag) for dtoken in sub_tokens[:-1]] + [token.dep_]
                last = len(sub_tokens) - 1
                if token.head.i == token.i:
                    heads = [(token, last) for _ in range(last + 1)]
                elif compounds:
                    heads = [token.head for _ in range(len(sub_tokens))]
                else:
                    heads = [(token, last) for _ in range(last)] + [token.head]
                surfaces = [dtoken.surface for dtoken in sub_tokens]
                attrs = {
                    "TAG": [dtoken.tag for dtoken in sub_tokens],
                    "DEP": deps,
                    "POS": tag_to_pos(
                        sub_tokens,
                        doc[token.i + 1].tag_ if token.i < len(doc) - 1 else None
                    )
                }
                try:
                    with doc.retokenize() as retokenizer:
                        retokenizer.split(token, surfaces, heads=heads, attrs=attrs)
                except Exception as e:
                    import sys
                    print("Retokenization error:", file=sys.stderr)
                    print(doc.text, file=sys.stderr)
                    print([(t.i, t.orth_) for t in doc], file=sys.stderr)
                    print(list(enumerate(doc.user_data["sub_tokens"])), file=sys.stderr)
                    raise e

                # work-around: retokenize() does not consider the head of the splitted tokens
                if not compounds:
                    for t in doc:
                        if t.i < token_i or token_i + len(sub_tokens) <= t.i:
                            if t.head.i == token_i:
                                t.head = doc[token_i + last]

                for t, dtoken in zip(
                    doc[token_i:token_i + len(sub_tokens)],
                    sub_tokens
                ):
                    t.lemma_ = dtoken.lemma

                if token_ent_type:  # work-around: _retokenize() sets value for Token.ent_iob but not for ent_type
                    for t in doc[token_i + 1:token_i + len(sub_tokens)]:
                        t.ent_type = token_ent_type

                if "inflections" in doc.user_data:
                    doc.user_data["inflections"] = _replace_list_entries(
                        doc.user_data["inflections"],
                        token_i,
                        tuple(dtoken.inf for dtoken in sub_tokens),
                    )
                if "reading_forms" in doc.user_data:
                    doc.user_data["reading_forms"] = _replace_list_entries(
                        doc.user_data["reading_forms"],
                        token_i,
                        tuple(dtoken.reading for dtoken in sub_tokens),
                    )

        del doc.user_data["sub_tokens"]
        return doc

    @property
    def split_mode(self) -> str:
        return self._split_mode

    @split_mode.setter
    def split_mode(self, mode: str):
        assert mode in (None, "A", "B", "C"), 'split_mode should be "A", "B", "C", or None'
        self._split_mode = mode

    def _get_config(self):
        config = OrderedDict(
            (
                ("split_mode", self._split_mode),
            )
        )
        return config

    def _set_config(self, config=None):
        self.split_mode = config.get("split_mode", None) if config else None

    def to_bytes(self, **_kwargs):
        serializers = OrderedDict(
            (
                ("cfg", lambda: srsly.json_dumps(self._get_config())),
            )
        )
        return util.to_bytes(serializers, [])

    def from_bytes(self, data, **_kwargs):
        deserializers = OrderedDict(
            (
                ("cfg", lambda b: self._set_config(srsly.json_loads(b))),
            )
        )
        util.from_bytes(data, deserializers, [])
        return self

    def to_disk(self, path, **_kwargs):
        path = util.ensure_path(path)
        serializers = OrderedDict(
            (
                ("cfg", lambda p: srsly.write_json(p, self._get_config())),
            )
        )
        return util.to_disk(path, serializers, [])

    def from_disk(self, path, **_kwargs):
        path = util.ensure_path(path)
        serializers = OrderedDict(
            (
                ("cfg", lambda p: self._set_config(srsly.read_json(p))),
            )
        )
        util.from_disk(path, serializers, [])
