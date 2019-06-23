"""Test utilities functions/methods"""

import unittest
import re
from collections import Counter
from contextlib import closing, redirect_stdout
from io import StringIO
from textwrap import dedent

from regexp import compile
from regexp.nodes import Node

class CommonTest(unittest.TestCase):
    def test_print_mesh(self):
        automaton = compile("ab*c")

        with closing(StringIO()) as buffer:
            with redirect_stdout(buffer):
                automaton.print_mesh()
            anonymized = re.sub(r"\([0-9]+\)", "(x)", buffer.getvalue())
            unspaced = re.sub(r" +", " ", anonymized)
            buffer_lines = Counter(unspaced.splitlines())
            testcase_lines = Counter([
                " --> (x)",
                "(x) Σ (x)",
                "(x) a (x)",
                "(x) Σ (x)",
                "(x) Σ (x)",
                "(x) b (x)",
                "(x) Σ (x)",
                "(x) c (x) -->"])
            self.assertEqual(buffer_lines, testcase_lines)

    def test_print_transitions(self):
        automaton = compile("ab*c")

        with closing(StringIO()) as buffer:
            with redirect_stdout(buffer):
                automaton.initial_node.print_transitions()
            anonymized = re.sub(r"\([0-9]+\)", "(x)", buffer.getvalue())
            unspaced = re.sub(r" +", " ", anonymized)
            buffer_lines = Counter(unspaced.splitlines())
            testcase_lines = Counter(["(x) a (x)", "(x) Σ (x)"])
            self.assertEqual(buffer_lines, testcase_lines)
