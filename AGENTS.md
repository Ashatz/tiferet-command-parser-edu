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
- **Semantic analysis** (`src/events/semantic.py`, `src/utils/semantic.py`) — Symbol table construction and name resolution from the parsed AST. Standalone domain/mapper copies in `SemanticRoutines/`.
- **IR generation** (`src/events/ir.py`) — Walks the parsed AST to produce a keter IR conforming to the schema in `IntermediateRepresentation/schema.txt`.

### Pipeline (Feature: `scan.event`)

Defined in `config.yml`. Two chained commands:

1. **PerformLexicalAnalysis** — Reads the source file via `tiferet.File`, tokenizes the full text via `LexerService` (which internally uses `BlockTracker` for INDENT/DEDENT injection). Returns `List[TokenAggregate]`.
2. **EmitScanResult** — Assembles the scan result payload (tokens, count, timestamp) and optionally writes to YAML/JSON file.

### Pipeline (Feature: `parse.event`)

Defined in `config.yml`. Three chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Parses token stream via `ParserService` (PLY yacc). Produces a `DeclarationAggregate` AST root, serialized to dict via `model_dump()`.
3. **EmitParseResult** — Assembles parse result payload with AST, optional token list, and delegates file output to `ScanOutputWriter`.

### Pipeline (Feature: `semantic.event`)

Defined in `config.yml`. Four chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Same as `parse.event`.
3. **PerformSemanticAnalysis** — Builds symbol table and resolves names from the AST.
4. **EmitSemanticResult** — Assembles semantic result payload and delegates to output writer.

### Pipeline (Feature: `ir.event`)

Defined in `config.yml`. Five chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Same as `parse.event`.
3. **PerformSemanticAnalysis** — Same as `semantic.event`.
4. **GenerateIR** — Walks the AST via `IRGenerator` (injected as `IRService`) and produces an `IREventGroup`.
5. **EmitIRResult** — Calls `ir.to_keter()` and writes the keter DSL to file via `ScanOutputWriter`.

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

samples/                 — End-to-end sample Tiferet source files for all pipeline stages
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

Scanner/                 — Standalone scanner deliverable (ECE 506 submission)
  LEXICAL_SPEC.md        — Lexical specification document
  SCANNER_PROCESS.md     — Scanner design process document
  lexer.py               — Standalone PLY lexer implementation
  lexer_assets.py        — Standalone lexer token constants and rules
  samples/               — Pre-computed scanner JSON outputs (pass cases)

Parser/                  — Standalone parser deliverable (ECE 506 submission)
  README.md              — Parser documentation
  grammar_specification.md — Grammar specification document
  parser.py              — Standalone PLY yacc parser implementation
  parser_assets.py       — Standalone parser grammar constants and AST builders
  test_parser.py         — Parser unit tests
  samples/               — Pre-computed parser JSON outputs (pass cases)

IntermediateRepresentation/
  schema.txt             — Keter IR schema definition (EventGroup, Events, Params, Returns, etc.)
  samples/               — Pre-computed keter IR outputs (.keter files)

SemanticRoutines/        — Semantic analysis layer (ECE 506 submission)
  ast_domain.py          — Pydantic AST domain objects (Type, Expression, Declaration, Statement, ParamList)
  ast_mapper.py          — Pydantic AST mapper aggregates with mutation methods
  samples/               — Pre-computed JSON outputs (AST, symbol table, and failure cases)
    pass_imports_only.json
    pass_minimal_event.json
    pass_minimal_injection_event.json
    pass_multiple_operator_events.json
    pass_helper_method_event.json
    fail_unresolved_attribute.json
    fail_unresolved_import.json

