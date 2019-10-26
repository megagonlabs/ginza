# coding: utf8
from pathlib import Path
import plac
import spacy
import sys
from sudachipy.tokenizer import Tokenizer as OriginalTokenizer
from .japanese_corrector import JapaneseCorrector
from .sudachi_tokenizer import SUDACHI_DEFAULT_MODE


def ex_attr(token):
    return token._


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    mode=("sudachi mode", "option", "m", str),
    use_sentence_separator=("enable sentence separator", "flag", "s"),
    disable_pipes=("disable pipes (csv)", "option", "d"),
    recreate_corrector=("recreate corrector", "flag", "c"),
    output_format=("output format", "option", "f", str, ['0', 'conllu', '1', 'cabocha']),
    output_path=("output path", "option", "o", Path),
    require_gpu=("enable require_gpu", "flag", "g"),
)
def run(
        model_path=None,
        mode=SUDACHI_DEFAULT_MODE,
        use_sentence_separator=False,
        disable_pipes='',
        recreate_corrector=False,
        output_path=None,
        output_format='0',
        require_gpu=False,
        *files,
):
    if require_gpu:
        spacy.require_gpu()
        print("GPU enabled", file=sys.stderr)
    if model_path:
        nlp = spacy.load(model_path)
    else:
        nlp = spacy.load('ja_ginza')
    if disable_pipes:
        print("disabling pipes: {}".format(disable_pipes), file=sys.stderr)
        nlp.disable_pipes(disable_pipes)
        print("using : {}".format(nlp.pipe_names), file=sys.stderr)
    if recreate_corrector:
        if 'JapaneseCorrector' in nlp.pipe_names:
            nlp.remove_pipe('JapaneseCorrector')
        corrector = JapaneseCorrector(nlp)
        nlp.add_pipe(corrector, last=True)

    if mode == 'A':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.A
    elif mode == 'B':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.B
    elif mode == 'C':
        nlp.tokenizer.mode = OriginalTokenizer.SplitMode.C
    else:
        raise Exception('mode should be A, B or C')
    print("mode is {}".format(mode), file=sys.stderr)
    if not use_sentence_separator:
        print("disabling sentence separator", file=sys.stderr)
        nlp.tokenizer.use_sentence_separator = False

    if output_path:
        output = open(str(output_path), 'w')
    else:
        output = sys.stdout

    try:
        if files:
            for path in files:
                with open(path, 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    print_result(line, nlp, True, output_format, output)
        else:
            while True:
                line = input()
                print_result(line, nlp, True, output_format, output)
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        output.close()


def print_result(line, nlp, print_origin, output_format, file=sys.stdout):
    if line.startswith('#'):
        print(line, file=file)
        return
    doc = nlp(line)
    if output_format in ['0', 'conllu']:
        print_conllu(doc, print_origin, file)
    elif output_format in ['1', 'cabocha']:
        print_cabocha(doc, file)
    else:
        raise Exception(output_format + ' is not supported')


def print_conllu(doc, print_origin, file):
    if print_origin:
        print('# text = {}'.format(doc.text), file=file)
    np_tokens = {}
    for chunk in doc.noun_chunks:
        np_tokens[chunk.start] = 'NP_B'
        for i in range(chunk.start + 1, chunk.end):
            np_tokens[i] = 'NP_I'
    for token in doc:
        print(conllu_token_line(token, np_tokens), file=file)
    print(file=file)


def conllu_token_line(token, np_tokens):
    bunsetu_bi = ex_attr(token).bunsetu_bi_label
    position_type = ex_attr(token).bunsetu_position_type
    info = '|'.join(filter(lambda s: s, [
        '' if not bunsetu_bi else 'BunsetuBILabel={}'.format(bunsetu_bi),
        '' if not position_type else 'BunsetuPositionType={}'.format(position_type),
        '' if token.whitespace_ else 'SpaceAfter=No',
        np_tokens.get(token.i, ''),
        '' if not token.ent_type else 'NE={}_{}'.format(token.ent_type_, token.ent_iob_),
    ]))

    return '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
        token.i + 1,
        token.orth_,
        token.lemma_,
        token.pos_,
        token.tag_.replace(',*', '').replace(',', '-'),
        'NumType=Card' if token.pos_ == 'NUM' else '_',
        0 if token.head.i == token.i else token.head.i + 1,
        token.dep_.lower() if token.dep_ else '_',
        '_',
        info if info else '_',
    )


def print_cabocha(doc, file):
    for t in doc:
        if ex_attr(t).bunsetu_bi_label == 'B':
            print(cabocha_bunsetu_line(t, doc), file=file)
        print(cabocha_token_line(t), file=file)
    print('EOS', file=file)


def cabocha_bunsetu_line(token, doc):
    bunsetu_index = ex_attr(token).bunsetu_index
    bunsetu_head_index = None
    bunsetu_dep_index = None
    bunsetu_func_index = None
    dep_type = 'D'
    for t in doc[token.i:]:
        if bunsetu_index != ex_attr(t).bunsetu_index:
            break
        tbi = ex_attr(t.head).bunsetu_index
        if bunsetu_index != tbi:
            bunsetu_head_index = t.i - token.i
            bunsetu_dep_index = tbi
        if bunsetu_func_index is None and ex_attr(t).bunsetu_position_type in {'FUNC', 'SYN_HEAD'}:
            bunsetu_func_index = t.i - token.i
    if bunsetu_head_index is None:
        bunsetu_head_index = 0
    if bunsetu_func_index is None:
        bunsetu_func_index = bunsetu_head_index
    if bunsetu_dep_index is None:
        bunsetu_dep_index = -1

    return '* {} {}{} {}/{} 0.000000'.format(
        bunsetu_index,
        bunsetu_dep_index,
        dep_type,
        bunsetu_head_index,
        bunsetu_func_index,
    )


def cabocha_token_line(token):
    return '{}\t{},{},{},{}\t{}'.format(
        token.orth_,
        ','.join(ex_attr(token).sudachi.part_of_speech()),
        token.lemma_,
        ex_attr(token).reading if ex_attr(token).reading else token.orth_,
        '',
        'O' if token.ent_iob_ == 'O' else '{}-{}'.format(token.ent_iob_, token.ent_type_),
    )


def main():
    plac.call(run)


if __name__ == '__main__':
    plac.call(run)
