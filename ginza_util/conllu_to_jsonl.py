# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import re
import sys
import os


SID_PATTERN = re.compile(
    r'^# sent_id = (.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
TOKEN_PATTERN = re.compile(
    r'^([1-9][0-9]*)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-9]*)\t([^\t]+)\t(_)\t([^\t]+)$'
)


def read_bccwj_ud(_path, file, yield_document=False):
    sentences = convert_lines(_path, file.readlines())
    for sentence in sentences:
        if not yield_document:
            yield sentence
    if yield_document:
        return sentences


def convert_file(_path):
    with open(str(_path), 'r') as file:
        return convert_lines(_path, file.readlines())


def convert_lines(_path, lines):
    docs = []
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
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            sentence_id = m.group(1)
            state = 'text'

        elif state == 'text':
            m = TEXT_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            sentence = m.group(1)
            state = 'ios'

        elif state == 'ios' and line != '':
            m = TOKEN_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            token_id = int(m.group(1)) - 1
            orth = m.group(2)
            lemma = m.group(3)
            if lemma == '*':
                lemma = orth
            pos = m.group(4)
            tag = m.group(5)
            head_id = int(m.group(7)) - 1
            if head_id == -1:
                head_id = token_id
            dep = m.group(8)
            tokens.append({
                'id': token_id,
                'dep': dep + '_as_' + pos if tag.endswith('可能') else dep,
                'head': head_id,
                'tag': tag,
                'orth': lemma,
            })

        elif state == 'ios' and line == '':
            if len(tokens) == 0:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            docs.append({
                'id': sentence_id,
                'paragraphs': [{
                    'raw': sentence,
                    'sentences': [{
                        'tokens': tokens,
                    }],
                }],
            })

            sentence_id = None
            sentence = ""
            tokens = []
            state = 'sid'

        else:
            error_line(state, _path, line_index, sentence_id, sentence, line)
            return []

    if state != 'sid':
        error_line(state, _path, len(lines), sentence_id, sentence, '<END OF FILE>')
        return []

    return docs


def convert_files(path):
    path_sentences = []

    if type(path) == list:
        print('targets: {}'.format(str(path)), file=sys.stderr)
        for p in path:
            path_sentences += convert_files(p)
        print(file=sys.stderr, flush=True)
        return path_sentences

    if os.path.isdir(path):
        print('loading {}'.format(str(path)), file=sys.stderr)
        for sub_path in os.listdir(path):
            path_sentences += convert_files(os.path.join(path, sub_path))
        print(file=sys.stderr)
    else:
        path_sentences += convert_file(path)
        print('.'.format(str(path)), end='', file=sys.stderr)

    sys.stderr.flush()
    return path_sentences


def print_jsonl(doc, file=sys.stdout):
    json.dump(doc, file, ensure_ascii=False)
    print(file=file)


def main():
    if len(sys.argv) > 1:
        for doc in convert_files(sys.argv[1:]):
            print_jsonl(doc)
    else:
        for doc in read_bccwj_ud('-', sys.stdin):
            print_jsonl(doc)


if __name__ == "__main__":
    # execute only if run as a script
    main()
