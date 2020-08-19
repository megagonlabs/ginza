# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import random
import re
import sys
import os

import plac

from spacy.util import get_lang_class
from spacy.syntax.nonproj import is_nonproj_tree, contains_cycle


NEW_DOC_ID_PATTERN = re.compile(
    r'^# newdoc id = (.+)$'
)

SID_PATTERN = re.compile(
    r'^# sent_id = (.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
TEXT_EN_PATTERN = re.compile(
    r'^# text_en = (.+)$'
)
TOKEN_PATTERN = re.compile(
    r'^([1-9][0-9]*)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-9]*)\t([^\t]+)\t(_)\t([^\t]+)$'
)
BUNSETU_PATTERN = re.compile(r"BunsetuBILabel=(.)")
NE_PATTERN = re.compile(r'NE=([^|]+)([|]|$)')

SPACY_NE_EXCEPTIONAL_CHARS = [".", ",", "!", "?", "'"]


def unify_range(gold_tokens, start, end, replacing_token, extend_dep_labels):
    head = None
    dep_outer_id = None
    dep_outer_label = None
    for g in gold_tokens[start:end]:
        head_id = g['id'] + g['head']
        if head_id < start or end <= head_id or g['head'] == 0:
            if dep_outer_id is None:
                head = g['id']
                dep_outer_id = head_id
                dep_outer_label = g['dep']
            elif dep_outer_id == head_id:
                head = head_id
            else:
                return False
    if dep_outer_id is None:
        print(gold_tokens[start:end], file=sys.stderr)
        raise Exception('unexpected state')
    elif start < dep_outer_id < end:
        dep_outer_id = start
    '''
    if start < end - 2:
        for g in gold_tokens[start:end]:
            if g['id'] == head:
                continue
            print(
                'left' if head == start else (
                    'outer' if head < start or end <= head else (
                        'mid' if head < end - 1 else 'final'
                    )
                ),
                g['dep'],
                g['pos'],
                ' '.join(g['orth'] for g in gold_tokens[start:end]),
                sep='\t',
            )
    '''
    g = gold_tokens[start]
    g['orth'] = replacing_token.orth_
    g['lemma'] = replacing_token.lemma_
    g['pos'] = replacing_token.pos_
    g['tag'] = replacing_token.tag_
    g['whitespace'] = replacing_token.whitespace_ != ''
    g['head'] = dep_outer_id - start
    g['dep'] = dep_outer_label

    for g in gold_tokens:
        if g['id'] <= start and end <= g['id'] + g['head']:
            g['head'] -= end - start - 1
        elif g['id'] <= start < g['id'] + g['head']:
            g['head'] = start - g['id']
        elif g['id'] + g['head'] <= start and end <= g['id']:
            g['head'] += end - start - 1
        elif g['id'] + g['head'] < end <= g['id']:
            g['head'] = end - g['id'] - 1
    for g in gold_tokens[end:]:
        g['id'] -= end - start - 1
    del gold_tokens[start + 1:end]

    return True


def _print(_prefix, _golds, _doc):
    print('{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
        _prefix,
        len(_golds),
        len(_doc),
        ','.join([g['pos'] for g in _golds]),
        ','.join([t.tag_ for t in _doc]),
        ','.join([g['orth'] for g in _golds]),
        ','.join([t.orth_ for t in _doc]))
    )


