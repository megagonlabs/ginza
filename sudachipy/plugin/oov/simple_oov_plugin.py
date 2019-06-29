from sudachipy import latticenode
from sudachipy.dictionarylib import wordinfo


class SimpleOovPlugin:
    def set_up(self, grammar):
        oov_pos_strings = ["補助記号", "一般", "*", "*", "*", "*"]
        self.left_id = 5968
        self.right_id = 5968
        self.cost = 3857
        self.oov_pos_id = grammar.get_part_of_speech_id(oov_pos_strings)
        self.oov_pos_id

    def get_oov(self, input_text, offset, has_other_words):
        nodes = self.provide_oov(input_text, offset, has_other_words)
        for n in nodes:
            n.begin = offset
            n.end = offset + n.get_word_info().head_word_length
        return nodes

    def provide_oov(self, input_text, offset, has_other_words):
        if not has_other_words:
            node = self.create_node()
            node.set_parameter(self.left_id, self.right_id, self.cost)
            length = input_text.get_code_points_offset_length(offset, 1)
            s = input_text.get_substring(offset, offset + length)
            info = wordinfo.WordInfo(surface=s, head_word_length=length, pos_id=self.oov_pos_id, normalized_form=s,
                                     dictionary_form_word_id=-1, dictionary_form=s, reading_form="",
                                     a_unit_split=[], b_unit_split=[], word_structure=[])
            node.set_word_info(info)
            return [node]
        else:
            return []

    def create_node(self):
        node = latticenode.LatticeNode()
        node.set_oov()
        return node
