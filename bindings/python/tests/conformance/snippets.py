"""Hand-picked SystemRDL snippets that stress the grammar's edges.

Each snippet is parsed by both sides; ANTLR decides whether it is valid, so
the list carries no expected results of its own.
"""

PROP = "addrmap top {{ {body} }};"
EXPR = "addrmap top {{ p = {expr}; }};"

EXPRESSIONS = [
    # precedence and associativity of every binary level
    "1 + 2 * 3", "1 * 2 + 3", "2 ** 3 ** 2", "1 - 2 - 3", "8 / 2 / 2", "7 % 4 * 2",
    "1 << 2 + 1", "1 + 2 << 1", "1 < 2 == 1", "1 == 2 < 3", "1 & 2 ^ 3 | 4",
    "1 | 2 ^ 3 & 4", "1 && 2 || 3", "1 || 2 && 3", "1 & 2 && 3 | 4",
    "a ? b : c ? d : e", "a ? b ? c : d : e", "1 + a ? 2 : 3", "a || b ? c : d",
    "1 ~^ 2", "1 ^~ 2", "1 >= 2", "1 <= 2", "1 != 2", "1 >> 2",
    # unary operators bind to a primary only
    "-1", "+1", "!a", "~a", "&a", "~&a", "|a", "~|a", "^a", "~^a", "^~a",
    "-a ** 2", "-(a + 1)", "- -1", "!!a", "-a.b", "~a->sw",
    # literals
    "0x1F", "0X1f_ff", "1_000", "8'hFF", "8'b1010_1010", "16'd65_535", "4'b2",
    "8'hG", "0x", "_1", "\"str\"", "\"a\\\"b\"", "\"a\\\\b\"", "\"a\\nb\"",
    "\"multi\nline\"", "true", "false", "rw", "wr", "r", "w", "na", "rw1", "w1",
    "rclr", "rset", "ruser", "woset", "woclr", "wot", "wzs", "wzc", "wzt", "wclr",
    "wset", "wuser", "compact", "regalign", "fullalign", "hw", "sw",
    "my_enum::val", "my_enum :: val",
    # casts
    "boolean'(1)", "bit'(1)", "longint'(1)", "8'(x)", "(4+4)'(x)", "x'(1)",
    "longint unsigned'(1)", "string'(1)",
    # concatenation, replication, array and struct literals
    "{a, b}", "{2{a}}", "{2{a, b}}", "{a}", "{}", "'{}", "'{1, 2}", "' {1}",
    "s'{}", "s'{a: 1, b: 2}", "s '{a: 1}", "s'{a: 1,}",
    # references
    "a.b.c", "a[0].b[1][2]", "a->sw", "a->rclr", "a->desc", "a.b->woset",
    "a->encode", "this", "\\rw", "\\reg.\\field",
]

SNIPPETS = [EXPR.format(expr=e) for e in EXPRESSIONS] + [
    # reserved words as identifiers and their escaped forms
    "reg r_t { field {} r; };",
    "reg r_t { field {} \\r; };",
    "reg reg {};",
    "reg \\reg {};",
    "reg r_t { field {} int; };",
    "reg r_t { field {} real; };",
    "reg r_t { field {} \\int; };",
    "reg r_t { field {} with; };",
    "reg r_t { field {} precedencetype; };",
    # component definitions and instances
    "addrmap top {};",
    "addrmap {} top;",
    "addrmap {};",
    "external addrmap top {} t;",
    "addrmap top {} external t;",
    "external addrmap {} t;",
    "internal reg {} r;",
    "addrmap top { reg_t r1, r2[4], r3[2][3], r4[7:0]; };",
    "addrmap top { reg_t r1 = 0 @ 0x10 += 4 %= 8; };",
    "addrmap top { reg_t r1 %= 8 @ 0x10; };",
    "addrmap top { external alias r1 reg_t r2; };",
    "addrmap top { alias r1 reg_t r2; };",
    "addrmap top { field_t #(.W(4), .R(1)) f; };",
    "reg r #(longint unsigned W = 4, string S = \"x\", bit B[] = '{1}) {};",
    "reg r #(accesstype A = rw, my_t M) {};",
    "reg r #() {};",
    "signal { } s;",
    "mem m {};",
    "regfile rf {} rfi[4] @ 0;",
    # property assignments
    "addrmap top { default sw = rw; };",
    "addrmap top { default posedge intr; };",
    "addrmap top { default encode = my_enum; };",
    "addrmap top { encode = my_enum; };",
    "addrmap top { a->encode = my_enum; };",
    "addrmap top { a->posedge intr; };",
    "addrmap top { nonsticky intr; };",
    "addrmap top { level intr; bothedge intr; negedge intr; };",
    "addrmap top { sw; hw = na; rclr; woset = true; };",
    "addrmap top { a.b[2]->desc = \"x\"; };",
    "addrmap top { a->sw = rw; };",
    "addrmap top { a->hw; };",
    "addrmap top { precedence = hw; };",
    "a->desc = \"root\";",
    "desc = \"root\";",
    "default name = \"x\";",
    # user-defined properties
    "property p { type = boolean; component = reg | field; };",
    "property p { type = longint unsigned[]; component = all; default = 1; };",
    "property p { type = ref; component = constraint; };",
    "property p { type = number; component = signal | mem; constraint = componentwidth; };",
    "property p { type = my_struct; component = addrmap; };",
    "property p { type = addrmap; component = regfile; };",
    "property p { };",
    "property p { type = string };",
    # enums
    "enum e { a; };",
    "enum e { a = 1; b = 2'h2 { name = \"B\"; desc = \"b\"; }; };",
    "enum e { };",
    "enum e { a { sw = rw; }; };",
    "enum e { a {}; };",
    # structs
    "struct s { boolean b; string st[]; my_t m; field f; };",
    "abstract struct s : base { longint unsigned x; };",
    "struct s {};",
    "struct s : base {};",
    # constraints
    "constraint c { x < 4; };",
    "constraint c { x == 4; y != 2; };",
    "constraint c { x + 1 < 4; };",
    "constraint c { x < y < z; };",
    "constraint c { x; };",
    "constraint c { x + 1; };",
    "constraint c { x = 4; };",
    "constraint c { this inside {1, 2, [4:7]}; };",
    "constraint c { a.b inside my_enum; };",
    "constraint c { this inside e; };",
    "constraint {} c1, c2;",
    "constraint c {} c1;",
    "constraint {};",
    "constraint c { x < 4 ? 1 : 2; };",
    "constraint c { x ? 1 : 2 < 3; };",
    "constraint c { (x < 4) == 1; };",
    # comments and whitespace
    "/* c */ addrmap top {}; // trailing",
    "addrmap top { /* nested /* not */ };",
    "// only a comment",
    "",
    "addrmap top {} \f;",
    ";",
    "addrmap top {}",
]
