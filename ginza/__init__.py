from functools import singledispatch
from typing import Callable, Iterable, Union, Tuple, TypeVar

from sudachipy.morpheme import Morpheme

from spacy.lang.ja import DetailedToken
from spacy.language import Language
from spacy.tokens import Doc, Span, Token

from .bunsetu_recognizer import *
from .compound_splitter import *
from .disable_sentencizer import *
from .ene_ontonotes_mapper import ENE_ONTONOTES_MAPPING


__all__ = [
    "make_compound_splitter", "make_bunsetu_recognizer", "make_disable_sentencizer",
    "force_using_normalized_form_as_lemma", "set_split_mode",
    "token_i", "text", "text_with_ws", "orth", "orth_",
    "ent_type", "ent_type_", "ent_iob", "ent_iob_",
    "lemma", "lemma_", "norm", "norm_",
    "pos", "pos_", "tag", "tag_", "dep", "dep_",
    "is_sent_start", "is_stop", "is_not_stop",
    "ent_label_ene", "ent_label_ontonotes",
    "reading_form", "inflection",
    "bunsetu_bi_label", "bunsetu_position_type", "is_bunsetu_head",
    "SEP", "default_join_func",
    "traverse",
    "head", "ancestors", "conjuncts", "children", "lefts", "rights", "subtree",
    "bunsetu", "phrase", "sub_phrases", "phrases",
    "sub_tokens",
    # from bunsetu_recognizer
    "bunsetu_span",
    "bunsetu_spans",
    "bunsetu_phrase_span",
    "bunsetu_phrase_spans",
    "bunsetu_head_list",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "bunsetu_position_types",
    "BunsetuRecognizer",
    # from compound_splitter
    "CompoundSplitter",
    "tag_to_pos",
]


@Language.factory(
    "compound_splitter",
    requires=[],
    assigns=[],
    retokenizes=True,
    default_config={"split_mode": None},
)
def make_compound_splitter(
    nlp: Language,
    name: str,
    split_mode: str = None,
):
    return CompoundSplitter(
        nlp.vocab,
        split_mode,
    )


@Language.factory(
    "bunsetu_recognizer",
    requires=["token.dep"],
    assigns=["token.dep"],
    retokenizes=False,
    default_config={},
)
def make_bunsetu_recognizer(
    nlp: Language,
    name: str,
    remain_bunsetu_suffix: bool = False,
):
    return BunsetuRecognizer(
        nlp.vocab,
        remain_bunsetu_suffix,
    )

@Language.factory(
    "disable_sentencizer",
    requires=[],
    assigns=[],
    retokenizes=False,
    default_config={},
)
def make_disable_sentencizer(
    nlp: Language,
    name: str,
):
    return DisableSentencizer(
        nlp.vocab,
    )


_morpheme_dictionary_form = None


def force_using_normalized_form_as_lemma(force: bool):
    global _morpheme_dictionary_form
    if force and not _morpheme_dictionary_form:
        _morpheme_dictionary_form = Morpheme.dictionary_form
        Morpheme.dictionary_form = Morpheme.normalized_form
    elif not force and _morpheme_dictionary_form:
        Morpheme.dictionary_form = _morpheme_dictionary_form


def set_split_mode(nlp: Language, mode: str):
    splitter = nlp.get_pipe("compound_splitter")
    splitter.split_mode = mode


# token field getters

def token_i(token: Token) -> int:
    return token.i


def text(token: Token) -> str:
    return token.text


def text_with_ws(token: Token) -> str:
    return token.text_with_ws


def orth(token: Token) -> int:
    return token.orth


def orth_(token: Token) -> str:
    return token.orth_


def ent_type(token: Token) -> int:
    return token.ent_type


def ent_type_(token: Token) -> str:
    return ENE_ONTONOTES_MAPPING.get(token.ent_type_, "OTHERS")


def ent_iob(token: Token) -> int:
    return token.ent_iob


def ent_iob_(token: Token) -> str:
    return token.ent_iob_


def lemma(token: Token) -> int:
    return token.lemma


def lemma_(token: Token) -> str:
    return token.lemma_


def norm(token: Token) -> int:
    return token.norm


def norm_(token: Token) -> str:
    return token.norm_


def pos(token: Token) -> int:
    return token.pos


def pos_(token: Token) -> str:
    return token.pos_


def tag(token: Token) -> int:
    return token.tag


def tag_(token: Token) -> str:
    return token.tag_


def dep(token: Token) -> int:
    return token.dep


def dep_(token: Token) -> str:
    return token.dep_


def is_sent_start(token: Token) -> bool:
    return token.is_sent_start


def is_stop(token: Token) -> bool:
    return token.is_stop


def is_not_stop(token: Token) -> bool:
    return not token.is_stop


def ent_label_ene(token: Token) -> str:
    if token.ent_iob_ in "BI":
        return token.ent_iob_ + "-" + token.ent_type_
    else:
        return token.ent_iob_


def ent_label_ontonotes(token: Token) -> str:
    if token.ent_iob_ in "BI":
        return token.ent_iob_ + "-" + ENE_ONTONOTES_MAPPING.get(token.ent_type_, "OTHERS")
    else:
        return token.ent_iob_


# token field getters for Doc.user_data

def reading_form(token: Token, use_orth_if_none=True) -> str:
    reading = token.doc.user_data["reading_forms"][token.i]
    if not reading and use_orth_if_none:
        reading = token.orth_
    return reading


def inflection(token: Token) -> str:
    return token.doc.user_data["inflections"][token.i]


# bunsetu related field getters for Doc.user_data

def bunsetu_bi_label(token: Token):
    return bunsetu_bi_labels(token.doc)[token.i]


