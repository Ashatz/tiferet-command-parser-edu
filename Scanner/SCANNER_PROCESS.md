# Scanner Process — How Lexical Scanning Works

**Project:** Tiferet Event Parser (Educational Scanner)  
**Course:** ECE 506 — Compiler Design  
**University of Arizona**  
**Date:** March 2026  

**Authors:** Andrew Shatz  

**Co-Author & Original Document Author:** Oz (oz-agent@warp.dev) — Authored this document, including pipeline walkthrough, token category reference, metrics analysis, and file reference section.

**Documentation Revision & Enhancement:** Grok (built by xAI) — Performed full content polishing, structural reorganization, academic tone refinement, terminology alignment, table formatting, clarity improvements, and final readiness adjustments for ECE 506 submission.

## 1. Purpose

The scanner performs **lexical analysis** (the first phase of a compiler front-end) on Python source files written in the Tiferet framework's Domain Event pattern. It reads a `.py` file, extracts meaningful artifact blocks, breaks the source text into a stream of classified tokens, computes domain-level metrics, and emits structured output.

This document explains the full scan pipeline, the role of each component, and how the two central modules — **`scan.py`** (domain events) and **`lexer.py`** (PLY-based lexer) — collaborate to carry out the scanning process.

## 2. Pipeline Overview

The scanner is organized as a **four-stage pipeline** defined in `config.yml` under the `scan.event` feature. Each stage is a Tiferet **Domain Event** — a self-contained operational unit that receives input, performs a focused task, and passes its result forward via a `data_key` binding.

```
Source File
    │
    ▼
┌───────────────┐   data_key: text_blocks
│  ExtractText  │──────────────────────────►
└───────────────┘
    │
    ▼
┌───────────────────┐   data_key: validated_blocks
│ LexerInitialized  │──────────────────────────────►
└───────────────────┘
    │
    ▼
┌──────────────────────────┐   data_key: analysis_result
│ PerformLexicalAnalysis   │──────────────────────────────►
└──────────────────────────┘
    │
    ▼
┌──────────────────┐  final payload (stdout / file)
│  EmitScanResult  │─────────────────────────────────►
└──────────────────┘
```

The Tiferet feature runner executes these events **sequentially**. Each event's return value is stored under its `data_key` and made available to all subsequent events as a keyword argument.

## 3. Stage-by-Stage Walkthrough

### 3.1 Stage 1 — ExtractText

**File:** `src/events/scan.py` (class `ExtractText`)  
**Input:** `source_file` (path), optional `group_type` (default `"event"`), optional `extract` filter  
**Output:** `text_blocks` — a list of block dicts

This event is responsible for **reading the source file and locating artifact blocks** within it. It delegates the actual parsing work to the `ArtifactBlockParser` utility (`src/utils/parser.py`).

**What happens:**

1. **File existence check** — Uses `self.verify()` to confirm the file exists on disk, raising `SOURCE_FILE_NOT_FOUND` if not.
2. **Read file** — Opens and reads all lines into memory.
3. **Parse extract filter** — If the user passed `-x add_error,get_error`, the comma-separated string is converted to a `set` of names by `ArtifactBlockParser.parse_extract_filter()`.
4. **Extract imports block** — `ArtifactBlockParser.extract_imports_block()` locates the `# *** imports` section and captures everything up to the next `# ***` top-level comment. This block is always included regardless of any `-x` filter.
5. **Extract artifact blocks** — `ArtifactBlockParser.extract_artifact_blocks()` walks lines looking for `# ** event: <name>` headers (or whatever `group_type` is). Each block runs from its header to the next header (or end of file). The result is a list of dicts, each containing:
   - `name` — the artifact name (e.g. `add_error`)
   - `line_start` / `line_end` — line range in the source
   - `text` — the raw source text of the block
   - `length_chars` — character count
