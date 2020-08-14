from functools import singledispatch
from typing import Callable, List, TypeVar

from spacy.lang.ja import DetailedToken
from spacy.language import Language
from spacy.tokens import Token

from .bunsetu_recognizer import *
from .compound_splitter import *
from .ene_ontonotes_mapper import ENE_ONTONOTES_MAPPING


__all__ = [
    "set_split_mode",
    "token_i", "text", "text_with_ws", "orth", "orth_",
    "ent_type", "ent_type_", "ent_iob", "ent_iob_",
    "lemma", "lemma_", "norm", "norm_",
    "pos", "pos_", "tag", "tag_", "dep", "dep_",
    "is_stop", "is_not_stop",
    "ent_label_ene", "ent_label_ontonotes",
    "reading_form", "inflection",
    "SEP", "default_join_func",
    "head", "ancestors", "conjuncts", "children", "subtree",
    "bunsetu", "phrase", "sub_phrases",
    "sub_tokens",
    # from bunsetu_recognizer
    "bunsetu_span",
    "bunsetu_spans",
    "bunsetu_phrase_span",
    "bunsetu_phrase_spans",
    "bunsetu_head_list",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "BunsetuRecognizer",
    # from compound_splitter
    "CompoundSplitter",
    "tag_to_pos",
]


def set_split_mode(nlp: Language, mode: str):
    splitter = nlp.get_pipe("CompoundSplitter")
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

def reading_form(token: Token) -> str:
    return token.doc.user_data["reading_forms"][token.i]


def inflection(token: Token) -> str:
    return token.doc.user_data["inflections"][token.i]


SEP = "+"


def default_join_func(elements):
    return SEP.join([element if isinstance(element, str) else str(element) for element in elements])


S = TypeVar('S')
T = TypeVar('T')
U = TypeVar('U')


# curried function: ex. head(lemma_)(token)
@singledispatch
def head(element_func: Callable[[Token], T]) -> T:
    return lambda token: element_func(token.head)


# overload: ex. head(token, lemma_)
@head.register
def _head(token: Token, element_func: Callable[[Token], T] = lambda token: token) -> T:
    return head(element_func)(token)


def _traverse(
        traverse_func: Callable[[Token], List[Token]],
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return lambda token: join_func([element_func(t) for t in traverse_func(token) if condition_func(t)])


# curried function: ex. ancestors(lemma_)(token)
@singledispatch
def ancestors(
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return _traverse(lambda t: t.ancestors, element_func, condition_func, join_func)


# overload: ex. ancestors(token, lemma_)
@ancestors.register
def _ancestors(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return ancestors(element_func, condition_func, join_func)(token)


# curried function: ex. conjuncts(lemma_)(token)
@singledispatch
def conjuncts(
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return _traverse(lambda t: t.conjuncts, element_func, condition_func, join_func)


# overload: ex. conjuncts(token, lemma_)
@ancestors.register
def _conjuncts(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return conjuncts(element_func, condition_func, join_func)(token)


# curried function: ex. children(lemma_)(token)
@singledispatch
def children(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return _traverse(lambda t: t.children, element_func, condition_func, join_func)


# overload: ex. children(token, lemma_)
@children.register
def _children(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return children(element_func, condition_func, join_func)(token)


# curried function: ex. subtree()(token)
@singledispatch
def subtree(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return _traverse(lambda token: token.subtree, element_func, condition_func, join_func)


# overload: ex. subtree(token, lemma_)
@subtree.register
def _subtree(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return subtree(element_func, condition_func, join_func)(token)


# curried function: ex. bunsetu(lemma_)(token)
@singledispatch
def bunsetu(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = default_join_func,
) -> Callable[[Token], U]:
    return lambda token: join_func([
        element_func(t) for t in bunsetu_span(token) if condition_func(t)
    ])


# overload: ex. bunsetu(token, lemma_)
@bunsetu.register
def _bunsetu(
        token: Token,
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = default_join_func,
) -> Callable[[Token], U]:
    return bunsetu(element_func, condition_func, join_func)(token)


# curried function: ex. phrase(lemma_)(token)
@singledispatch
def phrase(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = default_join_func,
) -> Callable[[Token], U]:
    return lambda token: join_func([
        element_func(t) for t in bunsetu_phrase_span(token) if condition_func(t)
    ])


# overload: ex. phrase(token, lemma_)
@phrase.register
def _phrase(
        token: Token,
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = default_join_func,
) -> Callable[[Token], U]:
    return phrase(element_func, condition_func, join_func)(token)


# curried function: ex. sub_phrases(lemma_)(token)
@singledispatch
def sub_phrases(
        phrase_func: Callable[[Token], T] = phrase,
        condition_func: Callable[[Token], bool] = is_not_stop,
        join_func: Callable[[List[S]], U] = lambda phrases: phrases,
) -> Callable[[Token], List[T]]:
    return lambda token: join_func([
        (
            t.dep_,
            phrase_func(t),
        ) for t in token.children if t.i in bunsetu_head_list(token.doc) and condition_func(t)
    ])


# overload: ex. sub_phrases(token, lemma_)
@sub_phrases.register
def _sub_phrases(
        token: Token,
        phrase_func: Callable[[Token], T] = phrase,
        condition_func: Callable[[Token], bool] = is_not_stop,
        join_func: Callable[[List[S]], U] = lambda phrases: phrases,
) -> List[T]:
    return sub_phrases(phrase_func, condition_func, join_func)(token)


# curried function: ex. sub_tokens("B", lambda sub_token: sub_token.lemma)(token)
@singledispatch
def sub_tokens(
        mode: str = "A",  # "A" or "B"
        sub_element_func: Callable[[DetailedToken], S] = lambda sub_token: sub_token,
        join_func: Callable[[List[S]], T] = default_join_func,
) -> Callable[[Token], T]:
    return lambda token: join_func([
        sub_element_func(t) for t in token.doc.user_data["sub_tokens"][token.i][{"A": 0, "B": 1}[mode]]
    ] if token.doc.user_data["sub_tokens"][token.i] else [
        sub_element_func(DetailedToken(
            token.orth_,
            token.tag_,
            inflection(token),
            token.lemma_,
            reading_form(token),
            None,
        ))
    ])


# overload: ex. sub_tokens(token, "B", lambda sub_token: sub_token.lemma)
@sub_tokens.register
def _sub_tokens(
        token: Token,
        mode: str = "A",  # "A" or "B"
        sub_element_func: Callable[[DetailedToken], S] = lambda sub_token: sub_token,
        join_func: Callable[[List[S]], T] = default_join_func,
) -> List[dict]:
    return sub_tokens(mode, sub_element_func, join_func)(token)