def bunsetu_position_type(token: Token):
    return bunsetu_position_types(token.doc)[token.i]


def is_bunsetu_head(token: Token):
    return token.i in token.doc.user_data["bunsetu_heads"]


SEP = "+"


def default_join_func(elements):
    return SEP.join([element if isinstance(element, str) else str(element) for element in elements])


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


# curried function: ex. traverse(children, lemma_)(token)
@singledispatch
def traverse(
        traverse_func: Callable[[Token], Iterable[Token]],
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = lambda lst: lst,
) -> Callable[[Union[Token, Span]], U]:
    return lambda token: join_func([
        element_func(t) for t in traverse_func(token) if condition_func(t)
    ])


# overload: ex. traverse(token, children, lemma_)
@traverse.register(Token)
def _traverse(
        token: Token,
        traverse_func: Callable[[Token], Iterable[Token]],
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = lambda lst: lst,
) -> U:
    return traverse(traverse_func, element_func, condition_func, join_func)(token)


def head(token: Token) -> Token:
    return token.head


def ancestors(token: Token) -> Iterable[Token]:
    return token.ancestors


def conjuncts(token: Token) -> Tuple[Token]:
    return token.conjuncts


def children(token: Token) -> Iterable[Token]:
    return token.children


def lefts(token: Token) -> Iterable[Token]:
    return token.lefts


def rights(token: Token) -> Iterable[Token]:
    return token.rights


def subtree(token: Token) -> Iterable[Token]:
    return token.subtree


# curried function: ex. bunsetu(lemma_)(token)
@singledispatch
def bunsetu(
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> Callable[[Token], U]:
    return traverse(bunsetu_span, element_func, condition_func, join_func)


# overload: ex. bunsetu(token, lemma_)
@bunsetu.register(Token)
def _bunsetu(
        token: Token,
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> U:
    return traverse(bunsetu_span, element_func, condition_func, join_func)(token)


# curried function: ex. phrase(lemma_)(token)
@singledispatch
def phrase(
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> Callable[[Token], U]:
    return traverse(bunsetu_phrase_span, element_func, condition_func, join_func)


# overload: ex. phrase(token)
@phrase.register(Token)
def _phrase(
        token: Token,
        element_func: Callable[[Token], T] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> U:
    return traverse(bunsetu_phrase_span, element_func, condition_func, join_func)(token)


# curried function: ex. sub_phrases(lemma_)(token)
@singledispatch
def sub_phrases(
        phrase_func: Callable[[Token], U] = _phrase,
        condition_func: Callable[[Token], bool] = lambda token: True,
) -> Callable[[Token], Iterable[Tuple[str, U]]]:
    return lambda token: _sub_phrases(
        token,
        phrase_func,
        condition_func,
    )


# overload: ex. sub_phrases(token, lemma_)
@sub_phrases.register(Token)
def _sub_phrases(
        token: Token,
        phrase_func: Callable[[Token], U] = _phrase,
        condition_func: Callable[[Token], bool] = lambda token: True,
) -> Iterable[Tuple[str, U]]:
    return [
        (
            t.dep_,
            phrase_func(t),
        ) for t in bunsetu_span(token).root.children if t.i in bunsetu_head_list(token.doc) and condition_func(t)
    ]


# curried function: ex. phrases(lemma_)(sent)
@singledispatch
def phrases(
        phrase_func: Callable[[Token], U] = _phrase,
        condition_func: Callable[[Token], bool] = lambda token: True,
) -> Callable[[Span], Iterable[U]]:
    return lambda sent: _phrases_span(
        sent,
        phrase_func,
        condition_func,
    ) if isinstance(sent, Span) else _phrases_doc(
        sent,
        phrase_func,
        condition_func,
    )


# overload: ex. phrases(sent, lemma_)
@phrases.register(Span)
def _phrases_span(
        sent: Span,
        phrase_func: Callable[[Token], U] = _phrase,
        condition_func: Callable[[Token], bool] = lambda token: True,
) -> Iterable[U]:
    return [
        phrase_func(t) for t in bunsetu_head_tokens(sent) if condition_func(t)
    ]


# overload: ex. phrases(doc, lemma_)
@phrases.register(Doc)
def _phrases_doc(
        doc: Doc,
        phrase_func: Callable[[Token], U] = _phrase,
        condition_func: Callable[[Token], bool] = lambda token: True,
) -> Iterable[U]:
    return [
        phrase_func(t) for t in bunsetu_head_tokens(doc[:]) if condition_func(t)
    ]


# curried function: ex. sub_tokens("B", lambda sub_token: sub_token.lemma)(token)
@singledispatch
def sub_tokens(
        mode: str = "A",  # "A" or "B"
        sub_token_func: Callable[[DetailedToken], T] = lambda sub_token: sub_token,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> Callable[[Token], U]:
    return lambda token: _sub_tokens(token, mode, sub_token_func, join_func)


# overload: ex. sub_tokens(token, "B", lambda sub_token: sub_token.lemma)
@sub_tokens.register(Token)
def _sub_tokens(
        token: Token,
        mode: str = "A",  # "A" or "B"
        sub_token_func: Callable[[DetailedToken], T] = lambda sub_token: sub_token.surface,
        join_func: Callable[[Iterable[T]], U] = default_join_func,
) -> U:
    if token.doc.user_data["sub_tokens"][token.i]:
        elements = token.doc.user_data["sub_tokens"][token.i][{"A": 0, "B": 1}[mode]]
    else:
        elements = [
            DetailedToken(
                token.orth_,
                token.tag_,
                inflection(token),
                token.lemma_,
                reading_form(token),
                None,
            )
        ]
    return join_func([
        sub_token_func(element) for element in elements
    ])
