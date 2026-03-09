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
samples/
  add_calc_event.py      — Single AddNumber calculator event (success case)
  add_error_event.py     — Single AddError event with service injection (success case)
  base_calc_event.py     — BasicCalcEvent base class with verify_number (success case)
  error_events.py        — Multi-event module: AddError, GetError, ListErrors, RenameError (success case)
  invalid_class_name_event.py        — Digit-prefixed class name (failure case)
  invalid_member_names_event.py      — Digit-prefixed attribute/method names (failure case)
  remove_error_message_event.py      — RemoveErrorMessage event (success case)

src/
  __init__.py            — Package exports and version (0.1.0)
  assets/
    __init__.py          — Assets package exports (imports lexer module)
    lexer.py             — Token constants, rule handlers (functions/regexes), RULES mapping dict
  domain/
    __init__.py          — Reserved for future domain objects
  events/
    settings.py          — Re-exports DomainEvent, TiferetError; imports local assets as `a`
    scan.py              — Scanner domain events: ExtractText, LexerInitialized, PerformLexicalAnalysis, EmitScanResult
    __init__.py          — Events package exports (DomainEvent, TiferetError, a, all events)
    tests/
      test_scan.py       — 17 tests for all scanner events (DomainEvent.handle pattern)
  interfaces/
    lexer.py             — LexerService abstract interface (extends tiferet Service)
    __init__.py          — Interfaces package exports
  utils/
    lexer.py             — TiferetLexer: generic PLY host that loads tokens and rules dynamically from assets
    parser.py            — ArtifactBlockParser: artifact block extraction, imports parsing, extract filtering
    output.py            — ScanOutputWriter: file output with YAML/JSON format auto-detection
    __init__.py          — Utils package exports
    tests/
      test_lexer.py      — 43 tests for all lexer token rules
      test_parser.py     — 13 tests for artifact block parser utility
      test_output.py     — 11 tests for scan output writer utility
```

## Key Files

### `src/events/scan.py`
All scanner domain events. Each event follows the Tiferet pattern: `@DomainEvent.parameters_required` for validation, `self.verify()` for domain rules, service injection via constructor. Parsing and output concerns are delegated to utility classes (`ArtifactBlockParser`, `ScanOutputWriter`).

- **ExtractText** — Reads source file, delegates artifact extraction to `ArtifactBlockParser`. The imports block (`__imports__`) is always included, even with `-x` extract filtering.
- **LexerInitialized** — Validates block content is non-empty.
- **PerformLexicalAnalysis** — Injects `LexerService`, tokenizes blocks, computes metrics via `Counter`.
- **EmitScanResult** — Builds output payload. Delegates file writing to `ScanOutputWriter`. Supports `--summary-only` and `--with-metrics` flags.

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

### `src/assets/lexer.py`
Lexer assets module containing all token constants, rule handlers, and the composable `RULES` mapping. Organized under `# *** constants`:

- **Token name constants** — Individual string constants (e.g., `ARTIFACT_IMPORTS_START = 'ARTIFACT_IMPORTS_START'`) for composing `TOKENS` tuples.
- **`TOKENS`** — Ordered tuple of all token names, sourced from individual constants.
- **`_python_keywords`** — Set of Python reserved words for keyword detection in the identifier rule.
- **Rule handlers** — Functions (e.g., `ARTIFACT_IMPORTS_START(self, t)` with docstring regex) and regex strings (e.g., `DOUBLESTAR = r'\*\*'`) that define lexer behavior. Named without any lexer-specific prefix; the `t_` PLY convention exists only in `RULES` keys.
- **`RULES`** — Dict mapping PLY `t_`-prefixed names to their handler constants. This is the composable unit for dynamic lexer configuration — different lexer variants assemble different `RULES` dicts from the same building blocks.

The assets module is accessed throughout the project via `a.lexer` (where `a` is the local `src.assets` package, imported through the events chain).

### `src/utils/lexer.py`
Generic PLY lexer host (`TiferetLexer`) implementing `LexerService`. Loads `TOKENS` and `RULES` dynamically from `a.lexer` (assets) at init time. Function rules are bound via `MethodType`; string rules are set directly. Only PLY infrastructure (`t_ignore`, `t_error`) and the public `tokenize`/`_find_column` methods remain on the class.

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
python -m pytest src/ -v    # 83 tests (42 lexer + 13 parser + 11 output + 17 events)
```

Tests use `DomainEvent.handle` for event invocation and mock `LexerService` for isolation. Utility tests validate parsing and output logic independently of domain events.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer generator
- `pyyaml>=6.0` — YAML output
- `pytest>=7.0` — Testing (dev)
