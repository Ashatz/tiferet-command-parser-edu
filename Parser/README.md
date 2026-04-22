# Parser — Syntactic Analysis for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)  
**Course:** ECE 506 — Compiler Design  
**University of Arizona**  
**Date:** April 2026  

**Author:** Andrew Shatz  
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

The parser performs **syntactic analysis** (the second phase of a compiler front-end) on Python source files written in the Tiferet framework's Domain Event pattern. It consumes the token stream produced by the lexer and `BlockTracker` (which injects synthetic `INDENT`/`DEDENT` tokens at class and method boundaries), then validates the token stream against an **LALR(1)** context-free grammar organized around Tiferet's three-tier artifact comment hierarchy:

- **Tier 1 — Groups** (`# ***`): Top-level module sections (imports, events, utils, etc.)
- **Tier 2 — Sections** (`# **`): Individual components within a group (import categories, event definitions)
- **Tier 3 — Members** (`# *`): Class-level members (attributes, init, methods)

The parser is implemented using **PLY (Python Lex-Yacc)** — a Python implementation of the classic `lex` and `yacc` compiler construction tools. The grammar is organized across six layers: artifact structure, import decomposition, class/member definitions, method signatures with typed parameters, code snippet bodies, and PEMDAS-correct expression trees with bitwise shift operators.

Construction of the intermediate representation produced by this parser (node types, enumerations, post-order printing, and serialization) is documented separately with the symbol table and name resolver in the [SemanticRoutines README](../SemanticRoutines/README.md).

## 2. Pipeline Overview

The parser integrates into the Tiferet feature pipeline as the `parse.event` feature, which chains three domain events:

```
Source File
    │
    ▼
┌──────────────────────────┐   data_key: tokens
│ PerformLexicalAnalysis   │──────────────────────────────►
└──────────────────────────┘
    │  Reads file via tiferet.File, tokenizes via
    │  TiferetLexer + BlockTracker (INDENT/DEDENT injection)
    ▼
┌────────────────────────────────┐   data_key: ast
│ PerformSyntacticAnalysis       │──────────────────►
└────────────────────────────────┘
    │  Parses token stream via TiferetParser (PLY yacc)
    │  against the LALR(1) grammar defined in Section 3
    ▼
┌──────────────────┐  final payload (stdout / file)
│ EmitResult       │─────────────────────────────────►
└──────────────────┘
```

The lexer stage tokenizes the source file into a list of `TokenAggregate` objects, including synthetic `INDENT`/`DEDENT` tokens injected by `BlockTracker` at class-body and method-body boundaries. The parser then validates this token stream against the grammar, and `EmitResult` (`src/events/output.py`) assembles the payload and writes the serialized result to JSON or YAML.

## 3. Grammar

The full formal grammar specification — including the 4-tuple definition (V, Σ, R, S), all non-terminals, terminals, production rules, LR(1) automaton, LALR verification, and worked examples — is in:

→ **[docs/guides/grammar_spec.md](../docs/guides/grammar_spec.md)**

An LR(1) parse table visualization for the structural core subset is provided in:

→ **[Tiferet Compiler LR(1).jpg](./Tiferet%20Compiler%20LR(1).jpg)**

### Grammar Overview

The parser implements its `p_*` grammar rule methods across six layers:

#### Layer 1 — Artifact Structure (Tier 1–2)

The top-level module structure mirrors Tiferet's artifact comment hierarchy:

```ebnf
Module       → GroupList
             | DOCSTRING NEWLINE GroupList
GroupList    → GroupList Group | ε
Group        → GroupHeader NEWLINE SectionList
GroupHeader  → ARTIFACT_IMPORTS_START | ARTIFACT_START
SectionList  → SectionList Section | ε
Section      → SectionHeader NEWLINE SectionBody
             | Annots SectionHeader NEWLINE SectionBody
             | SectionHeader NEWLINE Annots SectionBody
SectionHeader → ARTIFACT_SECTION | ARTIFACT_IMPORT_GROUP
SectionBody  → ClassDef | ImportBlock
Annots       → Annot | Annots Annot
Annot        → OBSOLETE NEWLINE | TODO NEWLINE
```

A source file is a **Module** containing **Groups** (opened by `# ***` headers), which contain **Sections** (opened by `# **` headers). Sections may be preceded or followed by `OBSOLETE`/`TODO` annotations.

