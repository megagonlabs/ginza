# encoding: utf8
from __future__ import unicode_literals, print_function

import re
import sys


ID_PATTERN = re.compile(
    r'^.*((OC|OW|OY|PB|PM|PN)(..)_([0-9]{5}))(|\..+)$'
)


def read_gsk2014a_xml(_path):
    in_text = False
    text = ''
    stack = []
    tags = []
    with open(_path, 'r') as xml:
        for line in xml:
            if line.startswith('<TEXT>'):
                in_text = True
            elif line.startswith('</TEXT>'):
                break
            elif in_text:
                prev = 0
                for m in re.finditer(r'<(/?[^>]+)>', line):
                    text += line[prev:m.start(0)]
                    prev = m.end(0)
                    tag = m.group(1)
                    offset = len(text)
                    if tag.startswith('/'):
                        begin_tag, begin = stack.pop()
                        assert begin_tag == tag[1:], _path + ' ' + str(offset) + ' ' + begin_tag + ' ' + tag
                        if not stack:
                            tags.append((begin_tag, begin, offset))
                    elif tag.startswith('rejectedBlock'):
                        return None, None
                    else:
                        stack.append((tag, offset))
                text += line[prev:]
        assert not stack, _path + ' ' + str(stack)
    return text, tags


def main():
    output_base_path = sys.argv[1]
    for conllu_path in sys.argv[2:]:
        file_id = ID_PATTERN.match(conllu_path).group(1)
        text, tags = read_gsk2014a_xml('corpus/gsk-ene-19.6.25/bccwj/xml/{}/{}.xml'.format(file_id[:2], file_id))
        tag_idx = 0
        in_tag = False
        offset = 0
        debug_sentence = ''
        output = []
        with open(conllu_path, 'r') as fin:
            for line in fin:
                line = line.rstrip('\n')
                if not text:
                    output.append((line, None))
                    continue
                if line.startswith('# text = '):
                    in_tag = False
                    debug_sentence = line
                    output.append((line, None))
                    continue
                if line.startswith('#'):
                    output.append((line, None))
                    continue
                if line == '':
                    if in_tag:  # for multi sentence NEs such as URLs
                        in_tag = False
                        l, n = output[-1]
                        if n.startswith('B'):
                            n = 'U-' + tag
                        elif n.startswith('I'):
                            n = 'L-' + tag
                        output[-1] = (l, n)
                        print(
                            'dividing ne span:',
                            file_id,
                            tag_begin,
                            tag_end,
                            tag,
                            text[tag_begin:offset].replace('\n', '\\n'),
                            '|',
                            text[offset:tag_end].replace('\n', '\\n'),
                            debug_sentence,
                            file=sys.stderr
                        )
                    output.append((line, None))
                    continue
                orth = line.split('\t')[1]
                new_offset = text.find(orth, offset)
                if new_offset == -1:
                    new_offset = text.find(orth.replace(' ', '　'), offset)
                if new_offset == -1:
                    if orth == 'ミュージカル':
                        orth = 'ミュージ\nカル'
                    elif orth == 'モテる':
                        orth = 'モテ\nる'
                    elif orth == 'すぎる':
                        orth = 'す\n\nぎる'
                    elif orth == 'いう':
                        orth = 'い\n\nう'
                    elif orth == '位置':
                        orth = '位\n置'
                    elif orth == '用いれ':
                        orth = '用\n\nいれ'
                    elif orth == '見込ま':
                        orth = '見\n\n込ま'
                    elif orth == 'なる':
                        orth = 'な\n\nる'
                    elif orth == '載せる':
                        orth = '載せ\n\nる'
                    new_offset = text.find(orth, offset)
                if new_offset - offset >= 2 and len(text[offset:new_offset].strip()) >= 2:
                    if orth == '不能':
                        orth = '不\n\n能'
                    elif orth == '退職':
                        orth = '退\n\n職'
                    elif orth == 'から':
                        orth = 'か\nら'
                    elif orth == '思う':
                        orth = '思\n\nう'
                    elif orth == '中敷き':
                        orth = '中敷\nき'
                    new_offset = text.find(orth, offset)
                assert new_offset >= 0, 'lost token: {} {}\n{}\n{}\n{}'.format(
                    file_id,
                    offset,
                    line,
                    text[offset:].replace('\n', '\\n'),
                    debug_sentence,
                )
                if text[offset:new_offset].strip() != '':
                    print(
                        'skipping text:',
                        file_id,
                        offset,
                        new_offset,
                        text[offset:new_offset].replace('\n', '\\n'),
                        debug_sentence,
                        file=sys.stderr
                    )
                offset = new_offset

                end = offset + len(orth)
                if 'SpaceAfter=No' not in line:
                    end += 1

                if tag_idx < len(tags):
                    tag, tag_begin, tag_end = tags[tag_idx]
                    if end <= tag_begin:
                        assert not in_tag, '{} {} {} {}\n{}\n{}\n{}'.format(
                            file_id,
                            offset,
                            end,
                            tag_begin,
                            tag_end,
                            line,
                            text[offset],
                        )
                        ner = 'O'
                    elif offset < tag_end and not in_tag:
                        if end < tag_end:
                            ner = 'B-' + tag
                            in_tag = True
                        else:
                            ner = 'U-' + tag
                            tag_idx += 1
                    elif end < tag_end:
                        assert in_tag, '{} {} {} {}\n{}\n{}\n{}'.format(
                            file_id,
                            offset,
                            end,
                            tag_begin,
                            tag_end,
                            line,
                            text[offset:],
                        )
                        ner = 'I-' + tag
                    elif tag_end <= end:
                        if in_tag:
                            ner = 'L-' + tag
                            tag_idx += 1
                            in_tag = False
                        elif tag_begin < offset:
                            ner = 'U-' + tag
                            tag_idx += 1
                        else:
                            ner = 'O'
                            tag_idx += 1
                            print(
                                'skipping tag:',
                                file_id,
                                tag_begin,
                                tag_end,
                                tag,
                                text[tag_begin:tag_end].replace('\n', '\\n'),
                                debug_sentence,
                                file=sys.stderr
                            )
                    else:
                        raise Exception("Unexpected state: token={} {}-{} {}, ne={}-{} {} {}".format(
                            file_id,
                            offset,
                            end,
                            text[offset:end].replace('\n', '\\n'),
                            tag_begin,
                            tag_end,
                            text[tag_begin:tag_end].replace('\n', '\\n'),
                            tag,
                        ))
                else:
                    ner = 'O'
                output.append((line, ner))
                offset = end
        if tags and tag_idx < len(tags):
            for tag_idx in range(tag_idx, len(tags)):
                print(
                    'skipping tag:',
                    file_id,
                    tag_begin,
                    tag_end,
                    text[tag_begin:tag_end].replace('\n', '\\n'),
                    '<EOF>',
                    file=sys.stderr
                )
        prev_ner = 'O'
        for line, ner in output:
            if not ner:
                ner = 'O'
            assert prev_ner[0] not in ['B', 'I'] or ner[0] in ['I', 'L'], '{}\n{} {} {}\n{}'.format(
                '\n'.join([line + ' ' + str(ner) for line, ner in output]),
                conllu_path,
                prev_ner,
                ner,
                line,
            )
            assert prev_ner[0] not in ['L', 'U', 'O'] or ner[0] in ['B', 'U', 'O'], '{}\n{} {} {}\n{}'.format(
                '\n'.join([line + ' ' + str(ner) for line, ner in output]),
                conllu_path,
                prev_ner,
                ner,
                line,
            )
            prev_ner = ner

        with open(output_base_path + '/' + conllu_path.split('/')[-1], 'w') as fout:
            for line, ner in output:
                if ner:
                    if line.endswith('\t'):
                        print(line + 'NE=' + ner, file=fout)
                    elif line.endswith('_'):
                        print(line[:-1] + '|NE=' + ner, file=fout)
                    else:
                        print(line + '|NE=' + ner, file=fout)
                else:
                    print(line, file=fout)


if __name__ == "__main__":
    # execute only if run as a script
    main()
