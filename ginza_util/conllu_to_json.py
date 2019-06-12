# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import re
import sys
import os

import plac

from spacy.util import get_lang_class
from spacy.syntax.nonproj import is_nonproj_tree, contains_cycle

from ginza.japanese_corrector import ex_attr


SID_PATTERN = re.compile(
    r'^# sent_id = (.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
TOKEN_PATTERN = re.compile(
    r'^([1-9][0-9]*)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-9]*)\t([^\t]+)\t(_)\t([^\t]+)$'
)


def rewrite_with_tokens(gold_tokens, rewriting_gold_index, tokens):
    g = gold_tokens[rewriting_gold_index]
    g_pos = g['pos']
    t = tokens[0]
    g['orth'] = t.orth_
    g['lemma'] = t.lemma_
    g['pos'] = t.pos_
    g['tag'] = t.tag_
    g['whitespace'] = t.whitespace_ != ''
    g['dep'] = g['dep'] if g_pos == t.pos_ else '{}_as_{}'.format(g['dep'], g_pos)
    if len(tokens) == 1:
        return
    label = 'as_{}'.format(g_pos)
    others = [
        {
            'id': rewriting_gold_index + i + 1,
            'orth': t.orth_,
            'lemma': t.lemma_,
            'pos': t.pos_,
            'tag': t.tag_,
            'dep': label,
            'head': -(i + 1),
            'whitespace': t.whitespace_ != '',
        } for i, t in enumerate(tokens[1:])
    ]
    for g in gold_tokens:
        if g['id'] <= rewriting_gold_index < g['id'] + g['head']:
            g['head'] += len(others)
        elif g['id'] + g['head'] <= rewriting_gold_index < g['id']:
            g['head'] -= len(others)
    for g in gold_tokens[rewriting_gold_index + 1:]:
        g['id'] += len(others)
    gold_tokens[rewriting_gold_index + 1:rewriting_gold_index + 1] = others


def unify_range(gold_tokens, start, end, replacing_token):
    dep_outer_id = None
    dep_outer_label = None
    head_pos = None
    for g in gold_tokens[start:end]:
        head_id = g['id'] + g['head']
        if head_id < start or end <= head_id or g['head'] == 0:
            if dep_outer_id is None:
                dep_outer_id = head_id
                dep_outer_label = g['dep']
                head_pos = g['pos']
            elif dep_outer_id != head_id:
                return False
    if dep_outer_id is None:
        print(gold_tokens[start:end], file=sys.stderr)
        raise Exception('unexpected state')
    elif start < dep_outer_id < end:
        dep_outer_id = start

    origin = gold_tokens[start]
    origin['orth'] = replacing_token.orth_
    origin['lemma'] = replacing_token.lemma_
    origin['pos'] = replacing_token.pos_
    origin['tag'] = replacing_token.tag_
    origin['inf'] = ex_attr(replacing_token).inf
    origin['whitespace'] = replacing_token.whitespace_ != ''
    origin['head'] = dep_outer_id - start
    origin['dep'] = dep_outer_label if head_pos == origin['pos'] else '{}_as_{}'.format(dep_outer_label, head_pos)

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


def retokenize(gold_tokens, doc, debug=False):
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
                rewrite_with_tokens(gold_tokens, index_g, doc[align_from_t:index_t + 1])
                index_g += index_t - align_from_t
                align_from_t = None
            elif align_from_g is not None:
                if debug:
                    _print('<', gold_tokens[align_from_g:index_g + 1], doc[index_t:index_t + 1])
                if unify_range(gold_tokens, align_from_g, index_g + 1, doc[index_t]):
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
                rewrite_with_tokens(gold_tokens, index_g, doc[index_t:index_t + 1])
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
    for g in gold_tokens:
        if g['head'] != 0 and g['tag'].endswith('可能') and g['dep'].find('as_') == -1:
            g['dep'] = '{}_as_{}'.format(g['dep'], g['pos'])
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


def convert_lines(path, lines, tokenizer, paragraph_id_regex, n_sents):
    paragraphs = []
    raw = ''
    sentences = []
    paragraph_id = None
    sentence_id = None
    sentence = ''
    tokens = []
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
                if sentences:
                    paragraphs.append({
                        'raw': raw,
                        'sentences': sentences,
                    })
                    raw = ''
                    sentences = []

            state = 'text'

        elif state == 'text':
            m = TEXT_PATTERN.match(line)
            if m is None:
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []

            sentence = m.group(1)
            raw += sentence
            state = 'ios'

        elif state == 'ios' and line != '':
            m = TOKEN_PATTERN.match(line)
            if m is None:
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
            whitespace = m.group(10).find('SpaceAfter=No') < 0
            tokens.append({
                'id': token_id,
                'orth': orth,
                'lemma': lemma,
                'pos': pos,
                'tag': tag,
                'dep': dep + '_as_' + pos if tag.endswith('可能') else dep,
                'head': head_id - token_id,
                'whitespace': whitespace,
            })

        elif state == 'ios' and line == '':
            if len(tokens) == 0:
                error_line(state, path, line_index, sentence_id, sentence, line)
                return []
            heads = [t['id'] + t['head'] for t in tokens]
            if is_nonproj_tree(heads):
                print(file=sys.stderr)
                print('skip(non-projective):', path, sentence_id, file=sys.stderr)
            elif contains_cycle(heads):
                print(file=sys.stderr)
                print('skip(cyclic)', path, sentence_id, file=sys.stderr)
            else:
                if tokenizer:
                    retokenize(tokens, tokenizer(
                        ''.join([t['orth'] + (' ' if t['whitespace'] else '') for t in tokens])
                    ))
                sentences.append({'tokens': tokens})
                if len(sentences) >= n_sents:
                    paragraphs.append({
                        'raw': raw,
                        'sentences': sentences,
                    })
                    raw = ''
                    sentences = []

            sentence_id = None
            sentence = ""
            tokens = []
            state = 'sid'

        else:
            error_line(state, path, line_index, sentence_id, sentence, line)
            return []

    if state != 'sid':
        error_line(state, path, len(lines), sentence_id, sentence, '<END OF FILE>')
        return []

    if sentences:
        paragraphs.append({
            'raw': raw,
            'sentences': sentences,
        })

    return paragraphs


def convert_files(path, tokenizer, paragraph_id_regex, n_sents):
    docs = []

    if type(path) == list:
        print('targets: {}'.format(str(path)), file=sys.stderr)
        for p in path:
            docs += convert_files(p, tokenizer, paragraph_id_regex, n_sents)
        print(file=sys.stderr, flush=True)
        return docs

    if os.path.isdir(path):
        print('loading {}'.format(str(path)), file=sys.stderr)
        for sub_path in os.listdir(path):
            docs += convert_files(os.path.join(path, sub_path), tokenizer, paragraph_id_regex, n_sents)
        print(file=sys.stderr)
    else:
        if path == '-':
            lines = sys.stdin.readlines()
        else:
            with open(str(path), 'r') as file:
                lines = file.readlines()
        paragraphs = convert_lines(path, lines, tokenizer, paragraph_id_regex, n_sents)
        docs.append({
            'id': str(path),
            'paragraphs': paragraphs,
        })
        print('.'.format(str(path)), end='', file=sys.stderr)

    sys.stderr.flush()
    return docs


def print_json(docs, file=sys.stdout):
    json.dump(docs, file, ensure_ascii=False, indent=1)
    print(file=file)


@plac.annotations(
    input_path=("Input path", "positional", None, str),
    retokenize_lang=("Retokenize", "option", "r", str),
    paragraph_id_regex=("Regex pattern for paragraph_id (default=r'')", 'option', 'p', str),
    n_sents=("Number of sentences per paragraph (default=10)", "option", "n", int),
)
def main(input_path='-', retokenize_lang='ja', paragraph_id_regex=r'^(.*)[\-:][^\-:]*$', n_sents=10):
    if retokenize_lang:
        tokenizer = get_lang_class(retokenize_lang)()
    else:
        tokenizer = None
    out = sys.stdout
    print_json(convert_files(input_path, tokenizer, paragraph_id_regex, n_sents), out)


if __name__ == '__main__':
    plac.call(main)