#### Layer 2 — Import Statements

Import statements are fully decomposed into the relative-path prefix, the module path, aliasing, and multi-import comma lists:

```ebnf
ImportBlock  → ImportStmt | ImportBlock ImportStmt
ImportStmt   → IMPORT ImportExpr NEWLINE
             | FROM FromExpr IMPORT ImportExpr NEWLINE
ImportExpr   → IDENTIFIER
             | IDENTIFIER AS IDENTIFIER
             | ImportExpr COMMA IDENTIFIER
FromExpr     → IDENTIFIER | DOT IDENTIFIER | DOT FromExpr | FromExpr DOT IDENTIFIER
```

#### Layer 3 — Class and Member Definitions (Tier 3)

```ebnf
ClassDef     → CLASS IDENTIFIER LPAREN SuperClsList RPAREN COLON NEWLINE INDENT ClassBody DEDENT
ClassBody    → DOCSTRING NEWLINE MemberList | MemberList
SuperClsList → IDENTIFIER | SuperClsList COMMA IDENTIFIER | ε
MemberList   → MemberList Member | Member | ε
Member       → ARTIFACT_MEMBER NEWLINE MemberStmt
             | Annots ARTIFACT_MEMBER NEWLINE MemberStmt
             | ARTIFACT_MEMBER NEWLINE Annots MemberStmt
MemberStmt   → AttrDecl | MethodDecl | Decorator NEWLINE MemberStmt
AttrDecl     → IDENTIFIER NEWLINE
             | IDENTIFIER COLON AttrTypes NEWLINE
AttrTypes    → IDENTIFIER | AttrTypes PIPE IDENTIFIER
```

#### Layer 4 — Method Definitions and Typed Parameters

Methods are parsed with full parameter typing, including support for `*args`, `**kwargs`, default values, union types, and return type annotations:

```ebnf
MethodDecl   → DEF MethodName LPAREN MethodParamList RPAREN RetAnnot COLON NEWLINE
               INDENT MethodDocString SnippetList DEDENT
MethodName   → IDENTIFIER | INIT
MethodParamList → SELF | SELF COMMA ParamList
ParamList    → Param | ParamList COMMA Param
Param        → IDENTIFIER
             | STAR IDENTIFIER | DOUBLESTAR IDENTIFIER
             | Param COLON ParamTypes
             | Param EQUALS NameOrLiteral
             | NEWLINE Param
ParamTypes   → IDENTIFIER | ParamTypes PIPE IDENTIFIER
RetAnnot     → ARROW RetTypes | ε
RetTypes     → IDENTIFIER | RetTypes PIPE IDENTIFIER
Decorator    → AT DecoratorCall
DecoratorCall → DecoratorIdent LPAREN DecoratorArgs RPAREN
```

#### Layer 5 — Method Bodies — Snippets and Statements

Method bodies are parsed as sequences of **snippets** — Tiferet's convention of comment-headed code blocks where each logical step is preceded by a descriptive comment:

```ebnf
SnippetList  → SnippetList Snippet | SnippetList NEWLINE | ε
Snippet      → CommentList StmtList | StmtList
CommentList  → CommentStmt | CommentList CommentStmt
CommentStmt  → LINE_COMMENT NEWLINE
StmtList     → Stmt | StmtList Stmt | ε
Stmt         → RETURN ReturnExpr NEWLINE
             | AssignExpr NEWLINE
             | OperationExpr NEWLINE
             | CallExpr NEWLINE
```

The `SnippetList` also consumes stray `NEWLINE` tokens (blank lines between snippets) to avoid premature reduction.

#### Layer 6 — Expressions (Precedence Hierarchy)

The expression grammar implements correct operator precedence via a recursive-descent hierarchy. The current grammar adds **bitwise shift** operators (`<<`, `>>`) between comparison and additive precedence to support strength reduction in later compiler phases:

