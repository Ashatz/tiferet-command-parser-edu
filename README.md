# tiferet-command-parser-edu

Educational parser and static analysis tool for the Tiferet Domain Event pattern — extracts structured YAML metadata and dependency graphs from domain-driven Python event code. Built for ECE 506: Compiler Design at the University of Arizona.

### Project Abstract

This project develops a domain-specific compiler front-end for analyzing Python code written in the Tiferet framework's Domain Event pattern — a highly regular dialect that embodies Domain-Driven Design (DDD) principles and Clean Architecture layering. In enterprise software development, domain experts define critical business requirements that must be faithfully translated into features and then reliably implemented, tested, and maintained by cross-functional teams of developers and QA engineers. DDD addresses this challenge by establishing a shared ubiquitous language, which Tiferet realizes through interdependent object-oriented design patterns and a consistent set of guidelines governing their structure and interaction within an application.
In DDD, a Domain Event represents a discrete, well-defined operation within the domain — an action that changes or queries domain state in response to a business requirement. Tiferet's `DomainEvent` base class formalizes this concept: each event encapsulates a single operation, receives its dependencies via constructor injection, validates inputs declaratively through the `@DomainEvent.parameters_required` decorator, and enforces domain rules via `verify` calls. Domain Events are composed into feature workflows, where each step in the workflow is itself an event, enabling fine-grained orchestration of business logic.
This project focuses exclusively on Domain Events, which reside at the heart of every working Tiferet application. As illustrated in the [calculator app](https://github.com/greatstrength/tiferet-calculator-app) example, Domain Events encapsulate operations essential for both core application behavior and feature workflow orchestration, while interacting with infrastructural components to persist, distribute, or transform model state. The Domain Event dialect is defined by a precise syntactic language: artifact comments serve as domain documentation, `DomainEvent` inheritance establishes the service boundary, `execute` methods orchestrate transactional use cases, injected service contracts provide infrastructure abstraction, model factories act as aggregate roots, and error codes form part of the shared domain vocabulary.
The compiler applies lexical analysis to recognize Tiferet idioms (artifact sections, import groups, validation decorators), syntactic analysis via Python's ast module to extract Domain Event classes and ordered execute snippets, and semantic analysis to resolve dependencies while enforcing DDD architectural rules. The resulting intermediate representation — a single consolidated YAML file capturing parameter contracts, ordered execution flow, and aggregated domain dependencies — serves as a semantically rich context store. This IR enables enhanced, AI-assisted generation of high-quality dependency visualizations in Mermaid and Graphviz DOT formats, where the depth of context significantly improves layout clarity, edge labeling, and relational insight beyond what generic extraction can achieve. The implementation demonstrates core compiler design methodologies — phase separation, domain-specific tokenization, AST-based analysis, semantic resolution, and multi-target code generation — applied to a production DDD framework. A public repository (tiferet-command-parser-edu) documents the process for the Domain Event pattern, serving as an educational artifact while preserving broader extensions for future inquiry.

### Project Overview (1.5–2 page summary)

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
# Scan an event file and print tokens to console
python compiler.py scan event src/events/scan.py

# Scan and write output to YAML
python compiler.py scan event src/events/scan.py -o results.yaml

# Scan only specific artifacts with metrics
python compiler.py scan event src/events/scan.py -x extract_text,emit_scan_result --with-metrics

# Summary-only mode (no token list)
python compiler.py scan event src/events/scan.py --summary-only
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
python -m pytest

# Run with verbose output
python -m pytest -v

# Run only lexer tests (37 tests)
python -m pytest src/utils/tests/test_lexer.py -v

# Run only event tests (17 tests)
python -m pytest src/events/tests/test_scan.py -v
```

**Lexer tests** (`src/utils/tests/test_lexer.py`) cover:
- All artifact comment types (imports start, start, import group, section, member)
- Docstrings (single-line and multiline)
- Line comments
- All structural keywords (class, def, init, execute, return, self)
- All domain idioms (parameters_required, verify, service_call, factory_call, const_ref)
- Python keywords, identifiers, string/number literals
- All punctuation and delimiters
- Line and column tracking
- Non-matching / unknown tokens (`@`, `$`, `` ` ``, `~`, `!`, `%`, `^`, `&`)
- Full Tiferet Domain Event snippet integration test
- Edge cases (empty input, whitespace-only input)

**Event tests** (`src/events/tests/test_scan.py`) cover:
- `ExtractText` — success, extract filter, missing param, file not found, no matching blocks
- `LexerInitialized` — success, missing param, empty blocks, empty text
- `PerformLexicalAnalysis` — success with mocked lexer service, missing param
- `EmitScanResult` — default, summary-only, with-metrics, no analysis, YAML output, JSON output

### Development Status

- **Current branch**: `v0.x-proto`
- **Version**: 0.1.0
- **Focus**: Lexical scanner for the Tiferet Domain Event pattern
- **License**: MIT (educational reuse encouraged)

### Acknowledgments

ECE 506: Compiler Design – University of Arizona  
Inspired by real-world DDD frameworks and the need for tools that preserve domain fidelity in large codebases.

Questions, feedback, or contributions welcome — especially for educational purposes!
