# Tiferet Command Parser — Educational Compiler Front-End

**Repository:** tiferet-command-parser-edu
**Version:** 0.3.2
**Branch:** ece-506-submission
**Framework:** Tiferet (DDD, Domain Events) + Pydantic (AST domain objects)
**Python:** >= 3.10
**Purpose:** Educational compiler front-end for ECE 506 (Compiler Design) — performs lexical scanning, syntactic parsing, and AST construction on Python source files written in the Tiferet framework's Domain Event dialect.

## Architecture

This project has two layers:

1. **Tiferet pipeline layer** (`src/`) — A Tiferet application using Domain Events wired via `config.yml` and executed through the Tiferet CLI context. Handles lexical analysis, syntactic parsing, and structured output emission.
2. **Semantic routines layer** (`SemanticRoutines/`) — A standalone Pydantic-based AST domain model and mapper layer. Consumes the JSON AST output from the Tiferet pipeline and provides typed domain objects for semantic analysis (e.g., symbol table construction, name resolution).

### Bounded Contexts

- **Lexical scanning** (`src/events/lexer.py`) — Source file reading, tokenization via PLY, INDENT/DEDENT injection via `BlockTracker`.
- **Syntactic parsing** (`src/events/parser.py`) — Token stream parsing into a Pydantic AST via PLY yacc, AST validation, result emission.
- **Semantic analysis** (`SemanticRoutines/`) — AST domain objects and mappers for downstream analysis (symbol table, name resolution). Currently in development.

### Pipeline (Feature: `scan.event`)

Defined in `config.yml`. Two chained commands:

1. **PerformLexicalAnalysis** — Reads the source file via `tiferet.File`, tokenizes the full text via `LexerService` (which internally uses `BlockTracker` for INDENT/DEDENT injection). Returns `List[TokenAggregate]`.
2. **EmitScanResult** — Assembles the scan result payload (tokens, count, timestamp) and optionally writes to YAML/JSON file.

### Pipeline (Feature: `parse.event`)

Defined in `config.yml`. Three chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Parses token stream via `ParserService` (PLY yacc). Produces a `DeclarationAggregate` AST root, serialized to dict via `model_dump()`.
3. **EmitParseResult** — Assembles parse result payload with AST, optional token list, and delegates file output to `ScanOutputWriter`.

## Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml, pydantic)
PROJECT_PROPOSAL.md      — ECE 506 project proposal
PROJECT_SUMMARY.md       — ECE 506 project summary
README.md                — Project readme

docs/
  guides/
    lexical_spec.md      — Formal lexical specification for all token types
    grammar_spec.md      — Context-free grammar specification
    utils/
      lexer.md           — Lexer utility guide
      parser.md          — Parser utility guide (TiferetParser, AST structure)

samples/                 — End-to-end sample Tiferet source files for CLI testing
  add_error_event.py                 — Single AddError event with service injection
  error_events.py                    — Multi-event module: AddError, GetError, ListErrors, RenameError
  obsolete_rename_error_event.py     — RenameError with OBSOLETE-annotated method
  todo_get_error_event.py            — GetError with TODO-annotated method
  invalid_identifier_names_event.py  — Digit-prefixed class/member names (failure case)
  invalid_annotation_event.py        — Malformed OBSOLETE/TODO annotations (failure case)

Scanner/                 — Standalone scanner deliverable (ECE 506 submission)
  LEXICAL_SPEC.md        — Lexical specification document
  SCANNER_PROCESS.md     — Scanner design process document
  lexer.py               — Standalone PLY lexer implementation
  lexer_assets.py        — Standalone lexer token constants and rules
  samples/               — Scanner-specific test samples (pass/fail cases)

Parser/                  — Standalone parser deliverable (ECE 506 submission)
  README.md              — Parser documentation
  grammar_specification.md — Grammar specification document
  parser.py              — Standalone PLY yacc parser implementation
  parser_assets.py       — Standalone parser grammar constants and AST builders
  test_parser.py         — Parser unit tests
  samples/               — Parser-specific test samples (pass/fail cases)

