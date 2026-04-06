# Tiferet Command Parser — Educational Scanner & Parser

**Repository:** tiferet-command-parser-edu
**Version:** 0.3.0
**Branch:** v0.3-release
**Framework:** Tiferet (DDD, Domain Events)
**Purpose:** Educational compiler front-end for ECE 506 (Compiler Design) — performs lexical scanning and syntactic parsing on Python source files written in the Tiferet framework's Domain Event pattern.

## Architecture

This project is a Tiferet application. It uses Domain Events as the primary operational units, wired via YAML configuration (`config.yml`), and executed through the Tiferet CLI context. The compiler reads Tiferet-patterned Python source files, extracts artifact blocks (including imports), tokenizes them using a PLY-based lexer, injects synthetic layout tokens, parses the token stream into a structured AST via a PLY yacc-based parser, computes domain metrics, and emits structured output (YAML/JSON).

The compiler has two bounded contexts:
- **Lexical scanning** (`src/events/scan.py`) — text extraction, tokenization, metrics, and scan result emission.
- **Syntactic parsing** (`src/events/parser.py`) — parser initialization, AST construction, and parse result emission.

### Pipeline (Feature: `scan.event`)

The `scan.event` pipeline chains lexical and syntactic events:

1. **ExtractText** — Reads source file, extracts `# *** imports` block and `# ** event:` artifact blocks. Supports `-x` filtering; imports are always included.
2. **LexerInitialized** — Validates that extracted text blocks are non-empty and ready for tokenization.
3. **PerformLexicalAnalysis** — Tokenizes blocks via `LexerService`, injects `INDENT`/`DEDENT` tokens via `IndentInjector`, and computes domain metrics.
4. **ParserInitialized** — Validates that the `ParserService` is properly instantiated.
5. **PerformSyntacticAnalysis** — Parses the token stream into a structured AST via `ParserService`.
6. **SyntacticAnalysisCompleted** — Finalizes the AST and enriches the result payload.
7. **EmitScanResult** — Assembles the final payload with optional metrics, summary-only mode, extracted artifact names, and file output.

### Pipeline (Feature: `parse.event`)

The `parse.event` pipeline shares lexical steps but uses a dedicated parse result emitter:

1. **ExtractText** — Same as `scan.event`.
2. **LexerInitialized** — Same as `scan.event`.
3. **PerformLexicalAnalysis** — Same as `scan.event`.
4. **ParserInitialized** — Same as `scan.event`.
5. **PerformSyntacticAnalysis** — Same as `scan.event`.
6. **EmitParseResult** — Assembles the parse result payload with AST, optional metrics, and file output.

## Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml)
docs/
  guides/
    lexical_spec.md      — Formal lexical specification for all 53 token types
    grammar_spec.md      — Context-free grammar specification and LR(1)/LALR verification
    utils/
      parser.md          — Parser utility guide (TiferetParser, ParserService, AST structure)
samples/
  empty_events.py                    — Empty placeholder events module (success case)
  add_error_event.py                 — Single AddError event with service injection (success case)
  error_events.py                    — Multi-event module: AddError, GetError, ListErrors, RenameError (success case)
  obsolete_rename_error_event.py     — RenameError with OBSOLETE-annotated method (success case)
  todo_get_error_event.py            — GetError with TODO-annotated method (success case)
  invalid_identifier_names_event.py  — Digit-prefixed class and member names (failure case)
  invalid_annotation_event.py        — Malformed OBSOLETE/TODO annotations (failure case)

