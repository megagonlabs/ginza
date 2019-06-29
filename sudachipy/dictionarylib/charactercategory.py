import re

from . import categorytype


class CharacterCategory(object):
    class Range(object):
        def __init__(self):
            self.low = 0
            self.high = 0
            self.categories = set()

        def contains(self, cp):
            if cp >= self.low and cp <= self.high:
                return True
            return False

        def containing_length(self, text):
            for i in range(len(text)):
                c = ord(text[i])
                if c < self.low or c > self.high:
                    return i
            return len(text)

    def __init__(self):
        self.range_list = []

    def get_category_types(self, code_point):
        for range_ in self.range_list:
            if range_.contains(code_point):
                return range_.categories
        return set(categorytype.CategoryType.DEFAULT)

    def read_character_definition(self, char_def=None):
        """
        :param char_def: path
        """

        if char_def is not None:
            f = open(char_def, 'r', encoding="utf-8")
        else:
            f = open("char.def", 'r', encoding="utf-8")

        for i, line in enumerate(f.readlines()):
            line = line.rstrip()
            if re.fullmatch(r"\s*", line) or re.match("#", line):
                continue
            cols = re.split(r"\s+", line)
            if len(cols) < 2:
                f.close()
                raise AttributeError("invalid format at line {}".format(i))
            if not re.match("0x", cols[0]):
                continue
            range_ = self.Range()
            r = re.split("\\.\\.", cols[0])
            range_.low = range_.high = int(r[0], 16)
            if len(r) > 1:
                range_.high = int(r[1], 16)
            if range_.low > range_.high:
                f.close()
                raise AttributeError("invalid range at line {}".format(i))
            for j in range(1, len(cols)):
                if re.match("#", cols[j]) or cols[j] is '':
                    break
                type_ = categorytype.CategoryType.get(cols[j])
                if type_ is None:
                    f.close()
                    raise AttributeError("{} is invalid type at line {}".format(cols[j], i))
                range_.categories.add(type_)
            self.range_list.append(range_)
        default_range = self.Range()
        default_range.low = 0
        default_range.high = float('inf')
        default_range.categories.add(categorytype.CategoryType.DEFAULT)
        self.range_list.reverse()
        self.range_list.append(default_range)

        f.close()
