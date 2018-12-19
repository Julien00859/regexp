from collections import defaultdict

SIGMA = object()

class Node:
    count = 0
    def __init__(self, is_final):
        self.is_final = is_final
        self.id = Node.count
        Node.count += 1

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def __str__(self):
        return "(%d)" % self.id

    def read(self, symbol):
        raise NotImplementedError("abstract method")

    def add(self, symbol):
        raise NotImplementedError("abstract method")

class NonDeterministNode(Node):
    def __init__(self, is_final):
        super().__init__(self, is_final)
        self.transitions = defaultdict(set)

    def read(self, symbol):
        return self.transitions.get(symbol, set())

    def add(self, node, symbol, *pairs):
        self.transitions[symbol].add(node)
        for node, symbol in pairs:
            self.transitions[symbol].add(node)

class DeterministNode(Node):
    def __init__(self, is_final):
        super().__init__(self, is_final)
        self.transitions = dict()

    def read(self, symbol):
        return self.transitions.get(SIGMA) or self.transitions.get(symbol)

    def add(self, node, symbol, *pairs):
        if symbol == "":
            raise ValueError("Cannot have empty transition.")
        if self.transitions.get(symbol) != node:
            raise ValueError("Cannot have same symbol going to differents nodes.")
        if SIGMA in self.transitions:
            if self.transitions.get(SIGMA) != node:
                raise ValueError("Sigma is going elsewhere.")
        else:
            self.transitions[symbol] = node
        for node, symbol in pairs:
            if symbol == "":
                raise ValueError("Cannot have empty transition.")
            if self.transitions.get(symbol) != node:
                raise ValueError("Cannot have same symbol going to differents nodes.")
            if SIGMA in self.transitions:
                if self.transition.get(SIGMA) != node:
                    raise ValueError("Sigma is going elsewhere.")
            else:
                self.transitions[symbol] = node


class DeterministCompletedNode(DeterministNode):
    void_node = DeterministNode(is_final=false)
    void_node.add(SIGMA, void_node)
    def read(self, symbol):
        self.transitions.get(symbol, self.void_node)

class Automaton:
    def __init__(self, initial_node):
        self.initial_node = initial_node

    def match(self, string):
        raise NotImplementedError("abstract method")

class NonDeterministAutomaton(Automaton):
    def match(self, string):
        new_nodes = {self.initial_node}
        self._expand(new_nodes)
        for letter in string:
            old_nodes = new_nodes
            new_nodes = set()
            for node in old_nodes:
                new_nodes |= node.read(symbol)
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
    def from_regexp(class_, regexp):
        raise NotImplementedError("todo")


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
        raise NotImplementedError("todo")

class DeterministCompletedAutomaton(DeterministAutomaton):
    def match(self, string):
        node = self.initial_node
        for letter in string:
            node = node.read(letter)
        return node.is_final
    
    @classmethod
    def from_da(class_, da):
        raise NotImplementedError("todo")

class DeterministCompletedMinimalAutomaton(DeterministCompletedAutomaton):
    @classmethod
    def from_dca(class_, dca):
        raise NotImplementedError("todo")

NDN = NonDeterministNode
DN = DeterministNode
DCN = DeterministCompletedNode
NDA = NonDeterministAutomaton
DA = DeterministAutomaton
DCA = DeterministCompletedAutomaton
DCMA = DeterministCompletedMinimalAutomaton