src/
  __init__.py            — Package exports and version (0.3.0)
  assets/
    __init__.py          — Assets package exports
    lexer.py             — Token constants (53 types), rule handlers (functions/regexes), RULES mapping dict
    parser.py            — Grammar constants (69 productions), precedence, RULES mapping, AST builders
  domain/
    __init__.py          — Reserved for future domain objects
  events/
    settings.py          — Re-exports DomainEvent, TiferetError; imports local assets as `a`
    scan.py              — Scanner domain events: ExtractText, LexerInitialized, PerformLexicalAnalysis, EmitScanResult
    parser.py            — Parser domain events: ParserInitialized, PerformSyntacticAnalysis, SyntacticAnalysisCompleted, EmitParseResult
    __init__.py          — Events package exports
    tests/
      test_scan.py       — 17 tests for all scanner events (DomainEvent.handle pattern)
      test_parser.py     — 9 tests for parser domain events
  interfaces/
    lexer.py             — LexerService abstract interface (extends tiferet Service)
    parser.py            — ParserService abstract interface (extends tiferet Service)
    __init__.py          — Interfaces package exports
  utils/
    lexer.py             — TiferetLexer: generic PLY host that loads tokens and rules dynamically from assets
    parser.py            — TiferetParser: PLY yacc-based parser with dynamic grammar loading from assets
    artifact.py          — ArtifactBlockParser: artifact block extraction, imports parsing, extract filtering
    output.py            — ScanOutputWriter: file output with YAML/JSON format auto-detection
    indent.py            — IndentInjector: post-tokenization INDENT/DEDENT injection for method bodies
    __init__.py          — Utils package exports
    tests/
      test_lexer.py      — 43 tests for all lexer token rules
      test_parser.py     — 16 tests for parser grammar rules and AST structure
      test_artifact.py   — 13 tests for artifact block parser utility
      test_output.py     — 11 tests for scan output writer utility
      test_indent.py     — 12 tests for IndentInjector
```

## Key Files

### `src/events/scan.py`
Scanner domain events. Each event follows the Tiferet pattern: `@DomainEvent.parameters_required` for validation, `self.verify()` for domain rules, service injection via constructor. Parsing and output concerns are delegated to utility classes.

- **ExtractText** — Reads source file, delegates artifact extraction to `ArtifactBlockParser`. The imports block (`__imports__`) is always included, even with `-x` extract filtering.
- **LexerInitialized** — Validates block content is non-empty.
- **PerformLexicalAnalysis** — Injects `LexerService`, tokenizes blocks, runs `IndentInjector.inject()` post-tokenization, computes metrics via `Counter`.
- **EmitScanResult** — Builds output payload. Delegates file writing to `ScanOutputWriter`. Supports `--summary-only` and `--with-metrics` flags.

### `src/events/parser.py`
Parser domain events. Dedicated bounded context for syntactic analysis, separate from lexical scanning.

- **ParserInitialized** — Validation gate: verifies `ParserService` is properly instantiated before parsing.
- **PerformSyntacticAnalysis** — Core analytical event: parses token stream via injected `ParserService`, validates the resulting AST root is a Module.
- **SyntacticAnalysisCompleted** — Terminal event: finalizes AST, enriches result with group count metadata.
- **EmitParseResult** — Final event in `parse.event` pipeline: assembles result payload with AST, optional metrics, and delegates file output to `ScanOutputWriter`.

### `src/utils/parser.py`
PLY yacc-based syntactic parser (`TiferetParser`) implementing `ParserService`. Dynamically loads grammar rules from `src/assets/parser.py`, mirroring the `TiferetLexer` pattern. Includes `TokenStream` adapter (feeds `List[Dict]` to PLY), `PLYToken` wrapper, semantic action dispatch table (`_SEMANTIC_ACTIONS`), and AST-building helper functions.

### `src/interfaces/parser.py`
Abstract `ParserService(Service)` with single method `parse(tokens) -> Dict[str, Any]`.

### `src/assets/parser.py`
Grammar assets: `TOKENS` (re-exported from lexer), `precedence` tuple, 69 BNF production rules as string constants, `RULES` mapping dict, and AST builder helper functions (`build_module`, `build_group`, `build_section`, `build_class_def`, `build_member`, `build_method_def`, etc.).

### `src/utils/indent.py`
Post-tokenization utility (`IndentInjector`) with a single static method:
- **`inject(tokens)`** — Injects `INDENT`/`DEDENT` tokens at method-body indentation boundaries. Enters body mode on `ARTIFACT_MEMBER` matching `# * method:` or `# * init`, tracks paren depth to skip multi-line signatures, manages a column stack to handle nested indentation.

