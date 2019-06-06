# encoding: utf8
from __future__ import unicode_literals, print_function

from spacy.tokens import Doc

__all__ = [
    'ex_attr',
    'Morph',
    'ParsedSentence',
    'create_parsed_sentences',
    'trailing_spaces',
    'rewrite_by_tokenizer',
    'correct_dep',
    'set_bunsetu_bi_type',
]


def ex_attr(token):
    return token._


class Morph:
    def __init__(self, _id, _offset, _surface, _lemma, _pos, _tag, _pos_detail, _inf, _trailing_space):
        self.id = _id
        self.offset = _offset
        self.surface = _surface
        self.lemma = _lemma
        self.pos = _pos
        self.tag = _tag
        self.pos_detail = _pos_detail
        self.inf = _inf
        self.trailing_space = _trailing_space
        self.dep_morph = None
        self.dep_label = None

    def __str__(self):
        if self.dep_morph is None:
            return '{},{},{},{},{}'.format(
                self.surface,
                self.lemma,
                self.pos,
                self.pos_detail.replace(',*', '').replace(',', '_'),
                self.inf.replace('*,*', '').replace(',', '_'),
            )
        else:
            return '{},{},{},{},{}/{},{},{}'.format(
                self.surface,
                self.lemma,
                self.pos,
                self.pos_detail.replace(',*', '').replace(',', '_'),
                self.inf.replace('*,*', '').replace(',', '_'),
                self.dep_label,
                self.dep_morph.id - self.id,
                self.dep_morph.surface,
            )

    @property
    def end(self):
        return self.offset + len(self.surface) + (1 if self.trailing_space else 0)


def create_parsed_sentences(doc, separate_sentences=True):
    if len(doc) == 0:
        return [ParsedSentence('', [])]
    sentences = []
    begin = 0
    base_idx = doc[0].idx
    if separate_sentences:
        for token in doc:
            if token.sent_start and token.i > 0:
                end = token.i
                morphs = [Morph(
                    i,
                    t.idx - base_idx,
                    t.orth_,
                    t.lemma_,
                    t.pos_,
                    t.tag_,
                    ex_attr(t).pos_detail,
                    ex_attr(t).inf,
                    t.whitespace_,
                ) for i, t in enumerate(doc[begin:end])]
                for m, t in zip(morphs, doc[begin:end]):
                    m.dep_morph = morphs[t.head.i - begin]
                    m.dep_label = t.dep_.lower()
                sentences.append(ParsedSentence(doc.text[base_idx:token.idx], morphs))
                begin = end
                base_idx = token.idx
    if begin < len(doc):
        morphs = [Morph(
            i,
            t.idx - base_idx,
            t.orth_,
            t.lemma_,
            t.pos_,
            t.tag_,
            ex_attr(t).pos_detail,
            ex_attr(t).inf,
            t.whitespace_,
        ) for i, t in enumerate(doc[begin:])]
        for m, t in zip(morphs, doc[begin:]):
            m.dep_morph = morphs[t.head.i - begin]
            m.dep_label = t.dep_.lower()
        sentences.append(ParsedSentence(doc.text[base_idx:], morphs))
    return sentences


