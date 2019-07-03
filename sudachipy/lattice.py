from . import dictionarylib
from . import latticenode


class Lattice:
    def __init__(self, grammar):
        self.end_lists = []
        self.size = 0
        self.capacity = 0
        self.eos_node = None

        self.grammar = grammar

        self.eos_params = grammar.get_eos_parameter()

        bos_node = latticenode.LatticeNode()
        bos_params = grammar.get_bos_parameter()
        bos_node.set_parameter(bos_params[0], bos_params[1], bos_params[2])
        bos_node.is_connected_to_bos = True
        self.end_lists.append([bos_node])

    def resize(self, size):
        if size > self.capacity:
            self.expand(size)
        self.size = size

        self.eos_node = latticenode.LatticeNode()
        self.eos_node.set_parameter(self.eos_params[0], self.eos_params[1], self.eos_params[2])
        self.eos_node.begin = self.eos_node.end = size

    def clear(self):
        for i in range(1, self.size + 1):
            self.end_lists[i].clear()
        self.size = 0
        self.eos_node = None

    def expand(self, new_size):
        expand_list = [[] for i in range(self.size, new_size)]
        self.end_lists.extend(expand_list)

        self.capacity = new_size

    def get_nodes_with_end(self, end):
        return self.end_lists[end]

    def get_nodes(self, begin, end):
        return filter(lambda node: node.begin is begin, self.end_lists[end])

    def insert(self, begin, end, node):
        n = node
        self.end_lists[end].append(n)
        n.begin = begin
        n.end = end

        self.connect_node(n)

    def remove(self, begin, end, node):
        self.end_lists[end].remove(node)

    def create_node(self):
        return latticenode.LatticeNode()

    def has_previous_node(self, index):
        return len(self.end_lists[index]) is not 0

    def connect_node(self, r_node):
        begin = r_node.begin
        r_node.total_cost = float('inf')
        for l_node in self.end_lists[begin]:
            if not l_node.is_connected_to_bos:
                continue
            connect_cost = self.grammar.get_connect_cost(l_node.right_id, r_node.left_id)
            if connect_cost == dictionarylib.grammar.Grammar.INHIBITED_CONNECTION:
                continue
            cost = l_node.total_cost + connect_cost
            if cost < r_node.total_cost:
                r_node.total_cost = cost
                r_node.best_previous_node = l_node

        r_node.is_connected_to_bos = not (r_node.best_previous_node is None)
        r_node.total_cost += r_node.cost

    def get_best_path(self):
        self.connect_node(self.eos_node)
        if not self.eos_node.is_connected_to_bos:    # EOS node
            raise AttributeError("EOS is not connected to BOS")
        result = []
        node = self.eos_node
        while node is not self.end_lists[0][0]:
            result.append(node)
            node = node.best_previous_node
        return list(reversed(result))

    def dump(self, output):
        index = 0
        for i in range(self.size + 1, -1, -1):
            r_nodes = self.end_lists[i] if i <= self.size else [self.eos_node]
            for r_node in r_nodes:
                print("{}: {}: ".format(index, r_node), end="")
                index += 1
                for l_node in self.end_lists[r_node.begin]:
                    cost = l_node.total_cost + \
                        self.grammar.get_connect_cost(l_node.right_id, r_node.left_id)
                    print("{} ".format(cost), file=output, end="")
                print(file=output)