### `src/utils/artifact.py`
Artifact block parser (`ArtifactBlockParser`) with static methods:
- **`parse_extract_filter`** — Converts comma-separated extract string to a set of names.
- **`extract_imports_block`** — Locates and extracts the `# *** imports` section.
- **`extract_artifact_blocks`** — Walks source lines to extract all blocks matching a group type.
- **`filter_blocks`** — Applies an optional name filter to a list of blocks.

### `src/utils/output.py`
Scan output writer (`ScanOutputWriter`) with static methods:
- **`detect_format`** — Resolves output format from explicit value or file extension auto-detection.
- **`write`** — Writes a result payload to file as YAML or JSON.
- **`parse_extract_names`** — Converts comma-separated extract string to a list for payload inclusion.

### `src/utils/lexer.py`
Generic PLY lexer host (`TiferetLexer`) with 53 token types organized by category:

- **Artifact comments:** `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`, `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`, `OBSOLETE`, `TODO`
- **Documentation:** `DOCSTRING`, `LINE_COMMENT`
- **Structural:** `CLASS`, `DEF`, `INIT`, `RETURN`, `SELF`
- **Generic:** `PYTHON_KEYWORD`, `IDENTIFIER`, `STRING_LITERAL`, `NUMBER_LITERAL`
- **Operators:** `DOUBLESTAR`, `PLUS`, `MINUS`, `STAR`, `SLASH`, `DOUBLESLASH`, `PERCENT`, `PIPE`, `AMPERSAND`, `TILDE`, `CARET`, `LSHIFT`, `RSHIFT`, `EQEQ`, `NOTEQ`, `LTEQ`, `GTEQ`, `LT`, `GT`, `AT`
- **Punctuation/Layout:** `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`, `COMMA`, `COLON`, `ARROW`, `DOT`, `EQUALS`, `NEWLINE`, `UNKNOWN`
- **Indentation (injected):** `INDENT`, `DEDENT`

### `src/interfaces/lexer.py`
Abstract `LexerService(Service)` with single method `tokenize(text) -> List[Dict]`.

### `config.yml`
Tiferet YAML configuration defining:
- **attrs** — Container attributes mapping event classes, lexer service, and parser service
- **features** — `scan.event` pipeline (7 chained commands: lexical + syntactic + emit) and `parse.event` pipeline (6 chained commands: lexical + syntactic + parse emit)
- **errors** — Structured error definitions (SOURCE_FILE_NOT_FOUND, TEXT_EXTRACTION_FAILED, LEXICAL_ERROR_DETECTED, PARSER_NOT_INITIALIZED, INVALID_AST_STRUCTURE, MISSING_AST)
- **cli** — CLI command definition with args (source_file, -o, --format, -x, --summary-only, --with-metrics, --metrics-format)
- **interfaces** — `compiler` (AppInterfaceContext) and `compiler_cli` (CliContext) configurations

## CLI Usage

```bash
# Full scan with lexical + syntactic analysis (YAML output)
python compiler.py scan event <source_file> -o output.yaml

# JSON output
python compiler.py scan event <source_file> -o output.json --format json

# Summary with metrics only
python compiler.py scan event <source_file> -o output.yaml --summary-only true --with-metrics true

# Extract specific artifacts (imports always included)
python compiler.py scan event <source_file> -o output.yaml -x add_error,get_error
```

## Testing

```bash
python -m pytest src/ -v    # 121 tests (43 lexer + 16 parser util + 13 artifact + 11 output + 12 indent + 17 scanner events + 9 parser events)
```

Tests use `DomainEvent.handle` for event invocation and mock `LexerService`/`ParserService` for isolation. Utility tests validate lexing, parsing, and output logic independently of domain events.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer and parser generator
- `pyyaml>=6.0` — YAML output
- `pytest>=7.0` — Testing (dev)
