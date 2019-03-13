class LatticeNode:
    def __init__(self, lexicon=None, left_id=None, right_id=None, cost=None, word_id=None):
        self.begin = 0
        self.end = 0

        self.total_cost = 0
        self.best_previous_node = None
        self.is_connected_to_bos = None

        self.is_oov = False
        self.extra_word_info = None

        if lexicon is left_id is right_id is cost is word_id is None:
            self.word_id = -1
            return

        self.lexicon = lexicon
        self.left_id = left_id
        self.right_id = right_id
        self.cost = cost
        self.word_id = word_id

    def set_parameter(self, left_id, right_id, cost):
        self.left_id = left_id
        self.right_id = right_id
        self.cost = cost

    def get_begin(self):
        return self.begin

    def get_end(self):
        return self.end

    def set_range(self, begin, end):
        self.begin = begin
        self.end = end

    def is_oov(self):
        return self.is_oov

    def set_oov(self):
        self.is_oov = True

    def get_word_info(self):
        if self.word_id >= 0:
            return self.lexicon.get_word_info(self.word_id)
        elif(self.extra_word_info is not None):
            return self.extra_word_info
        raise IndexError("this node has no WordInfo")

    def set_word_info(self, word_info):
        self.extra_word_info = word_info
        self.word_id = -1

    def get_path_cost(self):
        return self.cost

    def get_word_id(self):
        return self.word_id

    def get_dictionary_id(self):
        return self.word_id >> 28

    def __str__(self):
        surface = ""
        if self.word_id < 0 and self.extra_word_info is None:
            surface = "(None)"
        else:
            surface = self.get_word_info().surface

        return "{} {} {}({}) {} {} {}".format(
            self.get_begin(), self.get_end(), surface, self.word_id, self.left_id, self.right_id, self.cost
        )