6. **Apply filter** — If `-x` was specified, only blocks whose `name` appears in the filter set are kept.
7. **Prepend imports** — The imports block is inserted at position 0 so it is always tokenized first.
8. **Validation** — Verifies at least one block was found; raises `TEXT_EXTRACTION_FAILED` if none.

Each block dict represents a **unit of source text** ready for tokenization.

### 3.2 Stage 2 — LexerInitialized

**File:** `src/events/scan.py` (class `LexerInitialized`)  
**Input:** `text_blocks`  
**Output:** `validated_blocks` (same list, unchanged)

This is a **validation gate**. It confirms the blocks passed from Stage 1 are suitable for lexical analysis:

1. Verifies the list is non-empty.
2. Iterates every block and verifies its `text` field is non-empty after stripping whitespace.

If any block is empty, the event raises `TEXT_EXTRACTION_FAILED` with the offending block's name. If all checks pass, the blocks are returned unmodified as `validated_blocks`.

### 3.3 Stage 3 — PerformLexicalAnalysis

**File:** `src/events/scan.py` (class `PerformLexicalAnalysis`)  
**Input:** `validated_blocks`  
**Output:** `analysis_result` — a dict containing `tokens`, `token_count`, and `metrics`

This is the **core analytical stage**. It is the only event in the pipeline that requires an injected dependency — the `LexerService`. At runtime, Tiferet's dependency injection container resolves `lexer_service` to an instance of `TiferetLexer` (defined in `src/utils/lexer.py`).

**What happens:**

1. **Tokenization loop** — For each validated block, the event calls `self.lexer_service.tokenize(block['text'])`. The lexer returns a list of token dicts. All tokens from all blocks are accumulated into a single flat list (`all_tokens`).
2. **Indent injection** — After all blocks are tokenized, `IndentInjector.inject(all_tokens)` (`src/utils/indent.py`) performs a second pass over the flat stream. It enters body mode on any `ARTIFACT_MEMBER` whose value matches `# * method:` or `# * init`, tracks parenthesis depth to skip indentation changes inside multi-line function signatures, and manages a column stack to emit `INDENT` before a first deeper line and `DEDENT` when indentation returns to a shallower level or the next structural artifact comment is reached. The enriched stream replaces `all_tokens`.
3. **Metrics computation** — A `Counter` tallies every token's `type` field (including the injected `INDENT`/`DEDENT` tokens). From these counts, the event derives domain-meaningful metrics:

   - `commands_detected` — count of `CLASS` tokens (each class declaration = one event)
   - `docstrings_found` — count of `DOCSTRING` tokens
   - `indent_count` — count of `INDENT` tokens (method-body indent transitions)
   - `dedent_count` — count of `DEDENT` tokens (method-body dedent transitions)
   - `top_token_types` — the 10 most frequent token types
4. **Return** — The event returns a dict with `tokens` (the full token list, including injected layout tokens), `token_count`, and `metrics`.

### 3.4 Stage 4 — EmitScanResult

**File:** `src/events/scan.py` (class `EmitScanResult`)  
**Input:** `source_file`, `analysis_result`, output flags  
**Output:** Final result payload dict

This terminal event **assembles the output** and optionally writes it to a file. It builds a payload containing:

- `event_type` — always `"TokensScanned"`
- `timestamp` — UTC ISO timestamp
- `source_file` — original file path
- `token_count` — total tokens produced

Conditional fields are added based on CLI flags:

- `--with-metrics` or `--summary-only` → includes `metrics`
- `--summary-only` → **omits** the full `tokens` list (useful for high-level overviews)
- `-x` → includes `extracted_artifacts` (the list of artifact names that were filtered)

If `-o` was specified, the payload is written to file via `ScanOutputWriter.write()`, which supports YAML and JSON formats with auto-detection from file extension.

## 4. The Lexer — How Tokenization Works

### 4.1 Architecture

**Lexer host:** `src/utils/lexer.py` (class `TiferetLexer`)  
**Lexer assets:** `src/assets/lexer.py` (token constants, rule handlers, `TOKENS`, `RULES`)  
**Implements:** `LexerService` (abstract interface in `src/interfaces/lexer.py`)

