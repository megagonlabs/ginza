# coding: utf8
import json
from multiprocessing import Pool, cpu_count
from pathlib import Path
import sys

import plac
import spacy

from spacy.lang.ja import JapaneseDefaults

from . import set_split_mode, inflection, reading_form, ent_label_ene, ent_label_ontonotes
from .bunsetu_recognizer import bunsetu_head_list, bunsetu_phrase_span, bunsetu_bi_labels

MINI_BATCH_SIZE = 100


def run(
        model_path=None,
        split_mode=False,
        use_sentence_separator=False,
        hash_comment="print",
        output_path=None,
        output_format="0",
        require_gpu=False,
        parallel=1,
        files=None,
):
    if require_gpu:
        print("GPU enabled", file=sys.stderr)

    if use_sentence_separator:
        print("enabling sentence separator", file=sys.stderr)

    analyzer = Analyzer(
        model_path,
        split_mode,
        use_sentence_separator,
        hash_comment,
        output_format,
        require_gpu,
    )

    if parallel <= 0:
        parallel = max(1, cpu_count() + parallel)

    pool = None

    if output_path:
        output = open(str(output_path), "w")
    else:
        output = sys.stdout

    output_json = output_format in ["3", "json"]
    output_json_opened = False

    def output_json_open():
        nonlocal output_json_opened
        if output_json and not output_json_opened:
            print("[", file=output)
            output_json_opened = True
        elif output_json:
            print(" ,", file=output)

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
                    output_json_open()
                    print(ol, file=output)
        elif parallel == 1:
            analyzer.set_nlp()
            for path in files:
                with open(path, "r") as f:
                    for line in f:
                        for ol in analyzer.analyze_line(line):
                            output_json_open()
                            print(ol, file=output)
        else:
            buffer = []
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
                                    for ol in analyzer.analyze_line(line):
                                        output_json_open()
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
                                    output_json_open()
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
            if output_json and output_json_opened:
                print("]", file=output)
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
            split_mode,
            use_sentence_separator,
            hash_comment,
            output_format,
            require_gpu,
    ):
        self.model_path = model_path
        self.split_mode = split_mode
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

        if self.output_format in ["2", "mecab"]:
            nlp = JapaneseDefaults.create_tokenizer(config={
                "split_mode": self.split_mode
            }).tokenizer
        else:
            # TODO: Work-around for pickle error. Need to share model data.
            if self.model_path:
                nlp = spacy.load(self.model_path)
            else:
                nlp = spacy.load("ja_ginza")

            if self.split_mode:
                set_split_mode(nlp, self.split_mode)

            if not self.use_sentence_separator:  # TODO use Sentencizer
                nlp.tokenizer.use_sentence_separator = False
        self.nlp = nlp

    def analyze_lines_mp(self, lines):
        self.set_nlp()
        return tuple(self.analyze_line(line) for line in lines)

    def analyze_line(self, line):
        return analyze(self.nlp, self.hash_comment, self.output_format, line)


def analyze(nlp, hash_comment, output_format, line):
    line = line.rstrip("\n")
    if line.startswith("#"):
        if hash_comment == "print":
            return line,
        elif hash_comment == "skip":
            return (),
    if line == "":
        return "",
    if output_format in ["0", "conllu"]:
        doc = nlp(line)
        return analyze_conllu(doc)
    elif output_format in ["1", "cabocha"]:
        doc = nlp(line)
        return analyze_cabocha(doc)
    elif output_format in ["2", "mecab"]:
        doc = nlp.tokenize(line)
        return analyze_mecab(doc)
    elif output_format in ["3", "json"]:
        doc = nlp(line)
        return analyze_json(doc)
    else:
        raise Exception(output_format + " is not supported")


def bunsetu_info(doc):
    position_types = doc.user_data["bunsetu_position_types"]

    np_labels = [""] * len(doc)
    bunsetu_heads = bunsetu_head_list(doc)
    bunsetu_bi_list = bunsetu_bi_labels(doc)
    if bunsetu_head_list:
        for head_i in bunsetu_heads:
            bunsetu_head_token = doc[head_i]
            phrase = bunsetu_phrase_span(bunsetu_head_token)
            if phrase.label_ == "NP":
                for idx in range(phrase.start, phrase.end):
                    np_labels[idx] = "NP_B" if idx == phrase.start else "NP_I"
    return bunsetu_bi_list, position_types, np_labels


def analyze_json(doc):
    tokens = []
    for token in doc:
        t = {
            "id": token.i + 1,
            "orth": token.orth_,
            "tag": token.tag_,
            "pos": token.pos_,
            "lemma": token.lemma_,
            "head": token.head.i - token.i,
            "dep": token.dep_,
            "ner": "{}-{}".format(token.ent_iob_, token.ent_type_) if token.ent_type_ else token.ent_iob_,
        }
        if token.whitespace_:
            t["whitespace"] = token.whitespace_
        tokens.append("       " + json.dumps(t, ensure_ascii=False))
    tokens = ",\n".join(tokens)

    yield """ {{
  "paragraphs": [
   {{
    "raw": "{}",
    "sentences": [
     {{
      "tokens": [
{}
      ]
     }}
    ]
   }}
  ]
 }}""".format(
        doc.text,
        tokens,
    )


def analyze_conllu(doc, print_origin=True):
    bunsetu = bunsetu_info(doc)
    if print_origin:
        yield "# text = {}".format(doc.text)
    for token, (bunsetu_bi, position_type, np_label) in zip(
            doc,
            zip(*bunsetu),
    ):
        yield conllu_token_line(token, bunsetu_bi, position_type, np_label)
    yield ""


