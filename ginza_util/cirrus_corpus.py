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
    replaced = False
    for m in ASCII_TO_FULL.finditer(s):
        start = m.start()
        end = m.end()
        r += s[pos:start]
        org = s[start:end]
        r_start = len(r)
        for asc in org:
            c = ASCII_TO_FULL_MAP[asc]
            r += c
        replaced = True
        pos = end
    if replaced:
        r += s[pos:]
        return r
    else:
        return s


def text_sentence(input, output, sentence_divider=SENTENCE_DIVIDER):
    sentence_count = 0

    def print_sentence(sentence):
        nonlocal sentence_count, output
        sentence = convert_ascii_to_full(sentence)
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
        print(sentence, file=output)

    doc_id = None
    line_index = 0
    for line in input:
        doc = json.loads(line)

        if 'index' in doc:
            doc_id = doc['index']['_id']
            line_index += 1
            print('#%d id: %s' % (line_index, doc_id), file=sys.stderr, flush=True)
            continue

        text = doc['text']
        prev = 0
        for match in sentence_divider.finditer(text):
            print_sentence(text[prev:match.start()].strip().replace('\uFEFF', ''))
            prev = match.start()
        print_sentence(text[prev:].strip().replace('\uFEFF', ''))


if __name__ == '__main__':
    text_sentence(sys.stdin, sys.stdout)
