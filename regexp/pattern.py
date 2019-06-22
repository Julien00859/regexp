from itertools import tee, zip_longest
from .char import SIGMA
from .nodes import NDN

IGNORE_CASE = 0b1

class ParsingError(Exception):
    def __init__(self, message, pattern, index):
        substr = pattern[max(index-3, 0):min(index+3, len(pattern))]
        super().__init__("{}. At index {}: {}".format(message, index, substr))


def parse(pattern, flags):
    start = NDN()
    end = NDN(is_final=True)

    p1, p2 = tee(pattern)
    next(p2)
    iteratee = zip_longest(p1, p2)

    groups(start, end, iteratee, 0, pattern, flags=flags)
    try:
        next(iteratee)
    except StopIteration:
        pass
    else:
        raise ParsingError("Unmatched parenthesis", len(pattern)-1, pattern)
    return start


def groups(start, end, iteratee, start_index, pattern, flags):
    skip = False
    escape = False
    kleene_start = NDN()
    start.add("", kleene_start)
    last_node = kleene_start
    last_nodes = []

    for delta_index, (char, next_char) in enumerate(iteratee):
        index = start_index + delta_index
        if escape:
            if next_char == "*":
                start_in = NDN()
                end_in = concat(start_in, char, flags=flags)
                last_node = kleene(last_node, start_in, end_in, flags=flags)
                skip = True
            else:
                last_node = concat(last_node, char, flags=flags)

            escape = False

        elif char == "*" and skip:
            skip = False
        elif char == "*":
            raise ParsingError("Invalid Kleene", pattern, index)

        elif char == "\\":
            escape = True

        elif char == "(":
            sub_end = NDN()
            skip, start_index = groups(last_node, sub_end, iteratee, index + 1, pattern, flags=flags)
            last_node = sub_end

        elif char == ")":
            if next_char == "*":
                kleene(start, kleene_start, last_node, *last_nodes, flags=flags).add("", end)
                return True, index
            else:
                last_node.add("", end)
                return False, index

        elif char == "|":
            last_nodes.append(last_node)
            last_node.add("", end)
            last_node = kleene_start

        elif char != "ε":
            char_ = SIGMA if char == "Σ" else char
            if next_char == "*":
                start_in = NDN()
                end_in = concat(start_in, char_, flags=flags)
                last_node = kleene(last_node, start_in, end_in, flags=flags)
                skip = True
            else:
                last_node = concat(last_node, char_, flags=flags)

    if escape:
        raise ParsingError("Invalid escape sequence", pattern, index)
    last_node.add("", end)
    return skip, index


def kleene(start, start_in, *ends_in, flags):
    end = NDN()
    start.add("", start_in)
    start.add("", end)
    for end_in in ends_in:
        end_in.add("", start_in)
        end_in.add("", end)
    return end


def concat(start, char, flags):
    new = NDN()
    start.add(char, new)
    if flags & IGNORE_CASE:
        if "a" <= char <= "z":
            start.add(chr(ord(char) - 32), new)
        elif "A" <= char <= "A":
            start.add(chr(ord(char) + 32), new)
    return new
