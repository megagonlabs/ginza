# coding: utf8
from multiprocessing import Process, Queue, Event, cpu_count
from pathlib import Path
import queue
import re
import sys
import traceback
from typing import Generator, Iterable, Optional, List

import plac
from .analyzer import Analyzer

MINI_BATCH_SIZE = 100
GINZA_MODEL_PATTERN = re.compile(r"^(ja_ginza|ja_ginza_electra)$")
SPACY_MODEL_PATTERN = re.compile(r"^[a-z]{2}[-_].+[-_].+(sm|md|lg|trf)$")


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
        if self.is_json:
            if not self.output_json_opened:
                print("[", file=self.output)
                self.output_json_opened = True
            else:
                print(",", file=self.output)
        print(result, end="", file=self.output)


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
    parallel_level: int = 1,
    files: List[str] = None,
):
    if output_format in ["3", "json"] and hash_comment != "analyze":
        print(
            f'hash_comment="{hash_comment}" not permitted for JSON output. Forced to use hash_comment="analyze".',
            file=sys.stderr
        )

    if parallel_level <= 0:
        level = max(1, cpu_count() + parallel_level)
        if output_format in [2, "mecab"]:
            if require_gpu:
                print("GPU not used for mecab mode", file=sys.stderr)
                require_gpu = False
        elif parallel_level <= 0:
            if require_gpu:
                if level < 4:
                    print("GPU enabled: parallel_level' set to {level}", end="", file=sys.stderr)
                else:
                    print("GPU enabled: parallel_level' set to {level} but seems it's too much", end="", file=sys.stderr)
            else:
                print(f"'parallel_level' set to {level}", file=sys.stderr)
        elif require_gpu:
            print("GPU enabled", file=sys.stderr)
        parallel_level = level

    assert model_path is None or ensure_model is None
    if ensure_model:
        ensure_model = ensure_model.replace("-", "_")
        try:
            from importlib import import_module
            import_module(ensure_model)
        except ModuleNotFoundError:
            if GINZA_MODEL_PATTERN.match(ensure_model):
                print("Installing", ensure_model, file=sys.stderr)
                import pip
                pip.main(["install", ensure_model])
                print("Successfully installed", ensure_model, file=sys.stderr)
            elif SPACY_MODEL_PATTERN.match(ensure_model):
                print("Installing", ensure_model, file=sys.stderr)
                from spacy.cli.download import download
                download(ensure_model)
                print("Successfully installed", ensure_model, file=sys.stderr)
            else:
                raise OSError("E050", f'You need to install "{ensure_model}" before executing ginza.')
        model_name_or_path = ensure_model
    else:
        model_name_or_path = model_path

    analyzer = Analyzer(
        model_name_or_path,
        split_mode,
        hash_comment,
        output_format,
        require_gpu,
        disable_sentencizer,
        use_normalized_form,
    )

    output = _OutputWrapper(output_path, output_format)
    output.open()
    try:
        if not files and sys.stdin.isatty():
            _analyze_tty(analyzer, output)
        else:
            if not files:
                files = [0]
            if parallel_level == 1:
                _analyze_single(analyzer, output, files)
            else:
                _analyze_parallel(analyzer, output, files, parallel_level)
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


def _analyze_parallel(analyzer: Analyzer, output: _OutputWrapper, files: Iterable[str], parallel_level: int) -> None:
    try:
        in_queue = Queue(maxsize=parallel_level * 2)
        out_queue = Queue()

        p_analyzes = []
        abort = Event()
        for _ in range(parallel_level):
            p = Process(target=_multi_process_analyze, args=(analyzer, in_queue, out_queue, abort), daemon=True)
            p.start()
            p_analyzes.append(p)

        p_load = Process(target=_multi_process_load, args=(in_queue, files, MINI_BATCH_SIZE, parallel_level, abort), daemon=True)
        p_load.start()

        _main_process_write(out_queue, output, parallel_level, abort)

    except KeyboardInterrupt:
        abort.set()
    finally:
        for p in [p_load] + p_analyzes:
            try:
                p.join(timeout=1)
            except:
                if p.is_alive():
                    p.terminate()
                    p.join()


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


def _multi_process_load(in_queue: Queue, files: List[str], batch_size: int, n_analyze_process: int, abort: Event):
    try:
        for i, mini_batch in enumerate(_data_loader(files, batch_size)):
            if abort.is_set():
                break
            in_queue.put((i, mini_batch))
        else:
            for _ in range(n_analyze_process):
                in_queue.put("terminate")
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
        abort.set()


def _multi_process_analyze(analyzer: Analyzer, in_queue: Queue, out_queue: Queue, abort: Event):
    i = None
    mini_batch = []
    try:
        while True:
            if abort.is_set():
                break
            try:
                msg = in_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if msg == "terminate":
                out_queue.put(("terminating", i, None))
                break
            i, mini_batch = msg
            result = analyzer.analyze_batch(mini_batch)
            out_queue.put((None, i, result))
    except KeyboardInterrupt:
        pass
    except Exception as err:
        out_queue.put(("Error: {}\n{}".format(err, "".join(mini_batch)), i, None))
        traceback.print_exc()
        abort.set()


def _main_process_write(out_queue: queue, output: _OutputWrapper, parallel_level: int, abort: Event):
    cur = 0
    results = dict()
    terminating = 0
    while True:
        if abort.is_set():
            return
        try:
            msg, mini_batch_index, result = out_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if msg is not None:
            if msg == "terminating":
                terminating += 1
                if terminating == parallel_level:
                    return
                continue
            else:
                print(f"Analysis failed in mini_batch #{mini_batch_index}. Stopping all the processes.", file=sys.stderr)
                print(msg, file=sys.stderr)
                return

        # output must be ordered same as input text
        results[mini_batch_index] = result
        while results:
            if cur not in results.keys():
                break
            result = results[cur]
            del results[cur]
            cur += 1
            output.write(result)


@plac.annotations(
    split_mode=("split mode", "option", "s", str, ["A", "B", "C"]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    parallel=("parallel level (default=-1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginzame(
    split_mode=None,
    hash_comment="print",
    output_path=None,
    parallel=-1,
    *files,
):
    run(
        model_path=None,
        ensure_model=None,
        split_mode=split_mode,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format="mecab",
        require_gpu=False,
        use_normalized_form=True,
        parallel_level=parallel,
        disable_sentencizer=False,
        files=files,
    )


def main_ginzame():
    plac.call(run_ginzame)


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    ensure_model=("select model package of ginza or spacy", "option", "m", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C"]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    output_format=("output format", "option", "f", str, ["0", "conllu", "1", "cabocha", "2", "mecab", "3", "json"]),
    require_gpu=("enable require_gpu", "flag", "g"),
    use_normalized_form=("Use Token.norm_ instead of Token.lemma_", "flag", "n"),
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
        parallel_level=parallel,
        files=files,
    )


def main_ginza():
    plac.call(run_ginza)


if __name__ == "__main__":
    plac.call(run_ginza)
