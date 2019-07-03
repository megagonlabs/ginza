import mmap

from . import doublearraybuilder
from . import keyset


class DoubleArray(object):

    def __init__(self):
        self.array = None
        self.buffer = None
        self.size = 0

    def set_array(self, array, size):
        """
        :param array: bytes(int)
        """
        self.array = array
        self.size = size

    def array(self):
        return self.array

    def byte_array(self):
        return self.buffer

    def clear(self):
        self.buffer = None
        self.size = 0

    # def size(self):
    #     return self.size

    def total_size(self):
        return 4 * self.size

    def build(self, keys, values, progress_function):
        key_set = keyset.KeySet(keys, values)
        builder = doublearraybuilder.DoubleArrayBuilder(progress_function)
        builder.build(key_set)
        self.buffer = builder.copy()
        bytes_ = self.buffer.getvalue()
        self.array = [
            int.from_bytes(bytes_[4 * i: 4 * i + 4], byteorder='little')
            for i in range(len(bytes_) // 4)]
        self.size = len(self.array)
        # for i, binary in enumerate(self.array):
        #     print("{0:03d}".format(i), "{0:032b}".format(binary), file=sys.stderr)

    def open(self, input_file, position, total_size):
        if position < 0:
            position = 0

        self.buffer = mmap.mmap(input_file.fileno(), total_size, offset=position)
        self.array = self.buffer.as_int_buffer()
        self.size = self.array.capacity()

    def save(self, output_file):
        pass

    def exact_match_search(self, key):
        result = [-1, 0]
        node_pos = 0
        unit = self.array[node_pos]

        for k in key:
            node_pos ^= self.offset(unit) ^ k
            unit = self.array[node_pos]
            if (self.label(unit) is not k):
                return result
        if not self.has_leaf(unit):
            return result
        unit = self.array[node_pos ^ self.offset(unit)]
        result[0] = self.value(unit)
        result[1] = len(key)
        return result

    def common_prefix_search(self, key, offset):
        result = []

        node_pos = 0
        unit = self.array[node_pos]
        node_pos ^= self.offset(unit)

        for i in range(offset, len(key)):
            k = key[i]
            node_pos ^= k
            unit = self.array[node_pos]
            if self.label(unit) != k:
                return result

            node_pos ^= self.offset(unit)
            if (self.has_leaf(unit)):
                r = [self.value(self.array[node_pos]), i + 1]
                result.append(r)
        return result

    def has_leaf(self, unit):
        return ((unit >> 8) & 1) == 1

    def value(self, unit):
        return unit & ((1 << 31) - 1)

    def label(self, unit):
        return unit & ((1 << 31) | 0xFF)

    def offset(self, unit):
        return (unit >> 10) << ((unit & (1 << 9)) >> 6)

    def byte_to_u_int(self, b):
        return int.from_bytes(b, 'little', signed=False)
