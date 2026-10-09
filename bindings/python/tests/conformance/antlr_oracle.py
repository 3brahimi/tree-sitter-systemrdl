"""Reference parse of SystemRDL source with the systemrdl-compiler ANTLR grammar.

The compiler is imported from its source checkout (the test/systemrdl-compiler
submodule), so the reference is the exact grammar revision pinned there.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .tree_shape import Shape

COMPILER_DIR_ENV = "SYSTEMRDL_COMPILER_DIR"
DEFAULT_COMPILER_DIR = Path(__file__).resolve().parents[4] / "test" / "systemrdl-compiler"

#: Include directory the compiler's own tests pass as incl_search_paths.
INCLUDE_DIR = Path("test") / "rdl_src" / "incdir"

#: ANTLR rules that only choose between alternatives. The tree-sitter grammar
#: hides the matching rules (leading underscore), so both sides drop them.
TRANSPARENT_RULES = frozenset({
    "root_elem",
    "component_body_elem",
    "expr_primary",
    "literal",
    "udp_attr",
    "constraint_body_elem",
    "cast_width_expr",
    "struct_type",
    "prop_assignment_rhs",
})

#: Labelled alternatives (``#Label`` in SystemRDL.g4) map to their own node
#: names; ``NOP`` is the pass-through alternative of ``expr``.
LABELLED_RULES = {
    "UnaryExprContext": "unary_expr",
    "BinaryExprContext": "binary_expr",
    "TernaryExprContext": "ternary_expr",
    "NOPContext": None,
    "NumberIntContext": "number",
    "NumberHexContext": "number",
    "NumberVerilogContext": "number",
    "CastTypeContext": "cast_type",
    "CastWidthContext": "cast_width",
}


def compiler_dir() -> Path:
    return Path(os.environ.get(COMPILER_DIR_ENV, DEFAULT_COMPILER_DIR)).resolve()


@lru_cache(maxsize=1)
def _systemrdl():
    src = compiler_dir() / "src"
    if not (src / "systemrdl").is_dir():
        raise FileNotFoundError(
            f"systemrdl-compiler sources not found at {src}; run "
            f"`git submodule update --init` or set {COMPILER_DIR_ENV}"
        )
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    import systemrdl  # noqa: F401  (import for side effects: package init)
    from systemrdl.parser import SystemRDLLexer, SystemRDLParser

    return systemrdl, SystemRDLLexer.SystemRDLLexer, SystemRDLParser.SystemRDLParser


@dataclass(frozen=True)
class AntlrResult:
    error_count: int
    tokens: tuple[str, ...]
    shape: Shape | None


class PreprocessError(Exception):
    """The compiler's own preprocessor rejected the file."""


def preprocess_file(path: Path) -> str:
    """Run the compiler's Perl then Verilog preprocessor, as compile_file does."""
    systemrdl, _, _ = _systemrdl()
    from systemrdl.messages import RDLCompileError
    from systemrdl.preprocessor.perl_preprocessor import PerlPreprocessor
    from systemrdl.preprocessor.verilog_preprocessor import VerilogPreprocessor

    env = systemrdl.RDLCompiler(message_printer=_SilentPrinter()).env
    search_paths = [str(path.parent), str(compiler_dir() / INCLUDE_DIR)]
    try:
        text, seg_map = PerlPreprocessor(env, str(path), search_paths).preprocess()
        text, _ = VerilogPreprocessor(env, text, seg_map).preprocess()
    except RDLCompileError as exc:
        raise PreprocessError(str(exc)) from exc
    return text


def parse(text: str) -> AntlrResult:
    """Lex and parse *text* from rule ``root`` with the pure-Python ANTLR runtime."""
    _, lexer_cls, parser_cls = _systemrdl()
    import antlr4
    from antlr4.error.ErrorListener import ErrorListener

    class _Counter(ErrorListener):
        count = 0

        def syntaxError(self, *args):  # noqa: N802  (ANTLR callback name)
            _Counter.count += 1

    _Counter.count = 0
    lexer = lexer_cls(antlr4.InputStream(text))
    lexer.removeErrorListeners()
    lexer.addErrorListener(_Counter())
    stream = antlr4.CommonTokenStream(lexer)
    parser = parser_cls(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(_Counter())
    tree = parser.root()
    tokens = tuple(
        t.text for t in stream.tokens if t.type != antlr4.Token.EOF and t.channel == 0
    )
    shape = _shape(tree, parser_cls.ruleNames) if _Counter.count == 0 else None
    return AntlrResult(_Counter.count, tokens, shape)


def _shape(ctx, rule_names) -> Shape:
    from antlr4.tree.Tree import TerminalNode

    children: list[Shape] = []
    for child in ctx.getChildren():
        if isinstance(child, TerminalNode):
            continue
        sub = _shape(child, rule_names)
        name = _rule_name(child, rule_names)
        if name is None:
            children.extend(sub.children)
        else:
            children.append(Shape(name, sub.children))
    return Shape(_rule_name(ctx, rule_names) or "", tuple(children))


def _rule_name(ctx, rule_names) -> str | None:
    label = type(ctx).__name__
    if label in LABELLED_RULES:
        return LABELLED_RULES[label]
    name = rule_names[ctx.getRuleIndex()]
    return None if name in TRANSPARENT_RULES else name


class _SilentPrinter:
    """Swallow compiler messages; the caller only needs pass or fail."""

    def print_message(self, *args, **kwargs) -> None:
        pass
