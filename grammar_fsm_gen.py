#!/usr/bin/env python3

import logging
import sys
from collections import defaultdict
from itertools import zip_longest
from string import ascii_uppercase
from operator import itemgetter
from io import StringIO


logger = logging.getLogger("regexp")
logger.addHandler(logging.NullHandler())


class Line(tuple):
    """
    A Line is a immuable instanciation of a grammar rule at a precise
    point. A point is where the current parsing stands within the rule.

    A symbol is either a terminal (a character) or a non-terminal (a rule_no)
    """
    __slots__ = []
    def __new__(cls, rule_no, rule, index):
        assert index <= len(rule)
        return tuple.__new__(cls, (rule_no, rule, index))

    rule_no = property(itemgetter(0))
    rule = property(itemgetter(1))
    index = property(itemgetter(2))

    @property
    def point_terminal(self):
        return not self.point_end and self.rule[self.index] not in ascii_uppercase

    @property
    def point_non_terminal(self):
        return not self.point_end and self.rule[self.index] in ascii_uppercase

    @property
    def point_end(self):
        return self.index == len(self.rule)

    def point(self, symbol):
        return not self.point_end and self.rule[self.index] == symbol

    def __str__(self):
        dotted_rule = list(self.rule)
        dotted_rule[self.index:self.index] = '⋅'
        return f"{self.rule_no} → {''.join(dotted_rule)}"


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
    def init(cls, grammar, init_lines):
        logger.disabled = True
        self = cls()
        logger.disabled = False
        self.grammar = grammar
        self.lines = self._complete(grammar.rules, init_lines)

        # Reuse existing instances if found
        if flyweight := self.grammar.fsm.get(hash(self)):
            return flyweight
        else:
            self.grammar.fsm[hash(self)] = self

        # Handy unique id
        self.id = cls.count
        cls.count += 1

        # Inter-table references
        self.forward_links = {}  # one symbol to one table
        self.back_links = defaultdict(set)  # one symbol from many tables

        return self

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
                    new_lines.update(rules[rule_no])

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
        rules = [str(line) for line in self.lines]

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


class Grammar:
    def __init__(self, rules):
        start = next(iter(rules))
        if (len(rules[start]) == 1
            and len(next(iter(rules[start])).rule) != 1):
            self.rules = rules
        else:
            logger.warning("The grammar doesn't seem to be completed, doing it myself.")
            if start + "'" in rules:
                raise SyntaxError("Cannot complete the grammar as rule {start}' exists already.")
            self.rules = {start + "'": Line(start + "'", start, 0)}
            self.rules.update(rules)
        self.fsm = {}  # handy to keep tracks of all tables
                       # in the FSM related to this grammar

    @classmethod
    def from_file(cls, filepath):
        rules = defaultdict(set)
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if not line[0].isupper():
                    continue

                rule_no, rule = line.split(" := ")
                rule = rule.replace(" ", "").replace("ε", "")
                line = Line(rule_no, rule, 0)
                rules[rule_no].add(line)

        return cls(rules)

    def compute_fsm(self):
        """
        Compute the grammar FSM by discovering every table through
        symbol transition, complete the internal fsm structure.
        """
        def read(table, symbol):
            next_init = set()
            for line in table.lines:
                if line.point(symbol):
                    new_line = Line(line.rule_no, line.rule, line.index + 1)
                    next_init.add(new_line)

            next_table = Table.init(self, next_init)
            table.forward_links[symbol] = next_table
            next_table.back_links[symbol].add(table)

        Table.init(self, {next(iter(self.rules.values()))})
        new_tb = set(self.fsm.keys())
        while new_tb:
            known_tb = set(self.fsm.keys())
            for table in map(self.fsm.get, new_tb):
                for symbol in table.get_symbols():
                    read(table, symbol)
            new_tb = set(self.fsm.keys()) - known_tb
    

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3.8 %s <BNF file>" % __file__)

    g = Grammar.from_file(sys.argv[1])
    g.compute_fsm()

    if len(g.fsm) < 4:
        for tb in g.fsm.values():
            print(tb)
        sys.exit()

    it = iter(sorted(list(map(str, g.fsm.values())), key=len))
    for a, b, c, d in zip(it, it, it, it):
        filla, fillb, fillc, filld = [" " * x.index("\n") for x in [a, b, c, d]]
        for aa, bb, cc, dd in zip_longest(*[x.splitlines(keepends=False) for x in [a, b, c, d]]):
            print(aa or filla, bb or fillb, cc or fillc, dd or filld)
        print()
        print()

if __name__ == '__main__':
    main()