def retokenize(gold_tokens, doc, extend_dep_labels, debug=False):
    if debug:
        print(doc.text)
        print([g['orth'] + (' ' if g['whitespace'] else '') for g in gold_tokens])
        print([t.orth_ + t.whitespace_ for t in doc])
    length = len(doc.text)
    index_g = 0
    g_offset = 0
    index_t = 0
    t_offset = 0
    align_from_g = None
    align_from_t = None
    last_aligned_g = 0
    last_aligned_t = 0
    while g_offset < length and t_offset < length:
        g = gold_tokens[index_g]
        g_end = g_offset + len(g['orth'])
        if g['whitespace']:
            g_end += 1
        t = doc[index_t]
        t_end = t_offset + len(t.orth_)
        if t.whitespace_:
            t_end += 1
        if debug:
            print(index_g, g_offset, g_end, g['orth'], align_from_g, index_t, t_offset, t_end, t.orth_, align_from_t)
        if g_end == t_end:
            if align_from_t is not None:
                if debug:
                    _print('>', gold_tokens[index_g:index_g + 1], doc[align_from_t:index_t + 1])
                align_from_t = None
            elif align_from_g is not None:
                if debug:
                    _print('<', gold_tokens[align_from_g:index_g + 1], doc[index_t:index_t + 1])
                if unify_range(gold_tokens, align_from_g, index_g + 1, doc[index_t], extend_dep_labels):
                    index_g = align_from_g
                align_from_g = None
            elif g_offset == t_offset:
                if debug:
                    tag = g['tag'] == t.tag_
                    _print(
                        '==' if tag else '=',
                        gold_tokens[index_g:index_g + 1],
                        doc[index_t:index_t + 1]
                    )
            else:
                if debug:
                    _print('!', gold_tokens[last_aligned_g:index_g + 1], doc[last_aligned_t:index_t + 1])
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
    if last_aligned_g != len(gold_tokens) or g_offset != length or t_offset != length:
        raise Exception(
            'Unexpected state: len(gold_tokens)={},last_aligned_g={},len(gold)={},g_offset={},t_offset={}'.format(
                len(gold_tokens),
                last_aligned_g,
                length,
                g_offset,
                t_offset,
            )
        )
    heads = [g['id'] + g['head'] for g in gold_tokens]
    if is_nonproj_tree(heads):
        print(list(enumerate(heads)), file=sys.stderr)
        for t in gold_tokens:
            print(t, file=sys.stderr)
        raise Exception('non-projective')
    elif contains_cycle(heads):
        print(list(enumerate(heads)), file=sys.stderr)
        for t in gold_tokens:
            print(t, file=sys.stderr)
        raise Exception('cyclic')


