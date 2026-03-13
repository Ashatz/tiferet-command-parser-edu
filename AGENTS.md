# Tiferet Command Parser — Educational Scanner

**Repository:** tiferet-command-parser-edu
**Version:** 0.1.0
**Branch:** ece-506-submission
**Framework:** Tiferet (DDD, Domain Events)
**Purpose:** Educational compiler front-end for ECE 506 (Compiler Design) — performs lexical scanning on Python source files written in the Tiferet framework's Domain Event pattern.

## Architecture

This project is a Tiferet application. It uses Domain Events as the primary operational units, wired via YAML configuration (`config.yml`), and executed through the Tiferet CLI context. The scanner reads Tiferet-patterned Python source files, extracts artifact blocks (including imports), tokenizes them using a PLY-based lexer, injects synthetic layout tokens, computes domain metrics, and emits structured output (YAML/JSON).

### Pipeline (Feature: `scan.event`)

1. **ExtractText** — Reads source file, extracts `# *** imports` block and `# ** event:` artifact blocks. Supports `-x` filtering; imports are always included.
2. **LexerInitialized** — Validates that extracted text blocks are non-empty and ready for tokenization.
3. **PerformLexicalAnalysis** — Tokenizes blocks via `LexerService`, injects `INDENT`/`DEDENT` tokens via `IndentInjector`, and computes domain metrics.
4. **EmitScanResult** — Assembles the final payload with optional metrics, summary-only mode, extracted artifact names, and file output.

## Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml)
samples/
  empty_events.py                    — Empty placeholder events module (success case)
  add_error_event.py                 — Single AddError event with service injection (success case)
  error_events.py                    — Multi-event module: AddError, GetError, ListErrors, RenameError (success case)
  obsolete_rename_error_event.py     — RenameError with OBSOLETE-annotated method (success case)
  todo_get_error_event.py            — GetError with TODO-annotated method (success case)
  invalid_identifier_names_event.py  — Digit-prefixed class and member names (failure case)
  invalid_annotation_event.py        — Malformed OBSOLETE/TODO annotations (failure case)

Scanner/
  LEXICAL_SPEC.md        — Formal lexical specification for all 53 token types
  SCANNER_PROCESS.md     — Pipeline walkthrough and token category reference (ECE 506 submission doc)
  lexer.py               — Reference copy of src/utils/lexer.py
  lexer_assets.py        — Reference copy of src/assets/lexer.py

src/
  __init__.py            — Package exports and version (0.1.0)
  assets/
    __init__.py          — Assets package exports (imports lexer module)
    lexer.py             — Token constants (53 types), rule handlers (functions/regexes), RULES mapping dict
  domain/
    __init__.py          — Reserved for future domain objects
  events/
    settings.py          — Re-exports DomainEvent, TiferetError; imports local assets as `a`
    scan.py              — Scanner domain events: ExtractText, LexerInitialized, PerformLexicalAnalysis, EmitScanResult
    __init__.py          — Events package exports
    tests/
      test_scan.py       — 17 tests for all scanner events (DomainEvent.handle pattern)
  interfaces/
    lexer.py             — LexerService abstract interface (extends tiferet Service)
    __init__.py          — Interfaces package exports
  utils/
    lexer.py             — TiferetLexer: generic PLY host that loads tokens and rules dynamically from assets
    parser.py            — ArtifactBlockParser: artifact block extraction, imports parsing, extract filtering
    output.py            — ScanOutputWriter: file output with YAML/JSON format auto-detection
    indent.py            — IndentInjector: post-tokenization INDENT/DEDENT injection for method bodies
    __init__.py          — Utils package exports
    tests/
      test_lexer.py      — 43 tests for all lexer token rules
      test_parser.py     — 13 tests for artifact block parser utility
      test_output.py     — 11 tests for scan output writer utility
      test_indent.py     — 12 tests for IndentInjector
```

## Key Files

### `src/events/scan.py`
All scanner domain events. Each event follows the Tiferet pattern: `@DomainEvent.parameters_required` for validation, `self.verify()` for domain rules, service injection via constructor. Parsing and output concerns are delegated to utility classes.

- **ExtractText** — Reads source file, delegates artifact extraction to `ArtifactBlockParser`. The imports block (`__imports__`) is always included, even with `-x` extract filtering.
- **LexerInitialized** — Validates block content is non-empty.
- **PerformLexicalAnalysis** — Injects `LexerService`, tokenizes blocks, runs `IndentInjector.inject()` post-tokenization, computes metrics via `Counter`.
- **EmitScanResult** — Builds output payload. Delegates file writing to `ScanOutputWriter`. Supports `--summary-only` and `--with-metrics` flags.

### `src/utils/indent.py`
Post-tokenization utility (`IndentInjector`) with a single static method:

- **`inject(tokens)`** — Injects `INDENT`/`DEDENT` tokens at method-body indentation boundaries. Enters body mode on `ARTIFACT_MEMBER` matching `# * method:` or `# * init`, tracks paren depth to skip multi-line signatures, manages a column stack to handle nested indentation.

### `src/utils/parser.py`
Artifact block parser (`ArtifactBlockParser`) with static methods for:

- **`parse_extract_filter`** — Converts comma-separated extract string to a set of names.
- **`extract_imports_block`** — Locates and extracts the `# *** imports` section from source lines.
- **`extract_artifact_blocks`** — Walks source lines to extract all blocks matching a group type (e.g. `event`, `model`).
- **`filter_blocks`** — Applies an optional name filter to a list of blocks.

### `src/utils/output.py`
Scan output writer (`ScanOutputWriter`) with static methods for:

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
- **attrs** — Container attributes mapping event classes and lexer service
- **features** — `scan.event` pipeline with 4 chained commands
- **errors** — Structured error definitions (SOURCE_FILE_NOT_FOUND, TEXT_EXTRACTION_FAILED, LEXICAL_ERROR_DETECTED)
- **cli** — CLI command definition with args (source_file, -o, --format, -x, --summary-only, --with-metrics, --metrics-format)
- **interfaces** — `compiler` (AppInterfaceContext) and `compiler_cli` (CliContext) configurations

## CLI Usage

```bash
# Full scan (YAML output)
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
python -m pytest src/ -v    # 96 tests (43 lexer + 13 parser + 11 output + 17 events + 12 indent)
```

Tests use `DomainEvent.handle` for event invocation and mock `LexerService` for isolation. Utility tests validate parsing and output logic independently of domain events.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer generator
- `pyyaml>=6.0` — YAML output
- `pytest>=7.0` — Testing (dev)
