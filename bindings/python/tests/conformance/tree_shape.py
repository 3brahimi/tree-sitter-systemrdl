"""Grammar-independent tree shape shared by the ANTLR and tree-sitter sides."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shape:
    """A rule node: its name and its rule-node children (tokens dropped)."""

    name: str
    children: tuple["Shape", ...] = ()

    def sexp(self) -> str:
        if not self.children:
            return f"({self.name})"
        inner = " ".join(child.sexp() for child in self.children)
        return f"({self.name} {inner})"


def first_difference(a: Shape, b: Shape, path: str = "") -> str | None:
    """Describe the first place two shapes differ, or None if equal."""
    here = f"{path}/{a.name}"
    if a.name != b.name:
        return f"{path}: {a.name} != {b.name}"
    for i, (x, y) in enumerate(zip(a.children, b.children)):
        diff = first_difference(x, y, f"{here}[{i}]")
        if diff is not None:
            return diff
    if len(a.children) != len(b.children):
        return (
            f"{here}: {len(a.children)} children "
            f"{[c.name for c in a.children]} != {len(b.children)} "
            f"{[c.name for c in b.children]}"
        )
    return None
