# coding: utf8
from __future__ import unicode_literals, print_function

import datetime
import plac
import random
import spacy
from . import *
from .corpus import *
from .evaluate_ner import convert_files, evaluate


@plac.annotations(
    model_path=("Path to model directory", "option", "b", Path),
    clear_model=("Clear ner model", "flag", "c"),
    excluding_labels=("Optional excluding labels, csv", "option", "l", str),
    mini_batch_size=("Number of mini batch size", "option", "m", int),
    max_epochs=("Number of max epochs (default=32)", "option", "p", int),
    online_sgd_max_epochs=("Number of online SGD max epochs (default=0)", "option", "s", int),
    give_up_iter=("Number of training give-up iterations", "option", "u", int),
    evaluation_corpus_path=("Evaluation corpus path", "option", "e", Path),
    output_base_path=("Output base path (default=model_path)", "option", "o", Path),
    require_gpu=("enable require_gpu", "flag", "g"),
)
def train_parser_from_file(
        input_json_path,
        model_path=None,
        clear_model=False,
        excluding_labels='',
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
    corpus = convert_files(input_json_path)
    if evaluation_corpus_path:
        evaluation_gold = convert_files(evaluation_corpus_path)
    else:
        evaluation_gold = corpus[0:1000]
    train(
        corpus,
        model_path,
        clear_model,
        excluding_labels,
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
        excluding_labels='',
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

    if excluding_labels:
        excluding_labels = excluding_labels.split(',')
        print('excluding {}'.format(excluding_labels), file=sys.stderr)

    if output_base_path:
        output_path = output_base_path / model_path.name
    else:
        output_path = model_path

    if 'JapaneseCorrector' not in nlp.pipe_names:
        corrector = nlp.create_pipe('JapaneseCorrector')
        nlp.add_pipe(corrector, last=True)

    # add the parser to the pipeline if it doesn't exist
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner, after='parser')
        clear_model = True
    elif clear_model:
        nlp.remove_pipe('ner')
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner, after='parser')
        print("ner cleared", file=sys.stderr)
    # otherwise, get it, so we can add labels to it
    else:
        ner = nlp.get_pipe('ner')

    print('Rewriting gold corpus with tokenizer', file=sys.stderr, flush=True)
    disabled = nlp.disable_pipes(*nlp.pipe_names)
    checked = []
    checked_nes = 0
    rejected = []
    rejected_nes = 0
    for i, (sentence, nes) in enumerate(gold):
        if i % 100 == 0:
            print('.', end='', file=sys.stderr, flush=True)
        doc = nlp(sentence)
        borders = set()
        for t in doc:
            borders.add(t.idx)
            borders.add(t.idx + len(t.orth_))
        for begin, end, _ in nes:
            if begin not in borders or end not in borders:
                rejected.append((sentence, nes))
                rejected_nes += len(nes)
                break
        else:
            checked.append((sentence, nes))
            checked_nes += len(nes)
    print(file=sys.stderr)
    disabled.restore()

    print('{} sentences ({} nes) rejected due to token boundary disagreements, {} sentences ({} nes) used'.format(
        len(rejected),
        rejected_nes,
        len(checked),
        checked_nes,
    ), file=sys.stderr)

    entire_set = checked

    # add labels
    for sentence, nes in entire_set:
        for _, _, label in nes:
            ner.add_label(label)

    if clear_model:
        best = None
        best_model = None
    else:
        best = evaluate(evaluation_gold, nlp=nlp)
        best_model = nlp
    skipped_iter = 0
    batch_size = mini_batch_size
    itn = 1
    while itn <= max_epochs:
        # get names of other pipes to disable them during training
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in ['ner']]
        with nlp.disable_pipes(*other_pipes):  # only train NER
            optimizer = nlp.begin_training()
            sentences = entire_set
            start = datetime.datetime.now()
            print('training ner epoch #{}, mini batch size: {}, start: {}'.format(itn, batch_size, start), flush=True)
            random.shuffle(sentences)
            losses = {}
            batch_sents = []
            batch_golds = []
            for i, (sentence, nes) in enumerate(sentences):
                if i % 100 == 0:
                    print('.', end='', file=sys.stderr, flush=True)
                sents = [sentence]
                golds = [{'entities': [ne for ne in nes if ne[2] not in excluding_labels]}]
                turned = turn_full_half(sentence)
                if sentence != turned:
                    sents.append(turned)
                    golds *= 2
                batch_sents += sents
                batch_golds += golds
                if len(batch_sents) < batch_size and i + 1 < len(entire_set):
                    continue
                nlp.update(
                    batch_sents,
                    batch_golds,
                    drop=0.5,  # dropout - make it harder to memorise data
                    sgd=optimizer,  # callable to update weights
                    losses=losses)
                batch_sents = []
                batch_golds = []
            print(file=sys.stderr, flush=True)

        stats = evaluate(evaluation_gold, nlp=nlp)

        end = datetime.datetime.now()
        print('training ner epoch #%d end in %s: %s' % (itn, end - start, end))
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
    plac.call(train_parser_from_file)
