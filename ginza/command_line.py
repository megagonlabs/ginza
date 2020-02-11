# coding: utf8
from multiprocessing import Pool, cpu_count
from pathlib import Path
import plac
import spacy
import sys
from .sudachipy_tokenizer import init_dict, SudachipyTokenizer, SUDACHIPY_DEFAULT_SPLIT_MODE

MINI_BATCH_SIZE = 100


def ex_attr(token):
    return token._


def run(
        model_path=None,
        sudachipy_mode=SUDACHIPY_DEFAULT_SPLIT_MODE,
        use_sentence_separator=False,
        hash_comment='print',
        output_path=None,
        output_format='0',
        require_gpu=False,
        parallel=1,
        init_resource=False,
        files=None,
):
    if init_resource:
        init_dict()

    if require_gpu:
        print("GPU enabled", file=sys.stderr)

    if sudachipy_mode != SUDACHIPY_DEFAULT_SPLIT_MODE:
        print("sudachipy mode is {}".format(sudachipy_mode), file=sys.stderr)

    if use_sentence_separator:
        print("enabling sentence separator", file=sys.stderr)

    analyzer = Analyzer(
        model_path,
        sudachipy_mode,
        use_sentence_separator,
        hash_comment,
        output_format,
        require_gpu,
    )

    if parallel <= 0:
        parallel = max(1, cpu_count() + parallel)

    pool = None

    if output_path:
        output = open(str(output_path), 'w')
    else:
        output = sys.stdout

    try:
        if not files:
            if sys.stdin.isatty():
                parallel = 1
            else:
                files = [0]

        if not files:
            analyzer.set_nlp()
            while True:
                line = input()
                for ol in analyzer.analyze_line(line):
                    print(ol, file=output)
        elif parallel == 1:
            analyzer.set_nlp()
            for path in files:
                with open(path, 'r') as f:
                    for line in f:
                        for ol in analyzer.analyze_line(line):
                            print(ol, file=output)
        else:
            buffer = []
            for file_idx, path in enumerate(files):
                with open(path, 'r') as f:
                    while True:
                        eof, buffer = fill_buffer(f, MINI_BATCH_SIZE * parallel, buffer)
                        if eof and (file_idx + 1 < len(files) or len(buffer) == 0):
                            break  # continue to next file
                        if not pool:
                            if len(buffer) <= MINI_BATCH_SIZE:  # enough for single process
                                analyzer.set_nlp()
                                for line in buffer:
                                    for ol in analyzer.analyze_line(line):
                                        print(ol, file=output)
                                break  # continue to next file
                            parallel = (len(buffer) - 1) // MINI_BATCH_SIZE + 1
                            pool = Pool(parallel)

                        mini_batch_size = (len(buffer) - 1) // parallel + 1
                        mini_batches = [
                            buffer[idx * mini_batch_size:(idx + 1) * mini_batch_size] for idx in range(parallel)
                        ]
                        for mini_batch_result in pool.map(analyzer.analyze_lines_mp, mini_batches):
                            for lines in mini_batch_result:
                                for ol in lines:
                                    print(ol, file=output)

                        buffer.clear()  # process remaining part of current file

    except EOFError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if pool:
                pool.close()
        finally:
            output.close()


def fill_buffer(f, batch_size, buffer=None):
    if buffer is None:
        buffer = []

    for line in f:
        buffer.append(line)
        if len(buffer) == batch_size:
            return False, buffer
    return True, buffer


class Analyzer:
    def __init__(
            self,
            model_path,
            sudachipy_mode,
            use_sentence_separator,
            hash_comment,
            output_format,
            require_gpu,
    ):
        self.model_path = model_path
        self.sudachipy_mode = sudachipy_mode
        self.use_sentence_separator = use_sentence_separator
        self.hash_comment = hash_comment
        self.output_format = output_format
        self.require_gpu = require_gpu
        self.nlp = None

    def set_nlp(self):
        if self.nlp:
            return

        if self.require_gpu:
            spacy.require_gpu()

        if self.output_format in ['2', 'mecab']:
            nlp = SudachipyTokenizer(mode=self.sudachipy_mode).tokenizer
        else:
            # TODO: Work-around for pickle error. Need to share model data.
            if self.model_path:
                nlp = spacy.load(self.model_path)
            else:
                nlp = spacy.load('ja_ginza')

            nlp.tokenizer.set_mode(self.sudachipy_mode)
            if not self.use_sentence_separator:
                nlp.tokenizer.use_sentence_separator = False
        self.nlp = nlp

    def analyze_lines_mp(self, lines):
        self.set_nlp()
        return tuple(self.analyze_line(line) for line in lines)

    def analyze_line(self, line):
        return analyze(self.nlp, self.hash_comment, self.output_format, line)


def analyze(nlp, hash_comment, output_format, line):
    line = line.rstrip('\n')
    if line.startswith('#'):
        if hash_comment == 'print':
            return line,
        elif hash_comment == 'skip':
            return (),
    if line == '':
        return '',
    if output_format in ['0', 'conllu']:
        doc = nlp(line)
        return analyze_conllu(doc)
    elif output_format in ['1', 'cabocha']:
        doc = nlp(line)
        return analyze_cabocha(doc)
    elif output_format in ['2', 'mecab']:
        doc = nlp.tokenize(line)
        return analyze_mecab(doc)
    else:
        raise Exception(output_format + ' is not supported')