def conllu_token_line(token, bunsetu_bi, position_type, np_label):
    inf = inflection(token)
    reading = reading_form(token)
    ne = ent_label_ontonotes(token)
    ene = ent_label_ene(token)
    misc = "|".join(filter(lambda s: s, (
        "SpaceAfter=Yes" if token.whitespace_ else "SpaceAfter=No",
        "" if not bunsetu_bi else "BunsetuBILabel={}".format(bunsetu_bi),
        "" if not position_type else "BunsetuPositionType={}".format(position_type),
        np_label,
        "" if not inf else "Inf={}".format(inf),
        "" if not reading else "Reading={}".format(reading.replace("|", "\\|").replace("\\", "\\\\")),
        "" if not ne or ne == "O" else "NE={}".format(ne),
        "" if not ene or ene == "O" else "ENE={}".format(ene),
    )))

    return "\t".join([
        str(token.i + 1),
        token.orth_,
        token.lemma_,
        token.pos_,
        token.tag_.replace(",*", "").replace(",", "-"),
        "NumType=Card" if token.pos_ == "NUM" else "_",
        "0" if token.head.i == token.i else str(token.head.i + 1),
        token.dep_.lower() if token.dep_ else "_",
        "_",
        misc if misc else "_",
    ])


def analyze_cabocha(doc):
    bunsetu_bi_labels, bunsetu_position_types, np_labels = bunsetu_info(doc)
    lines = []
    for bunsetu_index, bunsetu in enumerate(doc.user_data["bunsetu"]):
        lines.append(cabocha_bunsetu_line(bunsetu["tokens"][0], bunsetu_index, doc))
        for token in bunsetu["tokens"]:
            lines.append(cabocha_token_line(token))
    lines.append("EOS")
    lines.append("")
    return lines


def cabocha_bunsetu_line(token, bunsetu_index, bunsetu_head_index, bunsetu_dep_index, bunsetu_func_index, dep_type):
    """
    dep_type = "D"
    for t in doc[token.i:]:
        if bunsetu_index != ex_attr(t).bunsetu_index:
            if bunsetu_func_index is None:
                bunsetu_func_index = t.i - token.i
            break
        tbi = ex_attr(t.head).bunsetu_index
        if bunsetu_index != tbi:
            bunsetu_head_index = t.i - token.i
            bunsetu_dep_index = tbi
        if bunsetu_func_index is None and ex_attr(t).bunsetu_position_type in {"FUNC", "SYN_HEAD"}:
            bunsetu_func_index = t.i - token.i
    else:
        if bunsetu_func_index is None:
            bunsetu_func_index = len(doc) - token.i
    if bunsetu_head_index is None:
        bunsetu_head_index = 0
    if bunsetu_dep_index is None:
        bunsetu_dep_index = -1
    """
    return "* {} {}{} {}/{} 0.000000".format(
        bunsetu_index,
        bunsetu_dep_index,
        dep_type,
        bunsetu_head_index,
        bunsetu_func_index,
    )


def cabocha_token_line(token, inf, reading):
    part_of_speech = token.tag_.replace("-", ",")
    part_of_speech += ",*" * (3 - part_of_speech.count(",")) + "," + inf
    return "{}\t{},{},{},{}\t{}".format(
        token.orth_,
        part_of_speech,
        token.lemma_,
        reading if reading else token.orth_,
        "*",
        "O" if token.ent_iob_ == "O" else "{}-{}".format(token.ent_iob_, token.ent_type_),
    )


def analyze_mecab(sudachipy_tokens):
    return tuple(mecab_token_line(t) for t in sudachipy_tokens) + ("EOS", "")


def mecab_token_line(token):
    reading = token.reading_form()
    return "{}\t{},{},{},{}".format(
        token.surface(),
        ",".join(token.part_of_speech()),
        token.normalized_form(),
        reading if reading else token.surface(),
        "*",
    )


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C", None]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    parallel=("parallel level (default=-1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginzame(
        model_path=None,
        split_mode=None,
        hash_comment="print",
        output_path=None,
        parallel=-1,
        *files,
):
    run(
        model_path=model_path,
        split_mode=split_mode,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format="mecab",
        require_gpu=False,
        parallel=parallel,
        files=files,
    )


def main_ginzame():
    plac.call(run_ginzame)


@plac.annotations(
    model_path=("model directory path", "option", "b", str),
    split_mode=("split mode", "option", "s", str, ["A", "B", "C", None]),
    hash_comment=("hash comment", "option", "c", str, ["print", "skip", "analyze"]),
    output_path=("output path", "option", "o", Path),
    output_format=("output format", "option", "f", str, ["0", "conllu", "1", "cabocha", "2", "mecab", "3", "json"]),
    require_gpu=("enable require_gpu", "flag", "g"),
    parallel=("parallel level (default=1, all_cpus=0)", "option", "p", int),
    files=("input files", "positional"),
)
def run_ginza(
        model_path=None,
        split_mode=None,
        hash_comment="print",
        output_path=None,
        output_format="conllu",
        require_gpu=False,
        parallel=1,
        *files,
):
    run(
        model_path=model_path,
        split_mode=split_mode,
        hash_comment=hash_comment,
        output_path=output_path,
        output_format=output_format,
        require_gpu=require_gpu,
        parallel=parallel,
        files=files,
    )


def main_ginza():
    plac.call(run_ginza)


if __name__ == "__main__":
    plac.call(run_ginza)
