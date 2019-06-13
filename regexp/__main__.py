#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import isfile
from string import ascii_uppercase
from sys import exit as sys_exit
from .automatons import DCMA, DCA, DA, NDA

parser = ArgumentParser()
parser.add_argument("regexp", help="Pattern to use")
parser.add_argument("files", nargs='+', help="Files to search")
parser.add_argument("-q", "--quiet", dest="quiet", action="store_const", const=True, default=False,
                    help="Don't output lines found")
parser.add_argument("-f", "--fullmatch", dest="fullmatch", action="store_const", const=True, default=False,
                    help="Match the pattern against a full line")
parser.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True, default=False)
args = parser.parse_args()


def titlelize(string):
    padding = 1 if string[0] in ascii_uppercase else 0
    for letter in ascii_uppercase:
        string = string.replace(letter, " " + letter)
    return string[padding:]


if not args.fullmatch:
    if not args.regexp.startswith("Σ*"):
        args.regexp = "Σ*%s" % args.regexp
    if not args.regexp.endswith("Σ*"):
        args.regexp = "%sΣ*" % args.regexp

automaton = args.regexp
for construct in (NDA.from_pattern, DA.from_nda, DCA.from_da, DCMA.from_dca):
    automaton = construct(automaton)
    if args.verbose:
        print(titlelize(automaton.__class__.__name__))
        automaton.print_mesh()
        print()

found = False
for filepath in filter(isfile, args.files):
    with open(filepath) as fd:
        for lineno, line in enumerate(fd.readlines()):
            if automaton.match(line):
                found = True
                if not args.quiet:
                    print(line, end="")

sys_exit(not found)

