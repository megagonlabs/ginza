# coding: utf8
from __future__ import unicode_literals, print_function

import json
import sys

import spacy


USAGE = '''
Usage: python evaluate_model.py spacy_model_path json_file1 [json_file2 ...]
'''


def evaluate_from_file(
        model_path,
        json_files,
):
    gold = []
    for file in json_files:
        with open(file, 'r', encoding="utf-8") as f:
            for doc in json.load(f):
                for paragraph in doc['paragraphs']:
                    for sentence in paragraph['sentences']:
                        tokens = sentence['tokens']
                        gold.append(tokens)

    nlp = spacy.load(model_path)
    nlp.tokenizer.use_sentence_separator = False

    return evaluate(
        gold,
        nlp,
        sys.stdout,
    )


def evaluate(
        gold_corpus,
        nlp,
        fout=sys.stdout,
        morph_custom_condition=lambda g, r: g['pos'] == r.pos_ if g['tag'].find('可能') >= 0 else None,
):
    stats = Stats()

    print('Evaluate {} sentences'.format(len(gold_corpus)), file=sys.stderr, flush=True)
    for i, gold_tokens in enumerate(gold_corpus):
        if i % 100 == 0:
            print('.', end='', file=sys.stderr, flush=True)

        offset = 0
        sentence = ''
        for idx, t in enumerate(gold_tokens):
            t['head'] = gold_tokens[idx + t['head']]
            t['offset'] = offset
            offset += len(t['orth'])
            t['end'] = offset
            sentence += t['orth']
            if 'whitespace' in t and t['whitespace']:
                offset += 1
                sentence += ' '
        try:
            doc = nlp(sentence)
            stats.evaluate(gold_tokens, doc, morph_custom_condition)
        except Exception as e:
            print("Evaluation error:", sentence, file=sys.stderr)
            raise e
    print(file=sys.stderr, flush=True)

    stats.print(fout)

    return stats


COMMON_FORMAT = "LAS={:.4f},UAS={:.4f},LAS_POS={:.4f},UAS_POS={:.4f},POS={:.4f},TAG={:.4f},boundary={:.4f}"