SemanticRoutines/        — Semantic analysis layer (ECE 506 submission)
  ast_domain.py          — Pydantic AST domain objects (Type, Expression, Declaration, Statement, ParamList)
  ast_mapper.py          — Pydantic AST mapper aggregates with mutation methods
  samples/               — Tiferet source files for semantic analysis testing
    pass_imports_only.py
    pass_minimal_event.py
    pass_minimal_injection_event.py
    pass_multiple_operator_events.py
  results_ast/           — Pre-computed JSON AST outputs from the parse pipeline
    pass_imports_only.json
    pass_minimal_event_parse.json
    pass_minimal_injection_event.json
    pass_minimal_injection_event_parse.json
    pass_multiple_operator_events.json
  results_symbol/        — Pre-computed symbol table + resolution outputs
    pass_imports_only_symbol.json
    pass_minimal_event_symbol.json
    pass_minimal_injection_event_symbol.json
    pass_multiple_operator_events_symbol.json

src/
  __init__.py            — Package exports and version (0.3.2)
  assets/
    __init__.py          — Exports `lexer` and `parser` asset modules
    lexer.py             — Token constants (55 types), rule handlers, RULES mapping dict
    parser.py            — Grammar precedence, AST builder helpers (build_module, build_group, etc.)
  domain/
    __init__.py          — Exports: TypeKind, ExprKind, StatementKind, Type, ParamList, Expression, Declaration, Statement, Token, SymbolKind, Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult
    ast.py               — Pydantic AST domain objects (TypeKind, ExprKind, StatementKind enums; Type, ParamList, Expression, Declaration, Statement models)
    lexer.py             — Pydantic Token domain object (type, value, lineno, lexpos)
    symbol.py            — Pydantic symbol table domain objects (SymbolKind enum; Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult models)
    tests/
      test_ast.py        — 13 tests for AST domain object instantiation and validation
      test_lexer.py      — 6 tests for Token domain object
      test_symbol.py     — 9 tests for symbol table domain objects
  events/
    __init__.py          — Exports: DomainEvent, TiferetError, a (assets)
    settings.py          — Re-exports DomainEvent, TiferetError from tiferet; imports local assets as `a`
    lexer.py             — Lexer domain events: PerformLexicalAnalysis, EmitScanResult
    parser.py            — Parser domain events: PerformSyntacticAnalysis, EmitParseResult
    tests/
      test_lexer.py      — 6 tests for lexer events (DomainEvent.handle pattern)
      test_parser.py     — 6 tests for parser events
  interfaces/
    __init__.py          — Exports: LexerService, ParserService
    lexer.py             — LexerService(Service): abstract `tokenize(text) -> List[TokenAggregate]`
    parser.py            — ParserService(Service): abstract `parse(tokens) -> Dict[str, Any]`
  mappers/
    __init__.py          — Exports: TokenAggregate/Tok, DeclarationAggregate/Decl, ExpressionAggregate/Expr, StatementAggregate/Stmt, TypeAggregate/Type, ParamListAggregate/ParamList, ScopeAggregate/SymbolScope
    lexer.py             — TokenAggregate: extends Token with factory methods (new, new_indent, new_dedent)
    ast.py               — AST mappers: TypeAggregate, ParamListAggregate, ExpressionAggregate, DeclarationAggregate, StatementAggregate — all with mutation methods and static factories
    symbol.py            — ScopeAggregate: extends Scope with static factories (new_module_scope, new_class_scope, new_method_scope) and mutation methods (add_symbol, add_child, remove_child, has_symbol, get_symbol)
    tests/
      test_lexer.py      — 9 tests for TokenAggregate mapper
      test_symbol.py     — 9 tests for ScopeAggregate factories and mutation
  utils/
    __init__.py          — Exports: TiferetLexer, TiferetParser, ScanOutputWriter, SymbolTableBuilder, NameResolver
    lexer.py             — BlockTracker (INDENT/DEDENT state machine) + TiferetLexer (PLY lexer host implementing LexerService)
    parser.py            — TokenStream (PLY adapter) + ParserBase + TiferetParser (PLY yacc parser implementing ParserService)
    artifact.py          — ArtifactBlockParser: static methods for block extraction and filtering
    output.py            — ScanOutputWriter: YAML/JSON file output with format auto-detection
    symbol.py            — SymbolTableBuilder (single-pass AST walker for scope/symbol construction) + NameResolver (second-pass name resolution against scope registry)
    tests/
      test_lexer.py      — 13 tests for TiferetLexer and BlockTracker
      test_parser.py     — 45 tests for TiferetParser grammar rules and AST structure
      test_artifact.py   — 13 tests for ArtifactBlockParser
      test_output.py     — 11 tests for ScanOutputWriter
      test_symbol.py     — 9 tests for SymbolTableBuilder and NameResolver (4 builder + 3 resolver + 2 edge cases)