def analyze_conllu(doc, print_origin=True):
    np_tokens = {}
    for chunk in doc.noun_chunks:
        np_tokens[chunk.start] = 'NP_B'
        for i in range(chunk.start + 1, chunk.end):
            np_tokens[i] = 'NP_I'
    if print_origin:
        return ('# text = {}'.format(doc.text),) + tuple(conllu_token_line(token, np_tokens) for token in doc) + ('',)
    else:
        return tuple(conllu_token_line(token, np_tokens) for token in doc) + ('',)


def conllu_token_line(token, np_tokens):
    bunsetu_bi = ex_attr(token).bunsetu_bi_label
    position_type = ex_attr(token).bunsetu_position_type
    ne = ex_attr(token).ne
    info = '|'.join(filter(lambda s: s, [
        '' if not bunsetu_bi else 'BunsetuBILabel={}'.format(bunsetu_bi),
        '' if not position_type else 'BunsetuPositionType={}'.format(position_type),
        'SpaceAfter=Yes' if token.whitespace_ else 'SpaceAfter=No',
        np_tokens.get(token.i, ''),
        '' if not token.ent_type else 'ENE7={}_{}'.format(token.ent_iob_, token.ent_type_),
        '' if not ne else 'NE={}'.format(ne),
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


def analyze_cabocha(doc):
    lines = []
    for t in doc:
        if ex_attr(t).bunsetu_bi_label == 'B':
            lines.append(cabocha_bunsetu_line(t, doc))
        lines.append(cabocha_token_line(t))
    lines.append('EOS')
    lines.append('')
    return lines


def cabocha_bunsetu_line(token, doc):
    bunsetu_index = ex_attr(token).bunsetu_index
    bunsetu_head_index = None
    bunsetu_dep_index = None
    bunsetu_func_index = None
    dep_type = 'D'
    for t in doc[token.i:]:
        if bunsetu_index != ex_attr(t).bunsetu_index:
            if bunsetu_func_index is None:
                bunsetu_func_index = t.i - token.i
            break
        tbi = ex_attr(t.head).bunsetu_index
        if bunsetu_index != tbi:
            bunsetu_head_index = t.i - token.i
            bunsetu_dep_index = tbi
        if bunsetu_func_index is None and ex_attr(t).bunsetu_position_type in {'FUNC', 'SYN_HEAD'}:
            bunsetu_func_index = t.i - token.i
    else:
        if bunsetu_func_index is None:
            bunsetu_func_index = len(doc) - token.i
    if bunsetu_head_index is None:
        bunsetu_head_index = 0
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
    part_of_speech = token.tag_.replace('-', ',')
    part_of_speech += ',*' * (3 - part_of_speech.count(',')) + ',' + ex_attr(token).inf
    return '{}\t{},{},{},{}\t{}'.format(
        token.orth_,
        part_of_speech,
        token.lemma_,
        ex_attr(token).reading if ex_attr(token).reading else token.orth_,
        '*',
        'O' if token.ent_iob_ == 'O' else '{}-{}'.format(token.ent_iob_, token.ent_type_),
    )


def analyze_mecab(sudachipy_tokens):
    return tuple(mecab_token_line(t) for t in sudachipy_tokens) + ('EOS', '')


def mecab_token_line(token):
    reading = token.reading_form()
    return '{}\t{},{},{},{}'.format(
        token.surface(),
        ','.join(token.part_of_speech()),
        token.normalized_form(),
        reading if reading else token.surface(),
        '*',
    )


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    sudachipy_mode=("sudachipy mode", "option", "m", str),
    hash_comment=("hash comment", "option", "c", str, ['print', 'skip', 'analyze']),
    output_path=("output path", "option", "o", Path),
    parallel=("parallel level (default=-1, all_cpus=0)", "option", "p", int),
    init_resource=("initialize resources", "flag", "i"),
    files=("input files", "positional"),
)
def run_ginzame(
        model_path=None,
        sudachipy_mode=SUDACHIPY_DEFAULT_SPLIT_MODE,
        hash_comment='print',
        output_path=None,
        parallel=-1,
        init_resource=False,
        *files,
):
    run(
        model_path=model_path,
        sudachipy_mode=sudachipy_mode,
        use_sentence_separator=False,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format='mecab',
        require_gpu=False,
        parallel=parallel,
        init_resource=init_resource,
        files=files,
    )


def main_ginzame():
    plac.call(run_ginzame)


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    sudachipy_mode=("sudachipy mode", "option", "m", str),
    use_sentence_separator=("enable sentence separator", "flag", "s"),
    hash_comment=("hash comment", "option", "c", str, ['print', 'skip', 'analyze']),
    output_path=("output path", "option", "o", Path),
    output_format=("output format", "option", "f", str, ['0', 'conllu', '1', 'cabocha', '2', 'mecab']),
    require_gpu=("enable require_gpu", "flag", "g"),
    parallel=("parallel level (default=1, all_cpus=0)", "option", "p", int),
    init_resource=("initialize resources", "flag", "i"),
    files=("input files", "positional"),
)
def run_ginza(
        model_path=None,
        sudachipy_mode=SUDACHIPY_DEFAULT_SPLIT_MODE,
        use_sentence_separator=False,
        hash_comment='print',
        output_path=None,
        output_format='conllu',
        require_gpu=False,
        parallel=1,
        init_resource=False,
        *files,
):
    run(
        model_path=model_path,
        sudachipy_mode=sudachipy_mode,
        use_sentence_separator=use_sentence_separator,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format=output_format,
        require_gpu=require_gpu,
        parallel=parallel,
        init_resource=init_resource,
        files=files,
    )


def main_ginza():
    plac.call(run_ginza)


if __name__ == '__main__':
    plac.call(run_ginza)