`TiferetLexer` is a **generic PLY (Python Lex-Yacc) based lexer host** that implements the `LexerService` contract. PLY is a Python implementation of the classic `lex` and `yacc` tools from compiler construction. In this part of the project, only the lexer (`ply.lex`) is used.

PLY works by scanning the input text left-to-right and matching regular expression patterns to produce tokens. However, unlike a conventional PLY lexer where patterns are defined inline on the class, `TiferetLexer` uses a **dynamic lexer architecture** that separates grammar from infrastructure.

#### Dynamic Lexer Architecture

The lexer's entire grammar — token names, regex patterns, and function handlers — lives in a centralized assets module (`src/assets/lexer.py`) as composable constants. The lexer class itself contains no grammar; it loads everything at init time.

The architecture has three layers:

1. **Assets** (`src/assets/lexer.py`) — Grammar as data. Contains:
   - **Token name constants** — Individual string constants (e.g., `ARTIFACT_IMPORTS_START = 'ARTIFACT_IMPORTS_START'`) that can be composed into different `TOKENS` tuples.
   - **`TOKENS` tuple** — The ordered master token list, referencing the individual constants.
   - **Rule handler constants** — Functions (with PLY docstring regex) and regex strings that define lexer behavior. Named without any lexer-specific prefix.
   - **`RULES` dict** — Maps PLY `t_`-prefixed names to their handler constants. This is the composable unit for dynamic lexer configuration.

2. **Import chain** — The assets module reaches the lexer via the Tiferet `a` convention:
   ```
   src/assets/__init__.py    →  from . import lexer
   src/events/settings.py    →  from .. import assets as a
   src/events/__init__.py    →  re-exports a
   src/utils/lexer.py        →  from ..events import a  →  a.lexer.TOKENS / a.lexer.RULES
   ```

3. **Host** (`src/utils/lexer.py`) — The `TiferetLexer.__init__` method iterates `a.lexer.RULES` and dynamically sets each rule on the instance:
   - **Function rules** are bound via `MethodType(rule, self)` — necessary because PLY calls `func(t)` but the function signature is `(self, t)`, and Python's descriptor protocol does not auto-bind `self` for instance attributes.
   - **String rules** are set directly as instance attributes.
   - After loading, `lex.lex(module=self)` builds the PLY lexer, discovering both class attributes (`tokens`, `t_ignore`, `t_error`) and the dynamically loaded rules.

Only PLY infrastructure remains on the class: `tokens` (sourced from `a.lexer.TOKENS`), `t_ignore` (whitespace handling), and `t_error` (unknown character fallback).

This design means new lexer dialects can be assembled by composing different `TOKENS` tuples and `RULES` dicts from the same pool of constants — without subclassing or modifying the lexer class.

### 4.2 Token Categories

The lexer defines **53 token types** organized into categories:

#### Artifact Comments (Tiferet-specific)
These tokens recognize the structured comment hierarchy that organizes Tiferet source code:

| Token                    | Pattern                          | Meaning                                      |
|--------------------------|----------------------------------|----------------------------------------------|
| `ARTIFACT_IMPORTS_START` | `# *** imports`                  | Top-level imports section header             |
| `ARTIFACT_IMPORT_GROUP`  | `# ** core`, `# ** app`, `# ** infra` | Import group category                        |
| `ARTIFACT_START`         | `# *** <section>`                | Any top-level section (events, models, etc.) |
| `ARTIFACT_SECTION`       | `# ** <category>: <name>`        | Mid-level component header                   |
| `ARTIFACT_MEMBER`        | `# * <component>`                | Low-level member (attribute, method, init)   |
| `OBSOLETE`               | `# - obsolete: <desc>` or `# -- obsolete: <desc>` | Marks artifact members as obsolete; requires colon and description |
| `TODO`                   | `# + todo: <desc>` or `# ++ todo: <desc>` | Marks artifact members with a pending task; requires colon and description |