```

## Key Concepts

### AST Domain Model (Pydantic)

The AST is built from Pydantic `BaseModel` classes defined in `src/domain/ast.py` and extended with mutation methods in `src/mappers/ast.py`. This is separate from the Tiferet framework's `schematics`-based DomainObject system.

- **TypeKind** — Enum: `unknown`, `None`, `bool`, `str`, `int`, `float`, `list`, `dict`, `class`, `func`, `artifact`, `module`
- **ExprKind** — Enum: `add`, `sub`, `mul`, `div`, `mod`, `exp`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `name`, `num_val`, `int_val`, `str_val`, `bool_val`, `assign`, `args_list`, `call`, `import`, `import_as`, `import_multi`, `artifact`, `comment`
- **StatementKind** — Enum: `decl`, `expr`, `if_else`, `for`, `while`, `print`, `return`, `block`, `import`, `import_from`, `artifact`, `comment`, `snippet`

AST nodes use linked-list chaining via `.next` fields (not Python lists). Mapper aggregates provide `set_next()`, `set_left()`, `set_right()`, `set_return_type()`, and static factories like `Decl.new_module_decl()`, `Stmt.new_artifact_stmt()`, `Expr.new_name_expr()`, etc.

### SemanticRoutines Layer

`SemanticRoutines/` contains a parallel copy of the AST domain/mapper files (`ast_domain.py`, `ast_mapper.py`) that mirrors `src/domain/ast.py` and `src/mappers/ast.py` but is importable as a standalone package for semantic analysis work. It also contains:

- `samples/` — Tiferet source files designed for semantic analysis testing
- `results_ast/` — Pre-computed JSON AST outputs produced by running `python compiler.py parse event <sample> -o <output>.json`
- `results_symbol/` — Directory for expected symbol table outputs (currently empty, to be populated during symbol table implementation)

### INDENT/DEDENT Injection

The `BlockTracker` class in `src/utils/lexer.py` handles indentation tracking. Unlike the previous `IndentInjector` (which was a separate post-processing step), `BlockTracker` is integrated directly into `TiferetLexer.tokenize()`. It:
- Tracks parenthesis depth to skip multi-line signatures
- Detects CLASS and METHOD boundaries via regex patterns on artifact tokens
- Computes column positions from `lexpos` against the original source text
- Injects `INDENT`/`DEDENT` `TokenAggregate` instances inline during tokenization

### Parser Architecture

`TiferetParser` extends `ParserBase` which implements `ParserService`. Grammar rules are defined as `p_*` methods directly on `TiferetParser` (PLY convention). The parser:
- Receives `List[TokenAggregate]` from the lexer
- Adapts them to PLY via `TokenStream` (wraps each in a `PLYToken`)
- Builds Pydantic `DeclarationAggregate` / `StatementAggregate` / `ExpressionAggregate` AST nodes in semantic actions
- Returns a `DeclarationAggregate` root (module declaration) which is serialized via `.model_dump(exclude_none=True, exclude_unset=True)`

## Key Files

### `src/events/lexer.py`
Two domain events:
- **PerformLexicalAnalysis** — Injects `LexerService`, reads source file via `tiferet.File`, tokenizes full text. Returns `List[TokenAggregate]`.
- **EmitScanResult** — Assembles result payload with tokens and metadata. Delegates file writing to `ScanOutputWriter`.

### `src/events/parser.py`
Two domain events:
- **PerformSyntacticAnalysis** — Injects `ParserService`, parses tokens into AST, validates root is a `Decl`, returns serialized dict.
- **EmitParseResult** — Assembles parse result with AST, optional tokens, and delegates file output.

### `src/utils/lexer.py`
Two classes:
- **BlockTracker** — State machine for INDENT/DEDENT injection. Tracks paren depth, CLASS/METHOD boundaries, column positions.
- **TiferetLexer** — PLY lexer host implementing `LexerService`. Loads token rules dynamically from `src/assets/lexer.py`. Integrates `BlockTracker` for layout token injection.

### `src/utils/parser.py`
Three classes:
- **TokenStream** — Adapter converting `List[TokenAggregate]` to PLY-compatible token stream.
- **ParserBase** — Base class with shared utilities (`parse_member_kind`, `get_attribute_type`, `p_error`). Loads precedence and tokens from `src/assets/parser.py`.
- **TiferetParser** — Full grammar implementation with `p_*` rule methods. Builds Pydantic AST nodes in semantic actions.

### `src/utils/artifact.py`
Artifact block parser (`ArtifactBlockParser`) with static methods:
- **`parse_extract_filter`** — Converts comma-separated extract string to a set of names.
- **`extract_imports_block`** — Locates and extracts the `# *** imports` section.
- **`extract_group_header`** — Extracts the first non-imports top-level group header.
- **`extract_artifact_blocks`** — Walks source lines to extract all blocks matching a group type.
- **`filter_blocks`** — Applies an optional name filter to a list of blocks.

