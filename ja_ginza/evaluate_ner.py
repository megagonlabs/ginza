# coding: utf8
from __future__ import unicode_literals, print_function

import json
import os
from pathlib import Path
import plac
import sys
from . import *


@plac.annotations(
    model_path=("Model directory path", "option", "b", Path),
)
def evaluate_from_file(
        input_json_path,
        model_path=None,
        print_stats=True,
        nlp=None,
):
    corpus = convert_files(input_json_path)
    return evaluate(corpus, model_path, print_stats, nlp)


def evaluate(
        gold_corpus,
        model_path=None,
        print_stats=True,
        nlp=None,
):
    if not nlp:
        nlp = load_model(model_path)
        nlp.tokenizer.use_sentence_separator = False

    stats = Stats()

    print('Evaluate {} sentences'.format(len(gold_corpus)), file=sys.stderr, flush=True)
    for i, (sentence, nes) in enumerate(gold_corpus):
        if i % 100 == 0:
            print('.', end='', file=sys.stderr, flush=True)
        doc = nlp(sentence)
        evaluate_ne_result(stats, doc, nes)
    print(file=sys.stderr)

    if print_stats:
        stats.print()

    return stats


def evaluate_ne_result(stats, doc, gold_nes):
    stats.sentences += 1
    i = 0
    for gold_start, gold_end, gold_label in gold_nes:
        stats.gold_ents[gold_label] = stats.gold_ents.get(gold_label, 0) + 1
        gold_start = int(gold_start)
        gold_end = int(gold_end)
        gold_border_level = -1
        gold_label_level = -1
        matched = False
        while True:
            if i >= len(doc.ents):
                break
            ent = doc.ents[i]
            start = doc[ent.start].idx
            end = doc[ent.end].idx if ent.end < len(doc) else len(doc.text)
            label = ent.label_
            if start >= gold_end:
                break

            stats.result_ents[label] = stats.result_ents.get(label, 0) + 1
            if end <= gold_start:
                stats.count_up_confusion_matrix('{NONE}', label)
                i += 1
                continue
            stats.count_up_confusion_matrix(gold_label, label)
            gold_border_level = overlap_count(
                gold_start, gold_end, start, end, label, gold_border_level,
                stats.correct_gold_borders, stats.correct_result_borders,
            )
            if gold_label == label:
                gold_label_level = overlap_count(
                    gold_start, gold_end, start, end, label, gold_label_level,
                    stats.correct_gold_labels, stats.correct_result_labels,
                )
            matched = True
            i += 1

        if not matched:
            stats.count_up_confusion_matrix(gold_label, '{NONE}')

    for ent in doc.ents[i:]:
        stats.result_ents[ent.label_] = stats.result_ents.get(ent.label_, 0) + 1
        stats.count_up_confusion_matrix('{NONE}', ent.label_)

    return stats


OVERLAP_LEVELS = [
    'overlap',
    'include',
    'one side border',
    'both borders',
]


def _count_up(d, label, level, count):
    if label not in d:
        d[label] = [0] * len(OVERLAP_LEVELS)
    for l in range(level + 1):
        d[label][l] += count


def overlap_count(g_b, g_e, r_b, r_e, label, prev_level, correct_golds, correct_results):
    if g_b == r_b and g_e == r_e:
        level = 3
    elif g_b == r_b or g_e == r_e:
        level = 2
    elif g_b <= r_b and r_e <= g_e:
        level = 1
    elif g_b < r_e and r_b < g_e:
        level = 0
    else:
        return prev_level
    if prev_level < level:
        if prev_level >= 0:
            _count_up(correct_golds, label, level, -1)
        _count_up(correct_golds, label, level, 1)
        prev_level = level
    _count_up(correct_results, label, level, 1)
    return prev_level


