import json
import os
import subprocess as sp
import sys
import tempfile
from functools import partial
from pathlib import Path
from typing import Iterator, List

import pytest

TEST_TEXT = "今日はかつ丼を食べた。明日は東京で蕎麦を食べる。\n#コメント"

run_cmd = partial(sp.run, encoding="utf-8", stdout=sp.PIPE)


@pytest.fixture(scope="module", autouse=True)
def download_model() -> None:
    run_cmd([sys.executable, "-m", "pip", "install", "ja-ginza"])
    run_cmd([sys.executable, "-m", "pip", "install", "ja-ginza-electra"])
    yield


@pytest.fixture(scope="module")
def tmpdir() -> Path:
    with tempfile.TemporaryDirectory() as dir_name:
        yield Path(dir_name)


@pytest.fixture(scope="module")
def input_file(tmpdir: Path) -> Path:
    file_path = (tmpdir / "test_input.txt").resolve()
    with open(file_path, "w") as fp:
        print(TEST_TEXT, file=fp)
    yield file_path
    file_path.unlink()


@pytest.fixture(scope="module")
def output_file(tmpdir: Path) -> Path:
    file_path = (tmpdir / "test_output.txt").resolve()
    file_path.touch()
    yield file_path
    file_path.unlink()


def _parse_conllu(result: str):
    # TODO: implement
    pass


def _parse_cabocha(result: str):
    # TODO: implement
    pass


def _parse_mecab(result: str):
    # TODO: implement
    pass


class TestCLIGinza:
    def test_help(self):
        for opt in ["-h", "--help"]:
            p = run_cmd(["ginza", opt])
            assert p.returncode == 0

    def test_input(self, input_file):
        # input file
        p = run_cmd(["ginza", input_file])

        # input from stdin
        p_stdin = sp.Popen(["ginza"], stdin=sp.PIPE, stdout=sp.PIPE)
        o, e = p_stdin.communicate(input=TEST_TEXT.encode())
        assert e is None
        assert o.decode("utf-8") == p.stdout

    # TODO: add user defined model to fixture and test it here
    @pytest.mark.parametrize(
        "model_path, exit_ok",
        [
            ("ja_ginza", True),
            ("not-exist-model", False),
        ],
    )
    def test_model_path(self, model_path, exit_ok, input_file):
        p = run_cmd(["ginza", "-b", model_path, input_file])
        assert (p.returncode == 0) is exit_ok

    @pytest.mark.parametrize(
        "ensure_model, exit_ok",
        [
            ("ja_ginza", True),
            ("ja-ginza", True),
            ("ja-ginza-electra", True),
            ("ja_ginza_electra", True),
            ("ja-ginza_electra", False),
            ("not-exist-model", False),
        ],
    )
    def test_ensure_model(self, ensure_model, exit_ok, input_file):
        p = run_cmd(["ginza", "-m", ensure_model, input_file])
        assert (p.returncode == 0) is exit_ok

    def test_double_model_spcification(self, input_file):
        p = run_cmd(["ginza", "-b", "ja_ginza", "-m", "ja_ginza", input_file])
        assert p.returncode != 0

    @pytest.mark.parametrize(
        "split_mode, input_text, expected",
        [
            ("A", "機能性食品", ["機能", "性", "食品"]),
            ("B", "機能性食品", ["機能性", "食品"]),
            ("C", "機能性食品", ["機能性食品"]),
        ],
    )
    def test_split_mode(self, split_mode, input_text, expected):
        p = run_cmd(["ginza", "-s", split_mode], input=input_text)
        assert p.returncode == 0

        def _sub_words(lines: Iterator) -> List[str]:
            return [l.split("\t")[1] for l in lines if len(l.split("\t")) > 1]

        assert _sub_words(p.stdout.split("\n")) == expected

    @pytest.mark.parametrize(
        "hash_comment, n_sentence, n_analyzed_sentence, exit_ok",
        [
            ("print", 3, 2, True),
            ("skip", 2, 2, True),
            ("analyze", 3, 3, True),
        ],
    )
    def test_hash_comment(self, hash_comment, n_sentence, n_analyzed_sentence, exit_ok, input_file):
        def _n_sentence(lines: Iterator) -> int:
            return len(list(filter(lambda x: x.startswith("#"), lines)))

        def _n_analyzed_sentence(lines: Iterator) -> int:
            return len(list(filter(lambda x: x.startswith("# text = "), lines)))

        p = run_cmd(["ginza", "-c", hash_comment, input_file])
        assert (p.returncode == 0) is exit_ok
        assert _n_sentence(p.stdout.split("\n")) == n_sentence
        assert _n_analyzed_sentence(p.stdout.split("\n")) == n_analyzed_sentence

    def test_output_path(self, input_file, output_file):
        p_s = run_cmd(["ginza", input_file])
        p_o = run_cmd(["ginza", "-o", output_file, input_file])
        assert p_o.returncode == 0

        def file_output():
            with open(output_file, "r") as fp:
                return [l.strip() for l in fp if l.strip()]

        def pipe_output():
            return [l.strip() for l in p_s.stdout.split("\n") if l.strip()]

        assert file_output() == pipe_output()

    @pytest.mark.parametrize(
        "output_format, result_parser",
        [
            ("conllu", _parse_conllu),
            ("cabocha", _parse_cabocha),
            ("mecab", _parse_mecab),
            ("json", json.loads),
        ],
    )
    def test_output_format(self, output_format, result_parser, input_file):
        # TODO: add more detailed tests.
        # difference between output_formats are complicated.
        # FIXME: output_format = mecab works more than 'format'.
        p = run_cmd(["ginza", "-c", "skip", "-f", output_format, input_file])
        assert p.returncode == 0
        try:
            result_parser(p.stdout.strip())
        except:
            pytest.fail("invalid output format.")

    def test_require_gpu(self, input_file):
        p = run_cmd(["ginza", "-g", input_file])
        gpu_available = int(os.environ.get("CUDA_VISIBLE_DEVICES", -1)) > 0
        assert (p.returncode == 0) is gpu_available

    def test_use_normalized_form(self, input_file):
        p = run_cmd(["ginza", "-n", input_file])
        lemmas = [l.split("\t")[2] for l in p.stdout.split("\n") if len(l.split("\t")) > 1]
        # 'カツ丼' is normlized_form of 'かつ丼'
        assert p.returncode == 0
        assert "カツ丼" in lemmas

    def test_diable_sentencizer(self, input_file):
        p = run_cmd(["ginza", "-d", input_file])

        def _n_analyzed_sentence(lines: Iterator) -> int:
            return len(list(filter(lambda x: x.startswith("# text = "), lines)))

        assert p.returncode == 0
        assert _n_analyzed_sentence(p.stdout.split("\n")) == 1

    def test_parallel(self, input_file):
        p = run_cmd(["ginza", "-p", "2", input_file])
        assert p.returncode == 0


class TestCLIGinzame:

    def test_ginzame(self, input_file):
        p_ginzame = run_cmd(["ginzame", input_file])
        p_ginza = run_cmd(["ginza", "-m", "ja_ginza", "-f", "2", input_file])

        assert p_ginzame.returncode == 0
        assert p_ginzame.stdout == p_ginza.stdout
