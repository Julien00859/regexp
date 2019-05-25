from collections import defaultdict, OrderedDict
from contextlib import redirect_stdout
from io import StringIO
from functools import partial

SIGMA = object()

class Node:
    count = 0
    def __init__(self, is_final):
        self.is_final = is_final
        self.id = Node.count
        Node.count += 1

    def __str__(self):
        return ("({:0%dd})" % len(str(self.count - 1))).format(self.id)

    __repr__ = __str__

    def read(self, char):
        raise NotImplementedError("abstract method")

    def add(self, char, node):
        raise NotImplementedError("abstract method")

    def print_transitions(self):
        raise NotImplementedError("abstract method")

    def __hash__(self):
        return self.id


class NonDeterministNode(Node):
    def __init__(self, is_final=False):
        super().__init__(is_final)
        self.transitions = defaultdict(set)

    def read(self, char):
        return self.transitions.get(char, set())

    def add(self, *pairs):
        ipairs = iter(pairs)
        for char, node in zip(ipairs, ipairs):
            self.transitions[char].add(node)

    def print_transitions(self):
        for char, nodes in self.transitions.items():
            for node in nodes:
                print(self, {SIGMA: "Σ", "": "ε"}.get(char, char), node, "-->" if node.is_final else "")


class DeterministNode(Node):
    def __init__(self, is_final):
        super().__init__(is_final)
        self.transitions = dict()

    def read(self, char):
        return self.transitions.get(char) or self.transitions.get(SIGMA)

    def add(self, *pairs):
        ipairs = iter(pairs)
        for char, node in zip(ipairs, ipairs):
            if char == "":
                raise ValueError("Cannot have empty transition.")
            self.transitions[char] = node

    def print_transitions(self):
        for char, node in self.transitions.items():
            print(self, {SIGMA: "Σ", "": "ε"}.get(char, char), node, "-->" if node.is_final else "")


trap_node = DeterministNode(is_final=False)
trap_node.add(SIGMA, trap_node)


class Automaton:
    def __init__(self, initial_node):
        self.initial_node = initial_node

    def match(self, string):
        raise NotImplementedError("abstract method")

    def print(self):
        buffer_ = StringIO()

        # Feed the buffer with the tree
        with redirect_stdout(buffer_):
            print(" " * len(str(Node.count - 1)), "-->", self.initial_node)
            seen = set()
            show = {self.initial_node}
            while show:
                next_nodes = set()
                for node in show:
                    node.print_transitions()
                    seen.add(node)
                    if isinstance(self, DA):
                        next_nodes.update(node.transitions.values())
                    else:
                        next_nodes.update(*node.transitions.values())
                show = next_nodes - seen

        # Pretty print the tree by sorting nodes and
        # printing final nodes at the end
        lines = buffer_.getvalue().splitlines()
        ends = []
        for idx, line in enumerate(lines):
            if line.endswith("-->"):
                ends.append(line)
                lines[idx] = None
        for line in sorted(filter(bool, lines)):
            print(line)
        for line in sorted(ends):
            print(line)

class NonDeterministAutomaton(Automaton):
    def match(self, string):
        new_nodes = {self.initial_node}
        self._expand(new_nodes)
        for char in string:
            old_nodes = new_nodes
            new_nodes = set()
            for node in old_nodes:
                new_nodes |= node.read(char)
                new_nodes |= node.read(SIGMA)
            self._expand(new_nodes)
            if not new_nodes:
                return False
        return any(map(lambda n: n.is_final, new_nodes))

    @staticmethod
    def _expand(nodes):
        new_nodes = nodes.copy()
        while True:
            next_nodes = set()
            for node in new_nodes:
                next_nodes.update(node.read(""))
            new_nodes = next_nodes - nodes
            if not new_nodes:
                break
            nodes.update(new_nodes)

    @classmethod
    def from_pattern(class_, pattern):
        from pattern import parse
        return parse(pattern)


