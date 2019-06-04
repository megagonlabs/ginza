# coding: utf8
from __future__ import unicode_literals, print_function

import plac
from pathlib import Path
import pickle
import sys
import spacy
from gensim.models import Word2Vec
from . import Japanese, create_model_path
from .corpus import sentence_iter
from .sudachi_tokenizer import read_sudachi_a, read_sudachi_b, read_sudachi_c
from .bccwj_ud_corpus import read_bccwj_ud


@plac.annotations(
    corpus_type=("Corpus type (default='sudachi_b')", "option", "t", str),
    base_model_path=("Path to base model directory", "option", "b", Path),
    model_name=("Output model name", "option", "n", str),
    model_version=("Output model version", "option", "v", str),
    dimension=("Dimension of the word vectors (default=100)", "option", "d", int),
    vocab_size=("Vocab size (default=100000)", "option", "s", int),
    min_count=("Min count (default=5)", "option", "c", int),
    window=("Context window size (default=7)", "option", "w", int),
    negative=("Number of negative samples (default=5)", "option", "p", int),
    n_workers=("Number of workers (default=8)", "option", "k", int),
    epochs=("Epochs (default=2)", "option", "e", int),
    output_dir=("Output directory (default='.')", "option", "o", Path),
    require_gpu=("enable require_gpu", "flag", "g"),
)
def train_word2vec_from_file(
        corpus_type='sudachi_b',
        base_model_path=None,
        model_name='bccwj_ud',
        model_version='1.0.0',
        dimension=100,
        vocab_size=100000,
        min_count=5,
        window=7,
        negative=5,
        n_workers=8,
        epochs=2,
        output_dir=Path('.'),
        require_gpu=False,
        input_path=None,
):
    if require_gpu:
        spacy.require_gpu()
        print("GPU enabled", file=sys.stderr)
    if corpus_type == 'sudachi_a':
        corpus_reader = read_sudachi_a
    elif corpus_type == 'sudachi_b':
        corpus_reader = read_sudachi_b
    elif corpus_type == 'sudachi_c':
        corpus_reader = read_sudachi_c
    elif corpus_type == 'bccwj_ud':
        corpus_reader = read_bccwj_ud
    else:
        raise Exception('%s not supported' % corpus_type)

    if base_model_path:
        print('load base model: {}'.format(base_model_path), file=sys.stderr)
        model = Word2Vec.load(str(model_file_path(base_model_path, 'w2v')))
        print('w2v loaded', file=sys.stderr)
        with open(str(model_file_path(base_model_path, 'pickle')), 'rb') as f:
            total_sents, word_store, word_counter = pickle.load(f)
        print('pickle loaded', file=sys.stderr)
    else:
        model = Word2Vec(
            size=dimension,
            window=window,
            min_count=min_count,
            workers=n_workers,
            sample=1e-5,
            negative=negative
        )
        total_sents = 0
        word_store = {}
        word_counter = []
        print('initialized', file=sys.stderr)

    total_sents, words = train_word2vec(
        model, total_sents, word_store, word_counter, corpus_reader, vocab_size, min_count, epochs, input_path
    )

    new_model_path = create_model_path(output_dir, model_name, model_version)

    nlp = Japanese(meta={'name': model_name, 'version': model_version})
    vocab = nlp.vocab
    for word in words:
        vocab.set_vector(word, model.wv[word])

    corrector = nlp.create_pipe('JapaneseCorrector')
    nlp.add_pipe(corrector, last=True)
    nlp.to_disk(new_model_path)
    print('saved: ', new_model_path, file=sys.stderr)

    model.save(str(model_file_path(new_model_path, 'w2v')))
    print('w2v saved', file=sys.stderr)

    with open(str(model_file_path(new_model_path, 'pickle')), 'wb') as f:
        pickle.dump((total_sents, word_store, word_counter), f)
    print('pickle saved', file=sys.stderr)


def train_word2vec(
        model,
        total_sents,
        word_store,
        word_counter,
        corpus_reader=read_sudachi_b,
        vocab_size=100000,
        min_count=5,
        epochs=1,
        input_path=None,
):
    total_words = sum(word_counter)
    next_id = len(word_store.keys())
    print('word count phase start ({}, {})'.format(total_sents, total_words, next_id), flush=True)
    for sentence in sentence_iter(input_path, corpus_reader):
        total_sents += 1
        for word in sentence:
            word_id = word_store.get(word, next_id)
            if word_id == next_id:
                word_store[word] = next_id
                next_id += 1
                word_counter.append(1)
            else:
                word_counter[word_id] += 1
            total_words += 1
    print('word count phase end ({}, {})'.format(total_sents, total_words, next_id), flush=True)

    size = 0
    if len(word_counter) > vocab_size:
        for freq in word_counter:
            if freq >= min_count:
                size += 1
    if size <= vocab_size:
        word_freq_map = {
            word: word_counter[word_id] for word, word_id in word_store.items() if word_counter[word_id] >= min_count
        }
    else:
        word_freqs = sorted(
            [
                (
                    word,
                    word_counter[word_id]
                ) for word, word_id in word_store.items() if word_counter[word_id] >= min_count
            ], key=lambda t: -t[1]
        )[:vocab_size]
        word_freq_map = {
            t[0]: t[1] for t in word_freqs
        }

    print('word2vec training phase start', flush=True)
    try:
        model.build_vocab_from_freq(word_freq_map)
    except RuntimeError:
        print('Vocabulary is fixed', file=sys.stderr)

    model.train(
        sentence_iter(input_path, corpus_reader),
        total_examples=total_sents,
        total_words=total_words,
        epochs=epochs,
    )
    print('word2vec training phase end', flush=True)
    if len(word_store) > 0:
        word = list(word_store.keys())[0]
        word_id = word_store[word]
        print('{},{},{}'.format(word_id, word, word_counter[word_id]))
        print(model[word], flush=True)
    return total_sents, word_freq_map.keys()


def model_file_path(path, file):
    return Path('{}.{}'.format(path, file))


if __name__ == '__main__':
    plac.call(train_word2vec_from_file)