These are defined as **function rules** (not string rules) in the assets module because PLY gives function rules higher priority. Since artifact comments are specializations of general comments, they must match first.

#### Structural Keywords
| Token     | Pattern    | Meaning                     |
|-----------|------------|---------------------------------|
| `CLASS`   | `class`    | Class declaration               |
| `DEF`     | `def`      | Function/method declaration     |
| `INIT`    | `__init__` | Constructor / injection point   |
| `RETURN`  | `return`   | Return statement                |
| `SELF`    | `self`     | Instance self-reference         |

These are resolved **inside** the `IDENTIFIER` rule handler (defined in `src/assets/lexer.py`). When PLY matches a generic identifier pattern `[a-zA-Z_][a-zA-Z0-9_]*`, the rule function checks the matched value against the structural keyword list and reassigns the token type accordingly.

#### Python Keywords
All remaining Python reserved words (`if`, `else`, `for`, `import`, `from`, `raise`, `try`, `with`, etc.) are classified as `PYTHON_KEYWORD` via the `_python_keywords` lookup set inside the `IDENTIFIER` rule handler.

#### Literals
| Token            | Pattern                     | Meaning                  |
|------------------|-----------------------------|--------------------------|
| `STRING_LITERAL` | Single/double quoted strings| String constants         |
| `NUMBER_LITERAL` | Integer and float patterns  | Numeric constants        |
| `DOCSTRING`      | Triple-quoted strings       | Documentation strings    |

The `NUMBER_LITERAL` rule includes a validity check: if trailing alphabetic characters are appended (e.g. `3abc`), the token is reclassified as `UNKNOWN` to flag the malformed literal.

#### Operators
Arithmetic (`+`, `-`, `*`, `/`, `//`, `**`, `%`), comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), bitwise (`|`, `&`, `~`, `^`, `<<`, `>>`), and the decorator marker `@`.

Multi-character operators (`**`, `//`, `==`, `!=`, `<=`, `>=`, `<<`, `>>`) are defined **before** their single-character counterparts so PLY applies longest-match.

#### Punctuation and Delimiters
`(`, `)`, `[`, `]`, `{`, `}`, `,`, `:`, `->`, `.`, `=`

