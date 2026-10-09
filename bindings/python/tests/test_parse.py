from unittest import TestCase

from tree_sitter import Language, Parser
import tree_sitter_systemrdl

SOURCE = b"""
addrmap top {
    reg {
        field { sw = rw; hw = r; } enable[0:0] = 0;
    } ctrl @ 0x0;
};
"""


class TestParse(TestCase):
    def setUp(self):
        self.language = Language(tree_sitter_systemrdl.language())
        self.parser = Parser(self.language)

    def test_language_metadata(self):
        self.assertEqual(self.language.name, "systemrdl")
        self.assertGreaterEqual(self.language.abi_version, 15)

    def test_parses_register_map_without_errors(self):
        tree = self.parser.parse(SOURCE)
        self.assertFalse(tree.root_node.has_error)
        self.assertEqual(tree.root_node.type, "root")

    def test_reports_syntax_errors(self):
        tree = self.parser.parse(b"addrmap top { reg { field f; } r }")
        self.assertTrue(tree.root_node.has_error)
