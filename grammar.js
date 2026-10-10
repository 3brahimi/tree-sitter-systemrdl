/**
 * @file SystemRDL 2.0 grammar for tree-sitter
 * @license MIT
 *
 * Mirrors SystemRDL.g4 from systemrdl-compiler (the reference parser): every
 * visible node is named after the ANTLR rule (or labelled alternative) it
 * matches. Rules that only choose between alternatives in SystemRDL.g4
 * (root_elem, component_body_elem, expr_primary, literal, udp_attr,
 * constraint_body_elem, cast_width_expr, struct_type, prop_assignment_rhs, and
 * the `expr` pass-through) are hidden here with a leading underscore.
 */

// Binding strength of SystemRDL.g4's `expr` alternatives, loosest first.
const PREC = {
  ternary: 1,
  bor: 2,
  band: 3,
  or: 4,
  xor: 5,
  and: 6,
  equality: 7,
  relational: 8,
  shift: 9,
  additive: 10,
  multiplicative: 11,
  exponent: 12,
};

const RELATIONAL_OPS = ["<", "<=", ">", ">="];
const EQUALITY_OPS = ["==", "!="];

// SystemRDL.g4 `expr` binary alternatives: [precedence, operators].
const BINARY_LEVELS = [
  [PREC.exponent, ["**"]],
  [PREC.multiplicative, ["*", "/", "%"]],
  [PREC.additive, ["+", "-"]],
  [PREC.shift, ["<<", ">>"]],
  [PREC.relational, RELATIONAL_OPS],
  [PREC.equality, EQUALITY_OPS],
  [PREC.and, ["&"]],
  [PREC.xor, ["^", "~^", "^~"]],
  [PREC.or, ["|"]],
  [PREC.band, ["&&"]],
  [PREC.bor, ["||"]],
];

// The same levels by name, loosest first, for the layered expression copies.
const LAYERS = [
  ["bor", ["||"]],
  ["band", ["&&"]],
  ["or", ["|"]],
  ["xor", ["^", "~^", "^~"]],
  ["and", ["&"]],
  ["equality", EQUALITY_OPS],
  ["relational", RELATIONAL_OPS],
  ["shift", ["<<", ">>"]],
  ["additive", ["+", "-"]],
  ["multiplicative", ["*", "/", "%"]],
  ["exponent", ["**"]],
];

// Every keyword the ANTLR lexer defines, including the Annex D reserved words.
// The ANTLR lexer never produces an ID for these, so they are reserved here.
const KEYWORDS = [
  "boolean",
  "bit",
  "longint",
  "unsigned",
  "string",
  "accesstype",
  "addressingtype",
  "onreadtype",
  "onwritetype",
  "alias",
  "external",
  "internal",
  "addrmap",
  "regfile",
  "reg",
  "field",
  "mem",
  "signal",
  "true",
  "false",
  "na",
  "rw",
  "wr",
  "r",
  "w",
  "rw1",
  "w1",
  "rclr",
  "rset",
  "ruser",
  "woset",
  "woclr",
  "wot",
  "wzs",
  "wzc",
  "wzt",
  "wclr",
  "wset",
  "wuser",
  "compact",
  "regalign",
  "fullalign",
  "hw",
  "sw",
  "posedge",
  "negedge",
  "bothedge",
  "level",
  "nonsticky",
  "abstract",
  "all",
  "component",
  "componentwidth",
  "constraint",
  "default",
  "enum",
  "encode",
  "inside",
  "number",
  "property",
  "ref",
  "struct",
  "this",
  "type",
  "alternate",
  "byte",
  "int",
  "precedencetype",
  "real",
  "shortint",
  "shortreal",
  "signed",
  "with",
  "within",
];

/** One or more `rule`, separated by `separator`. */
function sep1(separator, rule) {
  return seq(rule, repeat(seq(separator, rule)));
}

/** Left-associative binary alternatives over `operand`, one per level. */
function binaryLevels(levels, operand) {
  return choice(
    ...levels.map(([precedence, operators]) =>
      prec.left(
        precedence,
        seq(
          field("left", operand),
          field(
            "operator",
            operators.length === 1 ? operators[0] : choice(...operators),
          ),
          field("right", operand),
        ),
      ),
    ),
  );
}

