# encoding: utf8
from __future__ import unicode_literals, print_function

import json
import os
import re
import sys


SENTENCE_DIVIDER = re.compile(
    r'[ 　]*([\t\n\r]|[ 　]{5,})[ 　\t\n\r]*|' +
    r'(?<=[.．])[ 　][ 　\t\n\r]+|' +
    r'(?<=[!?！？。」】』〉》〕»›〙〛）｝］＞])[ 　]+(?![\-=~,+/*−一―‐＝≒≠≡〜￣，、。＋／÷＊×」】』〉》〕»›〙〛）｝］＞)}\]])[ 　\t\n\r]*|' +
    r'(?<=。)(?=[^ぁ-ん、。」】』〉》〕»›〙〛）｝］＞)}\] 　\t\n\r])'
)


ASCII_TO_FULL = re.compile(r'[ !-~]+')
ASCII_TO_FULL_MAP = {
    ' ': '　',
    '｡': '。', '｢': '「', '｣': '」', '､': '、', '･': '・',
    'ｦ': 'ヲ',
    'ｧ': 'ァ', 'ｨ': 'ィ', 'ｩ': 'ゥ', 'ｪ': 'ェ', 'ｫ': 'ォ',
    'ｬ': 'ャ', 'ｭ': 'ュ', 'ｮ': 'ョ', 'ｯ': 'ッ',
    'ｰ': 'ー',
    'ｱ': 'ア', 'ｲ': 'イ', 'ｳ': 'ウ', 'ｴ': 'エ', 'ｵ': 'オ',
    'ｶ': 'カ', 'ｷ': 'キ', 'ｸ': 'ク', 'ｹ': 'ケ', 'ｺ': 'コ',
    'ｻ': 'サ', 'ｼ': 'シ', 'ｽ': 'ス', 'ｾ': 'セ', 'ｿ': 'ソ',
    'ﾀ': 'タ', 'ﾁ': 'チ', 'ﾂ': 'ツ', 'ﾃ': 'テ', 'ﾄ': 'ト',
    'ﾅ': 'ナ', 'ﾆ': 'ニ', 'ﾇ': 'ヌ', 'ﾈ': 'ネ', 'ﾉ': 'ノ',
    'ﾊ': 'ハ', 'ﾋ': 'ヒ', 'ﾌ': 'フ', 'ﾍ': 'ヘ', 'ﾎ': 'ホ',
    'ﾏ': 'マ', 'ﾐ': 'ミ', 'ﾑ': 'ム', 'ﾒ': 'メ', 'ﾓ': 'モ',
    'ﾔ': 'ヤ', 'ﾕ': 'ユ', 'ﾖ': 'ヨ',
    'ﾗ': 'ラ', 'ﾘ': 'リ', 'ﾙ': 'ル', 'ﾚ': 'レ', 'ﾛ': 'ロ',
    'ﾜ': 'ワ',
    'ﾝ': 'ン',
    'ﾞ': '゛', 'ﾟ': '゜',
}
for _asc in range(ord('!'), ord('~') + 1):
    ASCII_TO_FULL_MAP[chr(_asc)] = chr(_asc - ord('!') + ord('！'))


def convert_ascii_to_full(s):
    r = ''
    pos = 0
    replacements = None
    for m in ASCII_TO_FULL.finditer(s):
        start = m.start()
        end = m.end()
        r += s[pos:start]
        org = s[start:end]
        r_start = len(r)
        for asc in org:
            c = ASCII_TO_FULL_MAP[asc]
            r += c
        if replacements is None:
            replacements = []
        replacements.append((r_start, len(r), org))
        pos = end
    if replacements:
        r += s[pos:]
        return r, replacements
    else:
        return s


def print_juman_sentence(s, out=sys.stdout):
    sentence = convert_ascii_to_full(s)
    if type(sentence) == str:
        print(sentence, file=out)
        return sentence

    sentence, replacements = sentence
    print('#\tr=%s\t#' % replacements, file=out)
    print(sentence, file=out)
    return sentence


def text_sentence(in_path, out_dir, sentence_divider=SENTENCE_DIVIDER, print_sentence_func=print_juman_sentence):
    sentence_count = 0

    def print_sentence(sentence, output=sys.stdout):
        nonlocal sentence_count
        if sentence == '^':
            return
        if sentence.startswith('^ '):
            sentence = sentence[2:]
        length = len(sentence)
        if length == 0:
            return
        if length > 2000:
            return

        sentence_count += 1
        if print_sentence_func is None:
            print(sentence, file=output)
            return sentence

        print_sentence_func(sentence, output)

    with open(in_path, 'r') as file:
        doc_id = None
        line_index = 0
        for line in file:
            doc = json.loads(line)

            if 'index' in doc:
                doc_id = doc['index']['_id']
                line_index += 1
                print('#%d id: %s' % (line_index, doc_id), file=sys.stderr, flush=True)
                continue

            text = doc['text']
            prev = 0
            filename = '{0:07d}.txt'.format((int(doc_id) // 100) * 100)
            with open(os.path.join(out_dir, filename), 'a') as out:
                print('#\td=%s\t#' % doc_id, file=out, flush=True)
                for match in sentence_divider.finditer(text):
                    print_sentence(text[prev:match.start()].strip().replace('\uFEFF', ''), out)
                    prev = match.start()
                print_sentence(text[prev:].strip(), out)


def convert_json_files(in_path, out_dir, func):
    print(in_path, file=sys.stderr, flush=True)
    if os.path.isdir(in_path):
        for sub_path in os.listdir(in_path):
            convert_json_files(os.path.join(in_path, sub_path), out_dir, func)
    elif in_path.endswith('.json'):
        func(in_path, out_dir)
    else:
        print('skipped: ' + in_path, file=sys.stderr, flush=True)


if __name__ == '__main__':
    for p in sys.argv[2:]:
        convert_json_files(p, sys.argv[1], text_sentence)
