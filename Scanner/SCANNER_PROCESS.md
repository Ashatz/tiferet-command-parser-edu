# Lexical Analysis — Scanner Design and Implementation  
**Tiferet Command Parser (Educational Compiler Front-End)**  
**ECE 506 — Compiler Design**  
**University of Arizona**  
**Spring 2026**  
**Authors:** Andrew Shatz, Lojain Syed  
**Documentation contribution:** Oz (oz-agent@warp.dev)

## 1. Purpose of the Scanner

The scanner is the **lexical analysis** phase of the Tiferet Command Parser — the first stage of the compiler front-end. Its primary responsibilities are:

- Reading Python source files written in the Tiferet Command dialect
- Identifying and extracting structured **artifact comment blocks** that organize domain logic
- Tokenizing the source text into a stream of classified tokens that carry domain-specific meaning
- Computing lightweight structural and domain-specific metrics
- Producing a structured result suitable for later syntactic and semantic analysis phases

This document describes the complete scanning pipeline, the interaction between domain-level orchestration (`scan.py`) and the low-level lexer (`lexer.py`), the token categories defined for the Tiferet dialect, and the rationale behind major design decisions.

## 2. Scanning Pipeline Overview

The scanner is structured as a **four-stage pipeline** orchestrated by the Tiferet domain-event runner and declared in `config.yml` under the `scan.command` feature.

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

Each stage is implemented as a self-contained **Tiferet Domain Event**. Output from one stage is passed to the next via named `data_key` bindings managed by the framework.

## 3. Detailed Stage Descriptions

### 3.1 ExtractText

**Location:** `src/events/scan.py` — class `ExtractText`  
**Purpose:** Locate and extract artifact comment blocks from raw source  
**Input:** source file path, optional group type (default: `"command"`), optional extract filter (`-x`)  
**Output key:** `text_blocks`

**Steps:**
1. Verify source file exists
2. Read all lines
3. Extract the `# *** imports` block (always included)
4. Identify artifact blocks starting with `# ** command: <name>`
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
**Purpose:** Input validation gate before tokenization  
**Input key:** `text_blocks`  
**Output key:** `validated_blocks`

**Checks performed:**
- List is non-empty
- Every block has non-empty `text` after stripping whitespace

Raises domain error `TEXT_EXTRACTION_FAILED` on violation.

### 3.3 PerformLexicalAnalysis

**Location:** `src/events/scan.py` — class `PerformLexicalAnalysis`  
**Dependencies:** `LexerService` (injected — resolved to `TiferetLexer`)  
**Input key:** `validated_blocks`  
**Output key:** `analysis_result`

**Core logic:**
1. Tokenize each block using `lexer_service.tokenize(block["text"])`
2. Accumulate all tokens into a single ordered list
3. Compute frequency count of every token type
4. Derive domain-specific metrics:
   - `commands_detected` (# of `CLASS` tokens)
   - `execute_methods_found` (# of `EXECUTE` tokens)
   - `parameters_required_decorators` (# of `PARAMETERS_REQUIRED`)
   - `docstrings_found` (# of `DOCSTRING`)
   - `top_token_types` (top 10 most frequent types)

**Output structure:**
```python
{
    "tokens": List[Dict],           # full token stream
    "token_count": int,
    "metrics": Dict[str, Any]
}
```

### 3.4 EmitScanResult

**Location:** `src/events/scan.py` — class `EmitScanResult`  
**Purpose:** Final formatting and output  
**Conditional fields (based on CLI flags):**
- `--with-metrics` / `--summary-only` → include `metrics`
- `--summary-only` → exclude full `tokens` list
- `-x` → include `extracted_artifacts` list
- `-o <path>` → write to file (YAML/JSON auto-detected by extension)

**Always included:**
- `event_type`: `"TokensScanned"`
- `timestamp`
- `source_file`
- `token_count`

## 4. Lexer Implementation — TiferetLexer

**Location:** `src/utils/lexer.py`  
**Technology:** PLY (`ply.lex`) — only the lexer portion is used  
**Interface implemented:** `LexerService` (`tokenize(text: str) → List[Dict]`)

### 4.1 Token Categories — Tiferet Command Dialect

| Category                     | Example Token Types                          | Priority / Matching Style          | Purpose / Notes                                                                 |
|------------------------------|----------------------------------------------|-------------------------------------|---------------------------------------------------------------------------------|
| Artifact comment hierarchy   | `ARTIFACT_IMPORTS_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`, `OBSOLETE` | Function rules (highest priority)   | Recognize `# ***`, `# **`, `# *` structured documentation                       |
| Domain-specific idioms       | `PARAMETERS_REQUIRED`                        | Function rule before `IDENTIFIER`   | `@DomainEvent.parameters_required` decorator                                    |
| Structural Python keywords   | `CLASS`, `DEF`, `INIT`, `EXECUTE`, `RETURN`, `SELF` | Reclassification inside `t_IDENTIFIER` | Domain-relevant method/class names                                             |
| Generic Python keywords      | `PYTHON_KEYWORD`                             | Reclassification inside `t_IDENTIFIER` | All other Python reserved words                                                |
| Literals                     | `STRING_LITERAL`, `NUMBER_LITERAL`, `DOCSTRING` | Standard regex rules               | `DOCSTRING` = triple-quoted only                                               |
| Operators & punctuation      | `+`, `==`, `<=`, `@`, `(`, `->`, `.`, etc.   | Longest-match ordering             | Multi-char operators defined before single-char versions                        |
| Layout & error               | `NEWLINE`, `UNKNOWN`                         | Built-in + `t_error` handler       | `UNKNOWN` emitted on unrecognized characters; scanning continues               |

### 4.2 Token Dictionary Format

Each token is returned as:
```python
{
    "type":   str,     # e.g. "CLASS", "EXECUTE", "STRING_LITERAL", "UNKNOWN"
    "value":  str,     # exact matched text
    "line":   int,     # 1-based
    "column": int      # 0-based offset from line start
}
```

## 5. Design Rationale — Key Decisions

- **Why PLY?**  
  Mirrors classic `lex` workflow taught in ECE 506, provides declarative rules, priority control via function/string rule ordering, and graceful error recovery.

- **Why separate event layer and lexer?**  
  Dependency injection + interface separation allows swapping lexer implementations (hand-written, re2c, etc.) without changing domain logic.

- **Why artifact block extraction first?**  
  Tiferet code is organized into semantically meaningful chunks via comment headers → tokenizing whole file loses this structure.

- **Why domain-specific metrics?**  
  Quick structural validation of Tiferet conventions (every command class has `execute`, documentation coverage, validation style).

## 6. Primary Source Files (Reference)

| File                          | GitHub Link (ece-506-submission branch)                                                                 | Role                                      |
|-------------------------------|----------------------------------------------------------------------------------------------------------|-------------------------------------------|
| `src/events/scan.py`          | https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/events/scan.py          | Pipeline orchestration (four domain events) |
| `src/utils/lexer.py`          | https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/lexer.py          | PLY-based lexer implementation            |
| `src/utils/parser.py`         | …/src/utils/parser.py                                                                                   | Artifact block extraction logic           |
| `src/interfaces/lexer.py`     | …/src/interfaces/lexer.py                                                                               | `LexerService` abstract interface         |
| `config.yml`                  | …/config.yml                                                                                            | Pipeline wiring & dependency registration |

This scanner forms a clean, well-separated lexical foundation for the rest of the Tiferet Command Parser pipeline.

Feedback and suggestions for improvement are welcome.