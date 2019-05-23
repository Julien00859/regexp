#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import isfile
from sys import exit as sys_exit
from automatons import DCMA, DCA, DA, NDA

parser = ArgumentParser()
parser.add_argument("regexp", help="Pattern to use")
parser.add_argument("files", nargs='+', help="Files to search")
parser.add_argument("-q", "--quiet", dest="quiet", action="store_const", const=True, default=False,
                    help="Don't output lines found")
parser.add_argument("-f", "--fullmatch", dest="fullmatch", action="store_const", const=True, default=False,
                    help="Match the pattern against a full line")
args = parser.parse_args()

if not args.fullmatch:
    if not args.regexp.startswith("Σ*"):
        args.regexp = "Σ*%s" % args.regexp
    if not args.regexp.endswith("Σ*"):
        args.regexp = "%sΣ*" % args.regexp

automaton = NDA.from_pattern(args.regexp)
try:
    automaton = DA.from_nda(automaton)
    automaton = DCA.from_da(automaton)
    automaton = DCMA.from_dca(automaton)
except NotImplementedError:
    pass

found = False
for filepath in filter(isfile, args.files):
    with open(filepath) as fd:
        for lineno, line in enumerate(fd.readlines()):
            if automaton.match(line):
                found = True
                if not args.quiet:
                    print(line, end="")

sys_exit(not found)

