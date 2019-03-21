# encoding: utf8
from __future__ import unicode_literals, print_function

import json
from pathlib import Path
import re
import sys

from spacy.morphology import POS_IDS
from spacy.symbols import *
from spacy.tokens import Doc
from .parse_tree import EOS, ParsedSentence

from sudachipy import config
from sudachipy import dictionary
from sudachipy.tokenizer import Tokenizer as OriginalTokenizer

LANG_NAME = 'ja_ginza'

SUDACHI_DEFAULT_MODE = 'C'
SUDACHI_DEFAULT_SPLITMODE = OriginalTokenizer.SplitMode.C


# TODO should be refactored to ensure Japanese UD's tag translation rules
TAG_MAP = {
    # Universal Dependencies Mapping (internal git)
    # https://github.com/mynlp/udjapanese/blob/master/UDJapaneseBCCWJ/unidic_to_udpos_mapping/bccwj_pos_suw_rule.json

    "記号,一般,*,*": {POS: SYM},
    "記号,文字,*,*": {POS: SYM},

    "感動詞,フィラー,*,*": {POS: INTJ},
    "感動詞,一般,*,*": {POS: INTJ},

    # spaces should be treated as token.whitespace_
    "空白,*,*,*": {POS: SPACE},

    "形状詞,一般,*,*": {POS: ADJ},
    "形状詞,タリ,*,*": {POS: ADJ},
    "形状詞,助動詞語幹,*,*": {POS: ADJ},
    "形容詞,一般,*,*": {POS: ADJ},
    "形容詞,非自立可能,*,*": {POS: ADJ},

    "助詞,格助詞,*,*": {POS: ADP},
    "助詞,係助詞,*,*": {POS: ADP},
    "助詞,終助詞,*,*": {POS: PART},
    "助詞,準体助詞,*,*": {POS: SCONJ},
    "助詞,接続助詞,*,*": {POS: CCONJ},
    "助詞,副助詞,*,*": {POS: ADP},
    "助動詞,*,*,*": {POS: AUX},
    "接続詞,*,*,*": {POS: SCONJ},

    "接頭辞,*,*,*": {POS: NOUN},
    "接尾辞,形状詞的,*,*": {POS: NOUN},
    "接尾辞,形容詞的,*,*": {POS: NOUN},
    "接尾辞,動詞的,*,*": {POS: NOUN},
    "接尾辞,名詞的,サ変可能,*": {POS: NOUN},
    "接尾辞,名詞的,一般,*": {POS: NOUN},
    "接尾辞,名詞的,助数詞,*": {POS: NOUN},
    "接尾辞,名詞的,副詞可能,*": {POS: NOUN},

    "代名詞,*,*,*": {POS: PRON},
    "動詞,一般,*,*": {POS: VERB},
    "動詞,非自立可能,*,*": {POS: VERB},
    "副詞,*,*,*": {POS: ADV},

    "補助記号,ＡＡ,一般,*": {POS: SYM},  # text art
    "補助記号,ＡＡ,顔文字,*": {POS: SYM},  # kaomoji
    "補助記号,一般,*,*": {POS: PUNCT},
    "補助記号,括弧開,*,*": {POS: PUNCT},  # open bracket
    "補助記号,括弧閉,*,*": {POS: PUNCT},  # close bracket
    "補助記号,句点,*,*": {POS: PUNCT},  # period or other EOS marker
    "補助記号,読点,*,*": {POS: PUNCT},  # comma

    "名詞,固有名詞,一般,*": {POS: PROPN},  # general proper noun
    "名詞,固有名詞,人名,一般": {POS: PROPN},  # person's name
    "名詞,固有名詞,人名,姓": {POS: PROPN},  # surname
    "名詞,固有名詞,人名,名": {POS: PROPN},  # first name
    "名詞,固有名詞,地名,一般": {POS: PROPN},  # place name
    "名詞,固有名詞,地名,国": {POS: PROPN},  # country name

    "名詞,助動詞語幹,*,*": {POS: AUX},
    "名詞,数詞,*,*": {POS: NUM},  # includes Chinese numerals

    "名詞,普通名詞,サ変可能,*": {POS: VERB},

    "名詞,普通名詞,サ変形状詞可能,*": {POS: VERB},
    "名詞,普通名詞,一般,*": {POS: NOUN},
    "名詞,普通名詞,形状詞可能,*": {POS: ADJ},
    "名詞,普通名詞,助数詞可能,*": {POS: NUM},
    "名詞,普通名詞,副詞可能,*": {POS: ADV},

    "連体詞,*,*,*": {POS: DET},
}
TAG_MAP.update(
    # add pos names as tags too
    {k: {POS: v} for k, v in POS_IDS.items()}
)


# see https://spacy.io/usage/processing-pipelines#component-example1
def separate_sentences(doc):
    for i, token in enumerate(doc[:-2]):
        if token.tag_:
            if token.tag_ == "補助記号,句点,*,*":
                next_token = doc[i+1]
                if next_token.tag_ != token.tag_:
                    next_token.sent_start = True