#### Layout and Error Handling
| Token     | Meaning                                                  |
|-----------|----------------------------------------------------------|
| `NEWLINE` | Line breaks (also updates PLY's line counter)            |
| `UNKNOWN` | Any unrecognized character (via the `t_error` handler)   |

#### Indentation (Synthetic)
These tokens are **not** emitted by the PLY lexer. They are injected into the token stream by `IndentInjector` after tokenization:

| Token    | Meaning                                                         |
|----------|-----------------------------------------------------------------|
| `INDENT` | Injected before the first line that is deeper than the method-member column |
| `DEDENT` | Injected when indentation returns to a shallower level, or when the next structural artifact comment exits the body |

### 4.3 The `tokenize()` Method

The public interface of `TiferetLexer` is a single method:

```python
def tokenize(self, text: str) -> List[Dict[str, Any]]
```

When called:

1. **Reset** — The lexer's line counter is reset to 1 and the input text is fed to PLY via `self.lexer.input(text)`.
2. **Iterate** — PLY's internal generator yields one token at a time. For each token, the method records:
   - `type` — the token type string (e.g. `"CLASS"`, `"PARAMETERS_REQUIRED"`, `"IDENTIFIER"`)
   - `value` — the matched text
   - `line` — the 1-based line number
   - `column` — the 0-based column offset, computed by `_find_column()` which locates the last newline before the token's position
3. **Return** — The full list of token dicts is returned.

### 4.4 Why PLY?

PLY is a well-established tool for compiler coursework because it mirrors the `lex`/`yacc` workflow taught in compiler design classes. Key advantages for this project:

- **Declarative rules** — Token patterns are defined as regex strings or functions with regex docstrings, making the lexical specification easy to read and extend.
- **Priority control** — Function rules match before string rules, and among function rules, definition order determines priority. This gives fine-grained control over how overlapping patterns (e.g. `@DomainEvent.parameters_required` vs. a plain `@` `IDENTIFIER` sequence) resolve.
- **Error recovery** — The `t_error` handler allows the lexer to emit `UNKNOWN` tokens and continue scanning rather than aborting on unrecognized input.

## 4.5 Indent Injection — IndentInjector

**File:** `src/utils/indent.py` (class `IndentInjector`, static method `inject`)

After the PLY lexer produces a flat token stream, `IndentInjector.inject(tokens)` performs a single left-to-right pass to insert `INDENT` and `DEDENT` tokens at method-body boundaries. This is a post-tokenization phase — PLY has no rules for these tokens; they are constructed and inserted directly into the stream.

**Algorithm:**
1. An `ARTIFACT_MEMBER` token whose value matches `# * method:` or `# * init` opens body mode and records `member_col` (the column of the comment).
2. Inside body mode, `LPAREN`/`LBRACK`/`LBRACE` increments `paren_depth`; `RPAREN`/`RBRACK`/`RBRACE` decrements it. While `paren_depth > 0`, newlines are passed through unchanged (multi-line function signatures are ignored).
3. On each `NEWLINE` with `paren_depth == 0`, the injector peeks at the next non-newline token:
   - If the next token is in the `exits_body` set (`ARTIFACT_MEMBER`, `ARTIFACT_SECTION`, `ARTIFACT_START`, etc.) → flush all pending `DEDENT`s and exit body mode.
   - If `next_col > member_col` and the column is deeper than the current stack top → push to stack and inject `INDENT`.
   - If `next_col < stack_top` → pop and inject `DEDENT` for each popped level.
4. At end-of-stream, any remaining stack entries produce trailing `DEDENT`s.

The enriched stream is then passed to metrics computation and returned as the final `tokens` list.

## 5. How PerformLexicalAnalysis and TiferetLexer Interact

The connection between the domain event layer and the lexer utility follows the **Dependency Injection** pattern central to Tiferet:

1. **Interface** — `LexerService` (`src/interfaces/lexer.py`) defines an abstract contract: `tokenize(text) -> List[Dict]`.
2. **Implementation** — `TiferetLexer` (`src/utils/lexer.py`) implements `LexerService` using PLY.
3. **Wiring** — `config.yml` registers `TiferetLexer` as the `lexer_service` container attribute. When Tiferet instantiates `PerformLexicalAnalysis`, it resolves `lexer_service` and injects the `TiferetLexer` instance into the event's constructor.
4. **Execution** — `PerformLexicalAnalysis.execute()` calls `self.lexer_service.tokenize()` for each text block. It never knows or cares that the concrete implementation uses PLY — it only depends on the abstract `LexerService` interface.

This separation means:
- The **lexer** is purely a utility with no domain logic — it turns text into tokens.
- The **event** owns the domain logic — it decides what to tokenize, how to aggregate results, and what metrics to compute.
- The lexer can be swapped (e.g. replaced with a hand-written scanner or a different generator) without modifying the event.

## 6. Metrics — What the Scanner Measures

The metrics produced by `PerformLexicalAnalysis` serve as a **structural fingerprint** of a Tiferet source file:

| Metric              | Token Source | What It Reveals                                                      |
|---------------------|--------------|----------------------------------------------------------------------|
| `commands_detected` | `CLASS`      | Number of domain event classes defined                               |
| `docstrings_found`  | `DOCSTRING`  | Documentation coverage                                               |
| `indent_count`      | `INDENT`     | Method-body indentation open transitions (structural depth measure)  |
| `dedent_count`      | `DEDENT`     | Method-body indentation close transitions                            |
| `top_token_types`   | All types    | Overall token distribution (top 10)                                  |

These metrics let a developer (or a course grader) quickly assess structural properties of a source file — e.g., `commands_detected` identifies how many domain event classes are present, `docstrings_found` reflects documentation coverage, and `indent_count`/`dedent_count` quantify the depth and breadth of method-body logic.

## 7. File Reference

The following files are included in this `Scanner/` directory as reference copies of the scanner's central modules:

| File               | Source                                                                                                   | Role                                           |
|--------------------|----------------------------------------------------------------------------------------------------------|------------------------------------------------|
| `scan.py`          | [`src/events/scan.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/events/scan.py) | All four domain events composing the scan pipeline |
| `lexer.py`         | [`src/utils/lexer.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/lexer.py) | Generic PLY lexer host — loads tokens and rules dynamically from assets |
| `lexer_assets.py`  | [`src/assets/lexer.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/assets/lexer.py) | Token constants, rule handlers (functions/regexes), `TOKENS` tuple, and `RULES` mapping dict |

### Supporting modules (not copied, located in `src/`):

| File                        | Role                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| [`src/utils/parser.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/parser.py) | `ArtifactBlockParser` — extracts imports and artifact blocks from source lines |
| [`src/utils/output.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/output.py) | `ScanOutputWriter` — writes result payloads to YAML/JSON files       |
| [`src/utils/indent.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/utils/indent.py) | `IndentInjector` — post-tokenization INDENT/DEDENT injection for method bodies |
| [`src/interfaces/lexer.py`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/src/interfaces/lexer.py) | `LexerService` — abstract interface for tokenization                 |
| [`config.yml`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/config.yml) | Tiferet YAML configuration wiring the pipeline, errors, CLI, and interfaces |

### Architecture guide:

| File                        | Role                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| [`docs/guides/utils/lexer.md`](https://github.com/Ashatz/tiferet-command-parser-edu/blob/ece-506-submission/docs/guides/utils/lexer.md) | Full guide to the dynamic PLY lexer architecture — assets, import chain, rule composition |

## 8. Sample Files

Scanner sample files live in `Scanner/samples/`. Each file is a Tiferet Domain Event source file designed to exercise specific scanner behaviors. Five are well-formed success cases; two are intentional failure cases.

### Passing Samples

These files are valid Tiferet source and should tokenize without `UNKNOWN` tokens (except where structurally expected).

| File | Description |
|------|-------------|
| `pass_empty_events.py` | Imports section with no event definitions — baseline success case for import-only scanning. |
| `pass_single_event.py` | Single `AddError` event with service injection, aggregate factory, multi-line calls, and `@parameters_required` decorator. |
| `pass_multi_event.py` | Multi-event module with 7 events (`AddError`, `GetError`, `ListErrors`, `RenameError`, `SetErrorMessage`, `RemoveErrorMessage`, `RemoveError`) — exercises the full token vocabulary across varied patterns. |
| `pass_obsolete_annotation.py` | `RenameError` event with `OBSOLETE` annotations at section and member levels — tests `OBSOLETE` token recognition with `# --` and `# -` prefixes. |
| `pass_todo_annotation.py` | `GetError` event with `TODO` annotations at section and member levels — tests `TODO` token recognition with `# ++` and `# +` prefixes. |

### Failing Samples

These files contain intentional lexical errors that the scanner should detect via `UNKNOWN` tokens or misclassified token types.

| File | Violation | Expected Behavior |
|------|-----------|-------------------|
| `fail_invalid_identifiers.py` | Digit-prefixed class name (`123AddError`), attribute name (`456error_service`), and method name (`789execute`). | Lexer emits `UNKNOWN` for the leading digit sequence; the trailing identifier portion is tokenized separately. |
| `fail_malformed_annotations.py` | `OBSOLETE` and `TODO` comments missing the required `colon: description` format (`# -- obsolete` instead of `# -- obsolete: ...`). | Lexer emits `LINE_COMMENT` instead of `OBSOLETE`/`TODO` — the annotation pattern does not match without the colon and description. |
