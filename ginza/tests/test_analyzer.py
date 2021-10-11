from pathlib import Path

import pytest

from ginza.analyzer import Analyzer


@pytest.fixture(scope='module')
def input_line() -> str:
    yield "今日はかつ丼を食べた。明日は蕎麦を食べたい。"


@pytest.fixture
def analyzer() -> Analyzer:
    default_params = dict(
        model_path=None,
        ensure_model=None,
        split_mode='A',
        hash_comment='print',
        output_format='conllu',
        require_gpu=False,
        disable_sentencizer=False
    )
    yield Analyzer(**default_params)


class TestAnalyzer:

    def test_model_path(self, mocker, analyzer):
        spacy_load_mock = mocker.patch('spacy.load')
        analyzer.model_path = 'ja_ginza'
        analyzer.set_nlp()
        spacy_load_mock.assert_called_once_with('ja_ginza')

    def test_ensure_model(self, mocker, analyzer):
        spacy_load_mock = mocker.patch('spacy.load')
        analyzer.ensure_model = 'ja_ginza_electra'
        analyzer.set_nlp()
        spacy_load_mock.assert_called_once_with('ja_ginza_electra')

    def test_mecab_format(self, mocker, analyzer):
        spacy_load_mock = mocker.patch('spacy.load')
        analyzer.output_format = 'mecab'
        analyzer.set_nlp()
        # specified model not loaded if output_fomart is mecab
        spacy_load_mock.assert_not_called()

    def test_require_gpu(self, mocker, analyzer):
        require_gpu_mock = mocker.patch('spacy.require_gpu')
        analyzer.require_gpu = 1
        analyzer.set_nlp()
        require_gpu_mock.assert_called_once()

    @pytest.mark.parametrize(
        "output_format, n_sentence, raises_analysis_before_set",
        [
            ('conllu', 2, TypeError),
            ('cabocha', 2, TypeError),
            ('mecab', 1, AttributeError),
            ('json', 2, TypeError),
        ],
    )
    def test_analyze_line(
        self, output_format, n_sentence, raises_analysis_before_set,
        input_line, analyzer
    ):
        analyzer.output_format = output_format
        with pytest.raises(raises_analysis_before_set):
            analyzer.analyze_line(input_line)
        try:
            analyzer.set_nlp()
            ret = analyzer.analyze_line(input_line)
        except:
            pytest.fail('failed to analyze_line')

        print(ret)
        assert len(ret) == n_sentence
