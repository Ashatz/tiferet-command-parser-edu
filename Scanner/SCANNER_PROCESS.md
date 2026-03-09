# Lexical Analysis — Scanner Design and Implementation  
**Tiferet Event Parser (Educational Compiler Front-End)**  
**ECE 506 — Compiler Design**  
**University of Arizona**  
**Spring 2026**  
**Authors:** Andrew Shatz, Lojain Syed  
**Documentation Author & Technical Editor:** Grok (built by xAI)  
**Role performed:** Full rewrite, structural reorganization, academic tone enhancement, replacement of “command” → “event” terminology throughout, consistency polishing, table formatting, and clarity improvements for final project submission.

## 1. Purpose of the Scanner

The scanner performs the **lexical analysis** phase — the first stage of the compiler front-end — for Python source files written in the Tiferet Event dialect. Its main responsibilities are:

- Reading `.py` files structured according to Tiferet conventions
- Identifying and extracting semantically meaningful **artifact comment blocks**
- Tokenizing source text into a classified token stream that preserves domain-specific meaning
- Computing lightweight structural and domain-oriented metrics
- Producing structured output suitable for downstream syntactic and semantic phases

This document explains the complete scanning pipeline, the division of responsibilities between the domain-level orchestration (`scan.py`) and the low-level PLY-based lexer (`lexer.py`), the token categories tailored to the Tiferet Event dialect, and the major design decisions.

## 2. Scanning Pipeline Overview

The scanner is implemented as a **four-stage pipeline** orchestrated by the Tiferet domain-event runner and configured in `config.yml` under the `scan.event` feature.

```
Source File (.py)
         │
         ▼
┌────────────────────┐
│     ExtractText    │  →  text_blocks
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  LexerInitialized  │  →  validated_blocks
└────────────────────┘
         │
         ▼
┌────────────────────┐
│PerformLexicalAnalysis│  →  analysis_result (tokens + metrics)
└────────────────────┘
         │
         ▼
┌────────────────────┐
│   EmitScanResult   │  →  final payload (stdout or file)
└────────────────────┘
```

Each stage is a self-contained **Tiferet Domain Event**. Outputs are passed forward using named `data_key` bindings managed by the framework.

## 3. Detailed Stage Descriptions

### 3.1 ExtractText

**Location:** `src/events/scan.py` — class `ExtractText`  
**Purpose:** Locate and extract artifact comment blocks from raw source  
**Input:** source file path, optional group type (default: `"event"`), optional extract filter (`-x`)  
**Output key:** `text_blocks`

**Steps:**
1. Verify source file exists
2. Read all lines
3. Extract the `# *** imports` block (always included)
4. Identify artifact blocks beginning with `# ** event: <name>`
5. Capture each block’s full text, line range, and name
6. Apply optional name filter from `-x` argument
7. Prepend imports block to the list
8. Validate that at least one block was extracted

**Output structure (per block):**
```python
{
    "name": str,
    "line_start": int,
    "line_end": int,
    "text": str,
    "length_chars": int
}
```

### 3.2 LexerInitialized

**Location:** `src/events/scan.py` — class `LexerInitialized`  
**Purpose:** Validation gate before tokenization  
**Input key:** `text_blocks`  
**Output key:** `validated_blocks`

**Checks:**
- List is non-empty
- Every block has non-empty `text` after stripping whitespace

Raises `TEXT_EXTRACTION_FAILED` on violation.

### 3.3 PerformLexicalAnalysis

**Location:** `src/events/scan.py` — class `PerformLexicalAnalysis`  
**Dependencies:** `LexerService` (injected — resolved to `TiferetLexer`)  
**Input key:** `validated_blocks`  
**Output key:** `analysis_result`

