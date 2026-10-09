[![CI](https://github.com/3brahimi/tree-sitter-systemrdl/actions/workflows/ci.yml/badge.svg)](https://github.com/3brahimi/tree-sitter-systemrdl/actions/workflows/ci.yml)

# tree-sitter-systemrdl

[SystemRDL 2.0](http://accellera.org/downloads/standards/systemrdl) register description language grammar for [tree-sitter](https://github.com/tree-sitter/tree-sitter).

The grammar follows `SystemRDL.g4` from [systemrdl-compiler](https://github.com/SystemRDL/systemrdl-compiler): visible nodes carry the ANTLR rule names, keywords are reserved, and keywords can be used as names when escaped (`\rw`). The tests check that both parsers accept the same input and build the same tree.

## Python

```sh
pip install "tree-sitter-systemrdl @ git+https://github.com/3brahimi/tree-sitter-systemrdl"
```

```python
from tree_sitter import Language, Parser
import tree_sitter_systemrdl

parser = Parser(Language(tree_sitter_systemrdl.language()))
tree = parser.parse(b"addrmap top { reg { field {} f; } r; };")
print(tree.root_node)
```

Requires py-tree-sitter 0.25 or later (the parser uses ABI 15). Building needs only a C compiler: the generated parser in `src/` is committed.

The grammar parses preprocessed source. Run `` `include ``, `` `define `` and embedded Perl (`<% %>`) through a SystemRDL preprocessor first.

## Development

The parser is generated without Node.js, using the tree-sitter CLI's built-in JavaScript engine:

```sh
tree-sitter generate --js-runtime native
tree-sitter test
```

The Python tests compare every parse with systemrdl-compiler's ANTLR parser, pinned as a submodule:

```sh
git submodule update --init
uv venv && uv pip install '.[test]'
.venv/bin/python -m pytest bindings/python/tests
```
