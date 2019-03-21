# coding: utf8
from __future__ import unicode_literals, print_function

from pathlib import Path
import plac
import sys
from .bccwj_ud_corpus import convert_files
from . import *
from .parse_tree import create_parsed_sentences, rewrite_by_tokenizer


@plac.annotations(
    corpus_type=("Corpus type (default='bccwj_ud')", "option", "t", str),
    model_path=("Model directory path", "option", "b", Path),
    parse_result_path=("Parse result path", "option", "p", Path),
    keep_gold_tokens=("Never rewrite gold corpus", "flag", "x"),
    evaluate_all_combinations=("Evaluate all combinations", "flag", "a"),
)
def evaluate_from_file(
        path,
        corpus_type='bccwj_ud',
        model_path=None,
        parse_result_path=None,
        keep_gold_tokens=False,
        evaluate_all_combinations=False,
        print_file=sys.stdout,
        nlp=None,
):
    parse_results = None
    if corpus_type == 'bccwj_ud':
        gold = convert_files(path)
        if parse_result_path:
            parse_results = convert_files(parse_result_path)
    else:
        gold = None
    if not nlp:
        nlp = load_model(model_path)
        nlp.tokenizer.use_sentence_separator = False

    rewritten = [g.clone() for g in gold]
    if not keep_gold_tokens:
        print('Rewriting gold corpus with tokenizer', file=sys.stderr)
        disabled = nlp.disable_pipes(*nlp.pipe_names)
        rewrite_by_tokenizer(rewritten, nlp, sys.stderr)
        disabled.restore()
        print(file=sys.stderr, flush=True)

    return evaluate(
        gold,
        rewritten,
        model_path,
        parse_results,
        keep_gold_tokens,
        evaluate_all_combinations,
        print_file,
        nlp
    )


def evaluate(
        gold_corpus,
        rewritten_corpus,
        model_path=None,
        parse_results=None,
        keep_gold_tokens=False,
        evaluate_all_combinations=False,
        print_file=None,
        nlp=None,
        morph_custom_condition=lambda g, r: g.pos == r.pos if g.pos_detail.find('可能') >= 0 else None,
):
    if not nlp:
        nlp = load_model(model_path)
        nlp.tokenizer.use_sentence_separator = False

    stats = EvaluationResult(keep_gold_tokens, evaluate_all_combinations)

    print('Evaluate {} sentences'.format(len(gold_corpus)), file=sys.stderr, flush=True)
    for i, (gold, rewritten) in enumerate(zip(gold_corpus, rewritten_corpus)):
        if i % 100 == 0:
            print('.', end='', file=sys.stderr, flush=True)
        try:
            stats.evaluate(gold, rewritten, nlp, morph_custom_condition, parse_results[i] if parse_results else None)
        except Exception as e:
            print("Evaluation error: {} {} {}".format(gold.path, gold.id, gold.line), file=sys.stderr)
            print(gold, file=sys.stderr, flush=True)
            raise e
    print(file=sys.stderr, flush=True)

    if print_file:
        stats.print(print_file)

    return stats


