"""tree-sitter side of the conformance check."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from tree_sitter import Language, Node, Parser

import tree_sitter_systemrdl
from .tree_shape import Shape

#: Named nodes that are tokens in ANTLR (no rule context of their own).
TOKEN_NODES = frozenset({"id", "comment"})


@dataclass(frozen=True)
class TsResult:
    has_error: bool
    tokens: tuple[str, ...]
    shape: Shape | None


@lru_cache(maxsize=1)
def _parser() -> Parser:
    return Parser(Language(tree_sitter_systemrdl.language()))


def parse(text: str) -> TsResult:
    source = text.encode()
    root = _parser().parse(source).root_node
    tokens = tuple(_leaves(root, source))
    shape = None if root.has_error else Shape("root", _children(root))
    return TsResult(root.has_error, tokens, shape)


def _children(node: Node) -> tuple[Shape, ...]:
    out = []
    for child in node.named_children:
        if child.type in TOKEN_NODES:
            continue
        out.append(Shape(child.type, _children(child)))
    return tuple(out)


def _leaves(node: Node, source: bytes):
    if node.type == "comment":
        return
    if node.child_count == 0:
        if node.end_byte > node.start_byte:
            yield source[node.start_byte:node.end_byte].decode()
        return
    for child in node.children:
        yield from _leaves(child, source)
