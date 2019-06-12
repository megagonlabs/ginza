# encoding: utf8
from __future__ import unicode_literals, print_function

from spacy.attrs import LANG
from spacy.language import Language
from spacy.tokens import Token
from spacy.util import get_model_meta
from spacy.vocab import Vocab
from .sudachi_tokenizer import SudachiTokenizer, TAG_MAP
from .japanese_corrector import JapaneseCorrector
from .syntax_iterators import SYNTAX_ITERATORS

__all__ = [
    'Japanese',
]


Language.factories['JapaneseCorrector'] = lambda nlp, **cfg: JapaneseCorrector(nlp)

if not Token.get_extension('inf'):
    Token.set_extension('inf', default='')
if not Token.get_extension('bunsetu_bi_label'):
    Token.set_extension('bunsetu_bi_label', default='')
if not Token.get_extension('bunsetu_position_type'):
    Token.set_extension('bunsetu_position_type', default='')


class JapaneseDefaults(Language.Defaults):
    lex_attr_getters = dict(Language.Defaults.lex_attr_getters)
    lex_attr_getters[LANG] = lambda text: 'ja'

    tag_map = TAG_MAP
    syntax_iterators = SYNTAX_ITERATORS  # TODO not works for spaCy 2.0.12, see work around in JapaneseCorrector

    @classmethod
    def create_tokenizer(cls, nlp=None):
        return SudachiTokenizer(nlp)

    @classmethod
    def create_lemmatizer(cls, nlp=None):
        return None

    @classmethod
    def create_vocab(cls, nlp=None):
        lex_attr_getters = dict(cls.lex_attr_getters)
        vocab = Vocab(lex_attr_getters=lex_attr_getters, tag_map=cls.tag_map,
                      lemmatizer=None)
        for tag_str, exc in cls.morph_rules.items():
            for orth_str, attrs in exc.items():
                vocab.morphology.add_special_case(tag_str, orth_str, attrs)
        return vocab


class Japanese(Language):
    lang = 'ja'
    Defaults = JapaneseDefaults
    Tokenizer = SudachiTokenizer

    def load(self, model_path, **overrides):
        meta = get_model_meta(model_path)
        pipeline = meta.get('pipeline', [])
        disable = overrides.get('disable', [])
        if pipeline is True:
            pipeline = JapaneseDefaults.pipe_names
        elif pipeline in (False, None):
            pipeline = []
        for name in pipeline:
            if name not in disable:
                config = meta.get('pipeline_args', {}).get(name, {})
                component = self.create_pipe(name, config=config)
                self.add_pipe(component, name=name)
        self.from_disk(model_path)
        return self

    def make_doc(self, text):
        return self.tokenizer(text)
