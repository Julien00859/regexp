import unittest
from .automatons import NDFA, DFA, DCFA, DCMFA
from .pattern import parse, IGNORE_CASE

class MatchCase(unittest.TestCase):
    def assertMatch(self, pattern, matchs, nomatchs, flags=0):
        automaton = parse(pattern, flags)
        for constructor in (NDFA, DFA.from_ndfa, DCFA.from_dfa, DCMFA.from_dcfa):
            automaton = constructor(automaton)
            for string in matchs:
                self.assertTrue(automaton.match(string),
                    "{} should match {}".format(automaton.__class__.__name__, string))
            for string in nomatchs:
                self.assertFalse(automaton.match(string),
                    "{} should not match {}".format(automaton.__class__.__name__, string))


class TestPattern(MatchCase):
    def test_single(self):
        self.assertMatch("a", ["a"], ["b"])

    def test_sigma(self):
        self.assertMatch("Σ", ["a", "b"], [""])

    def test_espilon(self):
        self.assertMatch("(ε|a)(ε|a)", ["", "a", "aa"], ["aaa"])

    def test_espace(self):
        self.assertMatch(r"\a", ["a"], ["", r"\a"])
        self.assertMatch(r"\*", ["*"], ["", r"\*"])
        self.assertMatch(r"\\", ["\\"], ["", "\\\\"])
        self.assertMatch(r"\\\\", ["\\\\"], ["", "\\"])

    def test_concat(self):
        self.assertMatch("abc", ["abc"], ["", "a", "ab", "bc", "c"])

    def test_alt(self):
        self.assertMatch("a|b", ["a", "b"], ["", "ab"])

    def test_kleene(self):
        self.assertMatch("a*", ["", "a", "aa", "aaa"], ["b"])

    def test_kleene_on_sigma(self):
        self.assertMatch("Σ*", ["", "a", "b", "aabbcaae"], [])

    def test_kleene_on_escape(self):
        self.assertMatch(r"\a*", ["", "a", "aa"], [r"\a"])

    def test_kleene_in_alt(self):
        self.assertMatch("a|b*", ["a", "", "b", "bb"], ["aa", "ab"])

    def test_kleene_on_alt(self):
        self.assertMatch("(a|b)*", ["", "a", "b", "aa", "bb", "ab", "ba", "aba", "bab"], [])

    def test_kleene_on_concat(self):
        self.assertMatch("(ab)*", ["", "ab", "abab"], ["a", "b", "aba", "bab"])

    def test_alt_of_concats(self):
        self.assertMatch("ab|cd", ["ab", "cd"], ["", "a", "b", "c", "d", "ac", "ad"])

    def test_concat_of_alts(self):
        self.assertMatch("(a|b)(c|d)", ["ac", "ad", "bc", "bd"], ["", "a", "b", "c", "d", "ca", "cb", "da", "db"])

    def test_nested_groups(self):
        self.assertMatch("a(b(c(d)))", ["abcd"], [])


class TestFlags(MatchCase):
    def test_ignore_case(self):
        self.assertMatch("a", ["a"], ["A"], flags=0)
        self.assertMatch("a", ["a", "A"], [], flags=IGNORE_CASE)
