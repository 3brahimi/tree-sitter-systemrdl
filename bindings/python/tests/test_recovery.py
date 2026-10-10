"""Editor-style error recovery: a typo must stay local, not swallow the file."""

from unittest import TestCase

from tree_sitter import Language, Node, Parser
import tree_sitter_systemrdl

REGISTERS = "\n".join(
    f'    reg {{ field {{ sw = rw; desc = "field {i}"; }} f[8] = 0; }} r{i} @ 0x{4 * i:x};'
    for i in range(10)
)
VALID = f'addrmap top {{\n    name = "top";\n{REGISTERS}\n}};\n'


def _errors(node: Node) -> list[Node]:
    if node.type == "ERROR" or node.is_missing:
        return [node]
    return [e for child in node.children for e in _errors(child)]


def _intact_definitions(node: Node, inside_error: bool = False) -> int:
    inside_error = inside_error or node.type == "ERROR"
    own = node.type == "component_def" and not inside_error and not node.has_error
    return int(own) + sum(_intact_definitions(c, inside_error) for c in node.children)


class TestRecovery(TestCase):
    def setUp(self):
        self.parser = Parser(Language(tree_sitter_systemrdl.language()))

    def parse(self, text: str) -> Node:
        return self.parser.parse(text.encode()).root_node

    def test_valid_baseline(self):
        root = self.parse(VALID)
        self.assertFalse(root.has_error)
        # the addrmap, 10 registers and their 10 fields
        self.assertEqual(_intact_definitions(root), 21)

    def test_unterminated_string_stays_local(self):
        # Strings may span lines (as in SystemRDL.g4), so an unclosed quote
        # runs to the next `"`. Recovery must resume there: only the broken
        # register and the next one may suffer, not the rest of the file.
        broken = VALID.replace('desc = "field 2";', 'desc = "field 2;', 1)
        root = self.parse(broken)
        errors = _errors(root)
        self.assertTrue(errors)
        largest = max(e.end_point[0] - e.start_point[0] + 1 for e in errors)
        self.assertEqual(largest, 1, "an unclosed quote swallowed later lines")
        # 21 definitions minus the addrmap, registers 2 and 3 and their fields
        self.assertGreaterEqual(_intact_definitions(root), 16)

    def test_missing_semicolon_is_a_missing_node(self):
        broken = VALID.replace("f[8] = 0; } r3", "f[8] = 0 } r3", 1)
        root = self.parse(broken)
        self.assertEqual([e.is_missing for e in _errors(root)], [True])
