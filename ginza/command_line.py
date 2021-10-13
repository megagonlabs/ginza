# coding: utf8
from multiprocessing import Pool, cpu_count
from pathlib import Path
import sys
from typing import Iterable, Optional, List

import plac
from . import force_using_normalized_form_as_lemma
from .analyzer import Analyzer

MINI_BATCH_SIZE = 100


class _OutputWrapper:
    def __init__(self, output_path, output_format):
        self.output = None
        self.output_path = output_path
        self.output_format = output_format
        self.output_json_opened = False

    @property
    def is_json(self):
        return self.output_format in ["3", "json"]

    def open(self):
        if self.output_path:
            self.output = open(self.output_path, "w")
        else:
            self.output = sys.stdout

    def close(self):
        if self.is_json and self.output_json_opened:
            print("]", file=self.output)
            self.output_json_opened = False
        if self.output_path:
            self.output.close()
        else:
            pass

    def write(self, *args, **kwargs):
        if self.is_json and not self.output_json_opened:
            print("[", file=self.output)
            self.output_json_opened = True
        elif self.is_json:
            print(" ,", file=self.output)
        print(*args, **kwargs, file=self.output)


def run(
    model_path: Optional[str] = None,
    ensure_model: Optional[str] = None,
    split_mode: Optional[str] = None,
    hash_comment: str = "print",
    output_path: Optional[Path] = None,
    output_format: str = "0",
    require_gpu: bool = False,
    disable_sentencizer: bool = False,
    use_normalized_form: bool = False,
    parallel: int = 1,
    files: List[str] = None,
):
    if require_gpu:
        print("GPU enabled", file=sys.stderr)
    if use_normalized_form:
        print("overriding Token.lemma_ by normalized_form of SudachiPy", file=sys.stderr)
        force_using_normalized_form_as_lemma(True)
    assert model_path is None or ensure_model is None

    analyzer = Analyzer(
        model_path,
        ensure_model,
        split_mode,
        hash_comment,
        output_format,
        require_gpu,
        disable_sentencizer,
    )

    if parallel <= 0:
        parallel = max(1, cpu_count() + parallel)

    output = _OutputWrapper(output_path, output_format)
    output.open()
    try:
        if not files:
            if sys.stdin.isatty():
                parallel = 1
                _analyze_tty(analyzer, output)
            else:
                _analyze_single(analyzer, output, files=[0])
        elif parallel == 1:
            _analyze_single(analyzer, output, files)
        else:
            _analyze_parallel(analyzer, output, files, parallel)
    finally:
        output.close()


def _analyze_tty(analyzer: Analyzer, output: _OutputWrapper) -> None:
    try:
        analyzer.set_nlp()
        while True:
            line = input()
            for sent in analyzer.analyze_line(line):
                for ol in sent:
                    output.write(ol)
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass


def _analyze_single(analyzer: Analyzer, output: _OutputWrapper, files: Iterable[str]) -> None:
    try:
        analyzer.set_nlp()
        for path in files:
            with open(path, "r") as f:
                for line in f:
                    for sent in analyzer.analyze_line(line):
                        for ol in sent:
                            output.write(ol)
    except KeyboardInterrupt:
        pass


def _analyze_parallel(analyzer: Analyzer, output: _OutputWrapper, files: Iterable[str], parallel: int) -> None:
    pool = None
    buffer = []
    try:
        for file_idx, path in enumerate(files):
            with open(path, "r") as f:
                while True:
                    eof, buffer = fill_buffer(f, MINI_BATCH_SIZE * parallel, buffer)
                    if eof and (file_idx + 1 < len(files) or len(buffer) == 0):
                        break  # continue to next file
                    if not pool:
                        if len(buffer) <= MINI_BATCH_SIZE:  # enough for single process
                            analyzer.set_nlp()
                            for line in buffer:
                                for sent in analyzer.analyze_line(line):
                                    for ol in sent:
                                        output.write(ol)
                            break  # continue to next file
                        parallel = (len(buffer) - 1) // MINI_BATCH_SIZE + 1
                        pool = Pool(parallel)
                    mini_batch_size = (len(buffer) - 1) // parallel + 1
                    mini_batches = [
                        buffer[idx * mini_batch_size : (idx + 1) * mini_batch_size] for idx in range(parallel)
                    ]
                    for mini_batch_result in pool.map(analyzer.analyze_lines_mp, mini_batches):
                        for sents in mini_batch_result:
                            for lines in sents:
                                for ol in lines:
                                    output.write(ol)
                    buffer.clear()  # process remaining part of current file
    except KeyboardInterrupt:
        pass
    finally:
        if pool:
            try:
                pool.close()
            except:
                pass

def fill_buffer(f, batch_size, buffer=None):
    if buffer is None:
        buffer = []

    for line in f:
        buffer.append(line)
        if len(buffer) == batch_size:
            return False, buffer
    return True, buffer


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C", None]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    use_normalized_form=("overriding Token.lemma_ by normalized_form of SudachiPy", "flag", "n"),
    parallel=("parallel level (default=-1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginzame(
    model_path=None,
    split_mode=None,
    hash_comment="print",
    output_path=None,
    use_normalized_form=False,
    parallel=-1,
    *files,
):
    run(
        model_path=model_path,
        ensure_model="ja_ginza",
        split_mode=split_mode,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format="mecab",
        require_gpu=False,
        use_normalized_form=use_normalized_form,
        parallel=parallel,
        disable_sentencizer=False,
        files=files,
    )


def main_ginzame():
    plac.call(run_ginzame)


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    ensure_model=("select model either ja_ginza or ja_ginza_electra", "option", "m", str, ["ja_ginza", "ja-ginza", "ja_ginza_electra", "ja-ginza-electra", None]),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C", None]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    output_format=("output format", "option", "f", str, ["0", "conllu", "1", "cabocha", "2", "mecab", "3", "json"]),
    require_gpu=("enable require_gpu", "flag", "g"),
    use_normalized_form=("overriding Token.lemma_ by normalized_form of SudachiPy", "flag", "n"),
    disable_sentencizer=("disable spaCy's sentence separator", "flag", "d"),
    parallel=("parallel level (default=1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginza(
    model_path=None,
    ensure_model=None,
    split_mode=None,
    hash_comment="print",
    output_path=None,
    output_format="conllu",
    require_gpu=False,
    use_normalized_form=False,
    disable_sentencizer=False,
    parallel=1,
    *files,
):
    run(
        model_path=model_path,
        ensure_model=ensure_model,
        split_mode=split_mode,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format=output_format,
        require_gpu=require_gpu,
        use_normalized_form=use_normalized_form,
        disable_sentencizer=disable_sentencizer,
        parallel=parallel,
        files=files,
    )


def main_ginza():
    plac.call(run_ginza)


if __name__ == "__main__":
    plac.call(run_ginza)
