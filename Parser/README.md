# Parser — Syntactic Analysis for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)  
**Course:** ECE 506 — Compiler Design  
**University of Arizona**  
**Date:** April 2026  

**Author:** Andrew Shatz  
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

The parser performs **syntactic analysis** (the second phase of a compiler front-end) on Python source files written in the Tiferet framework's Domain Event pattern. It consumes the token stream produced by the lexer and `BlockTracker` (which injects synthetic `INDENT`/`DEDENT` tokens at class and method boundaries), then constructs a structured **Pydantic AST** that reflects Tiferet's three-tier artifact comment hierarchy:

- **Tier 1 — Groups** (`# ***`): Top-level module sections (imports, events, utils, etc.)
- **Tier 2 — Sections** (`# **`): Individual components within a group (import categories, event definitions)
- **Tier 3 — Members** (`# *`): Class-level members (attributes, init, methods)

The parser is implemented using **PLY (Python Lex-Yacc)** — a Python implementation of the classic `lex` and `yacc` compiler construction tools. The grammar is an **LALR(1)** context-free grammar with **114 productions** organized across six layers: artifact structure, import decomposition, class/member definitions, method signatures with typed parameters, code snippet bodies, and PEMDAS-correct expression trees.

Unlike many educational parsers that use flat token sequences or generic content consumers, this parser builds **fully typed Pydantic AST nodes** with linked-list chaining (`.next` fields), position tracking (`lineno`, `col`), and a complete expression hierarchy supporting arithmetic operators, function calls, assignments, comparisons, and dotted name resolution.

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
    │  into a Pydantic DeclarationAggregate AST root
    ▼
┌──────────────────┐  final payload (stdout / file)
│ EmitResult       │─────────────────────────────────►
└──────────────────┘
```

The lexer stage tokenizes the source file into a list of `TokenAggregate` objects, including synthetic `INDENT`/`DEDENT` tokens injected by `BlockTracker` at class-body and method-body boundaries. The parser then constructs a full Pydantic AST from this token stream, and `EmitResult` (`src/events/output.py`) assembles the payload and writes the serialized AST to JSON or YAML.

## 3. Grammar

The full formal grammar specification — including the 4-tuple definition (V, Σ, R, S), all non-terminals, terminals, production rules, LR(1) automaton, LALR verification, and worked examples — is in:

→ **[docs/guides/grammar_spec.md](../docs/guides/grammar_spec.md)**

An LR(1) parse table visualization for the structural core subset is provided in:

→ **[Tiferet Compiler LR(1).jpg](./Tiferet%20Compiler%20LR(1).jpg)**

### Grammar Overview

The parser implements 114 grammar rule methods organized into six layers:

#### Layer 1 — Artifact Structure (Tier 1–2)

The top-level module structure mirrors Tiferet's artifact comment hierarchy:

```ebnf
Module       → GroupList
GroupList    → GroupList Group | ε
Group        → GroupHeader NEWLINE SectionList
GroupHeader  → ARTIFACT_IMPORTS_START | ARTIFACT_START
SectionList  → SectionList Section | ε
Section      → SectionHeader NEWLINE SectionBody
             | Annots SectionHeader NEWLINE SectionBody
             | SectionHeader Annots NEWLINE SectionBody
SectionHeader → ARTIFACT_SECTION | ARTIFACT_IMPORT_GROUP
SectionBody  → ClassDef | ImportBlock
Annots       → Annot | Annots Annot
Annot        → OBSOLETE NEWLINE | TODO NEWLINE
```

A source file is a **Module** containing **Groups** (opened by `# ***` headers), which contain **Sections** (opened by `# **` headers). Sections may be preceded or followed by `OBSOLETE`/`TODO` annotations.

#### Layer 2 — Import Statements

Import statements are parsed into structured AST expression nodes:

```ebnf
ImportBlock  → ImportStmt | ImportBlock ImportStmt
ImportStmt   → IMPORT ImportExpr NEWLINE
             | FROM FromExpr IMPORT ImportExpr NEWLINE
ImportExpr   → IDENTIFIER
             | IDENTIFIER AS IDENTIFIER
             | ImportExpr COMMA IDENTIFIER
FromExpr     → IDENTIFIER | DOT IDENTIFIER | DOT FromExpr
```

The current parser fully decomposes import statements into `import`, `from ... import`, `as` aliases, and multi-import comma lists, producing typed `Expression` nodes in the AST.

#### Layer 3 — Class and Member Definitions (Tier 3)

```ebnf
ClassDef     → CLASS IDENTIFIER LPAREN SuperClsList RPAREN COLON NEWLINE INDENT ClassBody DEDENT
ClassBody    → DOCSTRING NEWLINE MemberList | MemberList
SuperClsList → IDENTIFIER | SuperClsList COMMA IDENTIFIER | ε
MemberList   → MemberList Member | Member | ε
Member       → ARTIFACT_MEMBER NEWLINE MemberBody
             | Annots ARTIFACT_MEMBER NEWLINE MemberBody
MemberBody   → AttrDecl | MethodDef | DecoratedMethodDef
AttrDecl     → IDENTIFIER COLON AttrTypes NEWLINE
```