src/
  __init__.py            — Package exports and version (0.3.2)
  assets/
    __init__.py          — Exports `lexer` and `parser` asset modules
    lexer.py             — Token constants (58 types), rule handlers, RULES mapping dict
    parser.py            — Grammar precedence, AST builder helpers (build_module, build_group, etc.)
  domain/
    __init__.py          — Exports: TypeKind, ExprKind, StatementKind, Type, ParamList, Expression, Declaration, Statement, Token, SymbolKind, Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult, and all IR domain objects
    ast.py               — Pydantic AST domain objects (TypeKind, ExprKind, StatementKind enums; Type, ParamList, Expression, Declaration, Statement models)
    ir.py                — Pydantic IR domain objects (IRImport, IRImportGroup, IRAttribute, IRInjection, IRParam, IRReturn, IRSnippet, IRExecute, IRMethod, IREvent, IREventGroup, etc.) each with to_keter() serialization
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
    ir.py                — IR domain events: GenerateIR (injects IRService, produces IREventGroup), EmitIRResult (serializes to keter DSL)
    lexer.py             — Lexer domain events: PerformLexicalAnalysis, EmitScanResult
    parser.py            — Parser domain events: PerformSyntacticAnalysis, EmitParseResult
    semantic.py          — Semantic domain events: PerformSemanticAnalysis, EmitSemanticResult
    tests/
      test_ir.py         — 6 tests for GenerateIR and EmitIRResult
      test_lexer.py      — 6 tests for lexer events (DomainEvent.handle pattern)
      test_parser.py     — 6 tests for parser events
  interfaces/
    __init__.py          — Exports: LexerService, ParserService, IRService
    ir.py                — IRService(Service): abstract `generate(ast, symbol_table) -> IREventGroup`
    lexer.py             — LexerService(Service): abstract `tokenize(text) -> List[TokenAggregate]`
    parser.py            — ParserService(Service): abstract `parse(tokens) -> Dict[str, Any]`
  mappers/
    __init__.py          — Exports: TokenAggregate/Tok, DeclarationAggregate/Decl, ExpressionAggregate/Expr, StatementAggregate/Stmt, TypeAggregate/Type, ParamListAggregate/ParamList, ScopeAggregate/SymbolScope, IREventGroupAggregate
    ast.py               — AST mappers: TypeAggregate, ParamListAggregate, ExpressionAggregate, DeclarationAggregate, StatementAggregate — all with mutation methods and static factories
    ir.py                — IREventGroupAggregate: extends IREventGroup with add_event() and add_import_group() mutation helpers
    lexer.py             — TokenAggregate: extends Token with factory methods (new, new_indent, new_dedent)
    semantic.py          — ScopeAggregate: extends Scope with static factories (new_module_scope, new_class_scope, new_method_scope) and mutation methods (add_symbol, add_child, remove_child, has_symbol, get_symbol)
    tests/
      test_ir.py         — 4 tests for IREventGroupAggregate mutation helpers
      test_lexer.py      — 9 tests for TokenAggregate mapper
      test_semantic.py   — 9 tests for ScopeAggregate factories and mutation
  utils/
    __init__.py          — Exports: TiferetLexer, TiferetParser, ScanOutputWriter, SymbolTableBuilder, NameResolver, DocstringParser, IRGenerator
    artifact.py          — ArtifactBlockParser: static methods for block extraction and filtering
    ir.py                — DocstringParser (static RST extraction) + IRGenerator (implements IRService; walks AST via public build_* methods)
    lexer.py             — BlockTracker (INDENT/DEDENT state machine) + TiferetLexer (PLY lexer host implementing LexerService)
    output.py            — ScanOutputWriter: YAML/JSON/keter file output with format auto-detection
    parser.py            — TokenStream (PLY adapter) + ParserBase + TiferetParser (PLY yacc parser implementing ParserService)
    semantic.py          — SymbolTableBuilder (single-pass AST walker for scope/symbol construction) + NameResolver (second-pass name resolution against scope registry)
    tests/
      test_artifact.py   — 13 tests for ArtifactBlockParser
      test_ir.py         — 19 tests for DocstringParser and IRGenerator
      test_lexer.py      — 13 tests for TiferetLexer and BlockTracker
      test_output.py     — 11 tests for ScanOutputWriter
      test_parser.py     — 51 tests for TiferetParser grammar rules and AST structure
      test_semantic.py   — 9 tests for SymbolTableBuilder and NameResolver
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

- `samples/` — Pre-computed JSON outputs from the parse and semantic pipelines, including both pass and fail cases (AST outputs, symbol table outputs, and unresolved name error cases)

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

### `src/utils/ir.py`
Two classes:
- **DocstringParser** — Static methods: `strip()`, `parse_param_descriptions()`, `parse_return_descriptions()` for RST docstring extraction.
- **IRGenerator** — Implements `IRService`. Public `build_*` methods walk the `DeclarationAggregate` AST to produce an `IREventGroup`. `encode_expr()` encodes expression nodes to string.

### `src/utils/output.py`
Scan output writer (`ScanOutputWriter`) with static methods:
- **`detect_format`** — Resolves output format from extension (`yaml`, `json`, `keter`) or explicit value.
- **`write`** — Writes a result payload to file as YAML, JSON, or plain-text keter DSL.
- **`parse_extract_names`** — Converts comma-separated extract string to a list for payload inclusion.

