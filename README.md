# tiferet-command-parser-edu

Educational parser and static analysis tool for the Tiferet Domain Event pattern — extracts structured YAML metadata and dependency graphs from domain-driven Python event code. Built for ECE 506: Compiler Design at the University of Arizona.

### Project Abstract

This project develops a domain-specific compiler front-end for analyzing Python code written in the Tiferet framework's Domain Event pattern — a highly regular dialect that embodies Domain-Driven Design (DDD) principles and Clean Architecture layering. In enterprise software development, domain experts define critical business requirements that must be faithfully translated into features and then reliably implemented, tested, and maintained by cross-functional teams of developers and QA engineers. DDD addresses this challenge by establishing a shared ubiquitous language, which Tiferet realizes through interdependent object-oriented design patterns and a consistent set of guidelines governing their structure and interaction within an application.

In DDD, a Domain Event represents a discrete, well-defined operation within the domain — an action that changes or queries domain state in response to a business requirement. Tiferet's `DomainEvent` base class formalizes this concept: each event encapsulates a single operation, receives its dependencies via constructor injection, validates inputs declaratively through the `@DomainEvent.parameters_required` decorator, and enforces domain rules via `verify` calls. Domain Events are composed into feature workflows, where each step in the workflow is itself an event, enabling fine-grained orchestration of business logic.

This project focuses exclusively on Domain Events, which reside at the heart of every working Tiferet application. The Domain Event dialect is defined by a precise syntactic language: artifact comments serve as domain documentation, `DomainEvent` inheritance establishes the service boundary, `execute` methods orchestrate transactional use cases, injected service contracts provide infrastructure abstraction, model factories act as aggregate roots, and error codes form part of the shared domain vocabulary.

The compiler applies lexical analysis via PLY to recognize Tiferet idioms (artifact sections, import groups, validation decorators), syntactic analysis via PLY yacc to parse Domain Event classes into a structured Pydantic AST, semantic analysis to build symbol tables and resolve name references, and intermediate representation generation to produce a keter DSL capturing parameter contracts, ordered execution flow, and aggregated domain dependencies — serving as a semantically rich context store optimized for AI-assisted workflows.

### Project Overview

For the full project narrative — including detailed motivation (DDD & Clean Architecture context), scope, deliverables, compiler pipeline, educational outcomes, and future inquiry — see:

→ **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**

### Quick Start

**Prerequisites:** Python 3.10+, pip

```bash
# Clone the repository
git clone https://github.com/ashatz/tiferet-command-parser-edu.git
cd tiferet-command-parser-edu

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Usage

The compiler performs lexical scanning, syntactic parsing, semantic analysis, and intermediate representation generation on Python source files written in the Tiferet Domain Event pattern. It recognizes domain-specific tokens such as artifact comments, service calls, factory invocations, and structural keywords, builds a structured Pydantic AST reflecting the three-tier artifact hierarchy, constructs symbol tables with name resolution, and generates a keter IR.

#### CLI Commands

```bash
# Scan: tokenize a Tiferet event source file
python compiler.py scan event <source_file> -o output.yaml

# Parse: tokenize + parse into AST
python compiler.py parse event <source_file> -o output.json

# Semantic: lex + parse + build symbol table and resolve names
python compiler.py semantic event <source_file> -o output.json

# IR: lex + parse + semantic + generate keter IR
python compiler.py ir event <source_file> -o output.keter
```

**Common Options:**

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Write results to a file (format auto-detected from extension) |
| `--output-format` | Output format: `yaml`, `json`, `keter`, `console`, or `auto` |
| `--summary-only` | (scan) Output only metrics/summary (omit the full token list) |
| `--include-tokens` | (parse/semantic) Include tokens in the output |
| `--include-ast` | (semantic) Include the AST in the output |

**Examples:**

```bash
# Scan with YAML output
python compiler.py scan event samples/pass_minimal_event.py -o results.yaml

# Parse to JSON
python compiler.py parse event samples/pass_minimal_injection_event.py -o results.json

# Semantic analysis with AST included
python compiler.py semantic event samples/pass_multiple_operator_events.py -o results.json --include-ast true