class EvaluationResult:
    def __init__(self, keep_gold_tokens, evaluate_all_combinations):
        self.keep_gold_tokens = keep_gold_tokens
        self.evaluate_all_combinations = evaluate_all_combinations
        self.gold_gold = Stats()
        self.gold_rewritten = Stats()
        self.gold_tokenizer = Stats()
        self.rewritten_gold = Stats()
        self.rewritten_rewritten = Stats()
        self.rewritten_tokenizer = Stats()

    @property
    def gg(self):
        return self.gold_gold

    @property
    def gr(self):
        return self.gold_rewritten

    @property
    def gt(self):
        return self.gold_tokenizer

    @property
    def rg(self):
        return self.rewritten_gold

    @property
    def rr(self):
        return self.rewritten_rewritten

    @property
    def rt(self):
        return self.rewritten_tokenizer

    def score(self):
        if self.keep_gold_tokens:
            return self.gg.score()
        else:
            return self.rt.score()

    def evaluate(self, gold, rewritten, nlp, morph_custom_condition, parse_result=None):
        gold_result = None
        if self.evaluate_all_combinations or self.keep_gold_tokens:
            gold_result = parse_result if parse_result else create_parsed_sentences(nlp(gold), False)[0]
        rewritten_result = None
        if self.evaluate_all_combinations:
            rewritten_result = parse_result if parse_result else create_parsed_sentences(nlp(rewritten), False)[0]
        nlp_result = None
        rewritten_corrected = None
        if self.evaluate_all_combinations or not self.keep_gold_tokens:
            nlp_result = parse_result if parse_result else create_parsed_sentences(nlp(str(gold)), False)[0]
            rewritten_corrected = rewritten.apply_corrector(nlp.vocab)

        if self.evaluate_all_combinations or self.keep_gold_tokens:
            evaluate_parse_result(self.gg, gold, gold_result, morph_custom_condition)
        if self.evaluate_all_combinations:
            evaluate_parse_result(self.rg, rewritten_corrected, gold_result, morph_custom_condition)
            evaluate_parse_result(self.gr, gold, rewritten_result, morph_custom_condition)
            evaluate_parse_result(self.rr, rewritten_corrected, rewritten_result, morph_custom_condition)
            evaluate_parse_result(self.gt, gold, nlp_result, morph_custom_condition)
        if self.evaluate_all_combinations or not self.keep_gold_tokens:
            evaluate_parse_result(self.rt, rewritten_corrected, nlp_result, morph_custom_condition)

    def print(self, file=sys.stdout):
        if self.evaluate_all_combinations or self.keep_gold_tokens:
            print('--- compare GOLD dependencies to parse results using GOLD tokens ---', file=file)
            self.gg.print(file=file)
        if self.evaluate_all_combinations:
            print('--- compare GOLD dependencies to parse results using REWRITTEN tokens ---', file=file)
            self.gr.print(file=file)
            print('--- compare GOLD dependencies to parse results using TOKENIZER output ---', file=file)
            self.gt.print(file=file)
            print('--- compare REWRITTEN dependencies to parse results using GOLD tokens ---', file=file)
            self.rg.print(file=file)
            print('--- compare REWRITTEN dependencies to parse results using REWRITTEN tokens ---', file=file)
            self.rr.print(file=file)
        if self.evaluate_all_combinations or not self.keep_gold_tokens:
            print('--- compare REWRITTEN dependencies to parse results using TOKENIZER output ---', file=file)
            self.rt.print(file=file)


class Stats:
    def __init__(self):
        self.sentences = 0
        self.gold_tokens = 0
        self.result_tokens = 0
        self.custom_tokens = 0
        self.correct_tokens = 0
        self.correct_pos_tokens = 0
        self.correct_pos_uas_tokens = 0
        self.correct_pos_las_tokens = 0
        self.correct_uas_tokens = 0
        self.correct_las_tokens = 0
        self.correct_custom_tokens = 0
        self.correct_sentences = 0
        self.correct_pos_sentences = 0
        self.correct_pos_uas_sentences = 0
        self.correct_pos_las_sentences = 0
        self.correct_uas_sentences = 0
        self.correct_las_sentences = 0
        self.correct_roots = 0

    def score(self):
        return sum([
            self.correct_tokens,
            self.correct_pos_tokens,
            self.correct_pos_uas_tokens,
            self.correct_pos_las_tokens,
            self.correct_uas_tokens,
            self.correct_las_tokens,
            self.correct_custom_tokens,
            self.correct_sentences,
            self.correct_pos_sentences,
            self.correct_pos_uas_sentences,
            self.correct_pos_las_sentences,
            self.correct_uas_sentences,
            self.correct_las_sentences,
            self.correct_roots,
        ])

    def print(self, file=sys.stdout):
        print(" sentence={}, gold_token={}, result_token={}, custom={:.4f}({}/{})".format(
            self.sentences,
            self.gold_tokens,
            self.result_tokens,
            (self.correct_custom_tokens / self.custom_tokens) if self.custom_tokens > 0 else 0,
            self.correct_custom_tokens,
            self.custom_tokens,
        ), file=file)
        print("   sentence:LAS={:.4f},UAS={:.4f},LPOS={:.4f},UPOS={:.4f},POS={:.4f},boundary={:.4f},root={:.4f}".format(
            self.correct_las_sentences / self.sentences,
            self.correct_uas_sentences / self.sentences,
            self.correct_pos_las_sentences / self.sentences,
            self.correct_pos_uas_sentences / self.sentences,
            self.correct_pos_sentences / self.sentences,
            self.correct_sentences / self.sentences,
            self.correct_roots / self.sentences,
        ), file=file)
        print(" tkn_recall:LAS={:.4f},UAS={:.4f},LPOS={:.4f},UPOS={:.4f},POS={:.4f},boundary={:.4f}".format(
            self.correct_las_tokens / self.gold_tokens,
            self.correct_uas_tokens / self.gold_tokens,
            self.correct_pos_las_tokens / self.gold_tokens,
            self.correct_pos_uas_tokens / self.gold_tokens,
            self.correct_pos_tokens / self.gold_tokens,
            self.correct_tokens / self.gold_tokens,
        ), file=file)
        print("  precision:LAS={:.4f},UAS={:.4f},LPOS={:.4f},UPOS={:.4f},POS={:.4f},boundary={:.4f}".format(
            self.correct_las_tokens / self.result_tokens,
            self.correct_uas_tokens / self.result_tokens,
            self.correct_pos_las_tokens / self.result_tokens,
            self.correct_pos_uas_tokens / self.result_tokens,
            self.correct_pos_tokens / self.result_tokens,
            self.correct_tokens / self.result_tokens,
        ), file=file)
        file.flush()


