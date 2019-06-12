# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import re
import sys
import os

import plac

from spacy.syntax.nonproj import is_nonproj_tree, contains_cycle


SID_PATTERN = re.compile(
    r'^# sent_id = (.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
TOKEN_PATTERN = re.compile(
    r'^([1-9][0-9]*)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-9]*)\t([^\t]+)\t(_)\t([^\t]+)$'
)


def convert_lines(path, lines, paragraph_id_regex, n_sents):
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
            pos = m.group(4)
            tag = m.group(5)
            head_id = int(m.group(7)) - 1
            if head_id < 0:
                head_id = token_id
            dep = m.group(8)
            tokens.append({
                'id': token_id,
                'dep': dep + '_as_' + pos if tag.endswith('可能') else dep,
                'head': head_id - token_id,
                'tag': tag,
                'orth': orth,
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


def convert_files(path, paragraph_id_regex, n_sents):
    docs = []

    if type(path) == list:
        print('targets: {}'.format(str(path)), file=sys.stderr)
        for p in path:
            docs += convert_files(p, paragraph_id_regex, n_sents)
        print(file=sys.stderr, flush=True)
        return docs

    if os.path.isdir(path):
        print('loading {}'.format(str(path)), file=sys.stderr)
        for sub_path in os.listdir(path):
            docs += convert_files(os.path.join(path, sub_path), paragraph_id_regex, n_sents)
        print(file=sys.stderr)
    else:
        if path == '-':
            lines = sys.stdin.readlines()
        else:
            with open(str(path), 'r') as file:
                lines = file.readlines()
        paragraphs = convert_lines(path, lines, paragraph_id_regex, n_sents)
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
    paragraph_id_regex=("Regex pattern for paragraph_id (default=r'')", 'option', 'p', str),
    n_sents=("Number of sentences per paragraph (default=10)", "option", "n", int),
    lang=("Language (default='ja')", "option", "l", str),
)
def main(input_path='-', paragraph_id_regex=r'^(.*)[\-:][^\-:]*$', n_sents=10, lang='ja'):
    out = sys.stdout
    print_json(convert_files(input_path, paragraph_id_regex, n_sents), out)


if __name__ == '__main__':
    plac.call(main)