```ebnf
AssignExpr    → IdentExpr EQUALS AssignRHS
AssignRHS     → OperationExpr | CallExpr
ReturnExpr    → OperationExpr | CallExpr | ε

OperationExpr → ComparisonExpr
ComparisonExpr → ShiftExpr CompOp ShiftExpr | ShiftExpr
CompOp        → EQEQ | NOTEQ | LT | GT | LTEQ | GTEQ | PIPE | AMPERSAND

ShiftExpr     → ShiftExpr LSHIFT AdditiveExpr         (left-associative)
              | ShiftExpr RSHIFT AdditiveExpr
              | AdditiveExpr

AdditiveExpr  → AdditiveExpr PLUS  MultiplicativeExpr (left-associative)
              | AdditiveExpr MINUS MultiplicativeExpr
              | MultiplicativeExpr

MultiplicativeExpr → MultiplicativeExpr STAR  ExponentialExpr  (left-associative)
                   | MultiplicativeExpr SLASH ExponentialExpr
                   | MultiplicativeExpr PERCENT ExponentialExpr
                   | ExponentialExpr

ExponentialExpr → NameOrLiteral DOUBLESTAR ExponentialExpr  (right-associative)
                | NameOrLiteral

CallExpr      → IdentExpr LPAREN CallArgs RPAREN
CallArgs      → CallArg | CallArgs COMMA CallArg | ε
CallArg       → OperationExpr | CallExpr

NameOrLiteral → IdentExpr | LiteralExpr
LiteralExpr   → STRING_LITERAL | NUMBER_LITERAL | TRUE | FALSE
IdentExpr     → Ident | IdentDot
Ident         → IDENTIFIER | SELF
IdentDot      → Ident DOT IDENTIFIER | IdentDot DOT IDENTIFIER
```

The precedence hierarchy from lowest to highest:
1. **Comparison** — `==`, `!=`, `<`, `>`, `<=`, `>=`, `|`, `&`
2. **Shift** — `<<`, `>>` (left-associative)
3. **Addition/Subtraction** — `+`, `-` (left-associative)
4. **Multiplication/Division/Modulus** — `*`, `/`, `%` (left-associative)
5. **Exponentiation** — `**` (right-associative)
6. **Call** — `f(args)`
7. **Atom** — identifiers, dotted names, literals

## 4. Authoring Grammar Rules with PLY

PLY (Python Lex-Yacc) is a pure-Python port of the classic `lex`/`yacc` tools. The parser is generated at construction time by calling `yacc.yacc()` against a Python module (or class instance) that exposes:

- A `tokens` attribute listing every terminal name (sourced from the lexer).
- An optional `precedence` tuple declaring operator precedence and associativity.
- A set of `p_*` methods, one per production rule, whose **docstrings contain the rule itself**.
- A `p_error` method invoked on parse failure.

`TiferetParser` (`Parser/parser.py`) inherits from `ParserBase`, which registers `tokens` and `precedence` from `src/assets/parser.py` and constructs the underlying PLY parser in its `__init__`. Grammar rules are then declared as `p_*` methods directly on `TiferetParser`.

### 4.1 The `p_*` Rule Method Convention

Every grammar rule is a method whose **docstring is the production**. PLY parses that docstring — not the method body — to build the LALR(1) automaton. The method body is the **semantic action** that executes when the rule reduces.

The canonical shape is:

```python path=null start=null
# * method: p_some_rule (rule)
def p_some_rule(self, p):
    '''nonterminal : SYMBOL_1 SYMBOL_2 ... SYMBOL_N'''

    # Action body: construct a result and assign it to p[0].
    p[0] = ...
```

The `p` argument is a **production object** indexed from 1 to N, where `p[k]` is the value of the k-th symbol on the right-hand side of the rule. `p[0]` is the return slot — whatever you assign there becomes the semantic value of the non-terminal on the left. Terminals carry their lexer value (e.g. `'class'` for `CLASS`, or the raw identifier text for `IDENTIFIER`); non-terminals carry whatever their own reducing action placed into `p[0]`.

Example — the terminal rule `p_literal_expr` turns four alternative terminal tokens into a single literal value:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=1143
# * method: p_literal_expr (rule)
def p_literal_expr(self, p):
    '''literal_expr : STRING_LITERAL
             | NUMBER_LITERAL
             | TRUE
             | FALSE'''

    # Build a literal expression from a string, number, or boolean token.
    ln, col = self.pos(p, 1)
    p[0] = Expr.new_name_or_literal_expr(p[1], lineno=ln, col=col)
