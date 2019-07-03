from . import wordinfo


class WordInfoList(object):
    def __init__(self, bytes_, offset, word_size):
        self.bytes = bytes_
        self.offset = offset
        self._word_size = word_size

    def get_word_info(self, word_id):
        orig_pos = self.bytes.tell()
        index = self.word_id_to_offset(word_id)
        self.bytes.seek(index)
        surface = self.buffer_to_string()
        head_word_length = self.buffer_to_string_length()
        pos_id = int.from_bytes(self.bytes.read(2), 'little')
        normalized_form = self.buffer_to_string()
        if not normalized_form:
            normalized_form = surface
        dictionary_form_word_id = int.from_bytes(self.bytes.read(4), 'little', signed=True)
        reading_form = self.buffer_to_string()
        a_unit_split = self.buffer_to_int_array()
        b_unit_split = self.buffer_to_int_array()
        word_structure = self.buffer_to_int_array()

        dictionary_form = surface
        if dictionary_form_word_id >= 0 and dictionary_form_word_id != word_id:
            wi = self.get_word_info(dictionary_form_word_id)
            dictionary_form = wi.surface

        self.bytes.seek(orig_pos)

        return wordinfo.WordInfo(surface, head_word_length, pos_id, normalized_form,
                                 dictionary_form_word_id, dictionary_form, reading_form,
                                 a_unit_split, b_unit_split, word_structure)

    def word_id_to_offset(self, word_id):
        i = self.offset + 4 * word_id
        return int.from_bytes(self.bytes[i:i + 4], 'little', signed=False)

    def buffer_to_string_length(self):
        length = self.bytes.read_byte()
        if length < 128:
            return length
        low = self.bytes.read_byte()
        return ((length & 0x7F) << 8) | low

    def buffer_to_string(self):
        length = self.buffer_to_string_length()
        return self.bytes.read(2 * length).decode('utf-16-le')

    def buffer_to_int_array(self):
        length = self.bytes.read_byte()
        array = []
        for _ in range(length):
            array.append(int.from_bytes(self.bytes.read(4), 'little', signed=True))
        return array

    def size(self):
        return self._word_size
