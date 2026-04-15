# Utilities – TiferetLexer and BlockTracker

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`TiferetLexer` is a generic PLY lexer host that loads its entire grammar — token names, regex patterns, and function handlers — dynamically from a centralized assets module at init time. `BlockTracker` is a lightweight state machine that decides when and where to inject synthetic `INDENT` / `DEDENT` tokens while walking the flat token stream.

Together they form the lexical analysis pipeline: `TiferetLexer` tokenizes source text via PLY, and `BlockTracker` (integrated directly into `TiferetLexer.tokenize()`) injects layout tokens for class and method body boundaries.

**Files:**
- `src/utils/lexer.py` — `BlockTracker` and `TiferetLexer` classes
- `src/interfaces/lexer.py` — `LexerService` abstract interface
- `src/assets/lexer.py` — Token constants, rule handlers, `TOKENS`, `RULES`

The architecture splits into three layers:
- **Assets** (`src/assets/lexer.py`) — grammar as data: token constants, rule handlers, `TOKENS`, `RULES`
- **Import chain** (`src/events/settings.py` → `a.lexer`) — makes assets accessible project-wide
- **Host** (`src/utils/lexer.py`) — generic PLY host + integrated `BlockTracker`


## Quick examples

```python
from src.utils import TiferetLexer

# === Tokenize a snippet (includes INDENT/DEDENT by default) ===
lexer = TiferetLexer()
tokens = lexer.tokenize("class AddNumber(BasicCalcEvent):\n    pass\n")

for tok in tokens:
    print(f"{tok.type:20} {tok.value!r}")
# CLASS                'class'
# IDENTIFIER           'AddNumber'
# LPAREN               '('
# IDENTIFIER           'BasicCalcEvent'
# RPAREN               ')'
# COLON                ':'
# NEWLINE              '\n'
# INDENT               ''
# ...

# === Tokenize without INDENT/DEDENT ===
lexer = TiferetLexer(include_indent_dedent=False)
tokens = lexer.tokenize("# *** events\n# ** event: add_number\n")
```


## BlockTracker

`BlockTracker` is a state machine that tracks parenthesis depth, `CLASS`/`DEF` boundaries, and column positions to determine where `INDENT` and `DEDENT` tokens should be injected.

Key behaviors:
- **Parenthesis depth tracking** — skips multi-line signatures by counting `(`, `[`, `{` depth
- **CLASS/METHOD detection** — watches for `CLASS`, `DEF`, `ARTIFACT_SECTION`, and `ARTIFACT_MEMBER` tokens via regex patterns
- **Column computation** — computes 0-based column from `lexpos` against the original source text (no column attribute required on tokens)
- **INDENT injection** — emits an `INDENT` when the column increases after a class or method declaration
- **DEDENT injection** — emits one or more `DEDENT` tokens when column decreases, using a tab size of 4
- **Boundary flush** — `flush_dedents_for_boundary()` closes all open indentation levels at end-of-stream

### Integration with TiferetLexer

`BlockTracker` is instantiated inside `TiferetLexer.tokenize()` and operates inline during the PLY token iteration — it is not a separate post-processing step:

```python
def tokenize(self, text: str) -> List[TokenAggregate]:
    tracker = BlockTracker(text)
    result = []
    for t in self.lexer:
        token = self.map_lex_token(t)
        tracker.process_token(token, result)
        if self.include_indent_dedent and token.lineno > prev_lineno:
            tracker.apply_block(token.lexpos, token.lineno, result)
        result.append(token)
    result.extend(tracker.flush_dedents_for_boundary())
    return result
```


## Dynamic Rule Loading

The `TiferetLexer.__init__` method loads grammar rules from `a.lexer.RULES`:

```python
def __init__(self, include_indent_dedent: bool = True):
    for name, rule in a.lexer.RULES.items():
        if callable(rule):
            setattr(self, name, MethodType(rule, self))
        else:
            setattr(self, name, rule)
    self.lexer = Lex(module=self)
```

- **Callable (function rule):** Bound to the instance using `MethodType` because PLY calls function rules as `func(t)`, but the function signature is `(self, t)`. Python's descriptor protocol only auto-binds `self` for class attributes — instance attributes set via `setattr` need explicit binding.
- **String (regex rule):** Set directly as an instance attribute. PLY reads it via `getattr()`.


## The Assets Module: `src/assets/lexer.py`

### Token name constants
```python
ARTIFACT_IMPORTS_START = 'ARTIFACT_IMPORTS_START'
CLASS = 'CLASS'
IDENTIFIER = 'IDENTIFIER'
# ... 53 total (including INDENT, DEDENT)
```

### The `TOKENS` tuple
Defined _before_ rule handlers in the module (captures string values before shadowing).

### Rule handler constants
Two forms — function rules (with PLY docstring regex) and string rules (simple regex):

```python
# Function rule
def IDENTIFIER(self, t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value == 'class':
        t.type = 'CLASS'
    elif t.value in _python_keywords:
        t.type = 'PYTHON_KEYWORD'
    return t

# String rule
DOUBLESTAR = r'\*\*'
```

### The `RULES` mapping dict
```python
RULES = {
    't_ARTIFACT_IMPORTS_START': ARTIFACT_IMPORTS_START,
    't_DOUBLESTAR': DOUBLESTAR,
    't_IDENTIFIER': IDENTIFIER,
    # ...
}
```

The `t_` prefix exists only in `RULES` keys — the boundary between lexer-agnostic constants and PLY's naming convention.


## What stays on the class (and why)

| Attribute | Why it stays |
|-----------|-------------|
| `tokens = a.lexer.TOKENS` | PLY requires this at class level |
| `t_ignore = ' \t'` | PLY infrastructure — whitespace handling |
| `t_error(self, t)` | PLY infrastructure — unmatched character handling |


## Testing

Lexer utility tests: `src/utils/tests/test_lexer.py` (13 tests)
Lexer event tests: `src/events/tests/test_lexer.py` (6 tests)

```bash
python -m pytest src/utils/tests/test_lexer.py -v
python -m pytest src/events/tests/test_lexer.py -v
```

Events depend on the `LexerService` interface, not `TiferetLexer` directly. Mock the interface in event tests; use the real lexer in utility tests.


## Related reading

- [lexical_spec.md](../lexical_spec.md) — formal lexical specification for all token types
- [parser.md](parser.md) — TiferetParser utility guide
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
