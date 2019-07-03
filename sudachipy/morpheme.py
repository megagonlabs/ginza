class Morpheme:
    def __init__(self, list_, index):
        self.word_info = None
        self.list = list_
        self.index = index

    def begin(self):
        return self.list.get_begin(self.index)

    def end(self):
        return self.list.get_end(self.index)

    def surface(self):
        return self.list.get_surface(self.index)

    def part_of_speech(self):
        wi = self.get_word_info()
        return self.list.grammar.get_part_of_speech_string(wi.pos_id)

    def part_of_speech_id(self):
        wi = self.get_word_info()
        return wi.pos_id

    def dictionary_form(self):
        wi = self.get_word_info()
        return wi.dictionary_form

    def normalized_form(self):
        wi = self.get_word_info()
        return wi.normalized_form

    def reading_form(self):
        wi = self.get_word_info()
        return wi.reading_form

    def split(self, mode):
        wi = self.get_word_info()
        return self.list.split(mode, self.index, wi)

    def is_oov(self):
        return self.list.is_oov(self.index)

    def word_id(self):
        return self.list.path[self.index].get_word_id()

    def dictionary_id(self):
        return self.list.path[self.index].get_dictionary_id()

    def get_word_info(self):
        if not self.word_info:
            self.word_info = self.list.get_word_info(self.index)
        return self.word_info
