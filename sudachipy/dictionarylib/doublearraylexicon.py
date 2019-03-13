#import itertool
import struct

from . import lexicon
from .. import dartsclone
from . import wordidtable
from . import wordparameterlist
from . import wordinfolist


class DoubleArrayLexicon(lexicon.Lexicon):

    def __init__(self, bytes_, offset):
        self.trie = dartsclone.doublearray.DoubleArray()
        bytes_.seek(offset)
        self.size = int.from_bytes(bytes_.read(4), 'little')
        offset += 4
        bytes_.seek(offset)
        array = struct.unpack_from("<{}I".format(self.size), bytes_, offset)
        self.trie.set_array(array, self.size)
        offset += self.trie.total_size()

        self.word_id_table = wordidtable.WordIdTable(bytes_, offset)
        offset += self.word_id_table.storage_size()

        self.word_params = wordparameterlist.WordParameterList(bytes_, offset)
        offset += self.word_params.storage_size()

        self.word_infos = wordinfolist.WordInfoList(bytes_, offset, self.word_params.get_size())

    def lookup(self, text, offset):
        result = self.trie.common_prefix_search(text, offset)
        l = []
        for item in result:
            word_ids = self.word_id_table.get(item[0])
            length = item[1]
            for word_id in word_ids:
                l.append( (word_id, length) )
        return l

    def get_left_id(self, word_id):
        return self.word_params.get_left_id(word_id)

    def get_right_id(self, word_id):
        return self.word_params.get_right_id(word_id)

    def get_cost(self, word_id):
        return self.word_params.get_cost(word_id)

    def get_word_info(self, word_id):
        return self.word_infos.get_word_info(word_id)
