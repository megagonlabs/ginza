# encoding: utf8
from __future__ import unicode_literals, print_function

import re
import sys
import os

from .parse_tree import Morph, ParsedSentence


SID_PATTERN = re.compile(
    r'^# sent_id = ([^_]+_([^_]+_[^_]+)-.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
MORPH_PATTERN = re.compile(
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
    sentences = []
    sentence_morphs = []
    dep_morphs = []
    sentence_id = None
    sentence_line_index = 0
    sentence = ''
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
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            sentence_id = m.group(1)
            sentence_line_index = line_index + 1
            state = 'text'

        elif state == 'text':
            m = TEXT_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            sentence = m.group(1)
            state = 'ios'

        elif state == 'ios' and line != '':
            m = MORPH_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            morph_id = int(m.group(1)) - 1
            surface = m.group(2)
            base = m.group(3)
            if base == '*':
                base = surface
            pos = m.group(4)
            dep_morph_id = int(m.group(7)) - 1
            if dep_morph_id == -1:
                dep_morph_id = morph_id
            dep_label = m.group(8)
            tag = m.group(5)

            trailing_space = 'SpaceAfter=No' not in m.group(10).split('|')

            morph = Morph(
                morph_id,
                offset,
                surface,
                base,
                pos,
                tag,
                '',
                trailing_space,
            )
            sentence_morphs.append(morph)
            dep_morphs.append(dep_morph_id)
            morph.dep_label = dep_label
            offset = morph.end

        elif state == 'ios' and line == '':
            if len(sentence_morphs) == 0:
                error_line(state, _path, line_index, sentence_id, sentence, line)
                return []

            for m, dep_morph_id in zip(sentence_morphs, dep_morphs):
                m.dep_morph = sentence_morphs[dep_morph_id]
            sentence = ''.join([m.surface + ' ' if m.trailing_space else m.surface for m in sentence_morphs])
            parsed_sentence = ParsedSentence(sentence, sentence_morphs)
            parsed_sentence.path = str(_path)
            parsed_sentence.id = sentence_id
            parsed_sentence.line = sentence_line_index
            sentences.append(parsed_sentence)

            state = 'sid'
            sentence_id = None
            sentence_line_index = 0
            sentence = ""
            offset = 0
            dep_morphs = []
            sentence_morphs = []

        else:
            error_line(state, _path, line_index, sentence_id, sentence, line)
            return []

    if state != 'sid':
        error_line(state, _path, len(lines), sentence_id, sentence, '<END OF FILE>')
        return []

    return sentences


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


def main():
    if len(sys.argv) > 1:
        for sentence in convert_files(sys.argv[1:]):
            print(str(sentence))
    else:
        for sentence in read_bccwj_ud('-', sys.stdin):
            print(str(sentence))


if __name__ == "__main__":
    # execute only if run as a script
    main()
