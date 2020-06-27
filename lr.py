from collections import defaultdict, namedtuple
from itertools import zip_longest
from io import StringIO


START = "S"

Line = namedtuple("Line", ["rule_no", "rule", "index"])


rules = defaultdict(set)
with open("grammar.bnf") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        if line[0].isupper():
            rule_no, rule = line.split(" := ")
            if rule == "ε": rule = ""
            rules[rule_no].add(Line(rule_no, rule.replace(" ", ""), 0))


class Table:
    memoize = {}
    count = 0

    @classmethod
    def init(cls, init):
        self = cls()
        self.lines = set(init)

        lines = set(init)
        while True:
            new_lines = set()
            for line in lines:
                if (line.index < len(line.rule) and line.rule[line.index].isupper()):
                    rule_no = line.rule[line.index]
                    new_lines.update(rules[rule_no])

            new_lines.difference_update(self.lines)
            if not new_lines:
                break
            self.lines.update(new_lines)
            lines = new_lines
        self.lines = frozenset(self.lines)
        self.id = hash(self.lines)
        self.links = {}

        tb = Table.memoize.get(self.id)
        if tb:
            return tb
        self.humain_id = cls.count
        cls.count += 1
        self.back_links = defaultdict(set)
        cls.memoize[self.id] = self
        return self

    def all_symbols(self):
        symbols = set()
        for line in self.lines:
            if line.index < len(line.rule):
                symbols.add(line.rule[line.index])
        return symbols

    def read(self, symbol):
        next_init = set()
        for line in self.lines:
            if line.index < len(line.rule) and line.rule[line.index] == symbol:
                new_line = Line(line.rule_no, line.rule, line.index + 1)
                next_init.add(new_line)

        tb = Table.init(next_init)
        self.links[symbol] = tb.id
        tb.back_links[symbol].add(self)
        return tb

    def __str__(self):
        froms = [
            f"T{table.humain_id} {symbol} →"
            for symbol, tables in self.back_links.items()
            for table in tables                
        ]

        tos = [
            f"→ {symbol} T{Table.memoize[id].humain_id}"
            for symbol, id in self.links.items()
        ]

        rules = []
        for line in self.lines:
            dotted_rule = list(line.rule)
            dotted_rule[line.index:line.index] = '⋅'
            rules.append(f"{line.rule_no} → {''.join(dotted_rule)}")

        lru = max(map(len, rules), default=0)
        lfr = max(map(len, froms), default=0)
        lto = max(map(len, tos), default=0) + 5
        tmpl = "{:>%d}│ {:<%d} │{:<%d}" % (lfr, lru, lto)
        with StringIO() as buffer:
            suffix_len = (lto + lru - 2 - len(str(self.humain_id)))
            print(f"{' ' * lfr}Table {self.humain_id}{' ' * suffix_len}", file=buffer)
            print(f"{' ' * lfr}┌─{'─' * lru}─┐{' ' * lto}", file=buffer)
            for fro, rule, to in zip_longest(froms, rules, tos, fillvalue=""):
                print(tmpl.format(fro, rule, to), file=buffer)
            print(f"{' ' * lfr}└─{'─' * lru}─┘{' ' * lto}", file=buffer)
            return buffer.getvalue()

Table.init(rules[START])
new_ids = set(Table.memoize.keys())
while new_ids:
    known_ids = set(Table.memoize.keys())
    for table in map(Table.memoize.get, new_ids):
        for symbol in table.all_symbols():
            table.read(symbol)
    new_ids = set(Table.memoize.keys()) - known_ids

#for table in Table.memoize.values():
#    print(table)

it = iter(sorted(list(map(str, Table.memoize.values())), key=len))
for a, b, c, d in zip(it, it, it, it):
    filla, fillb, fillc, filld = [" " * x.index("\n") for x in [a, b, c, d]]
    for aa, bb, cc, dd in zip_longest(*[x.splitlines(keepends=False) for x in [a, b, c, d]]):
        print(aa or filla, bb or fillb, cc or fillc, dd or filld)
    print()
    print()
