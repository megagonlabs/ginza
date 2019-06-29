import os
from collections import defaultdict

from sudachipy import config
from sudachipy import latticenode
from sudachipy.dictionarylib import categorytype
from sudachipy.dictionarylib import wordinfo


class MeCabOovPlugin:
    class CategoryInfo:
        def __init__(self):
            self.type_ = None
            self.is_invoke = None
            self.is_group = None
            self.length = None

    class OOV:
        def __init__(self):
            self.left_id = None
            self.right_id = None
            self.cost = None
            self.pos_id = None

    def __init__(self):
        self.categories = {}
        self.oov_list = defaultdict(list)

    def set_up(self, grammar):
        char_def = os.path.join(config.RESOURCEDIR, "char.def")
        if not char_def:
            raise AttributeError("charDef is not defined")
        self.read_character_property(char_def)

        unk_def = os.path.join(config.RESOURCEDIR, "unk.def")
        if not unk_def:
            raise AttributeError("unkDef is not defined")
        self.read_oov(unk_def, grammar)

    def get_oov(self, input_text, offset, has_other_words):
        nodes = self.provide_oov(input_text, offset, has_other_words)
        for n in nodes:
            n.begin = offset
            n.end = offset + n.get_word_info().head_word_length
        return nodes

    def provide_oov(self, input_text, offset, has_other_words):
        nodes = []
        length = input_text.get_char_category_continuous_length(offset)
        if length > 0:
            for type_ in input_text.get_char_category_types(offset):
                if type_ not in self.categories:
                    continue
                cinfo = self.categories[type_]
                llength = length
                if cinfo.type_ not in self.oov_list:
                    continue
                oovs = self.oov_list[cinfo.type_]
                if cinfo.is_group and (cinfo.is_invoke or not has_other_words):
                    s = input_text.get_substring(offset, offset + length)
                    for oov in oovs:
                        nodes.append(self.get_oov_node(s, oov, length))
                        llength = -1
                if cinfo.is_invoke or not has_other_words:
                    for i in range(1, cinfo.length + 1):
                        sublength = input_text.get_code_points_offset_length(offset, i)
                        if sublength > llength:
                            break
                        s = input_text.get_substring(offset, offset + sublength)
                        for oov in oovs:
                            nodes.append(self.get_oov_node(s, oov, sublength))
        return nodes

    def create_node(self):
        node = latticenode.LatticeNode()
        node.set_oov()
        return node

    def get_oov_node(self, text, oov, length):
        node = self.create_node()
        node.set_parameter(oov.left_id, oov.right_id, oov.cost)
        info = wordinfo.WordInfo(surface=text, head_word_length=length, pos_id=oov.pos_id, normalized_form=text,
                                 dictionary_form_word_id=-1, dictionary_form=text, reading_form="",
                                 a_unit_split=[], b_unit_split=[], word_structure=[])
        node.set_word_info(info)
        return node

    def read_character_property(self, char_def):
        with open(char_def, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                cols = line.split()
                if len(cols) < 2:
                    raise RuntimeError("invalid format at line {}".format(i))
                if cols[0].startswith("0x"):
                    continue
                try:
                    type_ = getattr(categorytype.CategoryType, cols[0])
                except AttributeError:
                    raise RuntimeError("`{}` is invalid type at line {}".format(cols[0], i))
                if type_ in self.categories:
                    raise RuntimeError("`{}` is already defined at line {}".format(cols[0], i))

                info = self.CategoryInfo()
                info.type_ = type_
                info.is_invoke = (cols[1] != "0")
                info.is_group = (cols[2] != "0")
                info.length = int(cols[3])
                self.categories[type_] = info

    def read_oov(self, unk_def, grammar):
        with open(unk_def, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                cols = line.split(",")
                if len(cols) < 10:
                    raise RuntimeError("invalid format at line {}".format(i))
                try:
                    type_ = getattr(categorytype.CategoryType, cols[0])
                except AttributeError:
                    raise RuntimeError("`{}` is invalid type at line {}".format(cols[0], i))
                if type_ not in self.categories:
                    raise RuntimeError("`{}` is undefined at line {}".format(cols[0], i))

                oov = self.OOV()
                oov.left_id = int(cols[1])
                oov.right_id = int(cols[2])
                oov.cost = int(cols[3])
                pos = cols[4:10]
                oov.pos_id = grammar.get_part_of_speech_id(pos)
                self.oov_list[type_].append(oov)
