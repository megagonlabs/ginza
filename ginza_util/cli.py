# coding: utf8
import plac
import spacy
from sudachipy.tokenizer import Tokenizer as OriginalTokenizer
from ginza.japanese_corrector import JapaneseCorrector
from .bccwj_ud_corpus import convert_files
from .corpus import *
from .parse_tree import ParsedSentence
from ginza.sudachi_tokenizer import SUDACHI_DEFAULT_MODE


@plac.annotations(
    corpus_type=("Corpus type: specify text, bccwj_ud or (default=)None", "option", "t", str),
    model_path=("model directory path", "option", "b", str),
    mode=("sudachi mode", "option", "m", str),
    use_sentence_separator=("enable sentence separator", "flag", "s"),
    disable_pipes=("disable pipes (csv)", "option", "d"),
    recreate_corrector=("recreate corrector", "flag", "c"),
    output_path=("output path", "option", "o", Path),
    require_gpu=("enable require_gpu", "flag", "g"),
)
def main(
        corpus_type=None,
        model_path=None,
        mode=SUDACHI_DEFAULT_MODE,
        use_sentence_separator=False,
        disable_pipes='',
        recreate_corrector=False,
        output_path=None,
        require_gpu=False,
        *lines,
):
    if require_gpu:
        spacy.require_gpu()
        print("GPU enabled", file=sys.stderr)
    nlp = spacy.load(model_path)
    if disable_pipes:
        print("disabling pipes: {}".format(disable_pipes), file=sys.stderr)
        nlp.disable_pipes(disable_pipes)
        print("using : {}".format(nlp.pipe_names), file=sys.stderr)
    else:
        # to ensure reflect local changes of corrector
        if recreate_corrector and 'JapaneseCorrector' in nlp.pipe_names:
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
        if corpus_type:
            if corpus_type == 'bccwj_ud':
                for line in convert_files(lines):
                    print_result(line, nlp, True, output)
            else:
                for path in lines:
                    with open(path, 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        print_result(line, nlp, True, output)
        elif len(lines) > 0:
            for line in lines:
                print_result(line, nlp, True, output)
        else:
            while True:
                line = input()
                print_result(line, nlp, True, output)
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass
#    except Exception as e:
#        print(e, file=sys.stderr)
#        print('exception raised while analyzing the line:', line, file=sys.stderr)
    finally:
        output.close()


def print_result(line, nlp, print_origin, file=sys.stdout):
    if isinstance(line, ParsedSentence):
        if print_origin:
            print('# sent_id = {}'.format(getattr(line, 'sid', 'None')), file=file)
    elif line.startswith('#'):
        print(line, file=file)
        return
    doc = nlp(line)
    if print_origin:
        print('# text = {}'.format(doc.text), file=file)
    np_tokens = {}
    for chunk in doc.noun_chunks:
        np_tokens[chunk.start] = 'NP_B'
        for i in range(chunk.start + 1, chunk.end):
            np_tokens[i] = 'NP_I'
    for token in doc:
        print(token_line(token, np_tokens), file=file)
    print(file=file)


def token_line(token, np_tokens):
    bunsetu_bi = token._.bunsetu_bi_label
    position_type = token._.bunsetu_position_type
    info = '|'.join(filter(lambda s: s, [
        '' if bunsetu_bi else 'BunsetuBILabel={}'.format(bunsetu_bi),
        '' if position_type is None else 'BunsetuPositionType={}'.format(position_type),
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


if __name__ == '__main__':
    plac.call(main)