# Generate keter IR
python compiler.py ir event samples/pass_helper_method_event.py -o output.keter
```

#### Token Categories

The scanner recognizes 58 token types across the following families (see [lexical_spec.md](./docs/guides/lexical_spec.md) for the complete formal specification):

- **Artifact Comments** — `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`, `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`, `OBSOLETE`, `TODO`
- **Documentation** — `DOCSTRING`, `LINE_COMMENT`
- **Import Statements** — `FROM`, `IMPORT`, `AS`
- **Structural Keywords** — `CLASS`, `DEF`, `INIT`, `RETURN`, `SELF`
- **Generic Python** — `PYTHON_KEYWORD`, `IDENTIFIER`, `STRING_LITERAL`, `NUMBER_LITERAL`
- **Boolean & Operators** — `TRUE`, `FALSE`, `DOUBLESTAR`, `PLUS`, `MINUS`, `STAR`, `SLASH`, `DOUBLESLASH`, `PERCENT`, `PIPE`, `AMPERSAND`, `TILDE`, `CARET`, `LSHIFT`, `RSHIFT`, `EQEQ`, `NOTEQ`, `LTEQ`, `GTEQ`, `LT`, `GT`, `AT`
- **Punctuation** — `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`, `COMMA`, `COLON`, `ARROW`, `DOT`, `EQUALS`
- **Layout & Indentation** — `NEWLINE`, `UNKNOWN`, `INDENT`, `DEDENT`

Unrecognized characters are emitted as `UNKNOWN` tokens for error reporting.

### Sample Files

The `samples/` directory contains 14 Tiferet Domain Event source files used for end-to-end testing across all pipeline stages. Five are well-formed success cases; nine are intentional failure cases exercising parser, semantic, and structural error detection.

**Success cases:**

| File | Description |
|------|-------------|
| `pass_imports_only.py` | Imports-only module — baseline success case with no events |
| `pass_minimal_event.py` | Single minimal `Ping` event with no injection or dependencies |
| `pass_minimal_injection_event.py` | Event with constructor injection and service dependency |
| `pass_multiple_operator_events.py` | Multi-event module with arithmetic operators |
| `pass_helper_method_event.py` | Event with a helper method alongside `execute` |

**Failure cases:**

| File | Description |
|------|-------------|
| `fail_bare_function.py` | Top-level function outside artifact structure |
| `fail_class_bare_attribute.py` | Class attribute without member artifact comment |
| `fail_class_bare_method.py` | Class method without member artifact comment |
| `fail_class_no_section.py` | Class definition without section artifact comment |
| `fail_import_no_group.py` | Import statement without import group comment |
| `fail_missing_group_header.py` | Group-level content without top-level artifact header |
| `fail_missing_member_artifact.py` | Member without required artifact annotation |
| `fail_unresolved_attribute.py` | Reference to an undefined attribute (semantic error) |
| `fail_unresolved_import.py` | Reference to an unresolved import (semantic error) |

### Running Tests

The test suite validates domain objects, mappers, utilities, and domain events across all pipeline stages.

```bash
# Run all tests (196 total)
python -m pytest src/ -v

# Domain object tests
python -m pytest src/domain/tests/ -v        # 40 tests (AST, Token, IR, Semantic)

# Mapper tests
python -m pytest src/mappers/tests/ -v        # 22 tests (Token, AST, Semantic, IR)

# Utility tests
python -m pytest src/utils/tests/ -v          # 116 tests (Lexer, Parser, Artifact, Output, Semantic, IR)

