from collections import defaultdict
from typing import MutableMapping, Any
from .char import SIGMA, Character, char_to_str


class Node:
    count = 0
    transitions: MutableMapping[Character, Any]

    def __init__(self, is_final):
        self.is_final = is_final
        self.id = Node.count
        Node.count += 1

    def __str__(self):
        return ("({:0%dd})" % len(str(self.count - 1))).format(self.id)

    def __repr__(self): 
        return "<{} {} ({})>".format(
            self.__class__.__name__,
            self.id,
            ", ".join(map(char_to_str, self.transitions)))

    def read(self, char):
        raise NotImplementedError("abstract method")

    def add(self, char, node):
        raise NotImplementedError("abstract method")

    def print_transitions(self):
        raise NotImplementedError("abstract method")

    def __hash__(self):
        return self.id


class NonDeterministicNode(Node):
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
                print(self, char_to_str(char), node, "-->" if node.is_final else "")


class DeterministicNode(Node):
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
            print(self, char_to_str(char), node, "-->" if node.is_final else "")


trap_node = DeterministicNode(is_final=False)
trap_node.add(SIGMA, trap_node)

NDN = NonDeterministicNode
DN = DeterministicNode
