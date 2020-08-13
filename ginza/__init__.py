from functools import singledispatch
from typing import Callable, List, TypeVar

from spacy.tokens import Token
from spacy.lang.ja import DetailedToken

from .bunsetu_recognizer import *
from .ene_ontonotes_mapper import ENE_ONTONOTES_MAPPING


SEP = "+"


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


S = TypeVar('S')
T = TypeVar('T')
U = TypeVar('U')


@singledispatch
def sub_tokens(
        mode: str = "A",
        sub_element_func: Callable[[DetailedToken], S] = lambda sub_token: sub_token,
        join_func: Callable[[List[S]], T] = lambda lst: lst,
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


@sub_tokens.register
def sub_tokens_t(
        token: Token,
        mode: str = "A",
        sub_element_func: Callable[[dict], S] = lambda sub_token: sub_token,
        join_func: Callable[[List[S]], T] = lambda lst: lst,
) -> List[dict]:
    return sub_tokens(mode, sub_element_func, join_func)(token)


# curried functions for dependency tree traversing

@singledispatch
def head(element_func: Callable[[Token], T]) -> T:
    return lambda token: element_func(token.head)


@head.register
def head_t(token: Token, element_func: Callable[[Token], T] = lambda token: token) -> T:
    return head(element_func)(token) 


@singledispatch
def ancestors(
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return traverse(lambda t: t.ancestors, element_func, condition_func, join_func)


@ancestors.register
def ancestors_t(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return ancestors(element_func, condition_func, join_func)(token)


@singledispatch
def children(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return traverse(lambda t: t.children, element_func, condition_func, join_func)


@children.register
def children_t(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return children(element_func, condition_func, join_func)(token)


@singledispatch
def subtree(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return traverse(lambda token: token.subtree, element_func, condition_func, join_func)


@subtree.register
def subtree_t(
        token: Token,
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return subtree(element_func, condition_func, join_func)(token)


@singledispatch
def traverse(
        traverse_func: Callable[[Token], List[Token]],
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return lambda token: join_func([element_func(t) for t in traverse_func(token) if condition_func(t)])


@traverse.register
def traverse_t(
        token: Token,
        traverse_func: Callable[[Token], List[Token]],
        element_func: Callable[[Token], S] = lambda token: token,
        condition_func: Callable[[Token], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return traverse(traverse_func, element_func, condition_func, join_func)(token)


@singledispatch
def bunsetu(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return lambda bunsetu_head_token: join_func([
        element_func(t) for t in bunsetu_span(bunsetu_head_token) if condition_func(t)
    ])


@bunsetu.register
def bunsetu_t(
        token: Token,
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return bunsetu(element_func, condition_func, join_func)(token)


@singledispatch
def phrase(
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return lambda bunsetu_head_token: join_func([
        element_func(t) for t in bunsetu_phrase_span(bunsetu_head_token) if condition_func(t)
    ])


@phrase.register
def phrase_t(
        token: Token,
        element_func: Callable[[T], S] = lambda token: token,
        condition_func: Callable[[T], bool] = lambda token: True,
        join_func: Callable[[List[S]], U] = lambda tokens: tokens,
) -> Callable[[Token], U]:
    return phrase(element_func, condition_func, join_func)(token)


@singledispatch
def sub_phrases(
        phrase_func: Callable[[Token], T] = phrase,
        condition_func: Callable[[Token], bool] = is_not_stop,
) -> Callable[[Token], List[T]]:
    return lambda bunsetu_head_token: [
        (
            t.dep_,
            phrase_func(t),
        ) for t in bunsetu_head_token.children if t.i in bunsetu_head_list(bunsetu_head_token.doc) and condition_func(t)
    ]


@sub_phrases.register
def sub_phrases_t(
        token: Token,
        phrase_func: Callable[[Token], T] = phrase,
        condition_func: Callable[[Token], bool] = is_not_stop,
) -> List[T]:
    return sub_phrases(phrase_func, condition_func)(token)


__all__ = [
    "token_i", "text", "text_with_ws", "orth", "orth_",
    "ent_type", "ent_type_", "ent_iob", "ent_iob_",
    "lemma", "lemma_", "norm", "norm_",
    "pos", "pos_", "tag", "tag_", "dep", "dep_",
    "is_stop", "is_not_stop",
    "ent_label_ene", "ent_label_ontonotes",
    "reading_form", "inflection",
    "sub_tokens",
    "head", "ancestors", "children", "subtree", "traverse",
    "phrase", "sub_phrases",
    # from bunsetu_recognizer
    "bunsetu",
    "bunsetu_head_list",
    "bunsetu_head_tokens",
    "bunsetu_bi_labels",
    "bunsetu_span",
    "bunsetu_phrase_span",
    "BUNSETU_HEAD_SUFFIX",
    "PHRASE_RELATIONS",
    "POS_PHRASE_MAP",
]