# Domain event tests
python -m pytest src/events/tests/ -v         # 18 tests (Lexer, Parser, IR)
```

**Total: 196 tests** across 16 test files

### Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml, pydantic)

docs/
  guides/
    lexical_spec.md      — Formal lexical specification for all 58 token types
    grammar_spec.md      — Context-free grammar specification and LR(1)/LALR verification
    utils/
      lexer.md           — Lexer utility guide (dynamic PLY pattern, BlockTracker)
      parser.md          — Parser utility guide (TiferetParser, AST structure)

samples/                 — End-to-end sample files for all pipeline stages
  pass_imports_only.py               — Imports-only module (success case)
  pass_minimal_event.py              — Minimal event with no injection (success case)
  pass_minimal_injection_event.py    — Event with service injection (success case)
  pass_multiple_operator_events.py   — Multi-event module with operators (success case)
  pass_helper_method_event.py        — Event with helper method (success case)
  fail_bare_function.py              — Top-level function outside artifact structure (failure case)
  fail_class_bare_attribute.py       — Class attribute without member artifact (failure case)
  fail_class_bare_method.py          — Class method without member artifact (failure case)
  fail_class_no_section.py           — Class without section artifact (failure case)
  fail_import_no_group.py            — Import without group comment (failure case)
  fail_missing_group_header.py       — Content without top-level header (failure case)
  fail_missing_member_artifact.py    — Member without artifact annotation (failure case)
  fail_unresolved_attribute.py       — Undefined attribute reference (semantic failure)
  fail_unresolved_import.py          — Unresolved import reference (semantic failure)

src/
  __init__.py            — Package exports and version (0.3.2)
  assets/
    __init__.py          — Exports `lexer` and `parser` asset modules
    lexer.py             — Token constants (58 types), rule handlers, RULES mapping dict
    parser.py            — Grammar precedence, AST builder helpers (build_module, build_group, etc.)
  domain/
    __init__.py          — Exports: TypeKind, ExprKind, StatementKind, Type, ParamList, Expression, Declaration, Statement, Token, SymbolKind, Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult, and all IR domain objects
    ast.py               — Pydantic AST domain objects (TypeKind, ExprKind, StatementKind enums; Type, ParamList, Expression, Declaration, Statement models)
    ir.py                — Pydantic IR domain objects (IRImport, IRImportGroup, IRAttribute, IREvent, IREventGroup, etc.) each with to_keter() serialization
    lexer.py             — Pydantic Token domain object (type, value, lineno, lexpos)
    semantic.py          — Pydantic symbol table domain objects (SymbolKind enum; Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult models)
    tests/
      test_ast.py        — 13 tests for AST domain object instantiation and validation
      test_ir.py         — 12 tests for IR domain objects and to_keter() output
      test_lexer.py      — 6 tests for Token domain object
      test_semantic.py   — 9 tests for symbol table domain objects
  events/
    __init__.py          — Exports: DomainEvent, TiferetError, a (assets)
    settings.py          — Re-exports DomainEvent, TiferetError from tiferet; imports local assets as `a`
    lexer.py             — Lexer domain events: PerformLexicalAnalysis, EmitScanResult
    parser.py            — Parser domain events: PerformSyntacticAnalysis, EmitParseResult
    semantic.py          — Semantic domain events: PerformSemanticAnalysis, EmitSemanticResult
    ir.py                — IR domain events: GenerateIR, EmitIRResult
    tests/
      test_lexer.py      — 6 tests for lexer events (DomainEvent.handle pattern)
      test_parser.py     — 6 tests for parser events
      test_ir.py         — 6 tests for GenerateIR and EmitIRResult
  interfaces/
    __init__.py          — Exports: LexerService, ParserService, IRService
    lexer.py             — LexerService abstract interface (extends tiferet Service)
    parser.py            — ParserService abstract interface (extends tiferet Service)
    ir.py                — IRService abstract interface (extends tiferet Service)
  mappers/
    __init__.py          — Exports: TokenAggregate/Tok, DeclarationAggregate/Decl, ExpressionAggregate/Expr, StatementAggregate/Stmt, TypeAggregate/Type, ParamListAggregate/ParamList, ScopeAggregate/SymbolScope, IREventGroupAggregate
    ast.py               — AST mappers with mutation methods and static factories
    ir.py                — IREventGroupAggregate with add_event() and add_import_group() helpers
    lexer.py             — TokenAggregate with factory methods (new, new_indent, new_dedent)
    semantic.py          — ScopeAggregate with scope factories and mutation methods
    tests/
      test_ir.py         — 4 tests for IREventGroupAggregate mutation helpers
      test_lexer.py      — 9 tests for TokenAggregate mapper
      test_semantic.py   — 9 tests for ScopeAggregate factories and mutation
  utils/
    __init__.py          — Exports: TiferetLexer, TiferetParser, ScanOutputWriter, SymbolTableBuilder, NameResolver, DocstringParser, IRGenerator
    artifact.py          — ArtifactBlockParser: artifact block extraction, imports parsing, extract filtering
    ir.py                — DocstringParser (static RST extraction) + IRGenerator (implements IRService; walks AST to produce IREventGroup)
    lexer.py             — BlockTracker (INDENT/DEDENT state machine) + TiferetLexer (PLY lexer host implementing LexerService)
    output.py            — ScanOutputWriter: YAML/JSON/keter file output with format auto-detection
    parser.py            — TokenStream (PLY adapter) + ParserBase + TiferetParser (PLY yacc parser implementing ParserService)
    semantic.py          — SymbolTableBuilder (single-pass scope/symbol construction) + NameResolver (name resolution against scope registry)
    tests/
      test_artifact.py   — 13 tests for ArtifactBlockParser
      test_ir.py         — 19 tests for DocstringParser and IRGenerator
      test_lexer.py      — 13 tests for TiferetLexer and BlockTracker
      test_output.py     — 11 tests for ScanOutputWriter
      test_parser.py     — 51 tests for TiferetParser grammar rules and AST structure
      test_semantic.py   — 9 tests for SymbolTableBuilder and NameResolver
```

### Project Documentation
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** — ECE 506 course context and educational goals
- **[PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md)** — Completed ECE 506 initial project definition template
- **[lexical_spec.md](./docs/guides/lexical_spec.md)** — Formal lexical specification for all token types
- **[grammar_spec.md](./docs/guides/grammar_spec.md)** — Context-free grammar specification and LALR verification
- **[AGENTS.md](./AGENTS.md)** — AI agent codebase index

**Guides:**
- **[Dynamic PLY Lexer](./docs/guides/utils/lexer.md)** — Architecture guide for the dynamic lexer pattern (assets, import chain, rule composition)
- **[Parser Utility](./docs/guides/utils/parser.md)** — Parser utility guide (TiferetParser, AST structure)

### Development Status

- **Current branch**: `ece-506-submission`
- **Version**: 0.3.2
- **Focus**: Full compiler front-end (lexer, parser, semantic analysis, IR generation) for the Tiferet Domain Event pattern
- **License**: MIT (educational reuse encouraged)

### Acknowledgments

ECE 506: Compiler Design – University of Arizona  
Inspired by real-world DDD frameworks and the need for tools that preserve domain fidelity in large codebases.

Questions, feedback, or contributions welcome — especially for educational purposes!
