# tiferet-command-parser-edu

Educational parser and static analysis tool for the Tiferet Domain Event pattern — extracts structured YAML metadata and dependency graphs from domain-driven Python event code. Built for ECE 506: Compiler Design at the University of Arizona.

### Project Abstract

This project develops a domain-specific compiler front-end for analyzing Python code written in the Tiferet framework's Domain Event pattern — a highly regular dialect that embodies Domain-Driven Design (DDD) principles and Clean Architecture layering. In enterprise software development, domain experts define critical business requirements that must be faithfully translated into features and then reliably implemented, tested, and maintained by cross-functional teams of developers and QA engineers. DDD addresses this challenge by establishing a shared ubiquitous language, which Tiferet realizes through interdependent object-oriented design patterns and a consistent set of guidelines governing their structure and interaction within an application.

In DDD, a Domain Event represents a discrete, well-defined operation within the domain — an action that changes or queries domain state in response to a business requirement. Tiferet's `DomainEvent` base class formalizes this concept: each event encapsulates a single operation, receives its dependencies via constructor injection, validates inputs declaratively through the `@DomainEvent.parameters_required` decorator, and enforces domain rules via `verify` calls. Domain Events are composed into feature workflows, where each step in the workflow is itself an event, enabling fine-grained orchestration of business logic.

This project focuses exclusively on Domain Events, which reside at the heart of every working Tiferet application. The Domain Event dialect is defined by a precise syntactic language: artifact comments serve as domain documentation, `DomainEvent` inheritance establishes the service boundary, `execute` methods orchestrate transactional use cases, injected service contracts provide infrastructure abstraction, model factories act as aggregate roots, and error codes form part of the shared domain vocabulary.

The compiler applies lexical analysis to recognize Tiferet idioms (artifact sections, import groups, validation decorators), syntactic analysis via Python's `ast` module to extract Domain Event classes and ordered execute snippets, and semantic analysis to resolve dependencies while enforcing DDD architectural rules. The resulting intermediate representation — a single consolidated YAML file capturing parameter contracts, ordered execution flow, and aggregated domain dependencies — serves as a semantically rich context store optimized for AI-assisted workflows.

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

### Scanner Usage

The scanner performs lexical analysis on Python source files written in the Tiferet Domain Event pattern, recognizing domain-specific tokens such as artifact comments, service calls, factory invocations, and structural keywords.

#### CLI Commands

Scan a Tiferet event source file:

```bash
python compiler.py scan event <source_file>
```

**Options:**

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Write results to a YAML or JSON file |
| `--format` | Output format: `yaml`, `json`, `console`, or `auto` |
| `-x`, `--extract` | Comma-separated artifact names to extract (e.g., `add_error,get_error`) |
| `--summary-only` | Output only metrics/summary (omit the full token list) |
| `--with-metrics` | Include detailed lexical metrics section |
| `--metrics-format` | Metrics rendering format: `yaml`, `json`, or `text` |

**Examples:**

```bash
# Full scan with YAML output
python compiler.py scan event samples/error_events.py -o results.yaml

# JSON output
python compiler.py scan event samples/error_events.py -o results.json --format json

# Summary with metrics only (no token list)
python compiler.py scan event samples/error_events.py --summary-only true --with-metrics true

# Extract specific artifacts (imports are always included)
python compiler.py scan event samples/error_events.py -x add_error,get_error
```

#### Token Categories

The scanner recognizes the following token families (see [LEXICAL_SPEC.md](./LEXICAL_SPEC.md) for the complete formal specification):

- **Artifact Comments** — `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`, `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`
- **Documentation** — `DOCSTRING`, `LINE_COMMENT`
- **Structural Keywords** — `CLASS`, `DEF`, `EXECUTE`, `INIT`, `RETURN`, `SELF`
- **Domain Idioms** — `PARAMETERS_REQUIRED`, `VERIFY`, `SERVICE_CALL`, `FACTORY_CALL`, `CONST_REF`
- **Generic Python** — `PYTHON_KEYWORD`, `IDENTIFIER`, `STRING_LITERAL`, `NUMBER_LITERAL`
- **Punctuation** — `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`, `COMMA`, `COLON`, `ARROW`, `DOT`, `EQUALS`
- **Layout** — `NEWLINE`, `UNKNOWN`

Unrecognized characters are emitted as `UNKNOWN` tokens for error reporting.

### Running Tests

The test suite validates every token type, non-matching/unknown tokens, and the full event pipeline.

```bash
# Run all tests
python -m pytest src/ -v

# Run only lexer tests (37 tests)
python -m pytest src/utils/tests/test_lexer.py -v

# Run only event tests (17 tests)
python -m pytest src/events/tests/test_scan.py -v
```

**Total: 54 tests** (37 lexer + 17 events)

### Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml)
samples/
  error_events.py        — Sample input: Tiferet error event source file

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
    lexer.py             — TiferetLexer: PLY-based lexer implementing LexerService with 35 token types
    __init__.py          — Utils package exports
    tests/
      test_lexer.py      — 37 tests for all lexer token rules
```

### Project Documentation
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** — ECE 506 course context and educational goals
- **[PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md)** — Completed ECE 506 initial project definition template
- **[LEXICAL_SPEC.md](./LEXICAL_SPEC.md)** — Formal lexical specification for all token types
- **[AGENTS.md](./AGENTS.md)** — AI agent codebase index

### Development Status

- **Current branch**: `master`
- **Version**: 0.1.0
- **Focus**: Lexical scanner for the Tiferet Domain Event pattern
- **License**: MIT (educational reuse encouraged)

### Acknowledgments

ECE 506: Compiler Design – University of Arizona  
Inspired by real-world DDD frameworks and the need for tools that preserve domain fidelity in large codebases.

Questions, feedback, or contributions welcome — especially for educational purposes!
