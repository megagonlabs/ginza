from .path_rewrite_plugin import PathRewritePlugin
from sudachipy.dictionarylib.categorytype import CategoryType


class JoinNumericPlugin(PathRewritePlugin):
    def __init__(self):
        self.join_kanji_numeric = None
        self.join_all_numeric = None

    def set_up(self, grammar):
        self.join_kanji_numeric = True
        self.join_all_numeric = False

    def rewrite(self, text, path, lattice):
        begin_index = -1
        type_ = None

        i = -1
        while True:
            i += 1
            if i >= len(path):
                break
            node = path[i]
            types = self.get_char_category_types(text, node)
            if CategoryType.NUMERIC in types:
                if type_ == CategoryType.NUMERIC:
                    continue
                if type_ == CategoryType.KANJINUMERIC:
                    if self.join_all_numeric:
                        continue
                    elif self.join_kanji_numeric:
                        if (i - begin_index) > 1:
                            self.concatenate(path, begin_index, i, lattice)
                            i = begin_index + 1
                type_ = CategoryType.NUMERIC
                begin_index = i
            elif CategoryType.KANJINUMERIC in types:
                if type_ == CategoryType.KANJINUMERIC:
                    continue
                if type_ == CategoryType.NUMERIC:
                    if self.join_all_numeric:
                        continue
                    if (i - begin_index) > 1:
                        self.concatenate(path, begin_index, i, lattice)
                    i = begin_index + 1
                if self.join_kanji_numeric:
                    type_ = CategoryType.KANJINUMERIC
                    begin_index = i
                else:
                    type_ = None
                    begin_index = -1
            else:
                if begin_index >= 0:
                    if (i - begin_index) > 1:
                        self.concatenate(path, begin_index, i, lattice)
                    i = begin_index + 1
                type_ = None
                begin_index = -1
        if begin_index >= 0 and (len(path) - begin_index) > 1:
            self.concatenate(path, begin_index, len(path), lattice)
