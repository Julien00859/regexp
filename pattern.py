#!/usr/bin/env python3

from itertools import tee, zip_longest
from automatons import NDN, NDA, SIGMA

class ParsingError(Exception):
    def __init__(self, message, pattern, index):
        substr = pattern[max(index-3, 0):min(index+3, len(pattern))]
        super().__init__("{}. At index {}: {}".format(message, index, substr))


def parse(pattern):
    start = NDN()
    end = NDN(is_final=True)

    p1, p2 = tee(pattern)
    next(p2)
    iteratee = zip_longest(p1, p2)

    groups(start, end, iteratee, 0, pattern)
    try:
        next(iteratee)
    except StopIteration:
        pass
    else:
        raise ParsingError("Unmatched parenthesis", len(pattern)-1, pattern)
    return NDA(start)


def groups(start, end, iteratee, start_index, pattern):
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
                end_in = concat(start_in, char)
                last_node = kleene(last_node, start_in, end_in)
                skip = True
            else:
                last_node = concat(last_node, char)

            escape = False

        elif char == "*" and skip:
            skip = False
        elif char == "*":
            raise ParsingError("Invalid Kleene", pattern, index)

        elif char == "\\":
            escape = True

        elif char == "(":
            sub_end = NDN()
            skip, start_index = groups(last_node, sub_end, iteratee, index + 1, pattern)
            last_node = sub_end

        elif char == ")":
            if next_char == "*":
                kleene(start, kleene_start, last_node, *last_nodes).add("", end)
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
                end_in = concat(start_in, char_)
                last_node = kleene(last_node, start_in, end_in)
                skip = True
            else:
                last_node = concat(last_node, char_)

    if escape:
        raise ParsingError("Invalid escape sequence", pattern, index)
    last_node.add("", end)
    return skip, index


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

if __name__ == "__main__":
    tests = [
        ("abc", "abc"),
        ("a*", "", "a", "aa"),
        ("a|b", "a", "b"),
        ("a|b*", "", "a", "b", "bb"),
        ("(a|b)(c|d)", "ac", "ad", "bc", "bd"),
        ("Σ", "a", "b"),
        ("Σ*", "", "a", "aa"),
        ("(a|b)*", "", "a", "b", "aaa", "bbb", "aba", "bab", "aabb", "bbaa"),
        ("(ab|cd)*", "", "ab", "cd", "abab", "cdcd", "abcdab", "cdabcd", "ababcdcd", "cdcdabab"),
        ("\*", "*"),
        ("\**", "", "*", "**"),
        ("a(b|c)de*(fg|hi)*", "acd", "acde", "acdfg", "abdeee", "acdehi", "acdeefghi", "acdeefghifghi"),
        ("(fg*|hi)*", "", "f", "fg", "fgg", "hi", "fhi", "fghi", "fgghi", "hif", "hifg", "hifgg")
    ]

    for pattern, *strings in tests:
        automaton = parse(pattern)
        for string in strings:
            assert automaton.match(string), "{}: {}".format(pattern, string)