```

### 4.2 Alternatives, Lists, and Epsilon Rules

A single method can define multiple alternatives by separating the right-hand sides with `|` inside its docstring, as shown above. When the alternatives differ enough that the action needs to branch, PLY idiom is to split them across several `p_*` methods — one per alternative — each with its own focused action. The parser treats the collection of all alternatives for the same non-terminal as a single rule when building the automaton.

Left-recursive list accumulation is the standard PLY pattern for collecting repeated items without blowing the parse stack. The grammar defines two (or three) alternatives: a base/recursive extension and an epsilon (empty) case:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=269
# * method: p_group_list (rule)
def p_group_list(self, p):
    '''group_list : group_list group'''

    # Collect groups into a list via left-recursive accumulation.
    if p[1]:
        p[1].set_next(p[2])
        p[0] = p[1]
    else:
        p[0] = p[2]

# * method: p_group_list_empty (rule)
def p_group_list_empty(self, p):
    '''group_list : '''

    # Initialize an empty group list.
    p[0] = None
```

A rule with an empty right-hand side (`'''nonterminal : '''`) is the epsilon production. PLY reduces it immediately and hands whatever the action assigns to `p[0]` up to the caller. This pattern is used throughout the Tiferet grammar for `group_list`, `section_list`, `member_list`, `snippet_list`, `stmt_list`, `call_args`, `ret_annot`, and `super_cls_list`.

### 4.3 Precedence and Associativity

The expression grammar in Layer 6 encodes precedence **structurally** — each precedence level is its own non-terminal, and recursion placement determines associativity. Left recursion (`expr : expr OP inner_expr`) produces left-associativity; right recursion (`expr : inner_expr OP expr`) produces right-associativity. This is why `AdditiveExpr`, `MultiplicativeExpr`, and `ShiftExpr` are written left-recursive, while `ExponentialExpr` is written right-recursive.

PLY also accepts a `precedence` tuple for operator disambiguation. `ParserBase` imports the declared precedence directly from `src/assets/parser.py`:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/src/assets/parser.py start=13
# ** constant: precedence
precedence = (
    ('right', 'COLON'),
    ('right', 'ARROW'),
    ('nonassoc', 'ARTIFACT_START', 'ARTIFACT_SECTION', 'ARTIFACT_MEMBER',
                 'OBSOLETE', 'TODO', 'DEDENT'),
)
```

The `nonassoc` entries for the artifact and layout tokens prevent shift-reduce conflicts at structural boundaries: the parser prefers to shift on the next-tier artifact token rather than prematurely reduce the current tier.

### 4.4 Tracking Source Positions

PLY exposes two coordinate hooks on the production object: `p.lineno(k)` returns the line number of the k-th symbol, and `p.lexpos(k)` returns its absolute character offset in the source text. `ParserBase` wraps both in a single helper so rule actions can stamp their result with `(line, column)`:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=93
# * method: find_column
def find_column(self, lexpos: int) -> int:
    '''
    Compute the 0-based column of a token from its lexpos
    using the stored source text.
    '''

    if lexpos == 0:
        return 0
    last_newline = self.source_text.rfind('\n', 0, lexpos)
    if last_newline < 0:
        return lexpos
    return lexpos - last_newline - 1

# * method: pos
def pos(self, p, n: int) -> tuple:
    '''
    Extract (lineno, col) for the nth symbol in a grammar production.
    '''

    return (p.lineno(n), self.find_column(p.lexpos(n)))
```

Semantic actions call `self.pos(p, k)` to stamp each constructed node with its originating line and column for later error reporting.

### 4.5 Driving the Parse

PLY expects its input to come from a `.token()`-returning object. Because the Tiferet lexer emits a list of `TokenAggregate` objects (not a streaming PLY `Lexer`), `TokenStream` wraps that list and produces a PLY-compatible token on each call:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=42
# * method: token
def token(self):
    '''
    Return the next token as a PLY-compatible object, or None at end of stream.
    '''

    # Define a simple PLY token class for compatibility. ...
    class PLYToken:
        pass

    try:
        token = next(self.iter)
        ply_token = PLYToken()
        ply_token.type = token.type
        ply_token.value = token.value
        ply_token.lineno = token.lineno
        ply_token.lexpos = token.lexpos
        return ply_token
    except StopIteration:
        return None
```

`ParserBase.parse()` then hands the `TokenStream` to the generated parser via the `lexer=` keyword:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=126
# * method: parse
def parse(self, module_name: str, tokens: List[TokenAggregate], source_text: str = '') -> Dict[str, Any]:
    # Store the source text for column calculation.
    self.source_text = source_text or ''

    # Convert the list of TokenAggregate objects into a PLY-compatible token stream.
    token_stream = TokenStream(tokens)

    # Parse the token stream and return the result.
    return self.parser_service.parse(lexer=token_stream)
```

