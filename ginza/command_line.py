# coding: utf8
from multiprocessing import Process, Queue, Event, cpu_count
from pathlib import Path
import queue
import sys
import traceback
from typing import Generator, Iterable, Optional, List

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
            print("\n]", file=self.output)
            self.output_json_opened = False
        if self.output_path:
            self.output.close()
        else:
            pass

    def write(self, result: str):
        if self.is_json and not self.output_json_opened:
            print("[", file=self.output)
            self.output_json_opened = True
        elif self.is_json:
            print(",", file=self.output)
        print(result, end="", file=self.output)


def run(
    model_path: Optional[str] = None,
    ensure_model: Optional[str] = None,
    split_mode: Optional[str] = "C",
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
        if not files and sys.stdin.isatty():
            _analyze_tty(analyzer, output)
        else:
            if not files:
                files = [0]
            if parallel == 1:
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
            output.write(analyzer.analyze_line(line))
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
                    output.write(analyzer.analyze_line(line))
    except KeyboardInterrupt:
        pass


def _data_loader(files: List[str], batch_size: int) -> Generator[List[str], None, None]:
    mini_batch = []
    for path in files:
        with open(path, "r") as f:
            for line in f:
                mini_batch.append(line)
                if len(mini_batch) == batch_size:
                    yield mini_batch
                    mini_batch = []
    if mini_batch:
        yield mini_batch


def _multi_process_load(in_queue: Queue, files: List[str], batch_size: int, n_analyze_process: int):
    try:
        for i, mini_batch in enumerate(_data_loader(files, batch_size)):
            in_queue.put((i, mini_batch))
    finally:
        for _ in range(n_analyze_process):
            in_queue.put("terminate")


def _multi_process_analyze(analyzer: Analyzer, in_queue: Queue, out_queue: Queue, analyze_end: Event):
    while True:
        msg = in_queue.get(timeout=0.1)
        if msg == "terminate":
            analyze_end.set()
            break
        i, mini_batch = msg
        try:
            result = analyzer.analyze_batch(mini_batch)
            out_queue.put((None, i, result))
        except Exception as err:
            out_queue.put((err, i, None))
            traceback.print_exc()


def _multi_process_write(out_queue: queue, output: _OutputWrapper, analyze_ends: List[Event]):
    cur = 0
    results = dict()
    while True:
        try:
            err, i, result = out_queue.get(timeout=5)
        except queue.Empty:
            is_analyze_complete = all([e.is_set() for e in analyze_ends])
            if is_analyze_complete:
                break
            else:
                continue

        if err is not None:
            print("failed to analyze mini_batch {}".format(i), file=sys.stderr)
            print(err, file=sys.stderr)

        # output must be ordered same as input text
        results[i] = result
        while True:
            if cur not in results.keys():
                break
            result = results[cur]
            del results[cur]
            cur += 1

            if result is None:
                continue

            for sents in result:
                for lines in sents:
                    for ol in lines:
                        output.write(ol)

        is_analyze_complete = all([e.is_set() for e in analyze_ends])
        if is_analyze_complete and out_queue.empty():
            break


def _analyze_parallel(analyzer: Analyzer, output: _OutputWrapper, files: Iterable[str], parallel: int) -> None:
    try:
        in_queue = Queue(maxsize=parallel * 2)
        out_queue = Queue()

        p_analyzes = []
        e_analyzes = []
        for _ in range(parallel):
            e = Event()
            e_analyzes.append(e)
            p = Process(target=_multi_process_analyze, args=(analyzer, in_queue, out_queue, e), daemon=True)
            p.start()
            p_analyzes.append(p)

        p_load = Process(target=_multi_process_load, args=(in_queue, files, MINI_BATCH_SIZE, parallel), daemon=True)
        p_load.start()

        _multi_process_write(out_queue, output, e_analyzes)

        p_load.join()
        for p in p_analyzes:
            p.join()

    except KeyboardInterrupt:
        pass
    finally:
        try:
            if p_load.is_alive():
                p_load.terminate()
                p_load.join()
            for p in p_analyzes:
                if p.is_alive():
                    p.terminate()
                    p.join()
        except:
            pass


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C"]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    use_normalized_form=("overriding Token.lemma_ by normalized_form of SudachiPy", "flag", "n"),
    parallel=("parallel level (default=-1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginzame(
    model_path=None,
    split_mode="C",
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
    split_mode=("split mode", "option", "s", str, ["A", "B", "C"]),
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
    split_mode="C",
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
