from itertools import tee, zip_longest
from automatons import NDN, NDA, SIGMA

def ParsingError(Exception):
    tmpt = "{}. At index {}: {}"
    def __init__(self, message, index, pattern):
        substr = pattern[max(index-3, 0):min(index+3, len(pattern))]
        super(Exception).__init__(self, tmpt.format(message, index, substr))


def parse(pattern):
    start = NDN()
    end = NDN(is_final=True)

    p1, p2 = tee(pattern)
    next(p2)
    iteratee = zip_longest(p1, p2)

    groups(start, end, iteratee)
    try:
        next(iteratee)
    except StopIteration:
        pass
    else:
        raise ParsingError("Unmatched parenthesis", len(pattern)-1, pattern)
    return NDA(start)


def groups(start, end, iteratee):
    skip = False
    escape = False
    kleene_start = NDN()
    start.add("", kleene_start)
    last_node = kleene_start
    last_nodes = []

    for char, next_char in iteratee:
        if escape:
            if next_char == "*":
                start_in = NDN()
                end_in = concat(start_in, char)
                last_node = kleene(last_node, start_in, end_in)
                skip = True
            else:
                last_node = concat(last_node, char)

            escape = False

        if char == "*" and skip:
            skip = False
        elif char == "*":
            raise ParsingError("Invalid Kleene", pattern, index)

        elif char == "\\":
            escape = True

        elif char == "(":
            sub_end = NDN()
            skip = groups(last_node, sub_end, iteratee)
            last_node = sub_end

        elif char == ")":
            if next_char == "*":
                kleene(start, kleene_start, last_node, *last_nodes).add("", end)
                return True
            else:
                last_node.add("", end)
                return False

        elif char == "|":
            last_nodes.append(last_node)
            last_node.add("", end)
            last_node = kleene_start

        elif char != "ε":
            char_ = SIGMA if char == "Σ" else char
            if next_char == "*":
                start_in = NDN()
                end_in = concat(start_in, char_)
                last_node = kleene(last_node, start_in, end_in)
                skip = True
            else:
                last_node = concat(last_node, char_)

    last_node.add("", end)


def kleene(start, start_in, *ends_in):
    end = NDN()
    start.add("", start_in)
    start.add("", end)
    for end_in in ends_in:
        end_in.add("", start_in)
        end_in.add("", end)
    return end


def concat(start, char):
    new = NDN()
    start.add(char, new)
    return new

