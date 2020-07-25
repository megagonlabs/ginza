# encoding: utf8
from __future__ import unicode_literals, print_function

from .bunsetu_recognizer import *
from .compound_splitter import CompoundSplitter
from .ene_ontonotes_mapper import ENE_ONTONOTES_MAPPING


SEP = "+"


# token field getters

def token_i(token):
    return token.i


def text(token):
    return token.text


def text_with_ws(token):
    return token.text_with_ws


def orth(token):
    return token.orth


def orth_(token):
    return token.orth_


def ent_type(token):
    return token.ent_type


def ent_type_(token):
    return token.ent_type_


def ent_iob(token):
    return token.ent_iob


def ent_iob_(token):
    return token.ent_iob_


def lemma(token):
    return token.lemma


def lemma_(token):
    return token.lemma_


def norm(token):
    return token.norm


def norm_(token):
    return token.norm_


def pos(token):
    return token.pos


def pos_(token):
    return token.pos_


def tag(token):
    return token.tag


def tag_(token):
    return token.tag_


def dep(token):
    return token.dep


def dep_(token):
    return token.dep_


def is_stop(token):
    return token.is_stop


def is_not_stop(token):
    return not token.is_stop


def ent_label_ene(token):
    if token.ent_iob_ in "BI":
        return token.ent_iob_ + "-" + token.ent_type_
    else:
        return token.ent_iob_


def ent_label_ontonotes(token):
    if token.ent_iob_ in "BI":
        return token.ent_iob_ + "-" + ENE_ONTONOTES_MAPPING.get(token.ent_type_, "OTHERS")
    else:
        return token.ent_iob_


# token field getters for Doc.user_data

def reading_form(token):
    return token.doc.user_data["reading_forms"][token.i]


def inflection(token):
    return token.doc.user_data["inflections"][token.i]


# curried function for sub token extraction

def sub_tokens(mode="A", sub_element_func=lambda sub_token: sub_token, gather=lambda lst: lst):
    return lambda token: gather([
        sub_element_func(t) for t in token.doc.user_data["sub_tokens"][{"A": 0, "B": 1}[mode]][token.i]
    ])


# curried functions for dependency tree traversing

def head(element_func):
    return lambda token: element_func(token.head)


def ancestors(element_func, condition_func=lambda token: True, sep=SEP):
    return traverse(lambda t: t.ancestors, element_func, condition_func, sep)


def children(element_func, condition_func=lambda token: True, sep=SEP):
    return traverse(lambda t: t.children, element_func, condition_func, sep)


def subtree(element_func, condition_func=lambda token: True, sep=SEP):
    return traverse(lambda token: token.subtree, element_func, condition_func, sep)


def traverse(traverse_func, element_func, condition_func=lambda token: True, sep=SEP):
    return lambda token: sep.join([element_func(t) for t in traverse_func(token) if condition_func(t)])


def bunsetu(element_func=lambda t: t, sep=SEP):
    return lambda bunsetu_head_token: sep.join(
        element_func(t) for t in bunsetu_tokens(bunsetu_head_token)
    )


def phrase(element_func=lambda t: t, sep=SEP):
    return lambda bunsetu_head_token: sep.join(
        element_func(t) for t in bunsetu_phrase_tokens(bunsetu_head_token)
    )


def sub_phrases(
        phrase_func=phrase,
        condition_func=is_not_stop,
):
    return lambda bunsetu_head_token: [
        (
            t.dep_,
            phrase_func(t),
        ) for t in bunsetu_head_token.children if t.i in bunsetu_heads(bunsetu_head_token.doc) and condition_func(t)
    ]


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
    "bunsetu", "phrase", "sub_phrases",
    # from bunsetu_recognizer
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
]
