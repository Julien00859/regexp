#!/usr/bin/env python3

from argparse import ArgumentParser
from functools import partial
from os.path import isfile
from string import ascii_uppercase
from sys import exit as sys_exit
from .automatons import DCMFA, DCFA, DFA, NFA
from .pattern import IGNORE_CASE, expand

parser = ArgumentParser()
parser.add_argument("regexp", help="Pattern to use")
parser.add_argument("files", nargs='+', help="Files to search")
parser.add_argument("-q", "--quiet", dest="quiet", action="store_const", const=True, default=False,
                    help="Don't output lines found")
parser.add_argument("-x", "--fullmatch", dest="fullmatch", action="store_const", const=True, default=False,
                    help="Match the pattern against a full line")
parser.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True, default=False,
                    help="Debug mode, print generated automaton")
parser.add_argument("-i", "--ignore-case", action="store_const", const=IGNORE_CASE, default=0,
                    help="Ignore case distinctions")
args = parser.parse_args()

if not args.fullmatch:
    if not args.regexp.startswith("Σ*"):
        args.regexp = "Σ*%s" % args.regexp
    if not args.regexp.endswith("Σ*"):
        args.regexp = "%sΣ*" % args.regexp

automaton = args.regexp
print(expand(automaton))
for construct in (partial(NFA.from_extended_pattern, flags=args.ignore_case), DFA.from_ndfa, DCFA.from_dfa, DCMFA.from_dcfa):
    automaton = construct(automaton)
    if args.verbose:
        print(automaton.__doc__.strip().splitlines()[0])
        automaton.print_mesh()
        print()

found = False
for filepath in filter(isfile, args.files):
    with open(filepath) as fd:
        for lineno, line in enumerate(fd.readlines()):
            if automaton.match(line[:-1]):
                found = True
                if not args.quiet:
                    print(line, end="")

sys_exit(not found)

