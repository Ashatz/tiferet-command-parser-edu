# Parser — Syntactic Analysis for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)  
**Course:** ECE 506 — Compiler Design  
**University of Arizona**  
**Date:** April 2026  

**Author:** Andrew Shatz  
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

The parser performs **syntactic analysis** (the second phase of a compiler front-end) on Python source files written in the Tiferet framework's Domain Event pattern. It consumes the token stream produced by the lexer and `IndentInjector`, then constructs a structured **Abstract Syntax Tree (AST)** that reflects Tiferet's three-tier artifact comment hierarchy:

- **Tier 1 — Groups** (`# ***`): Top-level module sections (imports, events, utils, etc.)
- **Tier 2 — Sections** (`# **`): Individual components within a group (import categories, event definitions)
- **Tier 3 — Members** (`# *`): Class-level members (attributes, init, methods)

The parser is implemented using **PLY (Python Lex-Yacc)** — a Python implementation of the classic `lex` and `yacc` compiler construction tools. The grammar is an **LALR(1)** context-free grammar with 69 productions and 36 non-terminals.

## 2. Pipeline Overview

The parser integrates into the Tiferet feature pipeline as the `parse.event` feature, which chains six domain events:

```
Source File
    │
    ▼
┌───────────────┐   data_key: text_blocks
│  ExtractText  │──────────────────────────►
└───────────────┘
    │
    ▼
┌───────────────────┐   data_key: validated_blocks
│ LexerInitialized  │──────────────────────────────►
└───────────────────┘
    │
    ▼
┌──────────────────────────┐   data_key: analysis_result
│ PerformLexicalAnalysis   │──────────────────────────────►
└──────────────────────────┘
    │
    ▼
┌──────────────────────┐
│ ParserInitialized    │  (validation gate)
└──────────────────────┘
    │
    ▼
┌────────────────────────────────┐   data_key: ast
│ PerformSyntacticAnalysis       │──────────────────►
└────────────────────────────────┘
    │
    ▼
┌──────────────────┐  final payload (stdout / file)
│ EmitParseResult  │─────────────────────────────────►
└──────────────────┘
```

The first three stages (extraction, validation, lexical analysis) are shared with the `scan.event` pipeline. The parser-specific stages begin at **ParserInitialized**, which verifies the PLY yacc parser is ready, followed by **PerformSyntacticAnalysis**, which parses the token stream into an AST, and **EmitParseResult**, which assembles the output payload.

## 3. Grammar

The complete formal grammar specification — including the 4-tuple definition (V, Σ, R, S), all 36 non-terminals, 53 terminals, 69 productions, and worked examples from real Tiferet source files — is in:

→ **[grammar_specification.md](./grammar_specification.md)**

An LR(1) parse table visualization is provided in:

→ **[Tiferet Compiler LR(1).jpg](./Tiferet%20Compiler%20LR(1).jpg)**

### Grammar Highlights

- **Module** is the start symbol; a source file is a sequence of artifact groups.
- **Groups** are opened by `# ***` headers and contain sections.
- **Sections** are opened by `# **` headers and contain class definitions, function definitions, or import blocks.
- **Members** within classes are opened by `# *` headers and contain attribute declarations or method definitions.
- **Method/function bodies** are parsed as sequences of **code snippets** (optional comment header + statements) rather than full expression trees.
- **TokenSeq** is the generic content consumer; matched bracket groups (**Enclosed**) allow multi-line expressions inside parentheses, brackets, and braces.
- **OBSOLETE** and **TODO** annotations are modeled as optional prefixes at both the section and member tiers.

## 4. AST Structure

The parser produces a JSON/YAML-serializable AST with the following node types:

- **Module** — Root node containing a list of `groups`.
- **Group** — A `# ***` section with `header`, `sections`.
- **Section** — A `# **` component with `header`, `annotations`, `body`.
- **ClassDef** — Class with `name`, `bases`, `docstring`, `members`.
- **Member** — A `# *` artifact with `kind` (attribute/init/method), `annotations`, `body`.
- **MethodDef** — Method with `name`, `params`, `return_type`, `decorator`, `docstring`, `body` (list of snippets).
- **FuncDef** — Standalone function (same structure as MethodDef, no `self` requirement).
- **AttrDecl** — Typed attribute declaration with `name`, `type_annotation`.
- **ImportBlock** — List of `ImportStmt` nodes.
- **Snippet** — Logical code unit with optional `comment` and `statements`.
- **Stmt** — Statement with `tokens` (flat list + enclosed bracket groups) and optional `block` (compound statement body).
- **Annot** — Annotation with `kind` (OBSOLETE/TODO) and `text`.

## 5. Source Files

The parser implementation consists of two primary source files (standalone copies included in this directory for reference):

| Standalone Copy | Canonical Source | Description |
|-----------------|-----------------|-------------|
| `parser.py` | `src/utils/parser.py` | PLY yacc-based parser host (`TiferetParser`), `TokenStream` adapter, `PLYToken` wrapper, and semantic action dispatch |
| `parser_assets.py` | `src/assets/parser.py` | All 69 grammar productions as string constants, precedence rules, `RULES` mapping dict, and AST builder helper functions |

Additional modules involved in the parser pipeline:

