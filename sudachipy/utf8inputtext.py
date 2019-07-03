import copy


class UTF8InputText:
    def __init__(self, grammar, original_text, modified_text, bytes_, offsets, byte_indexes, char_categories, char_category_continuities):
        self.original_text = original_text
        self.modified_text = modified_text
        self.bytes = bytes_
        self.offsets = offsets
        self.byte_indexes = byte_indexes
        self.char_categories = char_categories
        self.char_category_continuities = char_category_continuities

    def get_original_text(self):
        return self.original_text

    def get_text(self):
        return self.modified_text

    def get_byte_text(self):
        return self.bytes

    def get_substring(self, begin, end):
        if begin < 0:
            raise IndexError(begin)
        if end > len(self.bytes):
            raise IndexError(end)
        if (begin > end):
            raise IndexError(end - begin)

        return self.modified_text[self.byte_indexes[begin]:self.byte_indexes[end]]

    def get_offset_text_length(self, index):
        return self.byte_indexes[index]

    def is_char_alignment(self, index):
        return (self.bytes[index] & 0xC0) is not 0x80

    def get_original_index(self, index):
        return self.offsets[index]

    def get_char_category_types(self, begin, end=None):
        if end is None:
            return self.char_categories[self.byte_indexes[begin]]
        if begin + self.get_char_category_continuous_length(begin) < end:
            return []
        b = self.byte_indexes[begin]
        e = self.byte_indexes[end]
        continuous_category = copy.deepcopy(self.char_categories[b])
        for i in range(b + 1, e):
            continuous_category = continuous_category & self.char_categories[i]
        return continuous_category

    def get_char_category_continuous_length(self, index):
        return self.char_category_continuities[index]

    def get_code_points_offset_length(self, index, code_point_offset):
        length = 0
        target = self.byte_indexes[index] + code_point_offset
        for i in range(index, len(self.bytes)):
            if self.byte_indexes[i] >= target:
                return length
            length += 1
        return length