def convert_lines(path, lines, tokenizer, paragraph_id_regex, n_sents, extend_dep_labels, ensure_end_period, _print_bunsetu_dep=False):
    paragraphs = []
    raw = ''
    sentences = []
    paragraph_id = None
    sentence_id = None
    sentence = ''
    tokens = []
    bunsetu_head_deps = {}
    bunsetu_all_deps = {}
    bunsetu_begin = None
    bunsetu_root = None
    bunsetu_head = None
    bunsetu_heads = None
    bunsetu_dep = None
    ent_target = False
    ents = []
    ent_start_char = None
    ent_label = None
    offset = 0
    state = 'sid'

    def error_line(_state, _path, _line_index, _sentence_id, _sentence, _line):
        print('Illegal format: state={}, file={} ({}), sent_id={}, {}'.format(
            _state, _path, _line_index + 1, _sentence_id, _sentence
        ), file=sys.stderr)
        print(_line, file=sys.stderr)
        raise ValueError

    for line_index, line in enumerate(lines):
        line = line.rstrip()

        if state == 'sid':
            m = SID_PATTERN.match(line)
            if m is None:
                m = NEW_DOC_ID_PATTERN.match(line)
                if m is not None:
                    continue
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []

            sentence_id = m.group(1)
            m = re.match(paragraph_id_regex, sentence_id)
            if m:
                new_paragraph_id = m.group(1)
            else:
                new_paragraph_id = ''
            if paragraph_id is None or paragraph_id != new_paragraph_id:
                paragraph_id = new_paragraph_id

            state = 'text'

        elif state == 'text':
            m = TEXT_PATTERN.match(line)
            if m is None:
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []

            sentence = m.group(1)
            state = 'ios'

        elif state == 'ios' and line != '':
            m = TOKEN_PATTERN.match(line)
            if m is None:
                m = TEXT_EN_PATTERN.match(line)
                if m is not None:
                    continue
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []

            token_id = int(m.group(1)) - 1
            orth = m.group(2)
            lemma = m.group(3)
            pos = m.group(4)
            tag = m.group(5)
            head_id = int(m.group(7)) - 1
            if head_id < 0:
                head_id = token_id
            dep = m.group(8)
            options = m.group(10)
            whitespace = options.find('SpaceAfter=No') < 0
            tokens.append({
                'id': token_id,
                'orth': orth,
                'lemma': lemma,
                'pos': pos,
                'tag': tag,
                'dep': dep,
                'head': head_id - token_id,
                'whitespace': whitespace,
                'ner': 'O',
            })

            m = BUNSETU_PATTERN.search(options)
            if m.group(1) == "B":
                if bunsetu_dep:
                    for h, d in bunsetu_heads:
                        assert bunsetu_begin <= h < token_id or h == bunsetu_head, str(bunsetu_heads) + line
                    if extend_dep_labels and bunsetu_dep.lower() != 'root':
                        tokens[bunsetu_root]['dep'] += '_bunsetu'
                    if bunsetu_dep not in bunsetu_head_deps:
                        bunsetu_head_deps[bunsetu_dep] = 0
                    bunsetu_head_deps[bunsetu_dep] += 1
                bunsetu_begin = token_id
                bunsetu_root = token_id
                bunsetu_head = head_id
                bunsetu_heads = []
                bunsetu_dep = dep
                bunsetu_heads.append((head_id, dep))
            elif head_id < bunsetu_begin or token_id <= bunsetu_head < head_id or dep.lower() == "root":
                bunsetu_root = token_id
                bunsetu_head = head_id
                bunsetu_dep = dep
                bunsetu_heads.append((head_id, dep))

            if bunsetu_dep not in bunsetu_all_deps:
                bunsetu_all_deps[bunsetu_dep] = 0
            bunsetu_all_deps[bunsetu_dep] += 1

            m = NE_PATTERN.search(options)
            if m:
                ent_target = True
                label = m.group(1)
                if label.startswith('B-'):
                    if ent_label:
                        print(line_index, ent_label, label, file=sys.stderr)
                        raise Exception('Bad NE label: ' + line)
                    ent_start_char = offset
                    if orth in SPACY_NE_EXCEPTIONAL_CHARS:
                        print(line_index, 'NE punctuation {} of {} dropped'.format(orth, label), file=sys.stderr)
                        if whitespace:
                            ent_start_char += 2
                        else:
                            ent_start_char += 1
                    ent_label = label[2:]
                elif label.startswith('I-'):
                    if not ent_label or ent_label != label[2:]:
                        print(line_index, ent_label, label, file=sys.stderr)
                        raise Exception('Bad NE label: ' + line)
                    if orth in ["."] and re.match(r'^([A-Z]+)$', tokens[-2]['orth']):
                        print(line_index, 'NE context including punctuation {}{} {} dropped'.format(
                            tokens[-2]['orth'], orth, label
                        ), file=sys.stderr)
                        ent_end_char = offset - 1
                        if tokens[-2]['whitespace']:
                            ent_end_char -= 1
                        if len(tokens) >= 3 and tokens[-3]['whitespace']:
                            ent_end_char -= 1
                        if ent_start_char < ent_end_char:
                            ents.append({
                                'start': ent_start_char,
                                'end': ent_end_char,
                                'label': ent_label,
                            })
                        if whitespace:
                            ent_start_char = offset + 2
                        else:
                            ent_start_char = offset + 1
                elif label.startswith('L-'):
                    if not ent_label or ent_label != label[2:]:
                        print(line_index, ent_label, label, file=sys.stderr)
                        raise Exception('Bad NE label: ' + line)
                    ent_end_char = offset + len(orth)
                    if orth in SPACY_NE_EXCEPTIONAL_CHARS:
                        print(line_index, 'NE punctuation {} of {} dropped'.format(orth, label), file=sys.stderr)
                        ent_start_char -= 1
                    elif tokens[-2]['orth'] in ["."] and re.match(r'^(x|info)$', orth):
                        print(line_index, 'NE context including punctuation {}{} {} dropped'.format(
                            tokens[-2]['orth'], orth, label
                        ), file=sys.stderr)
                        if tokens[-2]['whitespace']:
                            ent_end_char = offset - 2
                        else:
                            ent_end_char = offset - 1
                    ents.append({
                        'start': ent_start_char,
                        'end': ent_end_char,
                        'label': ent_label,
                    })
                    ent_start_char = None
                    ent_label = None
                elif label.startswith('U-'):
                    if ent_label:
                        print(line_index, ent_label, label, file=sys.stderr)
                        raise Exception('Bad NE label: ' + line)
                    if orth in SPACY_NE_EXCEPTIONAL_CHARS:
                        print(line_index, 'NE punctuation {} of {} dropped'.format(orth, label), file=sys.stderr)
                    else:
                        ents.append({
                            'start': offset,
                            'end': offset + len(orth),
                            'label': label[2:],
                        })
                        ent_start_char = None
                elif label == 'O':
                    tokens[-1]['ner'] = 'O'
                    if ent_label:
                        print(line_index, ent_label, label, file=sys.stderr)
                        raise Exception('Bad NE label: ' + line)
                else:
                    print(line_index, ent_label, label, file=sys.stderr)
                    raise Exception('Bad NE label: ' + line)
            elif ent_label:
                print(line_index, ent_label, label, file=sys.stderr)
                raise Exception('NE label not terminated: ' + line)
            offset += len(orth)
            if whitespace:
                offset += 1

        elif state == 'ios' and line == '':
            if len(tokens) == 0:
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []
            if ent_label:
                raise Exception('NE label not terminated')

            if bunsetu_dep:
                if extend_dep_labels and bunsetu_dep.lower() != 'root':
                    tokens[bunsetu_root]['dep'] += '_bunsetu'
                if bunsetu_dep not in bunsetu_head_deps:
                    bunsetu_head_deps[bunsetu_dep] = 0
                bunsetu_head_deps[bunsetu_dep] += 1

            heads = [t['id'] + t['head'] for t in tokens]
            if is_nonproj_tree(heads):
                print(file=sys.stderr)
                print('skip(non-projective):', path, sentence_id, file=sys.stderr)
            elif contains_cycle(heads):
                print(file=sys.stderr)
                print('skip(cyclic)', path, sentence_id, file=sys.stderr)
            else:
                if tokenizer:
                    retokenize(
                        tokens,
                        tokenizer(
                            ''.join([t['orth'] + (' ' if t['whitespace'] else '') for t in tokens])
                        ),
                        extend_dep_labels,
                    )
                if ent_target:
                    offset = 0
                    ent_label = None
                    ent_end = 0
                    ent_queue = []
                    for t in tokens:
                        end = offset + len(t['orth'])
                        if t['whitespace']:
                            end += 1
                        if ent_end > 0:
                            if offset < ent_end:
                                ent_queue.append(t)
                                offset = end
                                continue
                            if end >= ent_end:
                                if len(ent_queue) == 1:
                                    ent_queue[0]['ner'] = 'U-' + ent_label
                                else:
                                    ent_queue[0]['ner'] = 'B-' + ent_label
                                    for et in ent_queue[1:-1]:
                                        et['ner'] = 'I-' + ent_label
                                    ent_queue[-1]['ner'] = 'L-' + ent_label
                                ent_label = None
                                ent_end = 0
                                ent_queue.clear()
                        for ent in ents:
                            if ent['start'] < end and offset < ent['end']:
                                ent_label = ent['label']
                                ent_end = ent['end']
                                ent_queue.append(t)
                                break
                        offset = end
                    if ent_end > 0:
                        if len(ent_queue) == 1:
                            ent_queue[0]['ner'] = 'U-' + ent_label
                        else:
                            ent_queue[0]['ner'] = 'B-' + ent_label
                            for et in ent_queue[1:-1]:
                                et['ner'] = 'I-' + ent_label
                            ent_queue[-1]['ner'] = 'L-' + ent_label

                raw += sentence
                sentences.append({'tokens': tokens})
                if len(sentences) >= n_sents and (not ensure_end_period or tokens[-1]['orth'] == '。'):
                    paragraphs.append({
                        'raw': raw,
                        'sentences': sentences,
                    })
                    raw = ''
                    sentences = []

            sentence_id = None
            sentence = ""
            tokens = []
            bunsetu_begin = None
            bunsetu_head = None
            bunsetu_dep = None
            ent_target = False
            ents = []
            ent_start_char = None
            ent_label = None
            offset = 0
            state = 'sid'

        else:
            error_line(state, path, line_index, sentence_id, sentence, line)
            return []

    if state != 'sid':
        error_line(state, path, len(lines), sentence_id, sentence, '<END OF FILE>')
        return []

    if sentences:
        if not ensure_end_period or sentences[-1]['tokens'][-1]['orth'] == '。':
            paragraphs.append({
                'raw': raw,
                'sentences': sentences,
            })
        else:
            paragraph = paragraphs[-1]
            paragraphs[-1] = {
                'raw': raw + paragraphs['raw'],
                'sentences': sentences + paragraph['sentences'],
            }

    if _print_bunsetu_dep:
        for dep, count in sorted(bunsetu_head_deps.items()):
            print("bunsetu_dep:", dep, count, bunsetu_all_deps[dep], sep='\t')

    return paragraphs


