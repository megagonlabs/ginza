# coding: utf8
import plac
import sys
import threading
import time
import webbrowser
import spacy
from spacy import displacy
from spacy.gold import GoldCorpus
from ginza import *


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C", None]),
    style=("displacy style (default=dep)", "option", "d", str),
    compact=("compact", "flag", "c"),
    browser_command=("web browser command", "option", "w", str),
)
def main(
        model_path=None,
        split_mode=None,
        style='dep',
        compact=False,
        browser_command=None,
):
    if model_path:
        nlp = spacy.load(model_path)
    else:
        nlp = spacy.load("ja_ginza")

    if split_mode:
        set_split_mode(nlp, split_mode)

    if browser_command:
        browser = webbrowser.get(browser_command)
    else:
        browser = None

    print("Input a sentence line:", file=sys.stderr)
    line = input()
    docs = [nlp(line)]

    display(browser, docs, style, compact)


def display(browser, docs, style='dep', compact=False, url='http://localhost:5000'):
    if browser:
        thread = threading.Thread(target=open_browser, args=[browser, url])
        thread.start()
    else:
        print('open following url by web browser', file=sys.stderr)
        print(url, file=sys.stderr)
    displacy.serve(docs, style, options={'compact': compact, 'collapse_punct': False})


def open_browser(browser, url, wait=0.5):
    if wait:
        time.sleep(wait)
    browser.open(url)


if __name__ == '__main__':
    plac.call(main)
