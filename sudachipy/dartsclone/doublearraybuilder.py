from io import BytesIO

from . import dawgbuilder
from . import doublearraybuilderunit


class DoubleArrayBuilder(object):

    class DoubleArrayBuilderExtraUnit(object):
        def __init__(self):
            self.prev = 0
            self.next = 0
            self.is_fixed = False
            self.is_used = False

    def __init__(self, progress_function):
        self.BLOCK_SIZE = 256
        self.NUM_EXTRA_BLOCKS = 16
        self.NUM_EXTRAS = self.BLOCK_SIZE * self.NUM_EXTRA_BLOCKS
        self.UPPER_MASK = 0xFF << 21
        self.LOWER_MASK = 0xFF

        self.progress_function = progress_function
        self.clear()
        self.extras_head = 0

    def build(self, key_set):
        if key_set.has_values():
            dawg_builder = dawgbuilder.DAWGBuilder()
            self.build_dawg(key_set, dawg_builder)
            self.build_from_dawg_header(dawg_builder)
            dawg_builder.clear()
        else:
            self.build_from_key_set_header(key_set)

    def copy(self):
        buf = BytesIO()
        for u in self.units:
            buf.write(u.unit.to_bytes(4, byteorder='little', signed=False))
            # buf.write_int(u.unit, 'int', signed=False)
        buf.seek(0)
        return buf

    def clear(self):
        self.units = []
        self.extras = []
        self.labels = []
        self.table = []

    def num_blocks(self):
        return int(len(self.units) / self.BLOCK_SIZE)

    def get_extras(self, id):
        return self.extras[id % self.NUM_EXTRAS]

    def build_dawg(self, key_set, dawg_builder):
        dawg_builder.init()
        for i in range(key_set.size()):
            dawg_builder.insert(key_set.get_key(i), key_set.get_value(i))
            if self.progress_function is not None:
                # self.progress_function.accept(i + 1, key_set.size() + 1)
                self.progress_function(i + 1, key_set.size() + 1)
        dawg_builder.finish()

    def build_from_dawg_header(self, dawg):
        """
        num_units = 1
        while num_units < dawg.size():
            num_units <<= 1
        """

        self.table = [0] * dawg.num_intersections()
        self.extras = [self.DoubleArrayBuilderExtraUnit() for i in range(self.NUM_EXTRAS)]

        self.reserve_id(0)
        self.get_extras(0).is_used = True
        self.units[0].set_offset(1)
        self.units[0].set_label(0)

        if dawg.child(dawg.root()) is not 0:
            self.build_from_dawg_insert(dawg, dawg.root(), 0)

        self.fix_all_blocks()

        self.extras = None
        self.labels = None
        self.table = None

    def build_from_dawg_insert(self, dawg, dawg_id, dic_id):
        dawg_child_id = dawg.child(dawg_id)
        if dawg.is_intersection(dawg_child_id):
            intersection_id = dawg.intersection_id(dawg_child_id)
            offset = self.table[intersection_id]
            if offset is not 0:
                offset ^= dic_id
                if (offset & self.UPPER_MASK) is 0 or (offset & self.LOWER_MASK) is 0:
                    if dawg.is_leaf(dawg_child_id):
                        self.units[dic_id].set_has_leaf(True)
                    self.units[dic_id].set_offset(offset)
                    return

        offset = self.arrange_from_dawg(dawg, dawg_id, dic_id)
        if dawg.is_intersection(dawg_child_id):
            self.table[dawg.intersection_id(dawg_child_id)] = offset

        while True:
            child_label = dawg.label(dawg_child_id)
            dic_child_id = offset ^ child_label
            if child_label is not 0:
                self.build_from_dawg_insert(dawg, dawg_child_id, dic_child_id)
            dawg_child_id = dawg.sibling(dawg_child_id)
            if dawg_child_id is 0:
                break

    def arrange_from_dawg(self, dawg, dawg_id, dic_id):
        self.labels.clear()

        dawg_child_id = dawg.child(dawg_id)
        while(dawg_child_id is not 0):
            self.labels.append(dawg.label(dawg_child_id))
            dawg_child_id = dawg.sibling(dawg_child_id)

        offset = self.find_valid_offset(dic_id)
        self.units[dic_id].set_offset(dic_id ^ offset)

        dawg_child_id = dawg.child(dawg_id)
        for l in self.labels:
            dic_child_id = offset ^ l
            self.reserve_id(dic_child_id)

            if dawg.is_leaf(dawg_child_id):
                self.units[dic_id].set_has_leaf(True)
                self.units[dic_child_id].set_value(dawg.value(dawg_child_id))
            else:
                self.units[dic_child_id].set_label(l)

            dawg_child_id = dawg.sibling(dawg_child_id)
        self.get_extras(offset).is_used = True
        return offset

    def build_from_key_set_header(self, key_set):
        """
        num_units = 1
        while num_units < key_set.size():
            num_units <<= 1
        """

        self.extras = [self.DoubleArrayBuilderExtraUnit() for i in range(self.NUM_EXTRAS)]
        self.extras[2].next = 1

        self.reserve_id(0)
        self.get_extras(0).is_used = True
        self.units[0].set_offset(1)
        self.units[0].set_label(0)

        if key_set.size() > 0:
            self.build_from_key_set_insert(key_set, 0, key_set.size(), 0, 0)

        self.fix_all_blocks()

        self.extras = None
        self.labels = None

    def build_from_key_set_insert(self, key_set, begin, end, depth, dic_id):
        """
        :param key_set: KeySet
        :param begin: int
        :param end: int
        :param depth: int
        :param dic_id: int
        """
        offset = self.arrange_from_key_set(key_set, begin, end, depth, dic_id)

        while begin < end:
            if key_set.get_key_byte(begin, depth) is not 0:
                break
            begin += 1
        if begin is end:
            return

        last_begin = begin
        last_label = key_set.get_key_byte(begin, depth)
        while True:
            begin += 1
            if begin >= end:
                break
            label = key_set.get_key_byte(begin, depth)
            if label is not last_label:
                self.build_from_key_set_insert(key_set, last_begin, begin, depth + 1, offset ^ last_label)
                last_begin = begin
                last_label = key_set.get_key_byte(begin, depth)
        self.build_from_key_set_insert(key_set, last_begin, end, depth + 1, offset ^ last_label)

    def arrange_from_key_set(self, key_set, begin, end, depth, dic_id):

        self.labels.clear()

        value = -1
        for i in range(begin, end):
            label = key_set.get_key_byte(i, depth)
            if label is 0:
                if depth < len(key_set.get_key(i)):
                    raise AttributeError("invalid null character")
                elif key_set.get_value(i) < 0:
                    raise AttributeError("negative value")

                if value is -1:
                    value = key_set.get_value(i)
                if self.progress_function is not None:
                    # self.progress_function.accept(i + 1, key_set.size() + 1)
                    self.progress_function(i + 1, key_set.size() + 1)

            if len(self.labels) is 0:
                self.labels.append(label)
            elif label is not self.labels[-1]:
                if label < self.labels[-1]:
                    raise AttributeError("wrong key order")
                self.labels.append(label)

        offset = self.find_valid_offset(dic_id)
        self.units[dic_id].set_offset(dic_id ^ offset)

        for l in self.labels:
            dic_child_id = offset ^ l
            self.reserve_id(dic_child_id)
            if (l is 0):
                self.units[dic_id].set_has_leaf(True)
                self.units[dic_child_id].set_value(value)
            else:
                self.units[dic_child_id].set_label(l)
        self.get_extras(offset).is_used = True

        return offset

    def find_valid_offset(self, id):
        if self.extras_head >= len(self.units):
            return len(self.units) | (id & self.LOWER_MASK)

        unfixed_id = self.extras_head
        memo = []
        while True:
            # debug
            if unfixed_id not in memo:
                memo.append(unfixed_id)
            else:
                raise RuntimeError(unfixed_id, memo)

            offset = unfixed_id ^ self.labels[0]
            if self.is_valid_offset(id, offset):
                return offset
            unfixed_id = self.get_extras(unfixed_id).next

            if unfixed_id is self.extras_head:
                break

        return len(self.units) | (id & self.LOWER_MASK)

    def is_valid_offset(self, id, offset):
        if self.get_extras(offset).is_used:
            return False

        rel_offset = id ^ offset
        if (rel_offset & self.LOWER_MASK) is not 0 and (rel_offset & self.UPPER_MASK) is not 0:
            return False

        for i in range(1, len(self.labels)):
            if self.get_extras(offset ^ self.labels[i]).is_fixed:
                return False

        return True

    def reserve_id(self, id):
        if id >= len(self.units):
            self.expand_units()

        if id is self.extras_head:
            self.extras_head = self.get_extras(id).next
            if self.extras_head is id:
                self.extras_head = len(self.units)
        self.get_extras(self.get_extras(id).prev).next = self.get_extras(id).next
        self.get_extras(self.get_extras(id).next).prev = self.get_extras(id).prev
        self.get_extras(id).is_fixed = True

    def expand_units(self):
        src_num_units = len(self.units)
        src_num_blocks = self.num_blocks()

        dest_num_units = src_num_units + self.BLOCK_SIZE
        dest_num_blocks = src_num_blocks + 1

        if dest_num_blocks > self.NUM_EXTRA_BLOCKS:
            self.fix_block(src_num_blocks - self.NUM_EXTRA_BLOCKS)

        for i in range(src_num_units, dest_num_units):
            self.units.append(doublearraybuilderunit.DoubleArrayBuilderUnit())

        if dest_num_blocks > self.NUM_EXTRA_BLOCKS:
            for id_ in range(src_num_units, dest_num_units):
                self.get_extras(id_).is_used = False
                self.get_extras(id_).is_fixed = False

        for i in range(src_num_units + 1, dest_num_units):
            self.get_extras(i - 1).next = i
            self.get_extras(i).prev = i - 1

        self.get_extras(src_num_units).prev = dest_num_units - 1
        self.get_extras(dest_num_units - 1).next = src_num_units
        # It seems to me that meaningless because reassign in following
        # 2017.08.24 Hiyowa Kyobashi

        self.get_extras(src_num_units).prev = self.get_extras(self.extras_head).prev
        self.get_extras(dest_num_units - 1).next = self.extras_head

        self.get_extras(self.get_extras(self.extras_head).prev).next = src_num_units
        self.get_extras(self.extras_head).prev = dest_num_units - 1

    def fix_all_blocks(self):
        begin = 0
        if self.num_blocks() > self.NUM_EXTRA_BLOCKS:
            begin = self.num_blocks() - self.NUM_EXTRA_BLOCKS
        end = self.num_blocks()

        for block_id in range(begin, end):
            self.fix_block(block_id)

    def fix_block(self, block_id):
        begin = block_id * self.BLOCK_SIZE
        end = begin + self.BLOCK_SIZE

        unused_offset = 0
        offset = begin

        while offset is not end:
            if not self.get_extras(offset).is_used:
                unused_offset = offset
                break
            offset += 1

        for id_ in range(begin, end):
            if not self.get_extras(id_).is_fixed:
                self.reserve_id(id_)
                self.units[id_].set_label(id_ ^ unused_offset)

    def byte_to_u_int(self, b):
        return int.from_bytes(b, 'little', signed=False)
