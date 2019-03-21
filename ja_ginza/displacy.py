# coding: utf8
import plac
import threading
import time
import webbrowser
from spacy import displacy
from sudachipy.tokenizer import Tokenizer as OriginalTokenizer
from . import *
from .bccwj_ud_corpus import convert_files
from .corpus import *
from .parse_tree import correct_dep
from .sudachi_tokenizer import SUDACHI_DEFAULT_MODE


@plac.annotations(
    corpus_type=("Corpus type: specify text, bccwj_ud or (default=)None", "option", "t", str),
    model_path=("model directory path", "option", "b", str),
    mode=("sudachi mode", "option", "m", str),
    use_sentence_separator=("enable sentence separator", "flag", "s"),
    disable_pipes=("disable pipes (csv)", "option", "d"),
    recreate_corrector=("recreate corrector", "flag", "c"),
    style=("displacy style (default=dep)", "option", "s", str),
    browser_command=("web browser command", "option", "w", str),
)
def main(
        corpus_type=None,
        model_path=None,
        mode=SUDACHI_DEFAULT_MODE,
        use_sentence_separator=False,
        disable_pipes='',
        recreate_corrector=False,
        style='dep',
        browser_command=None,
        *lines,
):
    nlp = load_model(model_path)
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

    if browser_command:
        browser = webbrowser.get(browser_command)
    else:
        browser = None

    if corpus_type:
        if corpus_type == 'bccwj_ud':
            doc = correct_dep(convert_files(lines)[0].to_doc(nlp.vocab, True), False)
            print('Displaying first sentence with result and raw_result:', doc.text, file=sys.stderr)
            result = nlp(doc.text)
            with nlp.disable_pipes('JapaneseCorrector'):
                raw_result = nlp(doc.text)
            docs = [doc, result, raw_result]
        else:
            with open(str(lines[0]), 'r') as f:
                lines = f.readlines()
            if len(lines) > 5:
                print('Displaying first 5 sentences', file=sys.stderr)
            docs = [nlp(line) for line in lines[0:5]]
    else:
        if len(lines) == 0:
            lines = [input()]
        elif len(lines) > 5:
            print('Displaying first 5 sentences', file=sys.stderr)
            lines = lines[0:5]
        docs = [nlp(line) for line in lines]

    display(browser, docs, style)


def display(browser, docs, style='dep', url='http://localhost:5000'):
    if browser:
        thread = threading.Thread(target=open_browser, args=[browser, url])
        thread.start()
    else:
        print('open following url by web browser', file=sys.stderr)
        print(url, file=sys.stderr)
    displacy.serve(docs, style, options={'compact': True, 'collapse_punct': False})


def open_browser(browser, url, wait=0.5):
    if wait:
        time.sleep(wait)
    browser.open(url)


if __name__ == '__main__':
    plac.call(main)
