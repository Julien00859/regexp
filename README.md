# Regexp

Just a toy repo to test stuff with regexp, expose a small
script that mimic `GNU/grep` using the best regexp engine
available.

	usage: regexp [-h] [-q] [-f] regexp files [files ...]

	positional arguments:
	  regexp           Pattern to use
	  files            Files to search

	optional arguments:
	  -h, --help       show this help message and exit
	  -q, --quiet      Don't output lines found
	  -f, --fullmatch  Match the pattern against a full line