### `src/events/semantic.py`
Two domain events:
- **PerformSemanticAnalysis** — Validates the AST, builds a symbol table via `SymbolTableBuilder`, resolves names via `NameResolver`. Returns dict with `symbol_table` and `resolution`.
- **EmitSemanticResult** — Assembles semantic result payload with optional AST and tokens. Delegates file writing to `ScanOutputWriter`.

### `src/events/ir.py`
Two domain events:
- **GenerateIR** — Injects `IRService`; receives `ast` and optional `semantic` from pipeline; calls `ir_service.generate(ast, symbol_table)`; returns `IREventGroup`.
- **EmitIRResult** — Receives `IREventGroup`; calls `ir.to_keter()`; writes to `.keter` file or returns string.

### `src/utils/semantic.py`
Two classes:
- **SymbolTableBuilder** — Single-pass AST walker that constructs scopes (module, class, method) and populates symbol entries (imports, attributes, parameters, variables).
- **NameResolver** — Second-pass walker that resolves name references in expressions against the built scope registry, producing `ResolutionResult` with resolved and unresolved lists.

### `config.yml`
Tiferet YAML configuration defining:
- **attrs** — Container attributes for all pipeline events and services including `ir_service`, `generate_ir_event`, `emit_ir_result_event`
- **features** — `scan.event`, `parse.event`, `semantic.event`, and `ir.event` (5 commands: lex + parse + semantic + generate_ir + emit_ir)
- **errors** — `TEXT_EXTRACTION_FAILED`, `LEXICAL_ERROR_DETECTED`, `PARSER_NOT_INITIALIZED`, `INVALID_AST_STRUCTURE`, `MISSING_AST`
- **cli** — `scan event`, `parse event`, `semantic event`, and `ir event` commands
- **interfaces** — `compiler` (AppInterfaceContext) and `compiler_cli` (CliContext)

## CLI Usage

```bash
# Scan: tokenize and emit token list
python compiler.py scan event <source_file> -o output.yaml

# Parse: tokenize + parse into AST
python compiler.py parse event <source_file> -o output.json

# Semantic: lex + parse + build symbol table
python compiler.py semantic event <source_file> -o output.json

# IR: lex + parse + semantic + generate keter IR
python compiler.py ir event <source_file> -o output.keter
```

## Testing

```bash
python -m pytest src/ -v    # 196 tests total
```

Test breakdown:
- `src/domain/tests/test_ast.py` — 13 tests (AST domain objects)
- `src/domain/tests/test_ir.py` — 12 tests (IR domain objects, to_keter())
- `src/domain/tests/test_lexer.py` — 6 tests (Token domain object)
- `src/domain/tests/test_semantic.py` — 9 tests (Symbol table domain objects)
- `src/mappers/tests/test_ir.py` — 4 tests (IREventGroupAggregate mutation)
- `src/mappers/tests/test_lexer.py` — 9 tests (TokenAggregate mapper)
- `src/mappers/tests/test_semantic.py` — 9 tests (ScopeAggregate factories and mutation)
- `src/utils/tests/test_artifact.py` — 13 tests (ArtifactBlockParser)
- `src/utils/tests/test_ir.py` — 19 tests (DocstringParser + IRGenerator)
- `src/utils/tests/test_lexer.py` — 13 tests (TiferetLexer + BlockTracker)
- `src/utils/tests/test_output.py` — 11 tests (ScanOutputWriter)
- `src/utils/tests/test_parser.py` — 51 tests (TiferetParser grammar rules)
- `src/utils/tests/test_semantic.py` — 9 tests (SymbolTableBuilder + NameResolver)
- `src/events/tests/test_ir.py` — 6 tests (GenerateIR + EmitIRResult)
- `src/events/tests/test_lexer.py` — 6 tests (lexer domain events)
- `src/events/tests/test_parser.py` — 6 tests (parser domain events)

Tests use `DomainEvent.handle` for event invocation and mock `LexerService`/`ParserService` for isolation. Utility tests validate lexing, parsing, and output logic independently.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer and parser generator (PLY lex + yacc)
- `pyyaml>=6.0` — YAML output
- `pydantic` — AST domain objects and mappers (BaseModel, Field)
- `pytest>=7.0` — Testing (dev)
