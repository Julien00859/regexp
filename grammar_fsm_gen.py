#!/usr/bin/env python3

import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from operator import itemgetter
from io import StringIO
import regexp


logger = logging.getLogger("regexp")
logger.addHandler(logging.NullHandler())

termre = regexp.compile(r"[A-Z][A-Z0-9_]*")
nontermre = regexp.compile(r"[a-z][a-z0-9_]*")
stringre = regexp.compile(r'".*"(i|ε)')
patternre = regexp.compile(r"/.*/(i|ε)")


@dataclass(frozen=True)
class Line:
    rule_no: str
    rule: tuple
    index: int

    @property
    def point_term(self):
        return not self.point_end and termre.match(self.rule[self.index])

    @property
    def point_non_terminal(self):
        return not self.point_end and nontermre.match(self.rule[self.index])

    @property
    def point_end(self):
        return self.index >= len(self.rule)

    def point(self, symbol):
        return not self.point_end and self.rule[self.index] == symbol

    def shift(self):
        return type(self)(self.rule_no, self.rule, self.index + 1)

    def __str__(self):
        l = list(self.rule)
        l.insert(self.index, "⋅")
        return self.rule_no + ": " + " ".join(l)


def load_grammar(path):
    terminals = {}
    rules = defaultdict(list)

    with open(path, "r") as fd:
        for line in fd:
            try:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                lhs, _, rhs = line.partition(":")
                lhs = lhs.strip()
                rhs = rhs.strip()

                try:
                    lhs.encode('ascii')
                except UnicodeEncodeError as e:
                    raise SyntaxError from e

                if termre.match(lhs):
                    if stringre.match(rhs):
                        string, _, flags = rhs[1:].rpartition('"')
                        pattern = regexp.escape(string)
                    elif patternre.match(rhs):
                        pattern, _, flags = rhs[1:].rpartition("/")
                    else:
                        raise SyntaxError(rhs)

                    flags = set(flags)
                    terminals[lhs] = regexp.compile(
                        pattern,
                        regexp.IGNORE_CASE if "i" in flags else 0
                    )

                elif nontermre.match(lhs):
                    try:
                        rhs.encode('ascii')
                    except UnicodeEncodeError as e:
                        raise SyntaxError from e

                    for rule in rhs.split("|"):
                        tokens = tuple(rule.strip().split())
                        for token in tokens:
                            if not termre.match(token) and not nontermre.match(token):
                                raise SyntaxError(token)
                        rules[lhs].append(tokens)

                else:
                    raise SyntaxError(lhs)
            except Exception:
                print(line)
                raise

    return terminals, rules, next(iter(rules.keys()))


class Table:
    """
    Represent a immuable list of lines where the pointer may not be
    the first symbol of the rules with muable references to other
    tables.

    A Table is a node in a finite-state machine where transitions are
    symbols to read to move from one table to another.
    """

    count = 0  # used a uid generator

    def __init__(self):
        logger.warning(
            "Please instanciate %s via the %s.%s constructor.",
            type(self), type(self), self.init.__name__)

    @classmethod
    def init(cls, fsm, rules, init_lines):
        logger.disabled = True
        self = cls()
        logger.disabled = False
        self.lines = self._complete(rules, init_lines)

        # Reuse existing instances if found
        if flyweight := fsm.get(hash(self)):
            return flyweight
        else:
            fsm[hash(self)] = self

        # Handy unique id
        self.id = cls.count
        cls.count += 1

        # Inter-table references
        self.forward_links = {}  # one symbol to one table
        self.back_links = defaultdict(set)  # one symbol from many tables

        return self

    def __repr__(self):
        return f"T{self.id}"

    def __hash__(self):
        return hash(self.lines)

    def get_symbols(self):
        """ Set of all symbols that can be read from this table. """
        return {
            line.rule[line.index]
            for line in self.lines
            if not line.point_end
        }

    @staticmethod
    def _complete(rules, init_lines):
        """
        Explore every line that point to a non-terminal to add the
        corresponding rule recursively.
        """
        next_lines = init_lines.copy()
        known_lines = init_lines.copy()
        while next_lines:
            new_lines = set()
            for line in next_lines:
                if line.point_non_terminal:
                    rule_no = line.rule[line.index]
                    new_lines.update({
                        Line(rule_no, rule, 0)
                        for rule in rules[rule_no]
                    })

            new_lines.difference_update(known_lines)
            known_lines.update(new_lines)
            next_lines = new_lines

        return frozenset(known_lines)

    def __str__(self):
        froms = [
            f"T{table.id} {symbol} →"
            for symbol, tables in self.back_links.items()
            for table in tables                
        ]
        tos = [
            f"→ {symbol} T{table.id}"
            for symbol, table in self.forward_links.items()
        ]

        rls = list(globalrules)
        lines = sorted(self.lines, key=lambda line: rls.index(line.rule_no))
        rules = [str(line) for line in lines]


        lru = max(map(len, rules), default=0)
        lfr = max(map(len, froms), default=0)
        lto = max(map(len, tos), default=0) + 5
        tmpl = "{:>%d}│ {:<%d} │{:<%d}" % (lfr, lru, lto)
        with StringIO() as buffer:
            suffix_len = (lto + lru - 2 - len(str(self.id)))
            print(f"{' ' * lfr}Table {self.id}{' ' * suffix_len}", file=buffer)
            print(f"{' ' * lfr}┌─{'─' * lru}─┐{' ' * lto}", file=buffer)
            for fro, rule, to in zip_longest(froms, rules, tos, fillvalue=""):
                print(tmpl.format(fro, rule, to), file=buffer)
            print(f"{' ' * lfr}└─{'─' * lru}─┘{' ' * lto}", file=buffer)
            return buffer.getvalue()



