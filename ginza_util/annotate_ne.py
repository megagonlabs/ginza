# coding: utf8
import re
import sys
import plac
import spacy
from sudachipy.tokenizer import Tokenizer as OriginalTokenizer
from ginza.sudachi_tokenizer import SUDACHI_DEFAULT_MODE


SID_PATTERN = re.compile(
    r'^# sent_id = (.+)$'
)
TEXT_PATTERN = re.compile(
    r'^# text = (.+)$'
)
MORPH_PATTERN = re.compile(
    r'^([1-9][0-9]*)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([0-9]*)\t([^\t]+)\t(_)\t([^\t]+)$'
)


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    mode=("sudachi mode", "option", "m", str),
)
def main(
        model_path=None,
        mode=SUDACHI_DEFAULT_MODE,
):
    nlp = spacy.load(model_path)

    if mode == 'A':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.A
    elif mode == 'B':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.B
    elif mode == 'C':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.C
    else:
        raise Exception('mode should be A, B or C')
    print("mode is {}".format(mode), file=sys.stderr)
    nlp.tokenizer.use_sentence_separator = False

    in_file = sys.stdin
    out_file = sys.stdout

    start = None
    ents = None
    ne_start = None
    for line in in_file.readlines():
        line = line.rstrip()
        m = TEXT_PATTERN.match(line)
        if m:
            text = m.group(1)
            start = 0
            ents = nlp(text).ents
            ne_start = -1
        else:
            m = MORPH_PATTERN.match(line)
            if m:
                end = start + len(m.group(2))
                if m.group(10).find('SpaceAfter=No') < 0:
                    start += 1
                m = re.search(r'NE=([^|]+)', m.group(10))
                if m:
                    gold = m.group(1)
                else:
                    gold = ''
                label = ''
                for s in ents:
                    if s.start_char < end and start < s.end_char:
                        if ne_start < 0 or ne_start != s.start_char:
                            label = 'B-' + s.label_
                            ne_start = s.start_char
                        else:
                            label = 'I-' + s.label_
                        break
                else:
                    ne_start = -1
                if gold and not label:
                    line += '|>'
                elif gold != label:
                    line += '|NE=' + label + '>'
                print(line, file=out_file)
                start = end
                continue
        print(line, file=out_file)


if __name__ == '__main__':
    plac.call(main)