| File | Description |
|------|-------------|
| `src/events/parser.py` | Parser domain events: `ParserInitialized`, `PerformSyntacticAnalysis`, `SyntacticAnalysisCompleted`, `EmitParseResult` |
| `src/interfaces/parser.py` | Abstract `ParserService(Service)` interface with single method `parse(tokens) -> Dict` |
| `src/utils/indent.py` | `IndentInjector`: post-tokenization utility that injects synthetic `INDENT`/`DEDENT` tokens at class-body and method-body boundaries |
| `src/utils/artifact.py` | `ArtifactBlockParser`: artifact block extraction, imports parsing, group header extraction, and extract filtering |

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
| `-o`, `--output` | Write results to a YAML or JSON file |
| `--format` | Output format: `yaml`, `json`, `console`, or `auto` |
| `-x`, `--extract` | Comma-separated artifact names to extract |
| `--summary-only` | Output only metrics/summary (omit token list) |
| `--with-metrics` | Include detailed lexical metrics section |

**Examples:**

```bash
# Parse a minimal event and view the AST on stdout
python compiler.py parse event Parser/samples/pass_minimal_event.py

# Parse with YAML file output
python compiler.py parse event Parser/samples/pass_multi_section_event.py -o result.yaml

# Parse with JSON output
python compiler.py parse event Parser/samples/pass_annotated_event.py -o result.json --format json

# Summary with metrics only (no full token list)
python compiler.py parse event Parser/samples/pass_multi_member_event.py --summary-only true --with-metrics true
```

### Verifying Failing Samples

Failing samples produce `SyntaxError` exceptions with descriptive messages indicating which artifact hierarchy rule was violated:

```bash
# Attribute without # * member header → SyntaxError
python compiler.py parse event Parser/samples/fail_class_bare_attribute.py

# Method without # * member header → SyntaxError
python compiler.py parse event Parser/samples/fail_class_bare_method.py

# Import without # ** group header → SyntaxError
python compiler.py parse event Parser/samples/fail_import_no_group.py
```

### Running the Test Battery

The `Parser/` directory includes a standalone test battery that exercises all 10 sample programs directly against the parser:

```bash
python Parser/test_parser.py
```

Expected output:

```
PASSING PROGRAMS (expect valid Module AST)
  pass_minimal_event.py                            PASS  (2 groups)
  pass_annotated_event.py                          PASS  (2 groups)
  pass_multi_member_event.py                       PASS  (2 groups)
  pass_multi_section_event.py                      PASS  (2 groups)
  pass_standalone_function.py                      PASS  (2 groups)

FAILING PROGRAMS (expect SyntaxError or extraction rejection)
  fail_class_bare_attribute.py                     PASS  (SyntaxError raised)
  fail_class_bare_method.py                        PASS  (SyntaxError raised)
  fail_import_no_group.py                          PASS  (SyntaxError raised)
  fail_class_no_section.py                         PASS  (rejected: no matching artifact blocks)
  fail_bare_function.py                            PASS  (rejected: no matching artifact blocks)

Results: 10/10 passed, 0/10 failed
```

### Running the Full Automated Test Suite

```bash
# Run all tests (121 total)
python -m pytest src/ -v

# Run only parser utility tests (16 tests — grammar rules and AST structure)
python -m pytest src/utils/tests/test_parser.py -v

# Run only parser domain event tests (9 tests — pipeline events)
python -m pytest src/events/tests/test_parser.py -v

# Run only indent injector tests (12 tests — INDENT/DEDENT injection)
python -m pytest src/utils/tests/test_indent.py -v
```

## 7. Sample Test Files

The `samples/` directory contains 10 Tiferet Domain Event source files — 5 well-formed programs that parse successfully and 5 intentional failure cases.

### Passing Test Cases (5)

Each passing file is a complete, syntactically and semantically meaningful Tiferet Domain Event module.

| File | Description |
|------|-------------|
| `pass_minimal_event.py` | Single `Ping` event with one method — minimal valid program |
| `pass_annotated_event.py` | `RenameError` event with `OBSOLETE` section annotation and `TODO` member annotation |
| `pass_multi_member_event.py` | `ListErrors` event with attribute, init, and decorated `execute` method |
| `pass_multi_section_event.py` | Two events (`GetError`, `ListErrors`) in one module — multi-section parsing |
| `pass_standalone_function.py` | Standalone utility function under `# *** utils` — imports-only parse (no event sections) |

### Failing Test Cases (5)

| File | Failure Type | Description |
|------|-------------|-------------|
| `fail_class_bare_attribute.py` | **SyntaxError** | Attribute declaration without `# *` member header inside a class |
| `fail_class_bare_method.py` | **SyntaxError** | Method definition without `# *` member header inside a class |
| `fail_import_no_group.py` | **SyntaxError** | Import statement without `# **` import group header |
| `fail_bare_function.py` | Extraction-level | Function definition without `# **` section header — not extracted by artifact parser |
| `fail_class_no_section.py` | Extraction-level | Class definition without `# **` section header — not extracted by artifact parser |

The first three failures produce parser-level `SyntaxError` exceptions. The last two demonstrate extraction-level enforcement: code that lacks proper artifact comment headers is never presented to the parser, effectively rejecting it at the compilation pipeline's front gate.