def convert_files(path, tokenizer, paragraph_id_regex, n_sents, extend_dep_labels, ensure_end_period):
    docs = []

    if type(path) == list:
        print('targets: {}'.format(str(path)), file=sys.stderr)
        for p in path:
            docs += convert_files(p, tokenizer, paragraph_id_regex, n_sents, extend_dep_labels, ensure_end_period)
        print(file=sys.stderr, flush=True)
        return docs

    if os.path.isdir(path):
        print('loading {}'.format(str(path)), file=sys.stderr)
        for sub_path in os.listdir(path):
            docs += convert_files(
                os.path.join(path, sub_path),
                tokenizer,
                paragraph_id_regex,
                n_sents,
                extend_dep_labels,
                ensure_end_period,
            )
        print(file=sys.stderr)
    else:
        if path == '-':
            lines = sys.stdin.readlines()
        else:
            with open(str(path), 'r') as file:
                lines = file.readlines()
        paragraphs = convert_lines(
            path, lines, tokenizer, paragraph_id_regex, n_sents, extend_dep_labels, ensure_end_period
        )
        docs.append({
            'id': str(path),
            'paragraphs': paragraphs,
        })
        print('.'.format(str(path)), end='', file=sys.stderr)

    sys.stderr.flush()
    return docs


HALF_FULL_MAP = {
    chr(c): chr(c - ord('!') + ord('！')) for c in range(ord('!'), ord('~') + 1)
}
FULL_HALF_MAP = {
    v: k for k, v in HALF_FULL_MAP.items()
}
TURN_FULL_HALF_MAP = {}
TURN_FULL_HALF_MAP.update(FULL_HALF_MAP)
TURN_FULL_HALF_MAP.update(HALF_FULL_MAP)


