from itertools import tee, zip_longest
from .char import SIGMA
from .nodes import NDN

IGNORE_CASE = 0b1

class ParsingError(Exception):
    def __init__(self, message, pattern, index):
        substr = pattern[max(index-3, 0):min(index+3, len(pattern))]
        super().__init__("{}. At index {}: {}".format(message, index, substr))


def parse(pattern: str, flags: int) -> NDN:
    r"""
    Parse a pattern, return the resulting starting :func:`Node
    <regexp.nodes.NDN>`

    Available sequences are:

    * ``()``, group. Used to group expression together, create
      sub-patterns.
    * ``|``, union. Used for choices, match specifically one group out
      of the available choices.
    * ``*``, kleene star. Used for repetition, match the last character
      or group zero, one or multiple times.
    * ``Σ``, sigma. Used as catchall, represent the entire alphabet. Alias: .
    * ``ε``, epsilon. Used as bypass, void transition. Alias: ?
    * ``\``, escape. Use the next character as-is.

    Not available sequences are:

    * ``+``, match one or multiple times. Can be achieved by prefixing
      the character to a kleene: ``aa*``.
    * ``?``, match zero or one time. Can be achieved using epsilon: ``(a|ε)``
    * ``[0-9]``, match any character from 0 to 9. Can be achieved by
      writing the full sequence: ``(0|1|2|3|4|5|6|7|8|9)``
    * ``{n}``, match exactly ``n`` times. Can be achieved by concatenate
      ``n`` times the group or character.
    * ``{n,m}``, match between ``n`` and ``m`` times. Can be achieved
      with ``n`` concatenations and ``m-n`` epsilon unions.

    Available flags are:

    * :func:`<regexp.pattern.IGNORE_CASE>`: Match lowercase letters and
    uppercase letters indifferently.
    """
    def main():
        start = NDN()
        end = NDN(is_final=True)

        p1, p2 = tee(pattern)
        next(p2)
        iteratee = zip_longest(p1, p2)

        groups(start, end, iteratee, 0)
        try:
            next(iteratee)
        except StopIteration:
            pass
        else:
            raise ParsingError("Unmatched parenthesis", len(pattern)-1, pattern)
        return start

    def groups(start, end, iteratee, start_index):
        skip = False
        escape = False
        kleene_start = NDN()
        start.add("", kleene_start)
        last_node = kleene_start
        last_nodes = []
        index = start_index

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

            elif char == "\\":
                escape = True

            elif char == "*" and skip:
                skip = False
            elif char == "*":
                raise ParsingError("Invalid Kleene", pattern, index)

            elif char == "(":
                sub_end = NDN()
                skip, start_index = groups(last_node, sub_end, iteratee, index + 1)
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

            elif char not in ("ε", "?"):
                char_ = SIGMA if char in ("Σ", ".") else char
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
        if flags & IGNORE_CASE:
            if "a" <= char <= "z":
                start.add(chr(ord(char) - 32), new)
            elif "A" <= char <= "A":
                start.add(chr(ord(char) + 32), new)
        return new

    return main()


def escape(pattern: str) -> str:
    """Escape the given pattern to match pure text instead of regexp"""
    escaped = []
    for char in pattern:
        if char in {"*", "\\", "|", "ε", "?", "(", ")", "Σ", "."}:
            escaped.append("\\")
        escaped.append(char)
    return "".join(escaped)


def expand(extended_pattern: str) -> str:
    r"""
    Expand the given extended pattern to be compatible with
    :func:`<regexp.pattern.parse>` grammar.

    Supported extended sequences are:

    * ``[abc]``, single choice, expand to ``(a|b|c)``
    * ``[0-5]``, range choice, expand to ``(0|1|2|3|4|5)``
    * ``\s``, any space, expand to ``( |\n|\r|\t)``
    * ``\d``, any digit, equivalent to ``[0-9]``
    * ``\w``, any letter, equivalent to ``[a-zA-Z0-9_]``
    """

    p1, p2 = tee(extended_pattern)
    p1, p3 = tee(extended_pattern)
    try:
        next(p2)
        next(p3)
        next(p3)
    except StopIteration:
        pass
    iteratee = zip_longest(p1, p2, p3)
    expanded_pattern = []

    escape_ = False
    skip = 0
    expanding = False
    expansion = []
    for idx, (char, next_char, next_next_char) in enumerate(iteratee):
        if skip:
            skip -= 1
        elif expanding:
            if escape_:
                escape_ = False
                expansion.append(char)
            elif char == "\\":
                escape_ = True
            elif next_char == '-':
                skip = 2
                ord_range = range(ord(char), ord(next_next_char) + 1)
                chars = [escape(chr(c)) for c in ord_range]
                expansion.extend(chars)
            elif char == "]":
                expanding = False
                expanded_pattern.extend("(%s)" % "|".join(expansion))
                expansion = []
            else:
                expansion.append(escape(char))
        elif escape_:
            escape_ = False
            expanded_pattern.append(char)
        elif char == "\\":
            expansion = _tokens.get(next_char)
            if expansion:
                skip = 1
                expanded_pattern.extend(expansion)
            else:
                escape_ = True
                expanded_pattern.append(char)
        elif char == "[":
            expanding = True
        else:
            expanded_pattern.append(char)

    return "".join(expanded_pattern)

_tokens = {
    "s": "( |\n|\r|\t)",
    "d": expand(r"[0-9]"),
    "w": expand(r"[a-zA-Z0-9_]"),}
