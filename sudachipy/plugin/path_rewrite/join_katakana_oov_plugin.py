from sudachipy.dictionarylib.categorytype import CategoryType
from sudachipy.plugin.path_rewrite.path_rewrite_plugin import PathRewritePlugin


class JoinKatakanaOovPlugin(PathRewritePlugin):
    def __init__(self):
        self.oov_pos_id = None

    def set_up(self, grammar):
        pos = ["名詞", "普通名詞", "一般", "*", "*", "*"]
        if not pos:
            raise AttributeError("oovPOS is undefined")
        self.oov_pos_id = grammar.get_part_of_speech_id(pos)
        if self.oov_pos_id < 0:
            raise AttributeError("oovPOS is invalid")

    def rewrite(self, text, path, lattice):
        i = 0
        while True:
            if i >= len(path):
                break
            node = path[i]
            if (node.is_oov or (self.is_one_char(text, node) and self.can_oov_bow_node(text, node))) and \
                    self.is_katakana_node(text, node):
                begin = i - 1
                while True:
                    if begin < 0:
                        break
                    if not self.is_katakana_node(text, path[begin]):
                        begin += 1
                        break
                    begin -= 1
                if begin < 0:
                    begin = 0
                while begin != i and not self.can_oov_bow_node(text, path[begin]):
                    begin += 1
                end = i + 1
                while True:
                    if end >= len(path):
                        break
                    if not self.is_katakana_node(text, path[end]):
                        break
                    end += 1
                if (end - begin) > 1:
                    self.concatenate_oov(path, begin, end, self.oov_pos_id, lattice)
                    i = begin + 1 # skip next node, as we already know it is not a joinable katakana
            i += 1


    def is_katakana_node(self, text, node):
        return CategoryType.KATAKANA in self.get_char_category_types(text, node)

    def is_one_char(self, text, node):
        b = node.get_begin()
        return b + text.get_code_points_offset_length(b, 1) == node.get_end()

    def can_oov_bow_node(self, text, node):
        return CategoryType.NOOOVBOW not in text.get_char_category_types(node.get_begin())
