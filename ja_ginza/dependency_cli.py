import json
import sys
import spacy
from . import parse_tree
from .dependency_rule import import_from_module


def test(rules, nlp, sentence, expected_result=None, debug_level=0, simple=False):
    if not simple:
        print('sentence:', sentence)
        if expected_result is None:
            print('expected:   (not set)')
        else:
            print('expected:   {}'.format(expected_result))

    doc = nlp(sentence)
    extracted = None
    for rule in rules:
        candidates = rule.extract_candidates(doc, False)
        if candidates is not None:
            extracted = [t.orth_ for t in candidates]
            if simple:
                print('{}\t{}'.format(sentence.replace('"', "''"), ','.join(extracted)))
            else:
                print('candidates: {}'.format(extracted))
            break
    if extracted is None:
        if simple:
            print('{}\t'.format(sentence.replace('"', "''")))
        else:
            print('candidates: (no result)')
        extracted = []

    if debug_level == 3 or (
        debug_level >= 1 and expected_result not in extracted
    ) or (
        debug_level == 2 and len(extracted) > 1
    ):
        print('nlp:')
        for s in parse_tree.create_parsed_sentences(doc):
            print(s.to_string())
        print('trace:')
        for rule in rules:
            rule.extract_candidates(doc, True)
    if not simple:
        print()


def main():
    argv = sys.argv[1:]
    debug_level = 0
    simple = False
    lang = 'ja_ginza'
    module_name = None

    prev_len = -1
    while prev_len != len(argv):
        prev_len = len(argv)
        if len(argv) >= 1:
            if argv[0] in ['-d1', '--debug-on-not-included']:
                debug_level = 1
                argv = argv[1:]
        if len(argv) >= 1:
            if argv[0] in ['-d2', '--debug-on-excess-token']:
                debug_level = 2
                argv = argv[1:]
        if len(argv) >= 1:
            if argv[0] in ['-d', '-d3', '--debug', '--debug-all']:
                debug_level = 3
                argv = argv[1:]
        if len(argv) >= 1:
            if argv[0] in ['-s', '--simple']:
                simple = True
                argv = argv[1:]
        if len(argv) >= 1:
            if argv[0] in ['-l', '--lang']:
                lang = argv[1]
                argv = argv[2:]
        if len(argv) >= 1:
            if argv[0] in ['-r', '--rule_module']:
                module_name = argv[1]
                argv = argv[2:]
        if len(argv) >= 1:
            if argv[0] in ['-h', '--help']:
                print("""
Usage:
    python -m frameit.dependency_cli [OPTIONS] [INPUT_FILES]

INPUT_FILES:
    *.json
        The json files must have the structure of list of list.
        The inner list must have exactly two elements.
        The former element is sentence, and the latter element is expected result.
    text files
        Each line is treated as a sentence.
    default
        The stdin is used for sentence input.

OPTIONS:
    -d1, --debug-on-not-included
        Print debug information when analyzed candidate list includes expected result.
    -d2, --debug-on-excess-token
        Print debug information when analyzed candidate list has result(s) other than expected result.
    -d, -d3, --debug, --debug-all
        Print debug information always.
    -s, --simple
        Use simple output format (sentence[TAB]extracted_values)
    -l, --lang
        Specify spaCy language used for `nlp = spacy.load(lang_option_value)`.
    -r, --rule_module
        Specify a rule module which has DEPENDENCY_RULES variable. (default=lang option value)
    -h, --help
        Show this help.
""")
                return

    if module_name is None:
        raise Exception('Rule module must be specified by -r option')

    nlp = spacy.load(lang)
    rules = import_from_module(module_name)

    if argv:
        for filename in argv:
            with open(filename, 'r') as f:
                if filename.endswith('.json'):
                    tasks = json.load(f)
                else:
                    tasks = [(line.rstrip('\n'), None) for line in f.readlines()]
            for sentence, expected_result in tasks:
                test(rules, nlp, sentence, expected_result, debug_level=debug_level, simple=simple)
    else:
        while True:
            try:
                line = input()
                test(rules, nlp, line.rstrip('\n'), debug_level=debug_level, simple=simple)
            except EOFError:
                break


if __name__ == '__main__':
    main()
