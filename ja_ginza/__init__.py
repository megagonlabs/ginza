# encoding: utf8
from __future__ import unicode_literals, print_function

import sys
import spacy
from spacy.attrs import LANG
from spacy.language import Language
from spacy.tokens import Token
from spacy.util import get_model_meta
from spacy.vocab import Vocab
from .sudachi_tokenizer import SudachiTokenizer, LANG_NAME, TAG_MAP, SUDACHI_DEFAULT_MODE
from .parse_tree import correct_dep
from .syntax_iterators import SYNTAX_ITERATORS, noun_chunks

__all__ = [
    'Japanese',
    'JapaneseCorrector',
    'load_model',
    'save_model',
    'create_model_path',
]


Language.factories['JapaneseCorrector'] = lambda nlp, **cfg: JapaneseCorrector(nlp)

if not Token.get_extension('pos_detail'):
    Token.set_extension('pos_detail', default='')
if not Token.get_extension('inf'):
    Token.set_extension('inf', default='')


class JapaneseDefaults(Language.Defaults):
    lex_attr_getters = dict(Language.Defaults.lex_attr_getters)
    lex_attr_getters[LANG] = lambda text: LANG_NAME

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
    lang = LANG_NAME
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


def load_model(model_path):
    if model_path is None:
        model_path = '{}_bccwj_ud'.format(Japanese.lang)
        print("Loading model '%s'" % model_path, file=sys.stderr)
        return spacy.load(model_path)
    else:
        print("Loading model '%s'" % model_path, file=sys.stderr)
        return Japanese().load(model_path)


def save_model(model_path, nlp):
    if model_path is not None:
        if not model_path.exists():
            model_path.mkdir(parents=True)
        nlp.to_disk(str(model_path))
        print("Saved to", model_path)


def create_model_path(output_dir, model_name, model_version):
    return output_dir / '{}_{}-{}'.format(Japanese.lang, model_name, model_version)


class JapaneseCorrector:
    def __init__(self, nlp=None):
        self.rewrite_ne_as_proper_noun = False

    def __call__(self, doc):
        return correct_dep(doc, self.rewrite_ne_as_proper_noun)