def build_fsm(rules, start):
    """
    Compute the grammar FSM by discovering every table through
    symbol transition, complete the internal fsm structure.
    """
    fsm = {}

    def read(table, symbol):
        next_init = set()
        for line in table.lines:
            if line.point(symbol):
                next_init.add(line.shift())

        next_table = Table.init(fsm, rules, next_init)
        table.forward_links[symbol] = next_table
        next_table.back_links[symbol].add(table)

    Table.init(fsm, rules, {start})
    new_tb = set(fsm.keys())
    while new_tb:
        known_tb = set(fsm.keys())
        for table in map(fsm.get, new_tb):
            for symbol in table.get_symbols():
                read(table, symbol)
        new_tb = set(fsm.keys()) - known_tb

    return list(fsm.values())


def lr_derivation(tables):
    # (pop, read, push)
    transitions = []

    # shifts
    for table in tables:
        for token, next_table in table.forward_links.items():
            if termre.match(token):
                transitions.append(((table.id,), token, (table.id, next_table.id)))

    def reduce(tables, rule, index):
        if index >= 0:
            for prev_table in tables[0].back_links[rule[index]]:
                yield from reduce((prev_table, *tables), rule, index - 1)
        else:
            yield tables

    # reduces
    for table in tables:
        for line in table.lines:
            if line.point_end and line.rule_no != "s":
                for combo in reduce((table,), line.rule, line.index - 1):
                    transitions.append((tuple([tb.id for tb in combo]), "", (combo[0].id, combo[0].forward_links[line.rule_no].id)))
    return transitions



def main():
    from pprint import pprint
    if len(sys.argv) < 2:
        sys.exit("usage: python3.8 %s <BNF file>" % __file__)

    global globalrules
    terminals, rules, entryrule = load_grammar(sys.argv[1])
    globalrules = rules
    rules["s"] = [entryrule]
    nodes = build_fsm(rules, Line("s", (entryrule,), 0))

    pprint(terminals)
    pprint(rules)

    it = iter(list(map(str, nodes)))
    for a, b, c in zip_longest(it, it, it):
        filla, fillb, fillc = [" " * x.index("\n") if x else "" for x in [a, b, c]]
        for aa, bb, cc in zip_longest(*[x.splitlines(keepends=False) if x else "" for x in [a, b, c]]):
            print(aa or filla, bb or fillb, cc or fillc)
        print()
        print()

    for left in it:
        print(left)

    pprint(lr_derivation(nodes))

if __name__ == '__main__':
    main()


# aΣ(ε|a)(ε|a)abca|ba*Σ*a|b*(a|b)*(ab)*ab|cd(a|b)(c|d)a(b(c(d)))aa