#### Layer 4 — Method Definitions and Typed Parameters

Methods are parsed with full parameter typing, including support for `*args`, `**kwargs`, default values, union types, and return type annotations:

```ebnf
MethodDef    → DEF MethodName LPAREN MethodParams RPAREN RetAnnot COLON NEWLINE
               INDENT DOCSTRING NEWLINE SnippetList DEDENT
             | DEF MethodName LPAREN MethodParams RPAREN RetAnnot COLON NEWLINE
               INDENT SnippetList DEDENT
MethodName   → IDENTIFIER | INIT
MethodParams → SELF | SELF COMMA MethodParam
             | SELF COMMA MethodParam COMMA MethodParams
MethodParam  → IDENTIFIER COLON ParamTypes
             | IDENTIFIER COLON ParamTypes EQUALS DefaultVal
             | STAR IDENTIFIER | DOUBLESTAR IDENTIFIER
RetAnnot     → ARROW RetTypes | ε
ParamTypes   → IDENTIFIER | ParamTypes PIPE IDENTIFIER
RetTypes     → IDENTIFIER | RetTypes PIPE IDENTIFIER
Decorator    → AT DecoratorExpr NEWLINE
```

#### Layer 5 — Method Bodies — Snippets and Statements

Method and function bodies are parsed as sequences of **snippets** — Tiferet's convention of comment-headed code blocks where each logical step is preceded by a descriptive comment:

```ebnf
SnippetList  → SnippetList Snippet | SnippetList NEWLINE | ε
Snippet      → CommentList StmtList | StmtList
CommentList  → CommentStmt | CommentList CommentStmt
CommentStmt  → LINE_COMMENT NEWLINE
StmtList     → Stmt | StmtList Stmt | ε
```

The `SnippetList` also consumes stray `NEWLINE` tokens (blank lines between snippets) to avoid premature reduction. Statements within snippets use the expression grammar defined below.

#### Layer 6 — Expressions (PEMDAS Hierarchy)

The expression grammar implements correct operator precedence via a recursive-descent hierarchy:

```ebnf
Stmt          → RETURN ReturnExpr NEWLINE
              | AssignExpr NEWLINE
              | OperationExpr NEWLINE
              | CallExpr NEWLINE

AssignExpr    → IdentExpr EQUALS AssignRHS
AssignRHS     → OperationExpr | CallExpr

OperationExpr → ComparisonExpr
ComparisonExpr → AdditiveExpr CompOp AdditiveExpr | AdditiveExpr
CompOp        → EQEQ | NOTEQ | LT | GT | LTEQ | GTEQ | PIPE | AMPERSAND

AdditiveExpr  → AdditiveExpr PLUS  MultiplicativeExpr      (left-associative)
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
2. **Addition/Subtraction** — `+`, `-` (left-associative)
3. **Multiplication/Division/Modulus** — `*`, `/`, `%` (left-associative)
4. **Exponentiation** — `**` (right-associative)
5. **Call** — `f(args)`
6. **Atom** — identifiers, dotted names, literals

## 4. AST Structure

The parser produces a **Pydantic AST** with linked-list chaining (`.next` fields) rather than Python lists. The AST node types are defined in `src/domain/ast.py` and extended with mutation methods in `src/mappers/ast.py`.

### AST Node Types

- **Declaration** — Root node type for all declarations (module, class, method, attribute, artifact). Carries `name`, `type` (TypeKind), `code` (body statements), `params` (for methods), `metadata`, `next`, `lineno`, `col`.
- **Statement** — Wraps expressions and declarations into statement chains. Carries `kind` (StatementKind), `expr`, `decl`, `body`, `next`, `lineno`, `col`.
- **Expression** — Represents values, operations, calls, assignments, and imports. Carries `kind` (ExprKind), `value`, `name`, `left`, `right`, `next`, `lineno`, `col`.
- **Type** — Type annotations with `kind` (TypeKind), `name`, `subtype`, `return_type`, `params`.
- **ParamList** — Linked-list of method parameters with `name`, `type`, `required`, `default`, `next`.

### Type Enumerations

- **TypeKind** — `unknown`, `None`, `bool`, `str`, `int`, `float`, `list`, `dict`, `class`, `func`, `artifact`, `module`
- **ExprKind** — `add`, `sub`, `mul`, `div`, `mod`, `exp`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `name`, `num_val`, `int_val`, `str_val`, `bool_val`, `assign`, `args_list`, `call`, `import`, `import_as`, `import_multi`, `artifact`, `comment`
- **StatementKind** — `decl`, `expr`, `if_else`, `for`, `while`, `print`, `return`, `block`, `import`, `import_from`, `artifact`, `comment`, `snippet`

### Example: Minimal Event AST

For `samples/pass_minimal_event.py`, the parser produces a module declaration containing two artifact groups (imports and events), with the events group containing a section for the `Ping` class, which has a single `execute` method member with a return statement.

Pre-computed AST output: → **[Parser/samples/pass_minimal_event.json](./samples/pass_minimal_event.json)**

## 5. Source Files

### Parser Implementation

| File | Description |
|------|-------------|
| [`Parser/parser.py`](./parser.py) | Copy of `src/utils/parser.py` — `ParserBase` with shared utilities + `TiferetParser` with all 114 `p_*` grammar rule methods. This is the complete parser implementation. |

### Supporting Modules (canonical source in `src/`)

| File | Description |
|------|-------------|
| `src/assets/parser.py` | Precedence rules and AST builder helper functions |
| `src/events/parser.py` | Parser domain event: `PerformSyntacticAnalysis` |
| `src/events/output.py` | Consolidated terminal emit event: `EmitResult` (handles all pipeline stages) |
| `src/interfaces/parser.py` | Abstract `ParserService(Service)` interface |
| `src/domain/ast.py` | Pydantic AST domain objects (TypeKind, ExprKind, StatementKind, Type, ParamList, Expression, Declaration, Statement) |
| `src/mappers/ast.py` | AST mapper aggregates with mutation methods and static factories |

For a detailed walkthrough of the parser architecture, AST node structure, and `TokenStream` adapter design, see:

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

Parse a Tiferet event source file and produce a structured AST:

```bash
python compiler.py parse event <source_file>
```

**Options:**

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Write results to a YAML or JSON file (format auto-detected from extension) |
| `--output-format` | Output format: `yaml`, `json`, `console`, or `auto` |
| `--include-tokens` | Include the full token list in the output alongside the AST |

**Examples:**

```bash
# Parse a minimal event and view the AST on stdout
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

