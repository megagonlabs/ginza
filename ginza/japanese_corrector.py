# encoding: utf8

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


def _set_tag(token, tag):
    lemma = token.lemma_
    token.tag_ = tag  # work around: lemma_ must be set after tag_
    token.lemma_ = lemma


def correct_dep(doc):
    with doc.retokenize() as retokenizer:
        for i in range(len(doc)):
            token = doc[i]
            label = token.dep_
            p = label.find('_as_')
            if p >= 0:
                tag = label[p + 4:]
                if len(tag) > 0:
                    _set_tag(token, tag)
                token.dep_ = label[0:p]
            elif label.startswith('as_'):
                tag = label[3:]
                head = token.head
                if head.i + 1 == token.i:
                    pos_detail = '\t'.join([ex_attr(head).pos_detail, ex_attr(token).pos_detail])
                    inf = '\t'.join([ex_attr(head).inf, ex_attr(token).inf])
                    try:
                        retokenizer.merge(doc[head.i:token.i + 1], attrs={'TAG': tag})
                        token = doc[head.i]
                        ex_attr(token).pos_detail = pos_detail
                        ex_attr(token).inf = inf
                    except ValueError:
                        _set_tag(token, tag)
                elif head.i - 1 == token.i:
                    pos_detail = '\t'.join([ex_attr(token).pos_detail, ex_attr(head).pos_detail])
                    inf = '\t'.join([ex_attr(token).inf, ex_attr(head).inf])
                    try:
                        retokenizer.merge(doc[token.i:head.i + 1], attrs={'TAG': tag})
                        token = doc[token.i]
                        ex_attr(token).pos_detail = pos_detail
                        ex_attr(token).inf = inf
                    except ValueError:
                        _set_tag(token, tag)
                else:
                    _set_tag(token, tag)


FUNC_POS = {
    'AUX', 'ADP', 'SCONJ', 'CCONJ', 'PART',
}


FUNC_DEP = {
    'compound', 'case', 'mark', 'cc', 'aux', 'cop', 'nummod', 'amod', 'nmod', 'advmod', 'dep',
}


def set_bunsetu_bi_type(doc):
    if len(doc) == 0:
        ex_attr(doc).clauses = []
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
                t.dep_ == 'punct' and ex_attr(t).pos_detail.find('括弧開') < 0  # except open parenthesis
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
            t.dep_ == 'punct' and ex_attr(t).pos_detail.find('括弧開') >= 0  # open parenthesis
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

    ex_attr(doc).bunsetu_bi_label = ['B'] + [
        'I' if continuous[i - 1] == continuous[i] else 'B' for i in range(1, len(continuous))
    ]

    position_type = [
        'ROOT' if t.i == t.head.i else
        ('NO_HEAD' if t.dep_ == 'punct' else 'SEM_HEAD') if t.i == c else
        'FUNC' if t.i > c and t.pos_ in FUNC_POS else
        'CONT' for t, c in zip(doc, continuous)
    ]
    prev_c = None
    for t, p, c in zip(reversed(doc), reversed(position_type), reversed(continuous)):
        if p == 'FUNC':
            if prev_c is None or prev_c != c:
                position_type[t.i] = 'SYN_HEAD'
                prev_c = c
    ex_attr(doc).bunsetu_position_type = position_type
