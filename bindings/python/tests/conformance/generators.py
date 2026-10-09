"""Deterministic input generators for the conformance tests."""

from __future__ import annotations

import random
from collections.abc import Iterator, Sequence

BINARY_OPS = (
    "**", "*", "/", "%", "+", "-", "<<", ">>", "<", "<=", ">", ">=", "==", "!=",
    "&", "^", "~^", "^~", "|", "&&", "||",
)
UNARY_OPS = ("+", "-", "!", "~", "&", "~&", "|", "~|", "^", "~^", "^~")
ATOMS = (
    "a", "1", "0x1F", "8'hFF", '"s"', "true", "rw", "hw", "e::v", "a.b[1]",
    "a->sw", "a->desc", "s'{m: 1}", "'{1, 2}", "{a, b}", "{2{a}}",
    "boolean'(a)", "4'(a)",
)
CONSTRAINT_OPS = ("<", "==", "&&", "||", "&", "|", "+", "*", "?:")
MUTATIONS = ("delete", "duplicate", "swap", "replace")


def token_mutants(tokens: Sequence[str], count: int, seed: int) -> Iterator[str]:
    """Yield *count* copies of *tokens*, each with one token-level edit."""
    rng = random.Random(seed)
    for _ in range(count):
        edited = list(tokens)
        i = rng.randrange(len(edited))
        mutation = rng.choice(MUTATIONS)
        if mutation == "delete":
            del edited[i]
        elif mutation == "duplicate":
            edited.insert(i, edited[i])
        elif mutation == "swap" and i + 1 < len(edited):
            edited[i], edited[i + 1] = edited[i + 1], edited[i]
        else:
            edited[i] = rng.choice(tokens)
        yield " ".join(edited)


def random_expression(rng: random.Random, depth: int = 4) -> str:
    """A random expression over every operator and primary form."""
    roll = rng.random()
    if depth <= 0 or roll < 0.3:
        atom = rng.choice(ATOMS)
        return f"{rng.choice(UNARY_OPS)}{atom}" if rng.random() < 0.15 else atom
    if roll < 0.75:
        return f"{random_expression(rng, depth - 1)} {rng.choice(BINARY_OPS)} {random_expression(rng, depth - 1)}"
    if roll < 0.85:
        return (
            f"{random_expression(rng, depth - 1)} ? {random_expression(rng, depth - 1)}"
            f" : {random_expression(rng, depth - 1)}"
        )
    if roll < 0.95:
        return f"({random_expression(rng, depth - 1)})"
    return f"{rng.choice(UNARY_OPS)}({random_expression(rng, depth - 1)})"


def random_constraint_expression(rng: random.Random, operators: int) -> str:
    """A flat chain of comparison, logic and arithmetic operators."""
    tokens = ["a"]
    for _ in range(operators):
        op = rng.choice(CONSTRAINT_OPS)
        tokens += ["?", "b", ":", "c"] if op == "?:" else [op, rng.choice("xyz")]
    return " ".join(tokens)