class SudachiTokenizer(object):
    def __init__(self, nlp, mode=SUDACHI_DEFAULT_SPLITMODE):
        self.nlp = nlp

        resources_path = Path(__file__).parent / "resources"
        config.RESOURCEDIR = str(resources_path)
        setting_path = resources_path / "sudachi.json"
        config.SETTINGFILE = str(setting_path)

        with open(str(setting_path), "r", encoding="utf-8") as f:
            settings = json.load(f)
        settings['systemDict'] = str(resources_path / settings.get('systemDict', 'system_core.dic'))
        settings['characterDefinitionFile'] = str(resources_path / settings.get('characterDefinitionFile', 'char.def'))
        if 'oovProviderPlugin' in settings:
            for plugin in settings['oovProviderPlugin']:
                if plugin['class'] == 'com.worksap.nlp.sudachi.MeCabOovProviderPlugin':
                    plugin['charDef'] = str(resources_path / plugin.get('charDef', 'char.def'))
                    plugin['unkDef'] = str(resources_path / plugin.get('unkDef', 'unk.def'))

        dict_ = dictionary.Dictionary(settings)
        self.tokenizer = dict_.create()
        self.mode = mode
        self.use_sentence_separator = True

    def __call__(self, text):
        if isinstance(text, ParsedSentence):
            return text.to_doc(self.nlp.vocab)
        else:
            result = self.tokenizer.tokenize(self.mode, text)
            morph_spaces = []
            last_morph = None
            for m in result:
                if m.surface():
                    if m.part_of_speech()[0] == '空白':
                        if last_morph:
                            morph_spaces.append((last_morph, True))
                            last_morph = None
                        else:
                            morph_spaces.append((m, True))
                    elif last_morph:
                        morph_spaces.append((last_morph, False))
                        last_morph = m
                    else:
                        last_morph = m
            if last_morph:
                morph_spaces.append((last_morph, False))

            # the last space is removed by JapaneseReviser at the final stage of pipeline
            words = [m.surface() for m, spaces in morph_spaces] + [EOS]
            spaces = [space for m, space in morph_spaces] + [False]
            doc = Doc(self.nlp.vocab, words=words, spaces=spaces)
            for token, (morph, spaces) in zip(doc, morph_spaces):
                token.tag_ = ",".join(morph.part_of_speech()[0:4])
                token._.pos_detail = ",".join(morph.part_of_speech()[0:4])
                token._.inf = ",".join(morph.part_of_speech()[4:])
                token.lemma_ = morph.normalized_form()  # work around: lemma_ must be set after tag_ (spaCy's bug)
            doc[-1].tag = X
            doc[-1].lemma_ = EOS
            if self.use_sentence_separator:
                separate_sentences(doc)
            return doc

    # add dummy methods for to_bytes, from_bytes, to_disk and from_disk to
    # allow serialization (see #1557)
    def to_bytes(self, **exclude):
        return b''

    def from_bytes(self, bytes_data, **exclude):
        return self

    def to_disk(self, path, **exclude):
        return None

    def from_disk(self, path, **exclude):
        return self


SUDACHI_PATTERN = re.compile(
    r"^([^\t]*)\t"
    r"([^\t,]+,[^\t,]+,[^\t,]+,[^\t,]+),"
    r"([^\t,]+,[^\t,]+)\t"
    r"([^\t]*)\t"
    r"([^\t]*)\t"
    r"([^\t]*)\t"
    r"([^\t]+)"
    r"(\t\(OOV\))?$"
)


def read_sudachi_a(path, file, yield_document=False):
    return read_sudachi(path, file, yield_document, 'A')


def read_sudachi_b(path, file, yield_document=False):
    return read_sudachi(path, file, yield_document, 'B')


def read_sudachi_c(path, file, yield_document=False):
    return read_sudachi(path, file, yield_document, 'C')


def read_sudachi(path, file, yield_document=False, mode='B'):
    sentences = []
    sentence = []
    line = None
    state = 'EOS'
    for line_index, line in enumerate(file):
        if line_index == 0 and not line.startswith('#'):
            print('Skip file: %s' % path, file=sys.stderr)
            line = None
            break
        line = line.rstrip()
        if line.startswith('#'):
            continue
        elif line == 'EOS':
            if yield_document:
                sentences.append(sentence)
            else:
                yield sentence
            sentence = []
            state = 'EOS'
            continue
        elif line.startswith('@'):
            assert state != 'EOS', 'Bad state {}: {} #{}: {}'.format(state, path, line_index + 1, line)
            if line[1] != mode:
                continue
            if state == 'MORPH':
                sentence.pop()
                state = 'MODE'
            line = line[3:]
        else:
            state = 'MORPH'

        m = SUDACHI_PATTERN.match(line)
        surface = None
        if m:
            surface = m.group(1)
            if not surface:  # bug of sudachi java version
                surface = m.group(4)
        if surface:
            sentence.append(surface)
        else:
            print('Bad format in %s line #%d' % (path, line_index + 1), file=sys.stderr)
            print(line, file=sys.stderr)

    if line is not None and (line != 'EOS' or line.startswith('#\td')):
        print('File not ends with EOS or #d - %s' % path, file=sys.stderr)

    if yield_document:
        yield sentences
