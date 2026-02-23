# Tiferet Command Parser — Educational Scanner

**Repository:** tiferet-command-parser-edu
**Version:** 0.1.0
**Branch:** v0.x-proto
**Framework:** Tiferet (DDD, Domain Events)
**Purpose:** Educational compiler front-end for ECE 506 (Compiler Design) — performs lexical scanning on Python source files written in the Tiferet framework's Domain Event pattern.

## Architecture

This project is a Tiferet application. It uses Domain Events as the primary operational units, wired via YAML configuration (`config.yml`), and executed through the Tiferet CLI context. The scanner reads Tiferet-patterned Python source files, extracts artifact blocks (including imports), tokenizes them using a PLY-based lexer, computes domain metrics, and emits structured output (YAML/JSON).

### Pipeline (Feature: `scan.event`)

1. **ExtractText** — Reads source file, extracts `# *** imports` block and `# ** event:` artifact blocks. Supports `-x` filtering; imports are always included.
2. **LexerInitialized** — Validates that extracted text blocks are non-empty and ready for tokenization.
3. **PerformLexicalAnalysis** — Tokenizes blocks via `LexerService`, computes domain metrics (class count, verify calls, service calls, etc.).
4. **EmitScanResult** — Assembles the final payload with optional metrics, summary-only mode, extracted artifact names, and file output.

## Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml)

src/
  __init__.py            — Package exports and version (0.1.0)
  domain/
    __init__.py          — Reserved for future domain objects
  events/
    settings.py          — Re-exports DomainEvent, TiferetError, a from tiferet.events
    scan.py              — Scanner domain events: ExtractText, LexerInitialized, PerformLexicalAnalysis, EmitScanResult
    __init__.py          — Events package exports
    tests/
      test_scan.py       — 17 tests for all scanner events (DomainEvent.handle pattern)
  interfaces/
    lexer.py             — LexerService abstract interface (extends tiferet Service)
    __init__.py          — Interfaces package exports
  utils/
    lexer.py             — TiferetLexer: PLY-based lexer implementing LexerService with 30+ token types
    __init__.py          — Utils package exports
    tests/
      test_lexer.py      — 37 tests for all lexer token rules

docs/
  LEXICAL_SPEC.md        — Formal lexical specification (token types, regex patterns, examples)
  PROJECT_SUMMARY.md     — Course context and educational goals
  README.md              — Usage instructions, CLI commands, test instructions
```

## Key Files

### `src/events/scan.py`
All scanner domain events. Each event follows the Tiferet pattern: `@DomainEvent.parameters_required` for validation, `self.verify()` for domain rules, service injection via constructor.

- **ExtractText** — Parses source files for `# *** imports` and `# ** <group_type>:` blocks. The imports block (`__imports__`) is always included, even with `-x` extract filtering.
- **LexerInitialized** — Validates block content is non-empty.
- **PerformLexicalAnalysis** — Injects `LexerService`, tokenizes blocks, computes metrics via `Counter`.
- **EmitScanResult** — Builds output payload. Includes `extracted_artifacts` list when `-x` is used. Supports `--summary-only` and `--with-metrics` flags.

### `src/utils/lexer.py`
PLY-based lexer (`TiferetLexer`) with token types organized by category:

- **Artifact comments:** `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`, `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`
- **Domain idioms:** `PARAMETERS_REQUIRED`, `VERIFY`, `SERVICE_CALL`, `FACTORY_CALL`, `CONST_REF`
- **Structural:** `CLASS`, `DEF`, `INIT`, `EXECUTE`, `RETURN`, `SELF`
- **Generic:** `PYTHON_KEYWORD`, `IDENTIFIER`, `STRING_LITERAL`, `NUMBER_LITERAL`, `DOCSTRING`, `LINE_COMMENT`
- **Punctuation/Layout:** `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`, `COMMA`, `COLON`, `ARROW`, `DOT`, `EQUALS`, `NEWLINE`, `UNKNOWN`

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
python -m pytest src/ -v    # 54 tests (37 lexer + 17 events)
```

Tests use `DomainEvent.handle` for event invocation and mock `LexerService` for isolation.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer generator
- `pyyaml>=6.0` — YAML output
- `pytest>=7.0` — Testing (dev)
