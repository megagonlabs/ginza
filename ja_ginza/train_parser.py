# coding: utf8
from __future__ import unicode_literals, print_function

import datetime
import plac
import random
import spacy
from . import *
from .bccwj_ud_corpus import convert_files
from .corpus import *
from .evaluate_parser import evaluate
from .parse_tree import rewrite_by_tokenizer


@plac.annotations(
    corpus_type=("Corpus type (default='bccwj_ud')", "option", "t", str),
    model_path=("Path to model directory", "option", "b", Path),
    clear_model=("Clear parser model", "flag", "c"),
    keep_gold_tokens=("Never rewrite gold corpus with tokenizer", "flag", "x"),
    evaluate_all_combinations=("Evaluate all combinations", "flag", "a"),
    mini_batch_size=("Number of mini batch size", "option", "m", int),
    max_epochs=("Number of max epochs (default=32)", "option", "p", int),
    online_sgd_max_epochs=("Number of online SGD max epochs (default=0)", "option", "s", int),
    give_up_iter=("Number of parser training give-up iterations", "option", "u", int),
    evaluation_corpus_path=("Evaluation corpus path", "option", "e", Path),
    output_base_path=("Output base path (default=model_path)", "option", "o", Path),
    require_gpu=("enable require_gpu", "flag", "g"),
)
def train_from_file(
        input_path,
        corpus_type='bccwj_ud',
        model_path=None,
        clear_model=False,
        keep_gold_tokens=False,
        evaluate_all_combinations=False,
        mini_batch_size=128,
        max_epochs=32,
        online_sgd_max_epochs=0,
        give_up_iter=3,
        evaluation_corpus_path=None,
        output_base_path=None,
        require_gpu=False,
):
    if require_gpu:
        spacy.require_gpu()
        print("GPU enabled", file=sys.stderr)
    if corpus_type == 'bccwj_ud':
        corpus = convert_files(input_path)
        if evaluation_corpus_path:
            evaluation_gold = convert_files(evaluation_corpus_path)
        else:
            evaluation_gold = corpus[0:100]
    else:
        corpus = None
        evaluation_gold = None
    return train(
        corpus,
        model_path,
        clear_model,
        keep_gold_tokens,
        evaluate_all_combinations,
        mini_batch_size,
        max_epochs,
        online_sgd_max_epochs,
        give_up_iter,
        evaluation_gold,
        output_base_path
    )