**Core logic:**
1. Tokenize each block via `lexer_service.tokenize(block["text"])`
2. Accumulate all tokens into one ordered list
3. Compute frequency of every token type
4. Derive domain-specific metrics:
   - `events_detected` (# of `CLASS` tokens)
   - `execute_methods_found` (# of `EXECUTE` tokens)
   - `parameters_required_decorators` (# of `PARAMETERS_REQUIRED`)
   - `docstrings_found` (# of `DOCSTRING`)
   - `top_token_types` (top 10 most frequent types)

**Output structure:**
```python
{
    "tokens": List[Dict],
    "token_count": int,
    "metrics": Dict[str, Any]
}
```

### 3.4 EmitScanResult

**Location:** `src/events/scan.py` — class `EmitScanResult`  
**Purpose:** Final formatting and output delivery  
**Conditional fields (CLI-controlled):**
- `--with-metrics` / `--summary-only` → include `metrics`
- `--summary-only` → exclude full `tokens` list
- `-x` → include `extracted_artifacts` list
- `-o <path>` → write YAML or JSON (extension-based auto-detection)

**Always included:**
- `event_type`: `"TokensScanned"`
- `timestamp`
- `source_file`
- `token_count`

## 4. Lexer Implementation — TiferetLexer

**Location:** `src/utils/lexer.py`  
**Technology:** PLY (`ply.lex`) — lexer module only  
**Interface:** Implements `LexerService` (`tokenize(text: str) → List[Dict]`)

### 4.1 Token Categories — Tiferet Event Dialect

| Category                     | Example Token Types                          | Priority / Matching Style          | Purpose / Notes                                                                 |
|------------------------------|----------------------------------------------|-------------------------------------|---------------------------------------------------------------------------------|
| Artifact comment hierarchy   | `ARTIFACT_IMPORTS_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`, `OBSOLETE` | Function rules (highest)           | Recognize `# ***`, `# **`, `# *` structured documentation                       |
| Domain-specific idioms       | `PARAMETERS_REQUIRED`                        | Function rule before `IDENTIFIER`   | `@DomainEvent.parameters_required` decorator                                    |
| Structural Python keywords   | `CLASS`, `DEF`, `INIT`, `EXECUTE`, `RETURN`, `SELF` | Reclassification in `t_IDENTIFIER` | Domain-relevant names                                                          |
| Generic Python keywords      | `PYTHON_KEYWORD`                             | Reclassification in `t_IDENTIFIER` | Remaining Python reserved words                                                |
| Literals                     | `STRING_LITERAL`, `NUMBER_LITERAL`, `DOCSTRING` | Standard regex                     | `DOCSTRING` = triple-quoted only                                               |
| Operators & punctuation      | `+`, `==`, `<=`, `@`, `(`, `->`, `.`, etc.   | Longest-match ordering             | Multi-char before single-char operators                                        |
| Layout & error               | `NEWLINE`, `UNKNOWN`                         | Built-in + `t_error`               | `UNKNOWN` emitted on unrecognized input; scanning continues                    |

### 4.2 Token Dictionary Format

```python
{
    "type":   str,     # e.g. "CLASS", "EXECUTE", "STRING_LITERAL", "UNKNOWN"
    "value":  str,     # matched text
    "line":   int,     # 1-based
    "column": int      # 0-based offset from line start
}
```

## 5. Design Rationale — Key Decisions

- **PLY chosen** because it closely follows the `lex` model taught in ECE 506, offers declarative rules, priority ordering, and error recovery.
- **Event layer ↔ lexer separation** via dependency injection preserves modularity — lexer is a pure utility; domain logic lives in events.
- **Block extraction first** preserves Tiferet’s semantic organization via comment headers.
- **Domain metrics** enable quick validation of Tiferet conventions (e.g., every event class has an `execute` method).

## 6. Primary Source Files (Reference)

| File                          | GitHub Link (ece-506-submission branch)                                                                 | Role                                      |
|-------------------------------|----------------------------------------------------------------------------------------------------------|-------------------------------------------|
| `src/events/scan.py`          | https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/events/scan.py          | Pipeline orchestration (four domain events) |
| `src/utils/lexer.py`          | https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/lexer.py          | PLY-based lexer implementation            |
| `src/utils/parser.py`         | …/src/utils/parser.py                                                                                   | Artifact block extraction                 |
| `src/interfaces/lexer.py`     | …/src/interfaces/lexer.py                                                                               | `LexerService` interface                  |
| `config.yml`                  | …/config.yml                                                                                            | Pipeline & dependency configuration       |
