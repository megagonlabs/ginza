# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import os
import re
import sys

from .parse_tree import Morph, ParsedSentence


SID_PATTERN = re.compile(
    r'# S-ID:([^ ]+) '
)
BOC_PATTERN = re.compile(
    r'^\+ ([0-9]+) (-1|[0-9]+)[A-Z](.+<ne type="([^"]+)" target="([^"]+)"( possibility="([^"]+)")?/>)?'
)
REL_PATTERN = re.compile(
    r'<rel type="(ガ|ヲ|ニ|ト|デ|カラ|ヨリ|ヘ|マデ|マデニ|'
    'トシテ|ニアワセテ|ニオイテ|ニカギッテ|ニカギラズ|ニカランデ|ニカワッテ|ニクラベテ|ニクワエテ|ニシテ|ニソッテ|ニタイシテ|ニツイテ|'
    'ニツヅイテ|ニトッテ|ニトモナッテ|ニナランデ|ニムケテ|ニモトヅイテ|ニヨッテ|ニヨラズ|ヲツウジテ|ヲノゾイテ|ヲフクメテ|ヲメグッテ'
    ')" target="([^"]+)" sid="([^"]+)" tag="([^"]+)"/>'
)
MORPH_PATTERN = re.compile(
    r'^([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+)'
)

# https://ja.wikipedia.org/wiki/%E5%9B%BA%E6%9C%89%E8%A1%A8%E7%8F%BE%E6%8A%BD%E5%87%BA
# https://spacy.io/api/annotation#named-entities
NE_TYPE_MAP = {
    'ORGANIZATION': 'ORG',
    'PERSON': 'PERSON',
    'LOCATION': 'LOC',
    'DATE': 'DATE',
    'TIME': 'TIME',
    'MONEY': 'MONEY',
    'PERCENT': 'PERCENT',
    'ARTIFACT': 'PRODUCT',
}


ASCII_ALPHA = re.compile(r'[A-Za-z]+')


def convert_ascii_alpha(s):
    r = ''
    p = 0
    for m in ASCII_ALPHA.finditer(s):
        start = m.start()
        end = m.end()
        r += s[p:start]
        for c in s[start:end]:
            r += chr(ord(c) - ord('A') + ord('Ａ'))
        p = end
    r += s[p:]
    return r


def convert_file(_path):
    sentences = []
    sentence_morphs = []
    sentence_nes = []
    # sentence_id = None
    sentence = ''
    state = 'bos'
    ne_type = None
    ne_text = None
    last_ne_offset = 0

    def error_line(_state, _path, _line_index, _line):
        print('Illegal format: state={}, file={} ({})'.format(_state, _path, _line_index + 1), file=sys.stderr)
        print(_line, file=sys.stderr)
        raise ValueError

    def end_chunk():
        pass

    with open(_path, 'r') as file:
        lines = file.readlines()

    for line_index, line in enumerate(lines):
        line = line.rstrip()

        if line[0] == '#':
            if state != 'bos':
                error_line(state, _path, line_index, line)
                return []

            m = SID_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, line)
                return []

            state = 'bob'
            # sentence_id = m.group(1)

        elif line[0] == '*':
            if state == 'ioc':
                end_chunk()
            elif state != 'bob':
                error_line(state, _path, line_index, line)
                return []

            state = 'boc'

        elif line[0] == '+':
            if state == 'ioc':
                end_chunk()
            elif state != 'boc':
                error_line(state, _path, line_index, line)
                return []

            state = 'ioc'

            m = BOC_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, line)
                return []

            if m.group(4) is not None:
                if ne_type:
                    print('could not match ne "%s" in sentence "%s" - %s' % (ne_text, sentence, _path), file=sys.stderr)
                ne_type = m.group(4)
                ne_text = convert_ascii_alpha(m.group(5))
                if ne_type == 'OPTIONAL':
                    if m.group(7) is None:
                        ne_type = None
                        ne_text = None
                    else:
                        for t in m.group(7).split(','):
                            if t != 'NONE':
                                ne_type = t

        elif line == 'EOS':
            if state != 'ioc':
                error_line(state, _path, line_index, line)
                return []

            state = 'bos'

            end_chunk()
            """
            for key in sorted(sentence_chunks):
                c = sentence_chunks[key]
                print('%d %s %s %s' % (c.id, c.head.surface, c.dep_case, c.dep_chunk.head.surface))
                for m in c.morphs:
                    print('   %d %s %s %s %s' % (m.id, m.surface, m.base, m.pos, m.inflection))
            """
            sentences.append((
                ParsedSentence(sentence, sentence_morphs),
                sentence_nes,
            ))

            if ne_type is not None:
                print('could not match ne "%s" in sentence "%s" - %s' % (ne_text,  sentence, _path), file=sys.stderr)
                ne_type = None
                ne_text = None

            # sentence_id = None
            sentence = ""
            sentence_morphs = []
            sentence_nes = []
            last_ne_offset = 0

        else:
            if state != 'ioc':
                error_line(state, _path, line_index, line)
                return

            m = MORPH_PATTERN.match(line)
            if m is None:
                error_line(state, _path, line_index, line)
                return
            surface = m.group(1)
            base = m.group(3)
            if base == '*':
                base = surface
            pos = m.group(4)
            pos_detail = m.group(4) + ',' + m.group(5)
            if m.group(6) == '*':
                inflection = None
            else:
                inflection = m.group(6) + ',' + m.group(7)

            morph = Morph(
                len(sentence_morphs),
                len(sentence),
                surface,
                base,
                pos,
                pos_detail,
                inflection,
                False,
            )
            sentence += surface
            if ne_type:
                offset = sentence.find(ne_text, last_ne_offset)
                if offset >= last_ne_offset:
                    last_ne_offset = offset + len(ne_text)
                    sentence_nes.append((offset, last_ne_offset, NE_TYPE_MAP[ne_type]))
                    ne_type = ne_text = None

            sentence_morphs.append(morph)

    return sentences


def convert_files(path, path_sentences=None):
    if path_sentences is None:
        path_sentences = []
    if os.path.isdir(path):
        for sub_path in os.listdir(path):
            convert_files(os.path.join(path, sub_path), path_sentences)
    elif path.endswith('.KNP'):
        path_sentences += convert_file(path)
    else:
        print('skipped: ' + path, file=sys.stderr)
    return path_sentences


def main():
    print('[')
    first = True
    for p in sys.argv[1:]:
        for sentence, nes in convert_files(p):
            if first:
                first = False
            else:
                print(',')
            print(json.dumps((str(sentence), nes), ensure_ascii=False))
    print(']')


if __name__ == "__main__":
    # execute only if run as a script
    main()