### 4.6 Error Handling

PLY calls `p_error(self, p)` when the parser reaches a state with no valid action on the incoming token. `p` is the offending token (or `None` at end of input). `TiferetParser` converts this into a descriptive `SyntaxError` that names the violated artifact tier:

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Parser/parser.py start=227
# * method: p_error
def p_error(self, p):
    '''
    Report syntax errors using Tiferet artifact hierarchy terminology.
    '''

    if p:
        raise SyntaxError(
            f"Syntax error in Tiferet artifact hierarchy: "
            f"unexpected token '{p.type}' "
            f"(value={p.value!r}, line {getattr(p, 'lineno', '?')}). "
            f"Expected a valid # *** Group, # ** Section, or # * Member structure."
        )
    else:
        raise SyntaxError(
            "Unexpected end of input while parsing Tiferet Domain Event structure. "
            "Ensure all # *** Group, # ** Section, and # * Member blocks are complete."
        )
```

### 4.7 Helper Methods on `ParserBase`

Several small helpers are shared across the `p_*` rule methods so the rule bodies stay focused on grammar structure rather than string manipulation:

- **`parse_artifact_header(token_value)`** — Strips the `#` marker and splits an artifact header like `# ** event: ping` or `# *** imports` into a `(name, type)` tuple. Used by every rule that reduces `ARTIFACT_*` tokens into a header node.
- **`parse_member_kind(artifact_member_value)`** — Extracts the member discriminator (`attribute`, `method`, `init`, ...) from an `ARTIFACT_MEMBER` token so the member rule can dispatch on kind.
- **`get_attribute_type(type_str, additional_types=None)`** — Maps a type name string (`int`, `str`, `list`, `dict`, ...) onto the appropriate primitive or class type node. Used by `attr_types`, `param_types`, and `ret_types`.

Keeping these on `ParserBase` means every rule that needs them can call `self.helper(...)` without duplicating logic across `p_group_header_*`, `p_section_header_*`, `p_member_decl`, `p_attr_types_*`, and friends.

### 4.8 Adding a New Rule — Worked Example

To extend the grammar with a new production, follow this checklist:

1. **Identify the non-terminal and its right-hand side.** Pick a name that is unique within `TiferetParser` (PLY collapses all `p_*` methods targeting the same non-terminal into a single rule).
2. **Add the terminal tokens** it references to `src/assets/lexer.py` if they do not already exist, and ensure they appear in `TOKENS`.
3. **Declare any precedence or associativity** in the `precedence` tuple of `src/assets/parser.py` if the new operator would otherwise conflict with existing rules.
4. **Author the `p_*` method.** Put the production in the docstring, then write the semantic action. Call `self.pos(p, k)` to capture positions and use `ParserBase` helpers for any shared string-to-node conversion.
5. **Wire the rule into existing non-terminals** so it is reachable from `module`. A rule that never appears on the right-hand side of another rule is dead.
6. **Regenerate** by reinstantiating `TiferetParser`; PLY rebuilds the automaton in `__init__`. Watch PLY's output for any reported shift-reduce or reduce-reduce conflicts.
7. **Add focused unit tests** in `src/utils/tests/test_parser.py` covering both the happy path and any ambiguous neighbours.

For reference, the bitwise shift layer was added by (a) introducing `LSHIFT`/`RSHIFT` terminals in the lexer, (b) writing `p_shift_expr` as a left-recursive rule, and (c) re-targeting `p_comparison_expr` from `additive_expr` to `shift_expr`. No other changes were required — the surrounding precedence levels continued to work unmodified.

## 5. Source Files

### Parser Implementation

| File | Description |
|------|-------------|
| [`Parser/parser.py`](./parser.py) | Copy of `src/utils/parser.py` — `ParserBase` with shared utilities (`parse`, `pos`, `find_column`, helpers, `p_error`) + `TiferetParser` with every `p_*` grammar rule method. This is the complete parser implementation. |

### Supporting Modules (canonical source in `src/`)

