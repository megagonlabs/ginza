from .dictionarybuilder import DictionaryBuilder


class UserDictionaryBuilder(DictionaryBuilder):

    def __init__(self, grammar, system_lexicon):
        super().__init__()
        self.is_user_dictionary = True
        self.grammar = grammar
        self.system_lexicon = system_lexicon

    def build(self, lexicon_paths, matrix_input_stream, out_stream):
        """
        Violated LSP
        :param lexicon_paths:
        :param out_stream:
        :return:
        """
        self.logger.info('reading the source file...')
        for path in lexicon_paths:
            with open(path) as rf:
                self.build_lexicon(rf)
        self.logger.info('{} words\n'.format(len(self.entries)))

        self.write_grammar(None, out_stream)
        self.write_lexicon(out_stream)

    def get_posid(self, strs):
        pos_id = self.grammar.get_part_of_speech_id(strs)
        if pos_id < 0:
            pos_id = super().get_posid(strs) + self.grammar.get_part_of_speech_size()
        return pos_id

    def get_wordid(self, headword, pos_id, reading_form):
        wid = super().get_wordid(headword, pos_id, reading_form)
        if wid >= 0:
            return wid | (1 << 28)
        return self.system_lexicon.get_word_id1(headword, pos_id, reading_form)

    def check_wordid(self, wid):
        if wid >= (1 << 28):
            super().check_wordid(wid & ((1 << 28) - 1))
        elif wid < 0 or wid >= self.system_lexicon.size():
            raise ValueError('invalid word id')