class ParsedSentence(str):
    def __new__(cls, sentence, sentence_morphs):
        o = super(ParsedSentence, cls).__new__(cls, sentence)
        o.morphs = sentence_morphs
        offset = 0
        for m in sentence_morphs:
            if m == m.dep_morph:
                o.root = m
            m.offset = offset
            offset += len(m.surface)
            if m.trailing_space:
                offset += 1
        return o

    def clone(self, new_str=None):
        morphs = [
            Morph(
                m.id,
                m.offset,
                m.surface,
                m.lemma,
                m.pos,
                m.tag,
                m.pos_detail,
                m.inf,
                m.trailing_space,
            ) for m in self.morphs
        ]
        for m, s in zip(morphs, self.morphs):
            m.offset = s.offset
            m.dep_morph = morphs[s.dep_morph.id]
            m.dep_label = s.dep_label
        new_sentence = ParsedSentence(str(self) if new_str is None else new_str, morphs)
        if hasattr(self, 'origin'):
            new_sentence.origin = self.origin
        else:
            new_sentence.origin = self
        if hasattr(self, 'path'):
            new_sentence.path = self.path
        if hasattr(self, 'line'):
            new_sentence.line = self.line
        if hasattr(self, 'id'):
            new_sentence.id = self.id
        return new_sentence

    def to_doc(self, vocab, is_parsed=False):
        words = [morph.surface for morph in self.morphs]
        spaces = [morph.trailing_space for morph in self.morphs]
        doc = Doc(vocab, words=words, spaces=spaces)
        for token, morph in zip(doc, self.morphs):
            token.tag_ = morph.pos
            ex_attr(token).pos_detail = morph.pos_detail
            ex_attr(token).inf = morph.inf
            token.lemma_ = morph.lemma  # work around: lemma_ must be set after tag_ (spaCy's bug)
            if is_parsed and morph.dep_label:
                token.dep_ = morph.dep_label
                token.head = doc[morph.dep_morph.id]
        return doc

    def apply_corrector(self, vocab):
        doc = self.to_doc(vocab, True)
        correct_dep(doc)
        new_sentence = create_parsed_sentences(doc, False)[0]
        if hasattr(self, 'origin'):
            new_sentence.origin = self.origin
        else:
            new_sentence.origin = self
        if hasattr(self, 'path'):
            new_sentence.path = self.path
        if hasattr(self, 'line'):
            new_sentence.line = self.line
        if hasattr(self, 'id'):
            new_sentence.id = self.id
        return new_sentence

    def find_crossing_arcs(self):
        for m in self.morphs:
            dep_id = m.dep_morph.id
            if dep_id < m.id:
                for i in range(dep_id + 1, m.id):
                    if dep_id <= self.morphs[i].dep_morph.id <= m.id:
                        continue
                    return m, self.morphs[i]
            else:
                for i in range(m.id + 1, dep_id):
                    if m.id <= self.morphs[i].dep_morph.id <= dep_id:
                        continue
                    return m, self.morphs[i]
        return None

    def rewrite_with_tokens(self, rewriting_morph_index, tokens):
        origin = self.morphs[rewriting_morph_index]
        origin_pos = origin.pos
        t = tokens[0]
        origin.surface = t.orth_
        origin.lemma = t.lemma_
        origin.pos = t.pos_
        origin.tag = t.tag_
        origin.pos_detail = ex_attr(t).pos_detail
        origin.inf = ex_attr(t).inf
        origin.trailing_space = t.whitespace_
        if origin_pos != origin.pos:
            origin.dep_label = '{}_as_{}'.format(origin.dep_label, origin_pos)
        if len(tokens) == 1:
            return
        label = 'as_{}'.format(origin.pos.lower())
        others = [
            Morph(
                rewriting_morph_index + i + 1,
                origin.offset + t.idx - tokens[0].idx,
                t.orth_,
                t.lemma_,
                t.pos_,
                t.tag_,
                ex_attr(t).pos_detail,
                ex_attr(t).inf,
                t.whitespace_,
            ) for i, t in enumerate(tokens[1:])
        ]
        offset = origin.offset
        if origin.trailing_space:
            offset += 1
        for m in others:
            m.offset = offset
            offset += len(m.surface)
            if m.trailing_space:
                offset += 1
            m.dep_morph = origin
            m.dep_label = label
        for m in self.morphs[rewriting_morph_index+1:]:
            m.id += len(others)
        self.morphs[rewriting_morph_index+1:rewriting_morph_index+1] = others

    def unify_range(self, start, end, replacing_token):
        dep_outer_id = None
        dep_outer_label = None
        head = None
        for m in self.morphs[start:end]:
            if start <= m.dep_morph.id < end:
                if m.dep_morph.id == m.id:
                    if dep_outer_id:
                        return False
                    else:
                        dep_outer_id = m.id
                        dep_outer_label = m.dep_label
                        head = m
            elif dep_outer_id:
                if dep_outer_id == m.dep_morph.id:
                    head = m
                else:
                    return False
            else:
                dep_outer_id = m.dep_morph.id
                dep_outer_label = m.dep_label
                head = m
        if dep_outer_id is None:
            raise Exception('unexpected state')
        elif start < dep_outer_id < end:
            dep_outer_id = start

        origin = self.morphs[start]
        origin.surface = replacing_token.orth_
        origin.lemma = replacing_token.lemma_
        origin.pos = replacing_token.pos_
        origin.tag = replacing_token.tag_
        origin.pos_detail = ex_attr(replacing_token).pos_detail
        origin.inf = ex_attr(replacing_token).inf
        origin.trailing_space = replacing_token.whitespace_
        origin.dep_morph = self.morphs[dep_outer_id]
        origin.dep_label = dep_outer_label if origin.pos == head.pos else '{}_as_{}'.format(dep_outer_label, head.pos)

        for m in self.morphs:
            if start < m.dep_morph.id < end:
                m.dep_morph = origin
        del self.morphs[start + 1:end]
        for m in self.morphs:
            if m.id >= end:
                m.id -= end - start - 1

        return True

    def to_string(self):
        return '\n'.join([str(m) for m in self.morphs])


def _print(_prefix, _morphs, _tokens):
    print('{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
        _prefix,
        len(_morphs),
        len(_tokens),
        ','.join([m.pos_detail for m in _morphs]),
        ','.join([ex_attr(t).pos_detail for t in _tokens]),
        ','.join([m.surface for m in _morphs]),
        ','.join([t.orth_ for t in _tokens]))
    )


