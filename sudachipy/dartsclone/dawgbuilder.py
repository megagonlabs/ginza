import copy

from . import bitvector


class DAWGBuilder(object):
    class Node(object):
        def __init__(self):
            self.child = 0
            self.sibling = 0
            self.label = 0
            self.is_state = False
            self.has_sibling = False

        def reset(self):
            self.child = 0
            self.sibling = 0
            self.label = 0
            self.is_state = False
            self.has_sibling = False

        def get_value(self):
            return self.child

        def set_value(self, value):
            self.child = value

        def unit(self):
            if self.label is 0:
                return (self.child << 1) | (1 if self.has_sibling else 0)
            return (self.child << 2) | (2 if self.is_state else 0) | (1 if self.has_sibling else 0)

        def __str__(self):
            return "child: %d, sibling: %d, label: %c, is_state: %d, has_sibling: %d" % (
                self.child, self.sibling, self.label, int(self.is_state), int(self.has_sibling)
            )

    class Unit(object):
        def __init__(self):
            self.unit = 0

        def child(self):
            return self.unit >> 2

        def has_sibling(self):
            return (self.unit & 1) is 1

        def value(self):
            return self.unit >> 1

        def is_state(self):
            return (self.unit & 2) is 2

    def __init__(self):
        self.INITIAL_TABLE_SIZE = 1 << 10

        self.nodes = []
        self.units = []
        self.labels = []
        self.is_intersections = bitvector.BitVector()
        self.table = []
        self.node_stack = []
        self.recycle_bin = []
        self.num_states = 0

    def root(self):
        return 0

    def child(self, id):
        return self.units[id].child()

    def sibling(self, id):
        return id + 1 if self.units[id].has_sibling() else 0

    def value(self, id):
        return self.units[id].value()

    def is_leaf(self, id):
        return self.label(id) is 0

    def label(self, id):
        return self.labels[id]

    def is_intersection(self, id):
        return self.is_intersections.get(id)

    def intersecrion_id(self, id):
        return self.is_intersections.rank(id) - 1

    def num_intersections(self):
        return self.is_intersections.get_num_ones()

    def size(self):
        return len(self.units)

    def init(self):
        self.table = [0] * self.INITIAL_TABLE_SIZE

        self.append_node()
        self.append_unit()

        self.num_states = 1

        self.nodes[0].label = 0xFF
        self.node_stack.append(0)

    def finish(self):
        self.flush(0)

        self.units[0].unit = copy.deepcopy(self.nodes[0].unit())
        self.labels[0] = copy.deepcopy(self.nodes[0].label)

        self.nodes = None
        self.table = None
        self.node_stack = None
        self.recycle_bin = None

        self.is_intersections.build()

    def insert(self, key, value):
        if value < 0:
            raise AttributeError("negative value")
        if len(key) is 0:
            raise AttributeError("zero-length key")

        id_ = 0
        key_pos = 0

        while key_pos <= len(key):
            child_id = self.nodes[id_].child
            if child_id is 0:
                break

            key_label = key[key_pos] if key_pos < len(key) else 0
            if key_pos < len(key) and key_label is 0:
                raise AttributeError("invalid null character")

            unit_label = self.nodes[child_id].label
            if key_label < unit_label:
                raise AttributeError("wrong key order")
            elif key_label > unit_label:
                self.nodes[child_id].has_sibling = True
                self.flush(child_id)
                break
            id_ = child_id
            key_pos += 1

        if key_pos > len(key):
            return

        while key_pos <= len(key):
            key_label = key[key_pos] if key_pos < len(key) else 0
            child_id = self.append_node()

            if self.nodes[id_].child is 0:
                self.nodes[child_id].is_state = True
            self.nodes[child_id].sibling = self.nodes[id_].child
            self.nodes[child_id].label = key_label
            self.nodes[id_].child = child_id
            self.node_stack.append(child_id)

            id_ = child_id
            key_pos += 1
        self.nodes[id_].set_value(value)

    def clear(self):

        self.nodes = []
        self.units = []
        self.labels = []
        self.is_intersections = bitvector.BitVector()
        self.table = []
        self.node_stack = []
        self.recycle_bin = []
        self.num_states = 0

    def flush(self, id):
        while self.stack_top(self.node_stack) is not id:
            node_id = self.stack_top(self.node_stack)
            self.stack_pop(self.node_stack)

            if self.num_states >= len(self.table) - (len(self.table) >> 2):
                self.expand_table()

            num_siblings = 0
            n = node_id
            while n is not 0:
                num_siblings += 1
                n = self.nodes[n].sibling

            find_result = self.find_node(node_id)
            match_id = find_result[0]
            hash_id = find_result[1]

            if match_id is not 0:
                self.is_intersections.set(match_id, True)
            else:
                unit_id = 0
                for i in range(num_siblings):
                    unit_id = self.append_unit()
                n = node_id
                while n is not 0:
                    self.units[unit_id].unit = self.nodes[n].unit()
                    self.labels[unit_id] = self.nodes[n].label
                    unit_id -= 1
                    n = self.nodes[n].sibling
                match_id = unit_id + 1
                self.table[hash_id] = match_id
                self.num_states += 1

            n = node_id
            while n is not 0:
                next_ = self.nodes[n].sibling
                self.free_node(n)
                n = next_

            self.nodes[self.stack_top(self.node_stack)].child = match_id
        self.stack_pop(self.node_stack)

    def expand_table(self):
        table_size = len(self.table) << 1
        self.table.clear()
        self.table = [0] * table_size

        for id_ in range(1, len(self.units)):
            if self.labels[id_] is 0 or self.units[id_].is_state():
                find_result = self.find_unit(id_)
                hash_id = find_result[1]
                self.table[hash_id] = id_

    def find_unit(self, id):
        result = [0] * 2
        hash_id = self.hash_unit(id) % len(self.table)
        while True:
            unit_id = self.table[hash_id]
            if unit_id is 0:
                break
            hash_id = (hash_id + 1) % len(self.table)
        result[1] = hash_id
        return result

    def find_node(self, node_id):
        result = [0] * 2
        hash_id = self.hash_node(node_id) % len(self.table)
        while True:
            unit_id = self.table[hash_id]
            if unit_id is 0:
                break

            if self.are_equal(node_id, unit_id):
                result[0] = unit_id
                result[1] = hash_id
                return result
            hash_id = (hash_id + 1) % len(self.table)

        result[1] = hash_id
        return result

    def are_equal(self, node_id, unit_id):
        n = self.nodes[node_id].sibling
        while n is not 0:
            if not self.units[unit_id].has_sibling():
                return False
            unit_id += 1
            n = self.nodes[n].sibling

        if self.units[unit_id].has_sibling():
            return False

        n = node_id
        while n is not 0:
            if (self.nodes[n].unit() is not self.units[unit_id].unit) or (self.nodes[n].label is not self.labels[unit_id]):
                return False
            n = self.nodes[n].sibling
            unit_id -= 1

        return True

    def hash_unit(self, id):
        hash_value = 0
        while id is not 0:
            unit = self.units[id].unit
            label = self.labels[id]
            hash_value ^= self.hash((label << 24) ^ unit)

            if not self.units[id].has_sibling():
                break
            id += 1
        return hash_value

    def hash_node(self, id_):
        hash_value = 0
        while id_ is not 0:
            unit = self.nodes[id_].unit()
            label = self.nodes[id_].label
            hash_value ^= self.hash(((label & 0xFF) << 24) ^ unit)
            id_ = self.nodes[id_].sibling
        return hash_value

    def append_unit(self):
        self.is_intersections.append()
        self.units.append(self.Unit())
        self.labels.append(0)

        return self.is_intersections.get_size() - 1

    def append_node(self):
        if len(self.recycle_bin) is 0:
            id_ = len(self.nodes)
            self.nodes.append(self.Node())
        else:
            id_ = self.stack_top(self.recycle_bin)
            self.nodes[id_].reset()
            self.stack_pop(self.recycle_bin)
        return id_

    def free_node(self, id):
        self.recycle_bin.append(id)

    def hash(self, key):
        key = ~key + (key << 15)  # key = (key << 15) - key - 1
        key = key ^ (key >> 12)
        key = key + (key << 2)
        key = key ^ (key >> 4)
        key = key * 2057  # key = (key + (key << 3)) + (key << 1)
        key = key ^ (key >> 16)
        return key

    def stack_top(self, stack):
        return stack[-1]

    def stack_pop(self, stack):
        stack.pop()

    def byte_to_u_int(self, b):
        return b & 0xFF
