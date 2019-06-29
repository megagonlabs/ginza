from . import lexicon

class LexiconSet(lexicon.Lexicon):
    def __init__(self, system_lexicon):

        self.lexicons = []
        self.lexicons.append(system_lexicon)

    def add(self, lexicon):
        if not self.lexicons.contains(lexicon):
            self.lexicons.append(lexicon)

    def lookup(self, text, offset):
        if len(self.lexicons) is 1:
            return self.lexicons[0].lookup(text, offset)
        return self.Itr(text, offset)

    class Itr(object):
        def __iter__(self, text, offset):
            self.text = text
            self.offset = offset
            self.dict_id = 1
            self.iterator = LexiconSet.lexicons[self.dict_id].lookup(text, offset)
            return self

        def __next__(self):
            r = self.iterator.next()
            r[0] = LexiconSet.build_word_id(self.dict_id, r[0])
            return r

    def get_left_id(self, word_id):
        return self.lexicons[self.get_dictionary_id(word_id)].get_left_id(self.get_word_id(word_id))

    def get_right_id(self, word_id):
        return self.lexicons[self.get_dictionary_id(word_id)].get_right_id(self.get_word_id(word_id))

    def get_cost(self, word_id):
        return self.lexicons[self.get_dictionary_id(word_id)].get_cost(self.get_word_id(word_id))

    def get_word_info(self, word_id):
        return self.lexicons[self.get_dictionary_id(word_id)].get_word_info(self.get_word_id(word_id))

    def get_dictionary_id(self, word_id):
        return word_id >> 28

    def get_word_id(self, word_id):
        return 0x0FFFFFFF & word_id

    def build_word_id(self, dict_id, word_id):
        if word_id > 0x0FFFFFFF:
            raise AttributeError("word ID is too large: ", word_id)
        if dict_id > 0xF:
            raise AttributeError("dictionary ID is too large: ", dict_id)
        return dict_id << 28 | word_id
