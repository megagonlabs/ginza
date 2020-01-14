# encoding: utf8
from __future__ import unicode_literals, print_function

from collections import namedtuple

from spacy.attrs import LANG
from spacy.language import Language
from spacy.tokens import Token
from spacy.util import get_model_meta
from spacy.compat import copy_reg

from .stop_words import STOP_WORDS
from .syntax_iterators import SYNTAX_ITERATORS
from .tag_map import TAG_MAP

from .japanese_corrector import JapaneseCorrector
from .sudachipy_tokenizer import SudachipyTokenizer


ShortUnitWord = namedtuple("ShortUnitWord", ["surface", "lemma", "pos"])

Language.factories['JapaneseCorrector'] = lambda nlp, **cfg: JapaneseCorrector(nlp)


class JapaneseDefaults(Language.Defaults):
    lex_attr_getters = dict(Language.Defaults.lex_attr_getters)
    lex_attr_getters[LANG] = lambda _text: "ja"
    stop_words = STOP_WORDS
    tag_map = TAG_MAP
    syntax_iterators = SYNTAX_ITERATORS
    writing_system = {"direction": "ltr", "has_case": False, "has_letters": False}

    if not Token.get_extension('inf'):
        Token.set_extension('inf', default='')
    if not Token.get_extension('reading'):
        Token.set_extension('reading', default='')
    if not Token.get_extension('sudachi'):
        Token.set_extension('sudachi', default='')
    if not Token.get_extension('bunsetu_index'):
        Token.set_extension('bunsetu_index', default='')
    if not Token.get_extension('bunsetu_bi_label'):
        Token.set_extension('bunsetu_bi_label', default='')
    if not Token.get_extension('bunsetu_position_type'):
        Token.set_extension('bunsetu_position_type', default='')
    if not Token.get_extension('ne'):
        Token.set_extension('ne', default='')

    @classmethod
    def create_tokenizer(cls, nlp=None):
        return SudachipyTokenizer(nlp)

    @classmethod
    def create_lemmatizer(cls, nlp=None, lookups=None):
        return None


class Japanese(Language):
    lang = "ja"
    Defaults = JapaneseDefaults
    Tokenizer = SudachipyTokenizer

    def make_doc(self, text):
        return self.tokenizer(text)


def pickle_japanese(instance):
    return Japanese, tuple()


copy_reg.pickle(Japanese, pickle_japanese)


__all__ = [
    'Japanese',
]
