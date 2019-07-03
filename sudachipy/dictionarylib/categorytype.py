from enum import Enum


class CategoryType(Enum):
    DEFAULT = 1
    SPACE = 1 << 1
    KANJI = 1 << 2
    SYMBOL = 1 << 3
    NUMERIC = 1 << 4
    ALPHA = 1 << 5
    HIRAGANA = 1 << 6
    KATAKANA = 1 << 7
    KANJINUMERIC = 1 << 8
    GREEK = 1 << 9
    CYRILLIC = 1 << 10
    USER1 = 1 << 11
    USER2 = 1 << 12
    USER3 = 1 << 13
    USER4 = 1 << 14
    NOOOVBOW = 1 << 15

    def get_id(self):
        return self.id

    def get_type(self, id_):
        for type_ in CategoryType.values():
            if type_.get_id() is id_:
                return type_
        return None

    @staticmethod
    def get(str_):
        try:
            return CategoryType[str_]
        except KeyError:
            return None
