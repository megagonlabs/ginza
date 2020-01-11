# encoding: utf8
from .ent_type_mapping import *

__all__ = [
    'ex_attr',
    'JapaneseCorrector',
    'correct_dep',
    'set_bunsetu_bi_type',
]


def ex_attr(token):
    return token._


class JapaneseCorrector:
    def __init__(self, nlp, **cfg):
        self.nlp = nlp

    def __call__(self, doc):
        correct_dep(doc)
        set_bunsetu_bi_type(doc)
        return doc


def _as_range(token):
    begin = end = token.i
    pos = None
    while token.head.i != token.i and token.dep_.startswith('as_'):
        pos = token.dep_[3:]
        token = token.head
        if begin > token.i:
            begin = token.i
        if end < token.i:
            end = token.i
    if pos is None:
        return None
    else:
        return begin, end + 1, token.i, pos


def merge_ranges(doc):
    ranges = None
    for t in doc:
        as_range = _as_range(t)
        if as_range:
            begin, end, head_i, pos = as_range
            if ranges is None:
                ranges = [as_range]
            else:
                ranges = [r for r in ranges if r[1] <= begin or end <= r[0]]
                ranges.append(as_range)
    return ranges


def correct_dep(doc):
    for i, token in enumerate(doc):
        token = doc[i]
        label = token.dep_
        p = label.rfind('_as_')
        if p >= 0:
            corrected_pos = label[p + 4:]
            if len(corrected_pos) > 0:
                token.pos_ = corrected_pos
            dep = label[0:p]
            if dep == 'root' and token.head.i != token.i:
                token.dep_ = 'dep'
            else:
                token.dep_ = dep

    ranges = merge_ranges(doc)
    if ranges:
        with doc.retokenize() as retokenizer:
            for begin, end, head_i, pos in ranges:
                head = doc[head_i]
                tag = head.tag_
                inf = ex_attr(head).inf
                reading = ''.join([ex_attr(t).reading for t in doc[begin:end]])
                sudachi = [ex_attr(t).sudachi for t in doc[begin:end]]
                retokenizer.merge(doc[begin:end], attrs={'POS': pos, 'TAG': tag})
                ex_attr(doc[begin]).inf = inf
                ex_attr(doc[begin]).reading = reading
                ex_attr(doc[begin]).sudachi = sudachi

    for token in doc:
        if token.ent_type:
            ne_type = ENE_NE_MAPPING[token.ent_type_]
            if ne_type not in OMITTING_NE_TYPES:
                ex_attr(token).ne = '{}_{}'.format(token.ent_iob_, ne_type)


FUNC_POS = {
    'AUX', 'ADP', 'SCONJ', 'CCONJ', 'PART',
}


FUNC_DEP = {
    'compound', 'case', 'mark', 'cc', 'aux', 'cop', 'nummod', 'amod', 'nmod', 'advmod', 'dep',
}


def set_bunsetu_bi_type(doc):
    if len(doc) == 0:
        return doc

    continuous = [None] * len(doc)
    head = None
    for t in doc:
        # backward dependencies with functional relation labels
        if head is not None and (
                head == t.head.i or t.i == t.head.i + 1
        ) and (
                t.pos_ in FUNC_POS or
                t.dep_ in FUNC_DEP or
                t.dep_ == 'punct' and t.tag_.find('括弧開') < 0  # except open parenthesis
        ):
            if head < t.head.i:
                head = t.head.i
            continuous[head] = head
            continuous[t.i] = head
        else:
            head = t.i
    # print(continuous)
    head = None
    for t in reversed(doc):
        # backward dependencies with functional relation labels
        if head is not None and continuous[t.i] is None and head == t.head.i and(t.dep_ in {
            'compound', 'nummod', 'amod', 'aux',
        } or (
            t.dep_ == 'punct' and t.tag_.find('括弧開') >= 0  # open parenthesis
        )):
            continuous[t.i] = head
        else:
            head = t.i
    # print(continuous)
    head = None
    for t in doc:
        if continuous[t.i] is None:
            if head is None or t.pos_ in {'VERB', 'ADJ', 'ADV', 'INTJ'}:
                head = t.i
            continuous[t.i] = head
        else:
            head = None
    # print(continuous)

    '''
    for ne in doc.ents:  # NE spans should not be divided
        start = ne.start
        c = continuous[ne.start]
        for i in reversed(range(ne.start)):
            if continuous[i] == c:
                start = i
            else:
                break
        end = ne.end
        c = continuous[ne.end - 1]
        for i in range(ne.end, len(doc)):
            if continuous[i] == c:
                end = i + 1
            else:
                break
        outer_head = None
        for i in range(start, end):
            t = doc[i]
            if i == t.head.i or not (start <= t.head.i < end):
                if outer_head is None:
                    outer_head = i
                else:
                    break
        else:
            for i in range(start, end):
                continuous[i] = outer_head
    # print(continuous)
    '''

    index = -1
    for t, bi in zip(doc, ['B'] + [
        'I' if continuous[i - 1] == continuous[i] else 'B' for i in range(1, len(continuous))
    ]):
        if bi == 'B':
            index += 1
        ex_attr(t).bunsetu_index = index
        ex_attr(t).bunsetu_bi_label = bi

    position_type = [
        'ROOT' if t.i == t.head.i else
        ('NO_HEAD' if t.dep_ == 'punct' else 'SEM_HEAD') if t.i == c else
        'FUNC' if t.i > c and t.pos_ in FUNC_POS else
        'CONT' for t, c in zip(doc, continuous)
    ]
    prev_c = None
    for t, pt, c in zip(reversed(doc), reversed(position_type), reversed(continuous)):
        if pt == 'FUNC':
            if prev_c is None or prev_c != c:
                ex_attr(t).bunsetu_position_type = 'SYN_HEAD'
                prev_c = c
            else:
                ex_attr(t).bunsetu_position_type = pt
        else:
            ex_attr(t).bunsetu_position_type = pt
            prev_c = None
