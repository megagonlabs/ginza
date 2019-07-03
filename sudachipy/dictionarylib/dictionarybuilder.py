import csv
import re
from logging import DEBUG, StreamHandler, getLogger

from sortedcontainers import SortedDict

from sudachipy.dartsclone.doublearray import DoubleArray
from sudachipy.dictionarylib.jtypedbytebuffer import JTypedByteBuffer
from sudachipy.dictionarylib.wordinfo import WordInfo


class DictionaryBuilder(object):

    __BYTE_MAX_VALUE = 127
    __MAX_LENGTH = 255
    __COLS_NUM = 18
    __BUFFER_SIZE = 1024 * 1024
    __PATTERN_UNICODE_LITERAL = re.compile(r"\\u([0-9a-fA-F]{4}|{[0-9a-fA-F]+})")
    __ARRAY_MAX_LENGTH = __BYTE_MAX_VALUE  # max value of byte in Java
    __STRING_MAX_LENGTH = 32767  # max value of short in Java
    is_user_dictionary = False

    class WordEntry:
        headword = None
        parameters = None
        wordinfo = None
        aunit_split_string = None
        bunit_split_string = None
        cunit_split_string = None

    class PosTable(object):

        def __init__(self):
            self.table = []

        def get_id(self, str_):
            id_ = self.table.index(str_) if str_ in self.table else -1
            if id_ < 0:
                id_ = len(self.table)
                self.table.append(str_)
            return id_

        def get_list(self):
            return self.table

    @staticmethod
    def __default_logger():
        handler = StreamHandler()
        handler.terminator = ""
        handler.setLevel(DEBUG)
        logger = getLogger(__name__)
        logger.setLevel(DEBUG)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

    def __init__(self, *, logger=None):
        self.byte_buffer = JTypedByteBuffer()
        self.trie_keys = SortedDict()
        self.entries = []
        self.is_dictionary = False
        self.pos_table = self.PosTable()
        self.logger = logger or self.__default_logger()

    def build(self, lexicon_paths, matrix_input_stream, out_stream):
        self.logger.info('reading the source file...')
        for path in lexicon_paths:
            with open(path) as rf:
                self.build_lexicon(rf)
        self.logger.info('{} words\n'.format(len(self.entries)))

        self.write_grammar(matrix_input_stream, out_stream)
        self.write_lexicon(out_stream)

    def build_lexicon(self, lexicon_input_stream):
        line_no = -1
        try:
            for i, row in enumerate(csv.reader(lexicon_input_stream)):
                line_no = -1
                entry = self.parse_line(row)
                if entry.headword:
                    self.add_to_trie(entry.headword, len(self.entries))
                self.entries.append(entry)
        except Exception as e:
            if line_no > 0:
                self.logger.error(
                    '{} at line {} in {}\n'.format(e.args[0], line_no, lexicon_input_stream.name))
            raise e

    def parse_line(self, cols):
        if len(cols) != self.__COLS_NUM:
            raise ValueError('invalid format')
        cols = [self.decode(col) for col in cols]
        if not self.__is_length_valid(cols):
            raise ValueError('string is too long')
        if not cols[0]:
            raise ValueError('headword is empty')

        entry = self.WordEntry()
        # head word for trie
        if cols[1] != '-1':
            entry.headword = cols[0]
        # left-id, right-id, cost
        entry.parameters = [int(cols[i]) for i in [1, 2, 3]]
        # part of speech
        pos_id = self.get_posid(cols[5:11])
        if pos_id < 0:
            raise ValueError('invalid part of speech')

        entry.aunit_split_string = cols[15]
        entry.bunit_split_string = cols[16]
        entry.cunit_split_string = cols[17]
        self.check_splitinfo_format(entry.aunit_split_string)
        self.check_splitinfo_format(entry.bunit_split_string)
        self.check_splitinfo_format(entry.cunit_split_string)

        if cols[14] == 'A' and \
                not (entry.aunit_split_string == '*' and entry.bunit_split_string == '*'):
            raise ValueError('invalid splitting')

        head_length = len(cols[0].encode('utf-8'))
        dict_from_wordid = -1 if cols[13] == '*' else int(cols[13])
        entry.wordinfo = WordInfo(
            cols[4], head_length, pos_id, cols[12], dict_from_wordid, '', cols[11], None, None, None)
        return entry

    def __is_length_valid(self, cols):
        head_length = len(cols[0].encode('utf-8'))
        return head_length <= self.__STRING_MAX_LENGTH \
            and len(cols[4]) <= self.__STRING_MAX_LENGTH \
            and len(cols[11]) <= self.__STRING_MAX_LENGTH \
            and len(cols[12]) <= self.__STRING_MAX_LENGTH

    def add_to_trie(self, headword, word_id):
        key = headword.encode('utf-8')
        if key not in self.trie_keys:
            self.trie_keys[key] = []
        self.trie_keys[key].append(word_id)

    def get_posid(self, strs):
        return self.pos_table.get_id(','.join(strs))

    def write_grammar(self, matrix_input_stream, output_stream):
        self.logger.info('writing the POS table...')
        self.convert_postable(self.pos_table.get_list())
        self.byte_buffer.seek(0)
        output_stream.write(self.byte_buffer.read())
        self.__logging_size(self.byte_buffer.tell())
        self.byte_buffer.clear()

        self.logger.info('writing the connection matrix...')
        if not matrix_input_stream:
            self.byte_buffer.write_int(0, 'short')
            self.byte_buffer.write_int(0, 'short')
            self.byte_buffer.seek(0)
            output_stream.write(self.byte_buffer.read())
            self.__logging_size(self.byte_buffer.tell())
            self.byte_buffer.clear()
            return
        matrix = self.convert_matrix(matrix_input_stream)
        self.byte_buffer.seek(0)
        output_stream.write(self.byte_buffer.read())
        self.byte_buffer.clear()
        output_stream.write(matrix.read())
        self.__logging_size(matrix.tell() + 4)

    def convert_postable(self, pos_list):
        self.byte_buffer.write_int(len(pos_list), 'short')
        for pos in pos_list:
            for text in pos.split(','):
                self.write_string(text)

    def convert_matrix(self, matrix_input):
        header = matrix_input.readline().strip()
        if re.fullmatch(r"\s*", header):
            raise ValueError('invalid format at line 0')
        lr = header.split()
        lsize, rsize = [int(x) for x in lr]
        self.byte_buffer.write_int(lsize, 'short')
        self.byte_buffer.write_int(rsize, 'short')

        matrix = JTypedByteBuffer()

        for i, line in enumerate(matrix_input.readlines()):
            line = line.strip()
            if re.fullmatch(r"\s*", line) or re.match("#", line):
                continue
            cols = line.split()
            if len(cols) < 3:
                self.logger.warn('invalid format at line {}'.format(i))
                continue
            l, r, cost = [int(col) for col in cols]
            pos = matrix.tell()
            matrix.seek(2 * (l + lsize * r))
            matrix.write_int(cost, 'short')
            matrix.seek(pos)
        return matrix

    def write_lexicon(self, io_out):
        trie = DoubleArray()
        wordid_table = JTypedByteBuffer()
        keys = []
        vals = []
        for key, word_ids in self.trie_keys.items():
            keys.append(key)
            vals.append(wordid_table.tell())
            wordid_table.write_int(len(word_ids), 'byte')
            for wid in word_ids:
                wordid_table.write_int(wid, 'int')

        self.logger.info('building the trie...')

        def progress_func(n, s):
            if (n % (s / 10 + 1)) == 0:
                self.logger('.')
        trie.build(keys, vals, progress_func)
        self.logger.info('done\n')

        self.logger.info('writing the trie...')
        self.byte_buffer.clear()
        self.byte_buffer.write_int(trie.size, 'int')
        self.byte_buffer.seek(0)
        io_out.write(self.byte_buffer.read())
        self.byte_buffer.clear()

        io_out.write(trie.byte_array().read())
        self.__logging_size(trie.size * 4 + 4)
        del trie

        self.logger.info('writing the word-ID table...')
        self.byte_buffer.write_int(wordid_table.tell(), 'int')
        self.byte_buffer.seek(0)
        io_out.write(self.byte_buffer.read())
        self.byte_buffer.clear()

        wordid_table.seek(0)
        io_out.write(wordid_table.read())
        self.__logging_size(wordid_table.tell() + 4)
        del wordid_table

        self.logger.info('writing the word parameters...')
        self.byte_buffer.write_int(len(self.entries), 'int')
        for entry in self.entries:
            self.byte_buffer.write_int(entry.parameters[0], 'short')
            self.byte_buffer.write_int(entry.parameters[1], 'short')
            self.byte_buffer.write_int(entry.parameters[2], 'short')
            self.byte_buffer.seek(0)
            io_out.write(self.byte_buffer.read())
            self.byte_buffer.clear()
        self.__logging_size(len(self.entries) * 6 + 4)
        self.write_wordinfo(io_out)

    def write_wordinfo(self, io_out):
        mark = io_out.tell()
        io_out.seek(mark * 4 + len(self.entries))
        offsets = JTypedByteBuffer()
        self.logger.info('writing the word_infos...')
        base = io_out.tell()
        for entry in self.entries:
            wi = entry.wordinfo
            offsets.write_int(io_out.tell(), 'int')
            self.write_string(wi.surface)
            self.write_stringlength(wi.length())
            self.byte_buffer.write_int(wi.pos_id, 'short')
            if wi.normalized_form == wi.surface:
                self.write_string('')
            else:
                self.write_string(wi.normalized_form)
            self.byte_buffer.write_int(wi.dictionary_form_word_id, 'int')
            if wi.reading_form == wi.surface:
                self.write_string('')
            else:
                self.write_string(wi.reading_form)

            self.write_intarray(self.parse_splitinfo(entry.aunit_split_string))
            self.write_intarray(self.parse_splitinfo(entry.bunit_split_string))
            self.write_intarray(self.parse_splitinfo(entry.cunit_split_string))
            self.byte_buffer.seek(0)
            io_out.write(self.byte_buffer.read())
            self.byte_buffer.clear()
        self.__logging_size(io_out.tell() - base)
        self.logger.info('writing word_info offsets...')
        io_out.seek(mark)
        offsets.seek(0)
        io_out.write(offsets.read())
        self.__logging_size(offsets.tell())

    def decode(self, str_):
        def replace(match):
            uni_text = match.group()
            uni_text = uni_text.replace('{', '').replace('}', '')
            if len(uni_text) > 6:
                uni_text = ('\\U000{}'.format(uni_text[2:]))
            return uni_text.encode('ascii').decode('unicode-escape')
        return re.sub(self.__PATTERN_UNICODE_LITERAL, replace, str_)

    def check_splitinfo_format(self, str_):
        if str_.count('/') + 1 > self.__ARRAY_MAX_LENGTH:
            raise ValueError('too many units')

    def parse_splitinfo(self, info):
        if info == '*':
            return []
        words = info.split('/')
        if len(words) > self.__ARRAY_MAX_LENGTH:
            raise ValueError('too many units')
        ids = []
        for word in words:
            if self.__is_id(word):
                ids.append(self.parse_id(word))
            else:
                ids.append(self.word_to_id(word))
                if ids[-1] < 0:
                    return ValueError('not found such a word')
        return ids

    @staticmethod
    def __is_id(text):
        return re.match(r'U?\d+', text)

    def parse_id(self, text):
        if text.startswith('U'):
            id_ = int(text[1:])
            if self.is_user_dictionary:
                id_ |= (1 << 28)
        else:
            id_ = int(text)
        self.check_wordid(id_)
        return id_

    def word_to_id(self, text):
        cols = text.split(',')
        if len(cols) < 8:
            raise ValueError('too few columns')
        headword = self.decode(cols[0])
        pos_id = self.get_posid([cols[i] for i in range(1, 7)])
        if pos_id < 0:
            raise ValueError('invalid part of speech')
        reading = self.decode(cols[7])
        return self.get_wordid(headword, pos_id, reading)

    def get_wordid(self, headword, pos_id, reading_form):
        for i in range(len(self.entries)):
            info = self.entries[i].wordinfo
            if info.surface == headword \
                    and info.pos_id == pos_id \
                    and info.reading_form == reading_form:
                return i
        return -1

    def check_wordid(self, wid):
        if wid < 0 or wid >= len(self.entries):
            raise ValueError('invalid word ID')

    def write_string(self, text):
        len_ = 0
        for c in text:
            if 0x10000 <= ord(c) <= 0x10FFFF:
                len_ += 2
            else:
                len_ += 1
        self.write_stringlength(len_)
        self.byte_buffer.write_str(text)

    def write_stringlength(self, len_):
        if len_ <= self.__BYTE_MAX_VALUE:
            self.byte_buffer.write_int(len_, 'byte')
        else:
            self.byte_buffer.write_int((len_ >> 8) | 0x80, 'byte')
            self.byte_buffer.write_int((len_ & 0xFF), 'byte')

    def write_intarray(self, array):
        self.byte_buffer.write_int(len(array), 'byte')
        for item in array:
            self.byte_buffer.write_int(item, 'int')

    def __logging_size(self, size):
        self.logger.info('{} bytes\n'.format(size))