def is_correct_dep(g, r):
    return g.dep_morph.offset <= r.dep_morph.offset and g.dep_morph.end >= r.dep_morph.end or \
           g.dep_morph.offset >= r.dep_morph.offset and g.dep_morph.end <= r.dep_morph.end


def evaluate_parse_result(stats, gold, result, morph_custom_condition, print_input=False, debug=True):

    if print_input:
        print()
        print("gold:  ", gold.to_string())
        print("result:", result.to_string())
    stats.sentences += 1
    stats.gold_tokens += len(gold.morphs)
    stats.result_tokens += len(result.morphs)

    if gold.root.offset == result.root.offset and gold.root.end == result.root.end:
        stats.correct_roots += 1

    correct_tokens = 0
    correct_pos_tokens = 0
    correct_uas_tokens = 0
    correct_las_tokens = 0
    correct_pos_uas_tokens = 0
    correct_pos_las_tokens = 0
    custom_tokens = 0
    correct_custom_tokens = 0
    index_g = 0
    index_r = 0
    last_match_g = 0
    last_match_r = 0
    while index_g < len(gold.morphs) and index_r < len(result.morphs):
        g = gold.morphs[index_g]
        g_end = g.end
        r = result.morphs[index_r]
        r_end = r.end
        if g.offset == r.offset:
            if g_end == r_end:
                correct_tokens += 1
                if g.pos == r.pos:
                    correct_pos_tokens += 1
                    if is_correct_dep(g, r):
                        correct_uas_tokens += 1
                        correct_pos_uas_tokens += 1
                        if g.dep_label == r.dep_label:
                            correct_las_tokens += 1
                            correct_pos_las_tokens += 1
                else:
                    if is_correct_dep(g, r):
                        correct_uas_tokens += 1
                        if g.dep_label == r.dep_label:
                            correct_las_tokens += 1
        if debug:
            if g_end == r_end:
                print('{}\t{}\t{}'.format(
                    '=' if index_g == last_match_g and index_r == last_match_r else
                    '>' if index_g == last_match_g else
                    '<' if index_r == last_match_r else
                    '!',
                    ','.join([m.surface for m in gold.morphs[last_match_g:index_g + 1]]),
                    ','.join([m.surface for m in result.morphs[last_match_r:index_r + 1]]),
                ))
                last_match_g = index_g + 1
                last_match_r = index_r + 1
        if g_end <= r_end:
            index_g += 1
        if g_end >= r_end:
            index_r += 1

    tokens = len(gold.morphs)
    stats.correct_tokens += correct_tokens
    if correct_tokens == tokens:
        stats.correct_sentences += 1
    stats.correct_pos_tokens += correct_pos_tokens
    if correct_pos_tokens == tokens:
        stats.correct_pos_sentences += 1
    stats.correct_uas_tokens += correct_uas_tokens
    if correct_uas_tokens == tokens:
        stats.correct_uas_sentences += 1
    stats.correct_las_tokens += correct_las_tokens
    if correct_las_tokens == tokens:
        stats.correct_las_sentences += 1
    stats.correct_pos_uas_tokens += correct_pos_uas_tokens
    if correct_pos_uas_tokens == tokens:
        stats.correct_pos_uas_sentences += 1
    stats.correct_pos_las_tokens += correct_pos_las_tokens
    if correct_pos_las_tokens == tokens:
        stats.correct_pos_las_sentences += 1

    result_borders = {r.offset: (len(r.surface), r) for r in result.morphs}
    for g in gold.origin.morphs if hasattr(gold, 'origin') else gold.morphs:
        length, r = result_borders.get(g.offset, (0, None))
        if length == len(g.surface):
            custom = morph_custom_condition(g, r)
            if custom is not None:
                custom_tokens += 1
                if custom:
                    correct_custom_tokens += 1
                # else:
                    # print(custom, g.surface, r.surface, g.pos, r.pos, g.pos_detail, r.pos_detail)
    stats.custom_tokens += custom_tokens
    stats.correct_custom_tokens += correct_custom_tokens

    return stats


if __name__ == '__main__':
    plac.call(evaluate_from_file)
