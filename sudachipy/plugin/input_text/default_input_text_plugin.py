import os
from unicodedata import normalize


from sudachipy import config


class DefaultInputTextPlugin:
    def __init__(self):
        self.ignore_normalize_set = set()
        self.key_lengths = {}
        self.replace_char_map = {}

    def set_up(self):
        rewrite_def = os.path.join(config.RESOURCEDIR, "rewrite.def")
        if not rewrite_def:
            raise AttributeError("rewriteDef is not defined")
        self.read_rewrite_lists(rewrite_def)

    def rewrite(self, builder):
        offset = 0
        next_offset = 0
        text = builder.get_text()

        i = -1
        while True:
            i += 1
            if i >= len(text):
                break
            textloop = False
            offset += next_offset
            next_offset = 0
            original = text[i]

            # 1. replace char without normalize
            max_length = min(self.key_lengths.get(original, 0), len(text) - i)
            for l in range(max_length, 0, -1):
                replace = self.replace_char_map.get(text[i:i + l])
                if replace:
                    builder.replace(i + offset, i + l + offset, replace)
                    next_offset += len(replace) - l
                    i += l - 1
                    textloop = True
                    break
            if textloop:
                continue

            # 2. normalize
            # 2-1. capital alphabet (not only Latin but Greek, Cyrillic, etc.) -> small
            lower = original.lower()
            if lower in self.ignore_normalize_set:
                if original == lower:
                    continue
                replace = lower
            else:
                # 2-2. normalize (except in ignoreNormalize)
                #   e.g. full-width alphabet -> half-width / ligature / etc.
                replace = normalize("NFKC", lower)
            next_offset = len(replace) - 1
            if original != replace:
                builder.replace(i + offset, i + 1 + offset, replace)

    def read_rewrite_lists(self, rewrite_def):
        with open(rewrite_def, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if (not line) or line.startswith("#"):
                    continue
                cols = line.split()

                # ignored normalize list
                if len(cols) == 1:
                    key = cols[0]
                    if len(key) != 1:
                        raise RuntimeError("{} is not character at line {}".format(key, i))
                    self.ignore_normalize_set.add(key)
                # replace char list
                elif len(cols) == 2:
                    if cols[0] in self.replace_char_map:
                        raise RuntimeError("{} is already defined at line {}".format(cols[0], i))
                    if self.key_lengths.get(cols[0][0], 0) < len(cols[0]):
                        self.key_lengths[cols[0][0]] = len(cols[0])
                    self.replace_char_map[cols[0]] = cols[1]
                else:
                    raise RuntimeError("invalid format at line {}".format(i))