def to_full(s):
    return ''.join([
        HALF_FULL_MAP[c] if c in HALF_FULL_MAP else c for c in s
    ])


def to_half(s):
    return ''.join([
        FULL_HALF_MAP[c] if c in FULL_HALF_MAP else c for c in s
    ])


def turn_full_half(s):
    return ''.join([
        TURN_FULL_HALF_MAP[c] if c in TURN_FULL_HALF_MAP else c for c in s
    ])


def char_augmentation(paragraph):
    raw = ''
    sentences = []
    for sentence in paragraph['sentences']:
        text = ''.join([t['orth'] + (' ' if t['whitespace'] else '') for t in sentence['tokens']])
        turned_text = turn_full_half(str(text))
        if text == turned_text:
            continue
        # add variation of surface and lemma zenkaku-hankaku turning
        turn_surface = random.random() < 2 / 3
        if turn_surface:
            turn_lemma = random.random() < 0.5
        else:
            turn_lemma = True
        if turn_surface:
            raw += turned_text
        else:
            raw += text
        tokens = [t.copy() for t in sentence['tokens']]
        for t in tokens:
            if turn_surface:
                t['orth'] = turn_full_half(t['orth'])
            if turn_lemma:
                t['lemma'] = turn_full_half(t['lemma'])
        sentences.append({'tokens': tokens})
    if sentences:
        return [paragraph, {'raw': raw, 'sentences': sentences}]
    else:
        return [paragraph]


def print_json(docs, file=sys.stdout):
    json.dump(docs, file, ensure_ascii=False, indent=1)
    print(file=file)


@plac.annotations(
    input_path=("Input path", "positional", None, str),
    retokenize=("Retokenize", "flag", "r"),
    extend_dep_labels=("Extend dep labels", "flag", "e"),
    paragraph_id_regex=("Regex pattern for paragraph_id (default=r'')", 'option', 'p', str),
    n_sents=("Number of sentences per paragraph (default=10)", "option", "n", int),
    augmentation=("Enable Zenkaku/Hankaku augmentation", "flag", "a"),
    ensure_end_period=("Docs always end with period", "flag", "d"),
)
def main(
        input_path='-',
        retokenize=False,
        extend_dep_labels=False,
        paragraph_id_regex=r'^(.*)[\-:][^\-:]*$',
        n_sents=10,
        augmentation=False,
        ensure_end_period=False,
):
    if retokenize:
        tokenizer = get_lang_class('ja')()
    else:
        tokenizer = None
    out = sys.stdout
    docs = convert_files(input_path, tokenizer, paragraph_id_regex, n_sents, extend_dep_labels, ensure_end_period)
    if augmentation:
        random.seed(1)
        docs = [{
            'id': doc['id'],
            'paragraphs': sum([char_augmentation(p) for p in doc['paragraphs']], []),
        } for doc in docs]
    print_json(docs, out)


if __name__ == '__main__':
    plac.call(main)
