# encoding: utf8
import sys
from pathlib import Path


def file_iter(path):
    path = Path(path)
    if path.is_dir():
        for sub_path in sorted(path.iterdir(), key=lambda path_: str(path_)):
            for file_path in file_iter(sub_path):
                yield file_path
    else:
        yield path


def sentence_iter(in_path, corpus_reader, file=sys.stderr):
    def read_file(path_, file_):
        nonlocal corpus_reader
        count = 0
        for sentence in corpus_reader(path_, file_):
            count += 1
            if count % 100 == 0:
                print('.', end='', file=file, flush=True)
            sentence = [w for w in sentence if w not in ' 　\t\r\n']
            yield sentence

    if in_path is None:
        for s in read_file('-', sys.stdin):
            yield s
    elif isinstance(in_path, list):
        for p in in_path:
            for s in sentence_iter(p, corpus_reader, file):
                yield s
    else:
        for corpus_path in file_iter(in_path):
            print(str(corpus_path) + ' ', end='', file=file, flush=True)
            with open(str(corpus_path), 'r') as f:
                for s in read_file(corpus_path, f):
                    yield s
            print(file=file, flush=True)


HALF_FULL_MAP = {
    chr(c): chr(c - ord('!') + ord('！')) for c in range(ord('!'), ord('~') + 1)
}
FULL_HALF_MAP = {
    v: k for k, v in HALF_FULL_MAP.items()
}
TURN_FULL_HALF_MAP = {}
TURN_FULL_HALF_MAP.update(FULL_HALF_MAP)
TURN_FULL_HALF_MAP.update(HALF_FULL_MAP)


def to_full(s):
    return ''.join([
        HALF_FULL_MAP[c] if c in HALF_FULL_MAP else c for c in s
    ])


def to_half(s):
    return ''.join([
        FULL_HALF_MAP[c] if c in FULL_HALF_MAP else c for c in s
    ])


def turn_full_half(s):
    return ''.join([
        TURN_FULL_HALF_MAP[c] if c in TURN_FULL_HALF_MAP else c for c in s
    ])