| File | Description |
|------|-------------|
| `src/assets/lexer.py` | Token constants (`TOKENS` list, rule handlers) consumed by PLY as the terminal alphabet. |
| `src/assets/parser.py` | `precedence` tuple and re-export of `TOKENS`; imported by `ParserBase` during `yacc.yacc()`. |
| `src/events/parser.py` | Parser domain event: `PerformSyntacticAnalysis` (pipeline binding). |
| `src/events/output.py` | Terminal emit event: `EmitResult` (handles all pipeline stages). |
| `src/interfaces/parser.py` | Abstract `ParserService(Service)` interface that `ParserBase` implements. |

For a detailed walkthrough of the parser architecture and the `TokenStream` adapter, see:

→ **[docs/guides/utils/parser.md](../docs/guides/utils/parser.md)**

## 6. Testing the Parser

### Prerequisites

```bash
# Clone the repository
git clone https://github.com/ashatz/tiferet-command-parser-edu.git
cd tiferet-command-parser-edu

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running the Parser via CLI

Parse a Tiferet event source file:

```bash
python compiler.py parse event <source_file>
```

**Options:**

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Write results to a YAML or JSON file (format auto-detected from extension) |
| `--output-format` | Output format: `yaml`, `json`, `console`, or `auto` |
| `--include-tokens` | Include the full token list in the output alongside the parse result |

**Examples:**

```bash
# Parse a minimal event and view the result on stdout
python compiler.py parse event samples/pass_minimal_event.py

# Parse with JSON file output
python compiler.py parse event samples/pass_minimal_injection_event.py -o result.json

# Parse with YAML output
python compiler.py parse event samples/pass_multiple_operator_events.py -o result.yaml

# Parse with tokens included
python compiler.py parse event samples/pass_helper_method_event.py -o result.json --include-tokens true
```

### Verifying Failing Samples

Failing samples produce `SyntaxError` exceptions with descriptive messages indicating which artifact hierarchy rule was violated. The error message identifies the unexpected token type, its value, and line number:

```bash
# Bare function without # ** section header → SyntaxError
python compiler.py parse event samples/fail_bare_function.py
# SyntaxError: unexpected token 'DEF' (value='def', line 8)

# Attribute without # * member header → SyntaxError
python compiler.py parse event samples/fail_class_bare_attribute.py
# SyntaxError: unexpected token 'IDENTIFIER' (value='error_service', line 13)

# Method without # * member header → SyntaxError
python compiler.py parse event samples/fail_class_bare_method.py
# SyntaxError: unexpected token 'DEF' (value='def', line 12)

# Class without # ** section header → SyntaxError
python compiler.py parse event samples/fail_class_no_section.py
# SyntaxError: unexpected token 'CLASS' (value='class', line 8)

# Import without # ** group header → SyntaxError
python compiler.py parse event samples/fail_import_no_group.py
# SyntaxError: unexpected token 'FROM' (value='from', line 3)

# Missing group header entirely → SyntaxError
python compiler.py parse event samples/fail_missing_group_header.py
# SyntaxError: unexpected token 'LINE_COMMENT' (line 8)

# Missing member artifact comment → SyntaxError
python compiler.py parse event samples/fail_missing_member_artifact.py
# SyntaxError: unexpected token 'LINE_COMMENT' (line 24)
```

### Running the Automated Test Suite

The full pytest suite includes 59 parser-related tests:

```bash
# Run only parser utility tests (55 tests — grammar rules including shift grammar)
python -m pytest src/utils/tests/test_parser.py -v

# Run only parser domain event tests (4 tests — pipeline events via DomainEvent.handle)
python -m pytest src/events/tests/test_parser.py -v