/** Right-associative `condition ? consequence : alternative`. */
function ternary(condition, consequence, alternative) {
  return prec.right(
    PREC.ternary,
    seq(
      field("condition", condition),
      "?",
      field("consequence", consequence),
      ":",
      field("alternative", alternative),
    ),
  );
}

/**
 * A precedence-free copy of SystemRDL.g4's `expr` written as one rule per
 * level (`_<prefix>_<level>`), aliased to binary_expr and ternary_expr. With
 * no static precedence to cut paths short, GLR can follow every split of a
 * constraint comparison. Levels named in `skip` are left out.
 */
function layeredExpr(prefix, skip = []) {
  const layers = LAYERS.filter(([layer]) => !skip.includes(layer));
  const name = (layer) => `_${prefix}_${layer}`;
  const top = name("ternary");
  const rules = {
    [top]: ($) =>
      choice(alias($[`${top}_op`], $.ternary_expr), $[name(layers[0][0])]),
    [`${top}_op`]: ($) =>
      seq(
        field("condition", $[name(layers[0][0])]),
        "?",
        field("consequence", $._expr),
        ":",
        field("alternative", $[top]),
      ),
    [name("unary")]: ($) => choice($.unary_expr, $._expr_primary),
  };
  layers.forEach(([layer, operators], i) => {
    const next = i + 1 < layers.length ? name(layers[i + 1][0]) : name("unary");
    rules[name(layer)] = ($) =>
      choice(alias($[`${name(layer)}_op`], $.binary_expr), $[next]);
    rules[`${name(layer)}_op`] = ($) =>
      seq(
        field("left", $[name(layer)]),
        field(
          "operator",
          operators.length === 1 ? operators[0] : choice(...operators),
        ),
        field("right", $[next]),
      );
  });
  return rules;
}

