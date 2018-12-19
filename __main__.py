#!/usr/bin/env python3

from argparse import ArgumentParser
from automaton import dcma, dca, da, nda

parser = ArgumentParser()
parser.add_argument("regexp")
parser.add_argument("files")
parser.add_argument("-q", dest="quiet", action="store_const", const=True, default=False)
parser.add_argument("-f", dest="fullmatch", action="store_const", const=True, default=False)
args = parser.parse_args()

if not args.fullmatch:
    if not args.regexp.startswith(".*"):
        args.regexp = ".*%s" % args.regexp
    if not args.regexp.endswith(".*"):
        args.regexp = "%s.*" % args.regexp

automaton = dcma.from_dca(dca.from_da(da.from_nda(nda.from_regexp(args.regexp))))
found = False
for filepath in args.files:
    with open(filepath) as fd:
        for line in fd.readlines():
            if automaton.match(line):
                found = True
                if not args.quiet:
                    print(line)

sys.exit(not found)

