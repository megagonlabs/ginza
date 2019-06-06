# encoding: utf8
from .parse_tree import correct_dep, set_bunsetu_bi_type

__all__ = [
    'JapaneseCorrector',
]


class JapaneseCorrector:
    def __init__(self, nlp, **cfg):
        self.nlp = nlp

    def __call__(self, doc):
        correct_dep(doc)
        set_bunsetu_bi_type(doc)
        return doc