export default grammar({
  name: "systemrdl",

  word: ($) => $.id,

  extras: ($) => [/[ \t\r\n]/, $.comment],

  reserved: {
    global: (_) => KEYWORDS,
  },

  // Constraint comparisons: GLR keeps every candidate split alive until the
  // statement ends (see constr_relational).
  conflicts: ($) => [
    [$._cl_equality_op, $._cl_relational_op],
    [$._cl_and_op, $._cl_equality_op],
    [$._cl_equality, $._cl_relational_op],
    [$._cl_and, $._cl_equality_op],
  ],

  rules: {
    root: ($) => repeat(seq($._root_elem, ";")),

    _root_elem: ($) =>
      choice(
        $.component_def,
        $.enum_def,
        $.udp_def,
        $.struct_def,
        $.constraint_def,
        $.explicit_component_inst,
        $.local_property_assignment,
        $.dynamic_property_assignment,
        $._annex_d_reserved,
      ),

    // -------------------------------------------------------------------------
    // Components

    component_def: ($) =>
      choice(
        seq(
          $.component_named_def,
          optional(
            choice(
              seq($.component_inst_type, $.component_insts),
              $.component_insts,
            ),
          ),
        ),
        seq(
          $.component_anon_def,
          choice(
            seq($.component_inst_type, $.component_insts),
            $.component_insts,
          ),
        ),
        seq($.component_inst_type, $.component_named_def, $.component_insts),
        seq($.component_inst_type, $.component_anon_def, $.component_insts),
      ),

    explicit_component_inst: ($) =>
      seq(
        optional($.component_inst_type),
        optional($.component_inst_alias),
        field("type", $.id),
        $.component_insts,
      ),

    component_inst_alias: ($) => seq("alias", $.id),

    component_named_def: ($) =>
      seq(
        $.component_type,
        field("name", $.id),
        optional($.param_def),
        $.component_body,
      ),

    component_anon_def: ($) => seq($.component_type, $.component_body),

    component_body: ($) =>
      seq("{", repeat(seq($._component_body_elem, ";")), "}"),

    _component_body_elem: ($) =>
      choice(
        $.component_def,
        $.enum_def,
        $.struct_def,
        $.constraint_def,
        $.explicit_component_inst,
        $.local_property_assignment,
        $.dynamic_property_assignment,
      ),

    component_insts: ($) =>
      seq(optional($.param_inst), sep1(",", $.component_inst)),

    component_inst: ($) =>
      seq(
        field("name", $.id),
        optional(choice(repeat1($.array_suffix), $.range_suffix)),
        optional($.field_inst_reset),
        optional($.inst_addr_fixed),
        optional($.inst_addr_stride),
        optional($.inst_addr_align),
      ),

    field_inst_reset: ($) => seq("=", $._expr),
    inst_addr_fixed: ($) => seq("@", $._expr),
    inst_addr_stride: ($) => seq("+=", $._expr),
    inst_addr_align: ($) => seq("%=", $._expr),

    component_inst_type: (_) => choice("external", "internal"),

    component_type: ($) => choice($.component_type_primary, "signal"),

    component_type_primary: (_) =>
      choice("addrmap", "regfile", "reg", "field", "mem"),

    // -------------------------------------------------------------------------
    // Parameters

    param_def: ($) => seq("#", "(", sep1(",", $.param_def_elem), ")"),

    param_def_elem: ($) =>
      seq(
        $.data_type,
        field("name", $.id),
        optional($.array_type_suffix),
        optional(seq("=", $._expr)),
      ),

    param_inst: ($) => seq("#", "(", sep1(",", $.param_assignment), ")"),

    param_assignment: ($) => seq(".", field("name", $.id), "(", $._expr, ")"),

    // -------------------------------------------------------------------------
    // Expressions

    _expr: ($) =>
      choice($.unary_expr, $.binary_expr, $.ternary_expr, $._expr_primary),

    unary_expr: ($) =>
      seq(
        field(
          "operator",
          choice("+", "-", "!", "~", "&", "~&", "|", "~|", "^", "~^", "^~"),
        ),
        field("operand", $._expr_primary),
      ),

    binary_expr: ($) => binaryLevels(BINARY_LEVELS, $._expr),

    ternary_expr: ($) => ternary($._expr, $._expr, $._expr),

    _expr_primary: ($) =>
      choice(
        $._literal,
        $.concatenate,
        $.replicate,
        $.paren_expr,
        $.cast_type,
        $.cast_width,
        $.prop_ref,
        $.instance_ref,
        $.struct_literal,
        $.array_literal,
      ),

    concatenate: ($) => seq("{", sep1(",", $._expr), "}"),

    replicate: ($) => seq("{", $._expr, $.concatenate, "}"),

    paren_expr: ($) => seq("(", $._expr, ")"),

    cast_type: ($) =>
      seq(
        field("type", choice("boolean", "bit", "longint")),
        "'",
        "(",
        $._expr,
        ")",
      ),

    cast_width: ($) =>
      seq(
        field("width", choice($._literal, $.paren_expr)),
        "'",
        "(",
        $._expr,
        ")",
      ),

    // -------------------------------------------------------------------------
    // Array and range

    range_suffix: ($) => seq("[", $._expr, ":", $._expr, "]"),
    array_suffix: ($) => seq("[", $._expr, "]"),
    array_type_suffix: (_) => seq("[", "]"),

    // -------------------------------------------------------------------------
    // Data types

    data_type: ($) =>
      choice(
        $.basic_data_type,
        "accesstype",
        "addressingtype",
        "onreadtype",
        "onwritetype",
      ),

    basic_data_type: ($) =>
      choice(
        seq(choice("bit", "longint"), optional("unsigned")),
        "string",
        "boolean",
        $.id,
      ),

    // -------------------------------------------------------------------------
    // Literals

    _literal: ($) =>
      choice(
        $.number,
        $.string_literal,
        $.boolean_literal,
        $.accesstype_literal,
        $.onreadtype_literal,
        $.onwritetype_literal,
        $.addressingtype_literal,
        $.precedencetype_literal,
        $.enum_literal,
      ),

    // INT | HEX_INT | VLOG_INT
    number: (_) =>
      token(
        choice(
          /[0-9][0-9_]*/,
          /0[xX][0-9a-fA-F][0-9a-fA-F_]*/,
          /[0-9]+'[bB][01][01_]*/,
          /[0-9]+'[dD][0-9][0-9_]*/,
          /[0-9]+'[hH][0-9a-fA-F][0-9a-fA-F_]*/,
        ),
      ),

    // STRING: only \" and \\ are escapes; a backslash before any other
    // character is an error, as in SystemRDL.g4. The pieces are immediate
    // tokens, not one big token, so an unclosed quote stays a local error
    // instead of pairing with a later `"` and flipping the rest of the file.
    string_literal: (_) =>
      seq(
        '"',
        repeat(
          choice(
            token.immediate(prec(1, /[^"\\]+/)),
            token.immediate('\\"'),
            token.immediate("\\\\"),
          ),
        ),
        token.immediate('"'),
      ),

    boolean_literal: (_) => choice("true", "false"),

    array_literal: ($) => seq("'", "{", optional(sep1(",", $._expr)), "}"),

    struct_literal: ($) =>
      seq(field("type", $.id), "'", "{", optional(sep1(",", $.struct_kv)), "}"),

    struct_kv: ($) => seq(field("member", $.id), ":", $._expr),

    enum_literal: ($) => seq(field("enum", $.id), "::", field("member", $.id)),

    accesstype_literal: (_) => choice("na", "rw", "wr", "r", "w", "rw1", "w1"),
    onreadtype_literal: (_) => choice("rclr", "rset", "ruser"),
    onwritetype_literal: (_) =>
      choice(
        "woset",
        "woclr",
        "wot",
        "wzs",
        "wzc",
        "wzt",
        "wclr",
        "wset",
        "wuser",
      ),
    addressingtype_literal: (_) => choice("compact", "regalign", "fullalign"),
    precedencetype_literal: (_) => choice("hw", "sw"),

    // -------------------------------------------------------------------------
    // References

    instance_ref: ($) => sep1(".", $.instance_ref_element),

    instance_ref_element: ($) =>
      seq(field("name", $.id), repeat($.array_suffix)),

    prop_ref: ($) =>
      seq(
        $.instance_ref,
        "->",
        choice($.prop_keyword, field("property", $.id)),
      ),

    // -------------------------------------------------------------------------
    // Properties

    local_property_assignment: ($) =>
      seq(
        optional("default"),
        choice($.normal_prop_assign, $.encode_prop_assign, $.prop_mod_assign),
      ),

    dynamic_property_assignment: ($) =>
      seq(
        $.instance_ref,
        "->",
        choice($.normal_prop_assign, $.encode_prop_assign),
      ),

    normal_prop_assign: ($) =>
      seq(
        choice($.prop_keyword, field("property", $.id)),
        optional(seq("=", $._expr)),
      ),

    encode_prop_assign: ($) => seq("encode", "=", field("enum", $.id)),

    prop_mod_assign: ($) => seq($.prop_mod, field("property", $.id)),

    prop_keyword: (_) => choice("sw", "hw", "rclr", "rset", "woclr", "woset"),

    prop_mod: (_) =>
      choice("posedge", "negedge", "bothedge", "level", "nonsticky"),

    // -------------------------------------------------------------------------
    // User-defined properties

    udp_def: ($) =>
      seq(
        "property",
        field("name", $.id),
        "{",
        repeat1(seq($._udp_attr, ";")),
        "}",
      ),

    _udp_attr: ($) =>
      choice($.udp_type, $.udp_usage, $.udp_default, $.udp_constraint),

    udp_type: ($) =>
      seq("type", "=", $.udp_data_type, optional($.array_type_suffix)),

    udp_data_type: ($) =>
      choice($.component_type_primary, "ref", "number", $.basic_data_type),

    udp_usage: ($) => seq("component", "=", sep1("|", $.udp_comp_type)),

    udp_comp_type: ($) => choice($.component_type, "constraint", "all"),

    udp_default: ($) => seq("default", "=", $._expr),

    udp_constraint: (_) => seq("constraint", "=", "componentwidth"),

    // -------------------------------------------------------------------------
    // User-defined enumerations

    enum_def: ($) =>
      seq(
        "enum",
        field("name", $.id),
        "{",
        repeat1(seq($.enum_entry, ";")),
        "}",
      ),

    enum_entry: ($) =>
      seq(
        field("name", $.id),
        optional(seq("=", $._expr)),
        optional(seq("{", repeat(seq($.enum_prop_assign, ";")), "}")),
      ),

    enum_prop_assign: ($) => seq(field("property", $.id), "=", $._expr),

    // -------------------------------------------------------------------------
    // User-defined structs

    struct_def: ($) =>
      seq(
        optional("abstract"),
        "struct",
        field("name", $.id),
        optional(seq(":", field("base", $.id))),
        "{",
        repeat(seq($.struct_elem, ";")),
        "}",
      ),

    struct_elem: ($) =>
      seq(
        choice($.data_type, $.component_type),
        field("name", $.id),
        optional($.array_type_suffix),
      ),

    // -------------------------------------------------------------------------
    // Constraints

    constraint_def: ($) =>
      choice(
        seq($.constraint_named_def, optional($.constraint_insts)),
        seq($.constraint_anon_def, $.constraint_insts),
      ),

    constraint_named_def: ($) =>
      seq("constraint", field("name", $.id), $.constraint_body),

    constraint_anon_def: ($) => seq("constraint", $.constraint_body),

    constraint_body: ($) =>
      seq("{", repeat(seq($._constraint_body_elem, ";")), "}"),

    _constraint_body_elem: ($) =>
      choice(
        $.constr_relational,
        $.constr_prop_assign,
        $.constr_inside_values,
        $.constr_inside_enum,
      ),

    constraint_insts: ($) => sep1(",", $.id),

    // constr_relational: expr op=(LT|LEQ|GT|GEQ|EQ|NEQ) expr. ANTLR splits at
    // the rightmost comparison where both sides are complete expressions, so
    // the right side holds no comparison outside brackets or a ternary's
    // consequence: _cr_* is the layered expr without the comparison levels.
    constr_relational: ($) =>
      seq(
        field("left", $._cl_ternary),
        field("operator", choice(...RELATIONAL_OPS, ...EQUALITY_OPS)),
        field("right", $._cr_ternary),
      ),

    ...layeredExpr("cl"),
    ...layeredExpr("cr", ["equality", "relational"]),

    constr_prop_assign: ($) => seq(field("property", $.id), "=", $._expr),

    constr_inside_values: ($) =>
      seq($.constr_lhs, "inside", "{", sep1(",", $.constr_inside_value), "}"),

    constr_inside_enum: ($) => seq($.constr_lhs, "inside", field("enum", $.id)),

    constr_lhs: ($) => choice("this", $.instance_ref),

    constr_inside_value: ($) =>
      choice($._expr, seq("[", $._expr, ":", $._expr, "]")),

    // -------------------------------------------------------------------------
    // Lexer

    // Annex D reserved words: never valid in any rule, but the ANTLR lexer
    // still claims them. tree-sitter only reserves words that are tokens of
    // a reachable rule, so this rule pairs them with a token that cannot match.
    _annex_d_reserved: ($) =>
      seq(
        choice(
          "alternate",
          "byte",
          "int",
          "precedencetype",
          "real",
          "shortint",
          "shortreal",
          "signed",
          "with",
          "within",
        ),
        $._unmatchable,
      ),

    _unmatchable: (_) => token(prec(-1, /\x00\x01\x02\x03/)),

    // ID: an optional leading backslash escapes a keyword (`\rw`).
    id: (_) => /\\?[a-zA-Z_][a-zA-Z0-9_]*/,

    // SL_COMMENT and ML_COMMENT
    comment: (_) =>
      token(
        choice(
          seq("//", /[^\r\n]*/),
          seq("/*", /[^*]*\*+([^/*][^*]*\*+)*/, "/"),
        ),
      ),
  },
});
