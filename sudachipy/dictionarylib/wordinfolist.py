import struct

from . import wordinfo

class WordInfoList(object):
    def __init__(self, bytes_, offset, word_size):
        self.bytes = bytes_
        self.offset = offset

    def get_word_info(self, word_id):
        index = self.word_id_to_offset(word_id)

        surface = self.buffer_to_string(index)
        index += 1 + 2 * len(surface)
        head_word_length = self.bytes[index]
        index += 1
        pos_id = int.from_bytes(self.bytes[index:index+2], 'little')
        index += 2
        normalized_form = self.buffer_to_string(index)
        index += 1 + 2 * len(normalized_form)
        if not normalized_form:
            normalized_form = surface
        dictionary_form_word_id = int.from_bytes(self.bytes[index:index+4], "little", signed=True)
        index += 4
        reading_form = self.buffer_to_string(index)
        index += 1 + 2 * len(reading_form)
        a_unit_split = self.buffer_to_int_array(index)
        index += 1 + 4 * len(a_unit_split)
        b_unit_split = self.buffer_to_int_array(index)
        index += 1 + 4 * len(b_unit_split)
        word_structure = self.buffer_to_int_array(index)

        dictionary_form = surface
        if dictionary_form_word_id >= 0 and dictionary_form_word_id != word_id:
            wi = self.get_word_info(dictionary_form_word_id)
            dictionary_form = wi.surface

        return wordinfo.WordInfo(surface, head_word_length, pos_id, normalized_form,
                                 dictionary_form_word_id, dictionary_form, reading_form,
                                 a_unit_split, b_unit_split, word_structure)

    def word_id_to_offset(self, word_id):
        i = self.offset + 4 * word_id
        return int.from_bytes(self.bytes[i:i+4], "little", signed=False)

    def buffer_to_string(self, offset):
        length = self.bytes[offset]
        offset += 1
        end = offset + 2 * length
        return self.bytes[offset:end].decode("utf-16-le")

    def buffer_to_int_array(self, offset):
        length = self.bytes[offset]
        offset += 1
        array = struct.unpack_from("<{}I".format(length), self.bytes, offset)
        return array