The full pytest suite includes 57 parser-related tests:

```bash
# Run only parser utility tests (51 tests — grammar rules and AST structure)
python -m pytest src/utils/tests/test_parser.py -v

# Run only parser domain event tests (6 tests — pipeline events via DomainEvent.handle)
python -m pytest src/events/tests/test_parser.py -v

# Run all tests in the project (237 total)
python -m pytest src/ -v
```

## 7. Test Battery

### Passing Test Cases (5)

Each passing file is a complete, syntactically and semantically meaningful Tiferet Domain Event module. These files are used throughout all subsequent compiler phases (semantic analysis, type checking, IR generation, code generation, and optimization).

| # | Source File | Pre-computed AST | Description |
|---|------------|-----------------|-------------|
| 1 | [`samples/pass_imports_only.py`](../samples/pass_imports_only.py) | [`Parser/samples/pass_imports_only.json`](./samples/pass_imports_only.json) | Imports-only module with `core` and `app` import groups, no event definitions. Exercises Tier 1–2 artifact structure, `from ... import` with dotted paths, and multi-symbol imports. |
| 2 | [`samples/pass_minimal_event.py`](../samples/pass_minimal_event.py) | [`Parser/samples/pass_minimal_event.json`](./samples/pass_minimal_event.json) | Single `Ping` event with one `execute` method — minimal valid three-tier program. Exercises class definition with inheritance, method with `**kwargs`, return type annotation, docstring, snippet with return statement. |
| 3 | [`samples/pass_minimal_injection_event.py`](../samples/pass_minimal_injection_event.py) | [`Parser/samples/pass_minimal_injection_event.json`](./samples/pass_minimal_injection_event.json) | `Ping` event with constructor injection — attribute declaration, `__init__` method, and `execute` method. Exercises `# * attribute`, `# * init`, typed parameters, `self.pong` dotted name access, and assignment expressions. |
| 4 | [`samples/pass_multiple_operator_events.py`](../samples/pass_multiple_operator_events.py) | [`Parser/samples/pass_multiple_operator_events.json`](./samples/pass_multiple_operator_events.json) | Six arithmetic events (`Add`, `Subtract`, `Multiply`, `Divide`, `Modulus`, `Exponentiate`) in one module. Exercises multi-section parsing (SectionList repetition), all six arithmetic operators (`+`, `-`, `*`, `/`, `%`, `**`), and the full PEMDAS expression hierarchy. |
| 5 | [`samples/pass_helper_method_event.py`](../samples/pass_helper_method_event.py) | [`Parser/samples/pass_helper_method_event.json`](./samples/pass_helper_method_event.json) | `AddInteger` event with a `to_int` helper method alongside `execute`. Exercises multiple method members, chained arithmetic expression (`x + y * 3 - 2` parsed with correct PEMDAS precedence), RST docstrings, call expressions (`int(value)`, `self.to_int(a)`), and assignment with call RHS. |

**Verification:** Run any passing case through the CLI and confirm it produces valid JSON output with an `ast` key:

```bash
python compiler.py parse event samples/pass_minimal_event.py -o result.json
# Produces result.json with {"event_type": ..., "timestamp": ..., "source_file": ..., "ast": {...}}
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
