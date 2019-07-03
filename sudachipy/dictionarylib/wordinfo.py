class WordInfo:
    def __init__(self,
                 surface,
                 head_word_length,
                 pos_id,
                 normalized_form,
                 dictionary_form_word_id,
                 dictionary_form,
                 reading_form,
                 a_unit_split,
                 b_unit_split,
                 word_structure):
        self.surface = surface
        self.head_word_length = head_word_length
        self.pos_id = pos_id
        self.normalized_form = normalized_form
        self.dictionary_form_word_id = dictionary_form_word_id
        self.dictionary_form = dictionary_form
        self.reading_form = reading_form
        self.a_unit_split = a_unit_split
        self.b_unit_split = b_unit_split
        self.word_structure = word_structure

    def length(self):
        return self.head_word_length
