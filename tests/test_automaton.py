"""Test automaton methods"""


import unittest
from regexp import compile

class TestReadLazy(unittest.TestCase):
    def test_single_match(self):
        auto = compile("a")
        self.assertEqual(auto.read_lazy("a"), 1)

    def test_single_no_match(self):
        auto = compile("a")
        self.assertEqual(auto.read_lazy("b"), 0)

    def test_multiple(self):
        auto = compile("abcdef")
        self.assertEqual(auto.read_lazy("abcdef"), 6)

    def test_kleene(self):
        auto = compile("ab*")
        self.assertEqual(auto.read_lazy("abbbbbb"), 1)


class TestReadGreedy(unittest.TestCase):
    def test_single_match(self):
        auto = compile("a")
        self.assertEqual(auto.read_greedy("a"), 1)

    def test_single_no_match(self):
        auto = compile("a")
        self.assertEqual(auto.read_greedy("b"), 0)

    def test_multiple(self):
        auto = compile("abcdef")
        self.assertEqual(auto.read_greedy("abcdef"), 6)

    def test_kleene(self):
        auto = compile("ab*")
        self.assertEqual(auto.read_greedy("abbbbbb"), 7)
