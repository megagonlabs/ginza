# encoding: utf8
from __future__ import unicode_literals, print_function

import sys
from spacy.tokens import Doc
from .syntax_iterators import noun_chunks

__all__ = [
    'EOS',
    'Morph',
    'ParsedSentence',
    'create_parsed_sentences',
    'trailing_spaces',
    'rewrite_by_tokenizer',
    'correct_dep',
]


EOS = '$$'


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
                    t._.pos_detail,
                    t._.inf,
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
            t._.pos_detail,
            t._.inf,
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
        words = [morph.surface for morph in self.morphs] + [EOS]
        spaces = [morph.trailing_space for morph in self.morphs] + [False]
        doc = Doc(vocab, words=words, spaces=spaces)
        root_label = None
        for token, morph in zip(doc, self.morphs):
            token.tag_ = morph.pos
            token._.pos_detail = morph.pos_detail
            token._.inf = morph.inf
            token.lemma_ = morph.lemma  # work around: lemma_ must be set after tag_ (spaCy's bug)
            if is_parsed and morph.dep_label:
                if morph.id == morph.dep_morph.id:
                    root_label = morph.dep_label
                    token.dep_ = root_label if root_label.find('as_') >= 0 else '{}_as_{}'.format(root_label, morph.pos)
                    token.head = doc[-1]
                else:
                    token.dep_ = morph.dep_label
                    token.head = doc[morph.dep_morph.id]
        doc[-1].tag_ = 'X'  # work around: lemma_ must be set after tag_ (spaCy's bug)
        doc[-1].lemma_ = EOS
        if root_label:
            doc[-1].head = doc[-1]
            doc[-1].dep_ = 'root'
            doc.is_parsed = True
        return doc

    def apply_corrector(self, vocab):
        doc = correct_dep(self.to_doc(vocab, True), False)
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
        origin.pos_detail = t._.pos_detail
        origin.inf = t._.inf
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
                t._.pos_detail,
                t._.inf,
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
        origin.pos_detail = replacing_token._.pos_detail
        origin.inf = replacing_token._.inf
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
        ','.join([t._.pos_detail for t in _tokens]),
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
                            ) == t._.pos_detail.replace(
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
            if m.pos_detail.find('可能') >= 0 and m.dep_label.find('as_') < 0:
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


def correct_dep(doc, rewrite_ne_as_proper_noun):
    complex_tokens = []
    last_head = -1
    for token in doc[0:-1]:
        label = token.dep_
        p = label.find('_as_')
        if p >= 0:
            tag = label[p + 4:]
            if len(tag) > 0:
                lemma = token.lemma_
                token.tag_ = tag  # work around: lemma_ must be set after tag_ (spaCy's bug)
                token.lemma_ = lemma
            token.dep_ = label[0:p]

    for token in doc[0:-1]:
        label = token.dep_
        if label.startswith('as_'):
            head = token.head
            if last_head == head.i:
                complex_tokens[-1].append(token)
            else:
                complex_tokens.append([token])
                last_head = token.i
            tag = label[3:]
            if len(tag) > 0:
                lemma = token.lemma_
                token.tag_ = tag  # work around: lemma_ must be set after tag_ (spaCy's bug)
                token.lemma_ = lemma
            token.dep_ = 'dep'
        else:
            complex_tokens.append([token])
            last_head = token.i
    complex_tokens.append([doc[-1]])  # for root detection error

    index = 0
    count = 0
    index_map = [0] * (len(doc) + 1)  # last element is for ner
    for comp in complex_tokens:
        for _ in comp:
            index_map[count] = index
            count += 1
        index += 1
    index_map[-1] = count

    if len(complex_tokens) > 1:
        words, lemmas, tags, pos_details, infs, spaces, sent_starts, deps, heads = zip(*[
            (
                ''.join([t.orth_ + ' ' if t.whitespace_ else t.orth_ for t in comp[0:-1]] + [comp[-1].orth_]),
                ''.join([t.lemma_ + ' ' if t.whitespace_ else t.lemma_ for t in comp[0:-1]] + [comp[-1].lemma_]),
                comp[0].pos_,
                comp[0]._.pos_detail,
                comp[-1]._.inf,
                comp[-1].whitespace_,
                True if comp[0].sent_start else False,
                comp[0].dep_,
                index_map[comp[0].head.i],
            ) if len(comp) > 1 else (
                comp[0].orth_,
                comp[0].lemma_,
                comp[0].pos_,
                comp[0]._.pos_detail,
                comp[0]._.inf,
                comp[0].whitespace_,
                True if comp[0].sent_start else False,
                comp[0].dep_,
                index_map[comp[0].head.i],
            ) for comp in complex_tokens[0:-1]
        ])
    else:
        words = lemmas = tags = pos_details = infs = spaces = sent_starts = deps = heads = []
    new_doc = Doc(doc.vocab, words=words, spaces=spaces)
    for token, lemma, tag, pos_detail, inf, dep in zip(new_doc, lemmas, tags, pos_details, infs, deps):
        token.tag_ = tag
        token.lemma_ = lemma  # work around: lemma_ must be set after tag_ (spaCy's bug)
        token._.pos_detail = pos_detail
        token._.inf = inf
        token.dep_ = dep
    for token, sent_start in zip(new_doc, sent_starts):
        if sent_start:
            token.sent_start = True
    root_i = len(new_doc)
    for token, head in zip(new_doc, heads):
        if head == root_i:
            token.head = token
        else:
            token.head = new_doc[head]

    ents = []
    prev_start = prev_end = -1
    for ent in doc.ents:
        start = index_map[ent.start]
        end = max(index_map[ent.end], start + 1)
        if prev_end > start and prev_start < end:
            ents = ents[:-1]
        ents.append((ent.label, start, end))
        prev_start = start
        prev_end = end
    new_doc.ents = ents

    new_doc.is_tagged = doc.is_tagged
    new_doc.is_parsed = doc.is_parsed

    if rewrite_ne_as_proper_noun:
        for _, start, end in ents:
            for token in new_doc[start:end]:
                lemma = token.lemma_
                token.tag_ = 'PROPN'  # work around: lemma_ must be set after tag_ (spaCy's bug)
                token.lemma_ = lemma

    new_doc.noun_chunks_iterator = noun_chunks  # TODO work around for spaCy 2.0.12

    if len(doc.text) - len(EOS) != len(new_doc.text):
        print(
            'doc.text length is different from source={} to corrected={}'.format(
                len(doc.text) - len(EOS),
                len(new_doc.text)),
            file=sys.stderr
        )
        for t in doc:
            print('<', t.i, t.orth_, t.pos_, t.dep_, t.head.i, file=sys.stderr)
        for t in new_doc:
            print('>', t.i, t.orth_, t.pos_, t.dep_, t.head.i, file=sys.stderr)

    return new_doc