def rewrite_by_tokenizer(corpus, nlp, file=None, debug=False):
    eq = 0
    eq_pos = 0
    eq_pos_detail = 0
    fragmentation = 0
    unification = 0
    difference = 0

    for i, gold in enumerate(corpus):
        if file and i % 100 == 0:
            print('.', end='', file=file, flush=True)
        length = len(gold)
        tokens = nlp(str(gold))
        index_g = 0
        g_offset = 0
        index_t = 0
        t_offset = 0
        align_from_g = None
        align_from_t = None
        last_aligned_g = 0
        last_aligned_t = 0
        while g_offset < length and t_offset < length:
            g = gold.morphs[index_g]
            g_end = g_offset + len(g.surface)
            if g.trailing_space:
                g_end += 1
            t = tokens[index_t]
            t_end = t_offset + len(t.orth_)
            if t.whitespace_:
                t_end += 1
            # print(index_g, g_offset, g_end, g.surface, align_from_g, index_t, t_offset, t_end, t.orth_, align_from_t)
            if g_end == t_end:
                if align_from_t is not None:
                    if debug:
                        _print('>', gold.morphs[index_g:index_g + 1], tokens[align_from_t:index_t+1])
                        fragmentation += 1
                    gold.rewrite_with_tokens(index_g, tokens[align_from_t:index_t+1])
                    index_g += index_t - align_from_t
                    align_from_t = None
                elif align_from_g is not None:
                    if debug:
                        _print('<', gold.morphs[align_from_g:index_g + 1], tokens[index_t:index_t+1])
                        unification += index_g + 1 - align_from_g
                    if gold.unify_range(align_from_g, index_g + 1, tokens[index_t]):
                        index_g = align_from_g
                    align_from_g = None
                elif g_offset == t_offset:
                    if debug:
                        pos_detail = g.pos_detail.replace(
                                '-',
                                ','
                            ).replace(
                                '.*',
                                ''
                            ) == ex_attr(t).pos_detail.replace(
                                '.*',
                                ''
                            )
                        _print(
                            '==' if pos_detail else '=',
                            gold.morphs[index_g:index_g + 1],
                            tokens[index_t:index_t+1]
                        )
                        eq += 1
                        if g.pos == t.pos_:
                            eq_pos += 1
                        if pos_detail:
                            eq_pos_detail += 1
                    gold.rewrite_with_tokens(index_g, tokens[index_t:index_t + 1])
                else:
                    if debug:
                        _print('!', gold.morphs[last_aligned_g:index_g + 1], tokens[last_aligned_t:index_t + 1])
                        difference += index_g + 1 - last_aligned_g
                index_g += 1
                g_offset = g_end
                last_aligned_g = index_g
                index_t += 1
                t_offset = t_end
                last_aligned_t = index_t
            elif g_end > t_end:
                if g_offset == t_offset:
                    align_from_t = index_t
                if align_from_g is not None:
                    align_from_g = None
                index_t += 1
                t_offset = t_end
            else:
                if g_offset == t_offset:
                    align_from_g = index_g
                if align_from_t is not None:
                    align_from_t = None
                index_g += 1
                g_offset = g_end
        if last_aligned_g != len(gold.morphs) or g_offset != length or t_offset != length:
            raise Exception(
                'Unexpected state: len(gold.morphs)={},last_aligned_g={},len(gold)={},g_offset={},t_offset={}'.format(
                    len(gold.morphs),
                    last_aligned_g,
                    length,
                    g_offset,
                    t_offset,
                )
            )
        for m in gold.morphs:
            if m.pos_detail.find('可能') >= 0 and m.dep_label.find('as_') == -1:
                m.dep_label = '{}_as_{}'.format(m.dep_label, m.pos)
            elif m.id == m.dep_morph.id and m.dep_label.find('as_') < 0:
                m.dep_label = '{}_as_'.format(m.dep_label)
            # print(m.id, m.surface, m.pos, m.dep_label, m.dep_morph.surface, m.dep_morph.id)
    if debug:
        print('eq={}'.format(eq), file=file)
        print('eq_pos={}'.format(eq_pos), file=file)
        print('eq_pos_detail={}'.format(eq_pos_detail), file=file)
        print('fragmentation={}'.format(fragmentation), file=file)
        print('unification={}'.format(unification), file=file)
        print('difference={}'.format(difference), file=file)


def trailing_spaces(token):
    if token.whitespace_:
        doc = token.doc
        if token.i + 1 < len(doc):
            return doc.text[token.idx + len(token.orth_):doc[token.i + 1].idx]
        else:
            return doc.text[token.idx + len(token.orth_):]
    else:
        return None


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
