
import json
import pytest

from ginza.analyzer import Analyzer


TOKEN_TESTS = [
    ["今日はかつ丼を食べた。明日は蕎麦を食べたい。", ["今日","は","かつ丼","を","食べ","た","。","明日","は","蕎麦","を","食べ","たい","。"]]
]

MECAB_TESTS = [
    ["今日はかつ丼を食べた。明日は蕎麦を食べたい。", ["今日","は","かつ","丼","を","食べ","た","。","明日","は","蕎麦","を","食べ","たい","。"]]
]

BATCH_TESTS = [
    [
        [
            "銀座でランチをご一緒しましょう。",
            "東京タワーの近くに住んでいます。",
            "東京都選挙管理委員会の担当者は、次のように説明した。",
        ], [
            ["銀座","で","ランチ","を","ご","一緒","し","ましょう","。"],
            ["東京","タワー","の","近く","に","住ん","で","い","ます","。"],
            ["東京都","選挙管理委員会","の","担当者","は","、","次","の","よう","に","説明","し","た","。"],
        ]
    ]
]

@pytest.fixture
def analyzer() -> Analyzer:
    default_params = dict(
        model_name_or_path=None,
        split_mode=None,
        hash_comment="print",
        output_format="conllu",
        require_gpu=False,
        disable_sentencizer=False,
        use_normalized_form=False,
    )
    yield Analyzer(**default_params)


def _tokens_conllu(result: str):
    ret = []
    for line in result.split("\n"):
        if line.startswith("#") or line.strip() == "":
            continue
        ret.append(line.split("\t")[1])
    return ret


def _tokens_cabocha(result: str):
    ret = []
    for line in result.split("\n"):
        if line.startswith("*") or line.strip() in ("","EOS"):
            continue
        ret.append(line.split("\t")[0])
    return ret


def _tokens_mecab(result: str):
    ret = []
    for line in result.split("\n"):
        if line.startswith("#") or line.strip() in ("","EOS"):
            continue
        ret.append(line.split("\t")[0])
    return ret


def _tokens_json(result: str):
    data = json.loads(f"[{result}]")
    ret = []
    for d in data:
        for p in d["paragraphs"]:
            for s in p["sentences"]:
                for t in s["tokens"]:
                    ret.append(t["orth"])
    return ret

class TestAnalyzer:
    def test_model_path(self, mocker, analyzer):
        spacy_load_mock = mocker.patch("spacy.load")
        analyzer.model_path = "ja_ginza"
        analyzer.set_nlp()
        spacy_load_mock.assert_called_once_with("ja_ginza")

    def test_ensure_model(self, mocker, analyzer):
        spacy_load_mock = mocker.patch("spacy.load")
        analyzer.ensure_model = "ja_ginza_electra"
        analyzer.set_nlp()
        spacy_load_mock.assert_called_once_with("ja_ginza_electra")

    def test_require_gpu(self, mocker, analyzer):
        require_gpu_mock = mocker.patch("spacy.require_gpu")
        analyzer.require_gpu = 1
        analyzer.set_nlp()
        require_gpu_mock.assert_called_once()

    @pytest.mark.parametrize("input_text, tokens", TOKEN_TESTS)
    @pytest.mark.parametrize(
        "output_format, raises_analysis_before_set, tokens_func",
        [
            ("conllu", TypeError, _tokens_conllu),
            ("cabocha", TypeError, _tokens_cabocha),
            ("json", TypeError, _tokens_json),
        ],
    )
    def test_analyze_line(self, output_format, raises_analysis_before_set, input_text, tokens, tokens_func, analyzer):
        analyzer.output_format = output_format
        with pytest.raises(raises_analysis_before_set):
            analyzer.analyze_line(input_text)

        analyzer.set_nlp()
        ret = analyzer.analyze_line(input_text)
        assert tokens_func(ret) == tokens

    @pytest.mark.parametrize("input_text, tokens", MECAB_TESTS)
    @pytest.mark.parametrize(
        "output_format, raises_analysis_before_set, tokens_func",
        [
            ("mecab", AttributeError, _tokens_mecab),
        ],
    )
    def test_analyze_line_mecab(self, output_format, raises_analysis_before_set, input_text, tokens, tokens_func, analyzer):
        analyzer.output_format = output_format
        with pytest.raises(raises_analysis_before_set):
            analyzer.analyze_line(input_text)

        analyzer.set_nlp()
        ret = analyzer.analyze_line(input_text)
        assert tokens_func(ret) == tokens

    @pytest.mark.parametrize("input_batch, tokens_batch", BATCH_TESTS)
    @pytest.mark.parametrize(
        "output_format, tokens_func",
        [
            ("conllu", _tokens_conllu),
            ("cabocha", _tokens_cabocha),
            ("json", _tokens_json),
        ],
    )
    def test_analyze_batch(self, output_format, input_batch, tokens_batch, tokens_func, analyzer):
        analyzer.output_format = output_format
        ret = analyzer.analyze_batch(input_batch)
        assert tokens_func(ret) == sum(tokens_batch, [])
