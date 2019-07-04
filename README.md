# Regexp

Just a toy repo to test stuff with regexp, expose a small script that
mimic `GNU/grep` using the best regexp engine available.

## Grammar

Available sequences are:

* `()`, group. Used to group expression together, create sub-patterns.
* `|`, union. Used for choices, match specifically one group out of
the available choices.
* `*`, kleene star. Used for repetition, match the last character or
group zero, one or multiple times.
* `Σ`, sigma. Used as catchall, match any character.
* `ε`, epsilon. Used as bypass, read nothing.
* `\`, escape. Used to use the next character as-is.

Available *extended* sequences are:
* `[abc]`, expand to `(a|b|c)`
* `[1-5]`, expand to `(1|2|3|4|5)`
* `\s`, expand to `( |\n|\r|\t)`
* `\d`, expand to `[0-9]`
* `\w`, expand to `[a-zA-Z0-9_]`

Not available sequences are:

* `+`, match one or multiple times. Can be achieved by prefixing the
character to a kleene: `aa*`.
* `?`, match zero or one time. Can be achieved using epsilon: `(a|ε)`
* `{n}`, match exactly `n` times. Can be achieved by concatenate `n`
times the group or character.
* `{n,m}`, match between `n` and `m` times. Can be achieved with `n`
concatenations and `m-n` epsilon unions.

Example: `0b(0|1)(0|1)*` matches python binary numbers.

## Usage

	usage: regexp [-h] [-q] [-x] regexp files [files ...]

	positional arguments:
	  regexp           Pattern to use
	  files            Files to search

	optional arguments:
	  -h, --help       show this help message and exit
	  -q, --quiet      Don't output lines found
	  -x, --fullmatch  Match the pattern against a full line