def train(
        gold,
        model_path,
        clear_model=False,
        keep_gold_tokens=False,
        evaluate_all_combinations=False,
        mini_batch_size=128,
        max_epochs=32,
        online_sgd_max_epochs=0,
        give_up_iter=3,
        evaluation_gold=None,
        output_base_path=None,
):
    if model_path is None:
        raise Exception('model_path must be specified')

    nlp = load_model(model_path)
    nlp.tokenizer.use_sentence_separator = False

    if output_base_path:
        output_path = output_base_path / model_path.name
    else:
        output_path = model_path

    if 'JapaneseCorrector' not in nlp.pipe_names:
        corrector = nlp.create_pipe('JapaneseCorrector')
        nlp.add_pipe(corrector, last=True)

    # add the parser to the pipeline if it doesn't exist
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'parser' not in nlp.pipe_names:
        parser = nlp.create_pipe('parser')
        nlp.add_pipe(parser, first=True)
        print("parser created", file=sys.stderr)
        clear_model = True
    elif clear_model:
        nlp.remove_pipe('parser')
        parser = nlp.create_pipe('parser')
        nlp.add_pipe(parser, first=True)
        print("parser cleared", file=sys.stderr)
    # otherwise, get it, so we can add labels to it
    else:
        parser = nlp.get_pipe('parser')

    if keep_gold_tokens:
        print('Use gold corpus without rewriting', file=sys.stderr, flush=True)
        rewritten = gold
        evaluation_rewritten = evaluation_gold
    else:
        print('Rewriting gold corpus with tokenizer', file=sys.stderr, flush=True)
        disabled = nlp.disable_pipes(*nlp.pipe_names)
        rewritten = [g.clone() for g in gold]
        rewrite_by_tokenizer(rewritten, nlp, sys.stderr)
        print(file=sys.stderr, flush=True)
        evaluation_rewritten = [g.clone() for g in evaluation_gold]
        rewrite_by_tokenizer(evaluation_rewritten, nlp, sys.stderr)
        print(file=sys.stderr, flush=True)
        disabled.restore()

    checked = []
    checked_gold = []
    rejected = []
    rejected_gold = []
    for s, g in zip(rewritten, gold):
        crossing = s.find_crossing_arcs()
        if crossing:
            rejected.append(s)
            rejected_gold.append(g)
            m1, m2 = crossing
            print('Inconsistent entry:', s.path, s.id, s.line, file=sys.stderr)
            print('arcs are crossing between {}:{}->{}:{} and {}:{}->{}:{}'.format(
                m1.id,
                m1.surface,
                m1.dep_morph.id,
                m1.dep_morph.surface,
                m2.id,
                m2.surface,
                m2.dep_morph.id,
                m2.dep_morph.surface,
            ), file=sys.stderr)
        else:
            checked.append(s)
            checked_gold.append(g)
    print("training corpus statistics")
    print("  origin  : {} sentences, {} gold_tokens, {} rewritten_tokens".format(
        len(gold), sum([len(s.morphs) for s in gold]), sum([len(s.morphs) for s in rewritten]))
    )
    print("  rejected: {} sentences, {} gold_tokens, {} rewritten_tokens".format(
        len(rejected), sum([len(s.morphs) for s in rejected_gold]), sum([len(s.morphs) for s in rejected]))
    )
    print("  used    : {} sentences, {} gold_tokens, {} rewritten_tokens".format(
        len(checked), sum([len(s.morphs) for s in checked_gold]), sum([len(s.morphs) for s in checked])),
        flush=True
    )
    rewritten = checked

    entire_set = rewritten

    # add labels
    for sentence in entire_set:
        for m in sentence.morphs:
            parser.add_label(m.dep_label)

    if clear_model:
        best = None
        best_model = None
    else:
        best = evaluate(
            evaluation_gold,
            evaluation_rewritten,
            keep_gold_tokens=keep_gold_tokens,
            evaluate_all_combinations=evaluate_all_combinations,
            nlp=nlp,
            print_file=sys.stdout
        )
        best_model = nlp
    skipped_iter = 0
    batch_size = mini_batch_size
    exceptions = set()
    itn = 1
    while itn <= max_epochs:
        # get names of other pipes to disable them during training
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in ['parser']]
        with nlp.disable_pipes(*other_pipes):  # only train dependency parser
            optimizer = nlp.begin_training()
            start = datetime.datetime.now()
            print('training parser epoch #{}, mini batch size: {}, start: {}'.format(
                itn, batch_size, start
            ), flush=True)
            random.shuffle(entire_set)
            losses = {}
            batch_sents = []
            batch_golds = []
            for i, sentence in enumerate(entire_set):
                if i % 100 == 0:
                    print('.', end='', file=sys.stderr, flush=True)
                sents = [sentence]
                golds = [{
                    'heads': [m.dep_morph.id for m in sentence.morphs],
                    'deps': [m.dep_label for m in sentence.morphs],
                }]
                # for m, dep in zip(sents[0].morphs, golds[0]['deps']):
                #     print(m.id, m.surface, m.pos, m.dep_label, dep, m.dep_morph.id, m.dep_morph.surface)
                turned = turn_full_half(str(sentence))
                if sentence != turned:  # add variation of surface and lemma zenkaku-hankaku turning
                    turn_surface = random.random() < 2 / 3
                    if turn_surface:
                        turn_lemma = random.random() < 0.5
                    else:
                        turn_lemma = True
                    if turn_surface:
                        sent = sentence.clone(turned)
                    else:
                        sent = sentence.clone()
                    for m in sent.morphs:
                        if turn_surface:
                            m.surface = turn_full_half(m.surface)
                        if turn_lemma:
                            m.lemma = turn_full_half(m.lemma)
                    sents.append(sent)
                    golds *= 2
                batch_sents += sents
                batch_golds += golds
                if len(batch_sents) < batch_size and i + 1 < len(entire_set):
                    continue
                try:
                    nlp.update(
                        batch_sents,
                        batch_golds,
                        sgd=optimizer,
                        losses=losses)
                except ValueError as e:
                    s = str(e)
                    if s not in exceptions:
                        exceptions.add(s)
                        print(file=sys.stderr)
                        print('Exception ignored: {}'.format(s), file=sys.stderr, flush=True)
                batch_sents = []
                batch_golds = []
            print(file=sys.stderr)

        stats = evaluate(
            evaluation_gold,
            evaluation_rewritten,
            keep_gold_tokens=keep_gold_tokens,
            evaluate_all_combinations=evaluate_all_combinations,
            nlp=nlp,
            print_file=sys.stdout
        )

        end = datetime.datetime.now()
        print('training parser epoch #%d end in %s: %s' % (itn, end - start, end))
        print(losses, flush=True)

        if best is None or best.score() < stats.score():
            print('score: {} > best: {}'.format(stats.score(), best.score() if best else 'None'))
            best = stats
            best_model = nlp
            skipped_iter = 0
            save_model(output_path, nlp)
            if batch_size > 1 and itn == max_epochs:
                batch_size = 1
                max_epochs = itn + online_sgd_max_epochs
                print('proceed to online sgd mode')
        else:
            print('score: {} <= best: {}'.format(stats.score(), best.score()))
            skipped_iter += 1
            if skipped_iter >= give_up_iter:
                if batch_size > 1 and online_sgd_max_epochs > 0:
                    nlp = best_model
                    batch_size = 1
                    skipped_iter = 0
                    max_epochs = itn + online_sgd_max_epochs
                    print('proceed to online sgd mode')
                else:
                    print('give up')
                    print('best score model')
                    best.print()
                    break
        sys.stderr.flush()
        itn += 1

    return best


if __name__ == '__main__':
    plac.call(train_from_file)
