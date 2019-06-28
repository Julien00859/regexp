""""""


from collections import defaultdict
from typing import MutableMapping, Set, Any
from .char import SIGMA, Character, char_to_str


class Node:
    """Abstract Node"""

    count = 0
    transitions: MutableMapping[Character, Any]

    def __init__(self, is_final: bool):
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

    def read(self, char: str) -> Any:
        raise NotImplementedError("abstract method")

    def add(self, char: Character, node: "Node") -> None:
        raise NotImplementedError("abstract method")

    def print_transitions(self) -> None:
        raise NotImplementedError("abstract method")

    @classmethod
    def duplicate(cls, node):
        """Create a new node with the same is_final state as the given node"""
        if node is trap_node:
            return trap_node
        return cls(node.is_final)

    def __hash__(self):
        return self.id


class NDN(Node):
    """Non Deterministic Node"""

    transitions: MutableMapping[Character, Set[Node]]

    def __init__(self, is_final=False):
        super().__init__(is_final)
        self.transitions = defaultdict(set)

    def read(self, char: str) -> Set[Node]:
        return self.transitions.get(char, set())

    def add(self, char: Character, node: Node) -> None:
        self.transitions[char].add(node)

    def print_transitions(self) -> None:
        for char, nodes in self.transitions.items():
            for node in nodes:
                print(self, char_to_str(char), node, end="")
                print(" -->" if node.is_final else "")


class DN(Node):
    """Deterministic Node"""

    transitions: MutableMapping[Character, Node]

    def __init__(self, is_final: bool):
        super().__init__(is_final)
        self.transitions = dict()

    def read(self, char: str) -> Node:
        return self.transitions.get(char) or self.transitions.get(SIGMA)

    def add(self, char: Character, node: Node) -> None:
        if char == "":
            raise ValueError("Cannot have empty transition.")
        self.transitions[char] = node

    def print_transitions(self) -> None:
        for char, node in self.transitions.items():
            print(self, char_to_str(char), node, end="")
            print(" -->" if node.is_final else "")


trap_node = DN(is_final=False)
trap_node.add(SIGMA, trap_node)

NonDeterministicNode = NDN
DeterministicNode = DN
