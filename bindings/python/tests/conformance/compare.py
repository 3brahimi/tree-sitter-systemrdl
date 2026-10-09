"""Compare one SystemRDL text across the ANTLR reference and tree-sitter."""

from __future__ import annotations

from . import antlr_oracle, ts_side
from .tree_shape import first_difference


def mismatch(text: str) -> str | None:
    """Return why the two parsers disagree on *text*, or None if they agree.

    They agree when both reject it, or when both accept it with the same
    token sequence and the same tree of rule nodes.
    """
    ref = antlr_oracle.parse(text)
    got = ts_side.parse(text)
    ref_ok = ref.error_count == 0
    got_ok = not got.has_error
    if ref_ok != got_ok:
        return f"ANTLR {'accepts' if ref_ok else 'rejects'}, tree-sitter {'accepts' if got_ok else 'rejects'}"
    if not ref_ok:
        return None
    if ref.tokens != got.tokens:
        index = next(
            i for i, (a, b) in enumerate(zip(ref.tokens + ("<end>",), got.tokens + ("<end>",)))
            if a != b
        )
        return (
            f"token #{index} differs: ANTLR {ref.tokens[index:index + 3]} "
            f"vs tree-sitter {got.tokens[index:index + 3]}"
        )
    difference = first_difference(ref.shape, got.shape)
    if difference is not None:
        return f"tree differs at {difference}\n  ANTLR:       {ref.shape.sexp()}\n  tree-sitter: {got.shape.sexp()}"
    return None