class Stats:
    def __init__(self):
        self.sentences = 0
        self.gold_tokens = 0
        self.result_tokens = 0
        self.custom_tokens = 0
        self.correct_tokens = 0
        self.correct_tag_tokens = 0
        self.correct_pos_tokens = 0
        self.correct_pos_uas_tokens = 0
        self.correct_pos_las_tokens = 0
        self.correct_uas_tokens = 0
        self.correct_las_tokens = 0
        self.correct_custom_tokens = 0
        self.correct_sentences = 0
        self.correct_tag_sentences = 0
        self.correct_pos_sentences = 0
        self.correct_pos_uas_sentences = 0
        self.correct_pos_las_sentences = 0
        self.correct_uas_sentences = 0
        self.correct_las_sentences = 0
        self.correct_roots = 0
        self.dep_confusion = {}
        self.pos_confusion = {}

        self.gold_ents = 0
        self.result_ents = 0
        self.correct_ent_spans = 0
        self.correct_ent_labels = 0
        self.ent_confusion = {}

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
        def f1(p, r):
            if p + r == 0.0:
                return 0.0
            else:
                return 2 * p * r / (p + r)

        for title, matrix in (
                ('pos_confusion', self.pos_confusion),
                ('dep_confusion', self.dep_confusion),
                ('ent_confusion', self.ent_confusion),
        ):
            print(' {}'.format(title), file=file)
            max_label_len = str(max(len(g) for g in matrix.keys()))
            for gold, results in sorted(matrix.items(), key=lambda t: t[0]):
                results = matrix[gold]
                print(('  {:<' + max_label_len + '}({:>6}): {}').format(gold, sum(results.values()), ', '.join([
                    '{}={}'.format(pos, num) for pos, num in sorted(results.items(), key=lambda t:-t[1])
                ])), file=file)
            print(' precision, recall, f1', file=file)
            for gold, results in sorted(matrix.items(), key=lambda t: t[0]):
                results = matrix[gold]
                total = sum(results.values())
                correct = results.get(gold, results.get(gold.upper(), 0))
                output = sum(sum(v for k, v in r.items() if k.lower() == gold.lower()) for r in matrix.values())
                p = correct / output if output else 0
                r = correct / total if total else 0
                f = p * r * 2 / (p + r) if p and r else 0
                print(('  {:<' + max_label_len + '}: {:.3f}, {:.3f}, {:.3f}').format(gold, p, r, f), file=file)

        print("sentence={}, gold_token={}, result_token={}, custom_cond={:.4f}({}/{})".format(
            self.sentences,
            self.gold_tokens,
            self.result_tokens,
            (self.correct_custom_tokens / self.custom_tokens) if self.custom_tokens > 0 else 0,
            self.correct_custom_tokens,
            self.custom_tokens,
        ), file=file)
        print(("        token_f1:" + COMMON_FORMAT).format(
            f1(self.correct_las_tokens / self.gold_tokens, self.correct_las_tokens / self.result_tokens),
            f1(self.correct_uas_tokens / self.gold_tokens, self.correct_uas_tokens / self.result_tokens),
            f1(self.correct_pos_las_tokens / self.gold_tokens, self.correct_pos_las_tokens / self.result_tokens),
            f1(self.correct_pos_uas_tokens / self.gold_tokens, self.correct_pos_uas_tokens / self.result_tokens),
            f1(self.correct_pos_tokens / self.gold_tokens, self.correct_pos_tokens / self.result_tokens),
            f1(self.correct_tag_tokens / self.gold_tokens, self.correct_tag_tokens / self.result_tokens),
            f1(self.correct_tokens / self.gold_tokens, self.correct_tokens / self.result_tokens),
        ), file=file)
        print(("    token_recall:" + COMMON_FORMAT).format(
            self.correct_las_tokens / self.gold_tokens,
            self.correct_uas_tokens / self.gold_tokens,
            self.correct_pos_las_tokens / self.gold_tokens,
            self.correct_pos_uas_tokens / self.gold_tokens,
            self.correct_pos_tokens / self.gold_tokens,
            self.correct_tag_tokens / self.gold_tokens,
            self.correct_tokens / self.gold_tokens,
        ), file=file)
        print((" token_precision:" + COMMON_FORMAT).format(
            self.correct_las_tokens / self.result_tokens,
            self.correct_uas_tokens / self.result_tokens,
            self.correct_pos_las_tokens / self.result_tokens,
            self.correct_pos_uas_tokens / self.result_tokens,
            self.correct_pos_tokens / self.result_tokens,
            self.correct_tag_tokens / self.result_tokens,
            self.correct_tokens / self.result_tokens,
        ), file=file)
        print(("  whole_sentence:" + COMMON_FORMAT + ",root={:.4f}").format(
            self.correct_las_sentences / self.sentences,
            self.correct_uas_sentences / self.sentences,
            self.correct_pos_las_sentences / self.sentences,
            self.correct_pos_uas_sentences / self.sentences,
            self.correct_pos_sentences / self.sentences,
            self.correct_tag_sentences / self.sentences,
            self.correct_sentences / self.sentences,
            self.correct_roots / self.sentences,
        ), file=file)
        print("ent_gold={}, ent_result={}".format(
                self.gold_ents,
                self.result_ents,
        ), file=file)
        if self.gold_ents and self.result_ents:
            print("        ent_f1:SPAN_LABEL={:.4f},SPAN_ONLY={:.4f}".format(
                f1(self.correct_ent_labels / self.gold_ents, self.correct_ent_labels / self.result_ents),
                f1(self.correct_ent_spans / self.gold_ents, self.correct_ent_spans / self.result_ents),
            ), file=file)
            print("    ent_recall:SPAN_LABEL={:.4f},SPAN_ONLY={:.4f}".format(
                self.correct_ent_labels / self.gold_ents,
                self.correct_ent_spans / self.gold_ents,
            ), file=file)
            print(" ent_precision:SPAN_LABEL={:.4f},SPAN_ONLY={:.4f}".format(
                self.correct_ent_labels / self.result_ents,
                self.correct_ent_spans / self.result_ents,
            ), file=file)
        file.flush()

    def evaluate(self, gold, doc, morph_custom_condition, debug=False):
        def count(matrix, l1, l2):
            if l1 not in matrix:
                matrix[l1] = {}
            m2 = matrix[l1]
            if l2 in m2:
                m2[l2] += 1
            else:
                m2[l2] = 1

        self.sentences += 1
        self.gold_tokens += len(gold)
        self.result_tokens += len(doc)

        correct_tokens = 0
        correct_tag_tokens = 0
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
        while index_g < len(gold) and index_r < len(doc):
            g = gold[index_g]
            g_end = g['end']
            r = doc[index_r]
            r_end = r.idx + len(r.orth_)
            if g['offset'] == r.idx:
                if g_end == r_end:
                    correct_tokens += 1
                    count(self.pos_confusion, g['pos'], r.pos_)
                    if g['tag'] == r.tag_:
                        correct_tag_tokens += 1
                    if g['pos'] == r.pos_:
                        correct_pos_tokens += 1
                    if is_correct_dep(g, r):
                        correct_uas_tokens += 1
                        count(self.dep_confusion, g['dep'].lower(), r.dep_)
                        if g['pos'] == r.pos_:
                            correct_pos_uas_tokens += 1
                        if g['dep'].lower() == r.dep_.lower():
                            correct_las_tokens += 1
                            if g['pos'] == r.pos_:
                                correct_pos_las_tokens += 1
                    else:
                        count(self.dep_confusion, g['dep'].lower(), '_')
                    if g['dep'].lower() == 'root' and r.dep_.lower() == 'root':
                        self.correct_roots += 1
                elif g_end < r_end:
                    count(self.pos_confusion, g['pos'], '_')
                    count(self.dep_confusion, g['dep'].lower(), '_')
            elif g_end < r_end:
                count(self.pos_confusion, g['pos'], '_')
                count(self.dep_confusion, g['dep'].lower(), '_')

            if debug:
                if g_end == r_end:
                    print('{}\t{}\t{}'.format(
                        '=' if index_g == last_match_g and index_r == last_match_r else
                        '>' if index_g == last_match_g else
                        '<' if index_r == last_match_r else
                        '!',
                        ','.join(['-'.join((
                            m['orth'], m['pos'], m['dep'], str(m['head']['offset']), str(m['head']['end'])
                        )) for m in gold[last_match_g:index_g + 1]]),
                        ','.join(['-'.join((
                            m.orth_, m.pos_, m.dep_, str(m.head.idx), str(m.head.idx + len(m.head.orth_))
                        )) for m in doc[last_match_r:index_r + 1]]),
                    ))
                    last_match_g = index_g + 1
                    last_match_r = index_r + 1
            if g_end <= r_end:
                index_g += 1
            if g_end >= r_end:
                index_r += 1

        tokens = len(gold)
        self.correct_tokens += correct_tokens
        if correct_tokens == tokens:
            self.correct_sentences += 1
        self.correct_tag_tokens += correct_tag_tokens
        if correct_tag_tokens == tokens:
            self.correct_tag_sentences += 1
        self.correct_pos_tokens += correct_pos_tokens
        if correct_pos_tokens == tokens:
            self.correct_pos_sentences += 1
        self.correct_uas_tokens += correct_uas_tokens
        if correct_uas_tokens == tokens:
            self.correct_uas_sentences += 1
        self.correct_las_tokens += correct_las_tokens
        if correct_las_tokens == tokens:
            self.correct_las_sentences += 1
        self.correct_pos_uas_tokens += correct_pos_uas_tokens
        if correct_pos_uas_tokens == tokens:
            self.correct_pos_uas_sentences += 1
        self.correct_pos_las_tokens += correct_pos_las_tokens
        if correct_pos_las_tokens == tokens:
            self.correct_pos_las_sentences += 1

        result_borders = {r.idx: (len(r.orth_), r) for r in doc}
        for g in gold:
            length, r = result_borders.get(g['offset'], (0, None))
            if length == len(g['orth']):
                custom = morph_custom_condition(g, r)
                if custom is not None:
                    custom_tokens += 1
                    if custom:
                        correct_custom_tokens += 1
                    # else:
                        # print(custom, g.surface, r.surface, g.pos, r.pos, g.tag, r.tag)
        self.custom_tokens += custom_tokens
        self.correct_custom_tokens += correct_custom_tokens

        gold_ents = {}
        ent_label = None
        ent_begin = None
        for g in gold:
            ner = g['ner'] if 'ner' in g else '-'
            if ner.startswith('B-'):
                ent_label = ner[2:]
                ent_begin = g['offset']
            elif ner.startswith('L-'):
                gold_ents[(ent_begin, g['end'])] = ent_label
                ent_label = None
                ent_begin = None
            elif ner.startswith('U-'):
                gold_ents[(g['offset'], g['end'])] = ner[2:]
        result_ents = {}
        ent_label = None
        ent_begin = None
        ent_end = None
        for r in doc:
            if ent_label and r.ent_iob_ != 'I':
                result_ents[(ent_begin, ent_end)] = ent_label
                ent_label = None
                ent_begin = None
                ent_end = None
            if r.ent_iob_ == 'B':
                ent_label = r.ent_type_
                ent_begin = r.idx
                ent_end = r.idx + len(r.orth_)
            elif r.ent_iob_ == 'I':
                ent_end = r.idx + len(r.orth_)
        if ent_label:
            result_ents[(ent_begin, ent_end)] = ent_label

        self.gold_ents += len(gold_ents)
        self.result_ents += len(result_ents)
        for k, gold_label in gold_ents.items():
            if k in result_ents:
                self.correct_ent_spans += 1
                result_label = result_ents[k]
                count(self.ent_confusion, gold_label, result_label)
                if gold_label == result_label:
                    self.correct_ent_labels += 1
            else:
                count(self.ent_confusion, gold_label, '_')


def is_correct_dep(g, r):
    return g['head']['offset'] <= r.head.idx and g['head']['end'] >= r.head.idx + len(r.head.orth_) or \
           g['head']['offset'] >= r.head.idx and g['head']['end'] <= r.head.idx + len(r.head.orth_)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        exit(2)
    evaluate_from_file(sys.argv[1], sys.argv[2:])