### `src/utils/output.py`
Scan output writer (`ScanOutputWriter`) with static methods:
- **`detect_format`** — Resolves output format from explicit value or file extension auto-detection.
- **`write`** — Writes a result payload to file as YAML or JSON.
- **`parse_extract_names`** — Converts comma-separated extract string to a list for payload inclusion.

### `config.yml`
Tiferet YAML configuration defining:
- **attrs** — Container attributes: `perform_lexical_analysis_event`, `perform_syntactic_analysis_event`, `emit_scan_result_event`, `emit_parse_result_event`, `lexer_service`, `parser_service`
- **features** — `scan.event` (2 commands: lex + emit) and `parse.event` (3 commands: lex + parse + emit)
- **errors** — `TEXT_EXTRACTION_FAILED`, `LEXICAL_ERROR_DETECTED`, `PARSER_NOT_INITIALIZED`, `INVALID_AST_STRUCTURE`, `MISSING_AST`
- **cli** — `scan event` and `parse event` commands with args (source_file, -o, --output-format, --summary-only, --include-tokens)
- **interfaces** — `compiler` (AppInterfaceContext) and `compiler_cli` (CliContext)

## CLI Usage

```bash
# Scan: tokenize and emit token list
python compiler.py scan event <source_file> -o output.yaml
python compiler.py scan event <source_file> -o output.json --output-format json

# Parse: tokenize + parse into AST
python compiler.py parse event <source_file> -o output.json
python compiler.py parse event <source_file> -o output.json --include-tokens true
```

## Testing

```bash
python -m pytest src/ -v    # 149 tests total
```

Test breakdown:
- `src/domain/tests/test_ast.py` — 13 tests (AST domain objects)
- `src/domain/tests/test_lexer.py` — 6 tests (Token domain object)
- `src/domain/tests/test_symbol.py` — 9 tests (Symbol table domain objects)
- `src/mappers/tests/test_lexer.py` — 9 tests (TokenAggregate mapper)
- `src/mappers/tests/test_symbol.py` — 9 tests (ScopeAggregate mapper)
- `src/utils/tests/test_lexer.py` — 13 tests (TiferetLexer + BlockTracker)
- `src/utils/tests/test_parser.py` — 45 tests (TiferetParser grammar rules)
- `src/utils/tests/test_artifact.py` — 13 tests (ArtifactBlockParser)
- `src/utils/tests/test_output.py` — 11 tests (ScanOutputWriter)
- `src/utils/tests/test_symbol.py` — 9 tests (SymbolTableBuilder + NameResolver)
- `src/events/tests/test_lexer.py` — 6 tests (lexer domain events)
- `src/events/tests/test_parser.py` — 6 tests (parser domain events)

Tests use `DomainEvent.handle` for event invocation and mock `LexerService`/`ParserService` for isolation. Utility tests validate lexing, parsing, and output logic independently.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer and parser generator (PLY lex + yacc)
- `pyyaml>=6.0` — YAML output
- `pydantic` — AST domain objects and mappers (BaseModel, Field)
- `pytest>=7.0` — Testing (dev)