# Run all tests in the project
python -m pytest src/ -v
```

## 7. Test Battery

### Passing Test Cases (5)

Each passing file is a complete, syntactically and semantically meaningful Tiferet Domain Event module. These files are used throughout all subsequent compiler phases.

| # | Source File | Pre-computed Output | Description |
|---|------------|--------------------|-------------|
| 1 | [`samples/pass_imports_only.py`](../samples/pass_imports_only.py) | [`Parser/samples/pass_imports_only.json`](./samples/pass_imports_only.json) | Imports-only module with `core` and `app` import groups, no event definitions. Exercises Tier 1–2 artifact structure, `from ... import` with dotted paths, and multi-symbol imports. |
| 2 | [`samples/pass_minimal_event.py`](../samples/pass_minimal_event.py) | [`Parser/samples/pass_minimal_event.json`](./samples/pass_minimal_event.json) | Single `Ping` event with one `execute` method — minimal valid three-tier program. Exercises class definition with inheritance, method with `**kwargs`, return type annotation, docstring, and snippet with return statement. |
| 3 | [`samples/pass_minimal_injection_event.py`](../samples/pass_minimal_injection_event.py) | [`Parser/samples/pass_minimal_injection_event.json`](./samples/pass_minimal_injection_event.json) | `Ping` event with constructor injection — attribute declaration, `__init__` method, and `execute` method. Exercises `# * attribute`, `# * init`, typed parameters, `self.pong` dotted name access, and assignment expressions. |
| 4 | [`samples/pass_multiple_operator_events.py`](../samples/pass_multiple_operator_events.py) | [`Parser/samples/pass_multiple_operator_events.json`](./samples/pass_multiple_operator_events.json) | Six arithmetic events (`Add`, `Subtract`, `Multiply`, `Divide`, `Modulus`, `Exponentiate`) in one module. Exercises multi-section parsing (SectionList repetition), all six arithmetic operators (`+`, `-`, `*`, `/`, `%`, `**`), and the full expression precedence hierarchy. |
| 5 | [`samples/pass_helper_method_event.py`](../samples/pass_helper_method_event.py) | [`Parser/samples/pass_helper_method_event.json`](./samples/pass_helper_method_event.json) | `AddInteger` event with a `to_int` helper method alongside `execute`. Exercises multiple method members, chained arithmetic expression (`x + y * 3 - 2` parsed with correct precedence), RST docstrings, call expressions (`int(value)`, `self.to_int(a)`), and assignment with call RHS. |

**Verification:** Run any passing case through the CLI and confirm it produces a valid JSON envelope:

```bash
python compiler.py parse event samples/pass_minimal_event.py -o result.json
```

### Failing Test Cases (7)

Each failing file violates a specific rule in the artifact hierarchy grammar, causing the parser to reject the input with a `SyntaxError`. These test structural enforcement — the parser requires proper `# ***` Group, `# **` Section, and `# *` Member headers to delimit code blocks.

| # | Source File | Violation | Expected Error |
|---|------------|-----------|----------------|
| 1 | [`samples/fail_bare_function.py`](../samples/fail_bare_function.py) | `def` at top level without `# **` section header | `SyntaxError: unexpected token 'DEF'` |
| 2 | [`samples/fail_class_bare_attribute.py`](../samples/fail_class_bare_attribute.py) | Typed attribute inside class without `# *` member header | `SyntaxError: unexpected token 'IDENTIFIER'` |
| 3 | [`samples/fail_class_bare_method.py`](../samples/fail_class_bare_method.py) | Method inside class without `# *` member header | `SyntaxError: unexpected token 'DEF'` |
| 4 | [`samples/fail_class_no_section.py`](../samples/fail_class_no_section.py) | `class` under `# ***` without `# **` section header | `SyntaxError: unexpected token 'CLASS'` |
| 5 | [`samples/fail_import_no_group.py`](../samples/fail_import_no_group.py) | `from` statement without `# **` import group header | `SyntaxError: unexpected token 'FROM'` |
| 6 | [`samples/fail_missing_group_header.py`](../samples/fail_missing_group_header.py) | Content without any `# ***` group header | `SyntaxError: unexpected token 'LINE_COMMENT'` |
| 7 | [`samples/fail_missing_member_artifact.py`](../samples/fail_missing_member_artifact.py) | Method body without `# *` member artifact comment | `SyntaxError: unexpected token 'LINE_COMMENT'` |

**Verification:** Run any failing case and confirm it produces a `SyntaxError`:

```bash
python compiler.py parse event samples/fail_class_bare_attribute.py
# Error: Syntax error in Tiferet artifact hierarchy: unexpected token 'IDENTIFIER'
#   (value='error_service', line 13). Expected a valid # *** Group, # ** Section,
#   or # * Member structure.
```

### Failure Categories

The 7 failing test cases cover three categories of structural violations:

1. **Missing Group Header** (1 case) — Content appears without any `# ***` artifact group header, so the parser has no structural context.
2. **Missing Section Header** (3 cases) — A class, function, or import appears directly under a `# ***` group without the required `# **` section header.
3. **Missing Member Header** (3 cases) — An attribute, method, or code block appears inside a class without the required `# *` member header.

These failures demonstrate that the parser enforces the three-tier artifact hierarchy at every level — code that lacks proper artifact comment structure is rejected before any semantic analysis can occur.