class DeterministAutomaton(Automaton):
    def match(self, string):
        node = self.initial_node
        for letter in string:
            node = node.read(letter)
            if node is None:
                return False
        return node.is_final

    @classmethod
    def from_nda(class_, nda):
        r"""
        Pattern: a*b
                       /<-ε--\
        NDA: (0)--ε->(1)--a->(2)--ε->(3)--b->(4)->
               \----------ε--------->/

        Derivation table:    nodes  |    a    |  b
                           ----------+---------+-----
                            {0,1,3} | {1,2,3} | {4}
                            {1,2,3} | {1,2,3} | {4}
                              {4}   |         |

        ndn_to_dn: {{0,1,3}: {5}, {1,2,3}: {6}, {4}: {7}}

                    \<a-/
        DA: (5)--a-->(6)--b-->(7)
              \-------b------>/
        """
        initial_nodes = {nda.initial_node}
        nda._expand(initial_nodes)
        initial_nodes = frozenset(initial_nodes)

        stack = [initial_nodes]
        derivation_table = defaultdict(dict)

        # Create and fill the derivation table
        while stack:
            cur_nodes = stack.pop()
            alphabet = set()
            for node in cur_nodes:
                alphabet.update(node.transitions.keys())
            alphabet.difference_update(set([""]))

            for char in alphabet:
                all_targets = set()
                for node in cur_nodes:
                    targets = node.read(char)
                    nda._expand(targets)
                    all_targets.update(targets)
                cell_nodes = frozenset(all_targets)
                if cell_nodes not in derivation_table:
                    stack.append(cell_nodes)
                derivation_table[cur_nodes][char] = cell_nodes

        # Create a new determinist node for each group of
        # non-determinist nodes from the derivation table
        ndn_to_dn = {}
        for nodes in derivation_table:
            is_final = any(map(lambda n: n.is_final, nodes))
            dn = DN(is_final)
            ndn_to_dn[nodes] = dn

        # Link determinist nodes using the derivation table
        for nodes in derivation_table:
            dn = ndn_to_dn[nodes]
            for char in derivation_table[nodes]:
                dn.add(char, ndn_to_dn[derivation_table[nodes][char]])

        return class_(ndn_to_dn[initial_nodes])


class DeterministCompletedAutomaton(DeterministAutomaton):
    def match(self, string):
        node = self.initial_node
        for letter in string:
            node = node.read(letter)
            if node is trap_node:
                return False
        return node.is_final

    @classmethod
    def from_da(class_, da):
        dca = class_(da.initial_node)
        seen = set()
        nodes = [dca.initial_node]
        while nodes:
            node = nodes.pop()
            new_nodes = set(node.transitions.values()) - seen
            nodes.extend(new_nodes)
            seen |= new_nodes
            node.transitions.setdefault(SIGMA, trap_node)
        return dca


class DeterministCompletedMinimalistAutomaton(DeterministCompletedAutomaton):
    @classmethod
    def from_dca(class_, dca):
        # Gather automaton's nodes
        dca_nodes = set([dca.initial_node])
        new_nodes = set([dca.initial_node])
        while new_nodes:
            new_nodes_targets = set()
            for node in new_nodes:
                new_nodes_targets.update(set(node.transitions.values()))
            new_nodes = new_nodes_targets - dca_nodes
            dca_nodes.update(new_nodes)
        dca_nodes = sorted(list(dca_nodes), key=lambda n: n.id)

        # Gather automaton's alphabet
        # determinism (=order) is important and sigma must be the last
        alphabet = set()
        for node in dca_nodes:
            alphabet.update(node.transitions.keys())
        alphabet.remove(SIGMA)
        alphabet = sorted(list(alphabet)) + [SIGMA]

        # Create the minimal derivation table
        nodes = None
        new_nodes = OrderedDict((node, int(not node.is_final) + 1) for node in dca_nodes)
        system = 3
        while nodes != new_nodes:
            nodes = new_nodes
            derivations = defaultdict(int)
            for node in nodes:
                for rank, char in enumerate(alphabet):
                    target = node.transitions.get(char)
                    if target:
                        derivations[node] += nodes[target] * system ** rank

            system = 1
            ids = {}
            new_nodes = OrderedDict()
            for node in nodes:
                if derivations[node] not in ids:
                    ids[derivations[node]] = system
                    system += 1
                new_nodes[node] = ids[derivations[node]]

        # Rename
        dca_to_id = nodes

        # Create nodes for new automaton
        id_to_dcma = {dca_to_id[node]: DeterministNode(node.is_final) for node in dca_nodes}

        # Link DCMA nodes
        seen_ids = set()
        for dca_node in dca_nodes:
            dca_node_id = dca_to_id[dca_node]
            if dca_node_id not in seen_ids:
                seen_ids.add(dca_node_id)
                dcma_node = id_to_dcma[dca_node_id]
                for char, dca_target in dca_node.transitions.items():
                    dcma_target = id_to_dcma[dca_to_id[dca_target]]
                    dcma_node.add(char, dcma_target)

        return class_(id_to_dcma[dca_to_id[dca.initial_node]])




NDN = NonDeterministNode
DN = DeterministNode
NDA = NonDeterministAutomaton
DA = DeterministAutomaton
DCA = DeterministCompletedAutomaton
DCMA = DeterministCompletedMinimalistAutomaton