class Stats:
    def __init__(self):
        self.sentences = 0
        self.gold_ents = {}
        self.result_ents = {}
        self.correct_gold_borders = {}
        self.correct_result_borders = {}
        self.correct_gold_labels = {}
        self.correct_result_labels = {}
        self.label_confusion_matrix = {}

    def score(self):
        return sum([sum([
                l[0] + l[-1] for l in d.values()
            ]) for d in [
                self.correct_gold_borders,
                self.correct_result_borders,
                self.correct_gold_labels,
                self.correct_result_labels,
            ]
            ])

    def print(self, file=sys.stdout):
        all_labels = sorted(self.gold_ents.keys() | self.result_ents.keys())
        # 全てのlabelの存在を保証
        for label in all_labels:
            if label not in self.gold_ents:
                self.gold_ents[label] = 0
            if label not in self.result_ents:
                self.result_ents[label] = 0
            _count_up(self.correct_gold_borders, label, 0, 0)
            _count_up(self.correct_result_borders, label, 0, 0)
            _count_up(self.correct_gold_labels, label, 0, 0)
            _count_up(self.correct_result_labels, label, 0, 0)

        for label in all_labels:
            golds = self.gold_ents[label]
            results = self.result_ents[label]
            print('label: {}, gold_ent={}, result_ent={}'.format(
                label,
                golds,
                results,
            ), file=file)
            if golds == 0:
                golds = 1
            if results == 0:
                results = 1
            gold_borders = self.correct_gold_borders[label]
            result_borders = self.correct_result_borders[label]
            gold_labels = self.correct_gold_labels[label]
            result_labels = self.correct_result_labels[label]
            for level in range(len(OVERLAP_LEVELS)):
                print(' {}'.format(OVERLAP_LEVELS[level]), file=file)
                print("  recall: {:.4f} (label={:.4f}), precision: {:.4f} (label={:.4f})".format(
                    gold_borders[level] / golds,
                    gold_labels[level] / golds,
                    result_borders[level] / results,
                    result_labels[level] / results,
                ), file=file)
        print(file=file)
        golds = sum(self.gold_ents.values())
        results = sum(self.result_ents.values())
        print("labels: <ALL>, sentence={}, gold_ent={}, result_ent={}".format(
            self.sentences,
            golds,
            results,
        ), file=file)
        if golds == 0:
            golds = 1
        if results == 0:
            results = 1
        gold_borders = [sum(all_labels) for all_labels in zip(*self.correct_gold_borders.values())]
        result_borders = [sum(all_labels) for all_labels in zip(*self.correct_result_borders.values())]
        gold_labels = [sum(all_labels) for all_labels in zip(*self.correct_gold_labels.values())]
        result_labels = [sum(all_labels) for all_labels in zip(*self.correct_result_labels.values())]
        for level in range(len(OVERLAP_LEVELS)):
            print(' {}'.format(OVERLAP_LEVELS[level]), file=file)
            print("  recall: {:.4f} (label={:.4f}), precision: {:.4f} (label={:.4f})".format(
                gold_borders[level] / golds,
                gold_labels[level] / golds,
                result_borders[level] / results,
                result_labels[level] / results,
            ), file=file)
        print(file=file)
        print('label confusion matrix', file=file)
        all_labels.append('{NONE}')
        col_width = max(map(lambda s: len(s), all_labels))
        print('|'.join([label.center(col_width) for label in [''] + all_labels]), file=file)
        for l1, label1 in enumerate(all_labels):
            line = label1.center(col_width)
            for l2, label2 in enumerate(all_labels):
                label = _confusion_matrix_label(label1, label2)
                count = self.label_confusion_matrix.get(label, 0)
                line += '|' + str(count).rjust(col_width)
            print(line, file=file)

    def count_up_confusion_matrix(self, label1, label2):
        label = _confusion_matrix_label(label1, label2)
        if label in self.label_confusion_matrix:
            self.label_confusion_matrix[label] += 1
        else:
            self.label_confusion_matrix[label] = 1


def _confusion_matrix_label(label1, label2):
    return label1 + ':' + label2


def convert_files(path, top=True):
    if top:
        print('loading {}'.format(str(path)), file=sys.stderr, flush=True)

    sentences = []

    if type(path) == list:
        for p in path:
            sentences += convert_files(p, False)
        return sentences

    if os.path.isdir(path):
        for sub_path in os.listdir(path):
            sentences += convert_files(os.path.join(path, sub_path), False)
    else:
        with open(path, 'r') as f:
            print('.'.format(str(path)), end='', file=sys.stderr, flush=True)
            sentences += json.load(f)

    if top:
        print(file=sys.stderr, flush=True)

    return sentences


if __name__ == '__main__':
    plac.call(evaluate_from_file)
