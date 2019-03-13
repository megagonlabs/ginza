from . import latticenode
from . import morpheme
from . import tokenizer


class MorphemeList:
    def __init__(self, input_, grammar, lexicon, path):
        self.input_text = input_
        self.grammar = grammar
        self.lexicon = lexicon
        self.path = path

    def __getitem__(self, index):
        return morpheme.Morpheme(self, index)

    def __len__(self):
        return len(self.path)

    def __iter__(self):
        for index in range(len(self.path)):
            yield morpheme.Morpheme(self, index)
        return

    def get_begin(self, index):
        return self.input_text.get_original_index(self.path[index].get_begin())

    def get_end(self, index):
        return self.input_text.get_original_index(self.path[index].get_end())

    def get_surface(self, index):
        begin = self.get_begin(index)
        end = self.get_end(index)
        return self.input_text.get_original_text()[begin:end]

    def get_word_info(self, index):
        return self.path[index].get_word_info()

    def split(self, mode, index, wi):
        if mode is tokenizer.Tokenizer.SplitMode.A:
            word_ids = wi.a_unit_split
        elif mode is tokenizer.Tokenizer.SplitMode.B:
            word_ids = wi.b_unit_split
        else:
            return [self.__getitem__(index)]

        if len(word_ids) is 0 or len(word_ids) is 1:
            return [self.__getitem__(index)]

        offset = self.path[index].get_begin()
        nodes = []
        for wid in word_ids:
            n = latticenode.LatticeNode(self.lexicon, 0, 0, 0, wid)
            n.begin = offset
            offset += n.get_word_info().head_word_length
            n.end = offset
            nodes.append(n)

        return MorphemeList(self.input_text, self.grammar, self.lexicon, nodes)

    def is_oov(self, index):
        return self.path[index].is_oov

    def get_internal_cost(self):
        return self.path[-1].get_path_cost() - self.path[0].get_path_cost()
