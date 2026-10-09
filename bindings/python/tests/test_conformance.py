"""The tree-sitter grammar must parse exactly like systemrdl-compiler's ANTLR grammar.

The reference is the compiler checked out at test/systemrdl-compiler (a git
submodule; override with SYSTEMRDL_COMPILER_DIR). For every input both parsers
must agree on acceptance, and on accepted input produce the same tokens and the
same tree of rule nodes. Without the submodule these tests are skipped, unless
REQUIRE_CONFORMANCE=1 (as in CI), where they fail instead.
"""

from __future__ import annotations

import os
import random
import zlib
from pathlib import Path

import pytest

from conformance import antlr_oracle
from conformance.compare import mismatch
from conformance.generators import (
    random_constraint_expression,
    random_expression,
    token_mutants,
)
from conformance.snippets import SNIPPETS

MUTANTS_PER_FILE = 20
RANDOM_EXPRESSIONS = 500
RANDOM_CONSTRAINTS = 500
SOURCE_DIRS = ("test", "examples")


def _source_files() -> list[Path]:
    root = antlr_oracle.compiler_dir()
    if not (root / "src" / "systemrdl").is_dir():
        message = (
            f"systemrdl-compiler not found at {root}; run "
            "`git submodule update --init` or set SYSTEMRDL_COMPILER_DIR"
        )
        if os.environ.get("REQUIRE_CONFORMANCE") == "1":
            raise RuntimeError(message)
        pytest.skip(message, allow_module_level=True)
    return sorted(f for d in SOURCE_DIRS for f in (root / d).rglob("*.rdl"))


SOURCE_FILES = _source_files()


def _file_id(path: Path) -> str:
    return path.relative_to(antlr_oracle.compiler_dir()).as_posix()


def _preprocessed(path: Path) -> str:
    try:
        return antlr_oracle.preprocess_file(path)
    except antlr_oracle.PreprocessError as exc:
        pytest.skip(f"the compiler's preprocessor rejects this file: {exc}")


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_file_id)
def test_compiler_source_file(path: Path) -> None:
    problem = mismatch(_preprocessed(path))
    assert problem is None, problem


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_file_id)
def test_token_mutants(path: Path) -> None:
    reference = antlr_oracle.parse(_preprocessed(path))
    if reference.error_count or not reference.tokens:
        pytest.skip("only valid, non-empty files are mutated")
    seed = zlib.crc32(_file_id(path).encode())
    failures = [
        f"{problem}\n  input: {text}"
        for text in token_mutants(reference.tokens, MUTANTS_PER_FILE, seed)
        if (problem := mismatch(text)) is not None
    ]
    assert not failures, "\n".join(failures[:3])


@pytest.mark.parametrize("text", SNIPPETS)
def test_snippet(text: str) -> None:
    problem = mismatch(text)
    assert problem is None, problem


def test_random_expressions() -> None:
    rng = random.Random(1)
    failures = []
    for _ in range(RANDOM_EXPRESSIONS):
        expression = random_expression(rng)
        for text in (f"addrmap top {{ p = {expression}; }};", f"addrmap top {{ r_t r @ {expression}; }};"):
            if (problem := mismatch(text)) is not None:
                failures.append(f"{problem}\n  input: {text}")
    assert not failures, "\n".join(failures[:3])


def test_random_constraint_expressions() -> None:
    rng = random.Random(7)
    failures = []
    for _ in range(RANDOM_CONSTRAINTS):
        text = f"constraint c {{ {random_constraint_expression(rng, rng.randint(1, 4))}; }};"
        if (problem := mismatch(text)) is not None:
            failures.append(f"{problem}\n  input: {text}")
    assert not failures, "\n".join(failures[:3])
