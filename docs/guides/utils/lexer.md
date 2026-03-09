# Utilities – TiferetLexer (Dynamic PLY Lexer)

**Project:** Tiferet Command Parser — Educational Scanner  
**Repository:** https://github.com/ashatz/tiferet-command-parser-edu  
**Date:** March 09, 2026  
**Version:** 0.1.0

## Overview

`TiferetLexer` is a generic PLY lexer host that loads its entire grammar — token names, regex patterns, and function handlers — dynamically from a centralized assets module at init time.

What makes it different from a conventional PLY lexer?  
It contains _no grammar at all_. Every token definition and every rule handler lives in `src/assets/lexer.py` as a composable constant. The lexer class is pure infrastructure: give it a `TOKENS` tuple and a `RULES` dict, and it builds itself. New lexer dialects are just new dicts assembled from the same building blocks — no subclassing, no copy-pasting.

The architecture splits into three layers:
- **Assets** (`src/assets/lexer.py`) — grammar as data: token constants, rule handlers, `TOKENS`, `RULES`
- **Import chain** (`src/events/settings.py` → `a.lexer`) — makes assets accessible project-wide
- **Host** (`src/utils/lexer.py`) — generic PLY host that loads assets at init time

## When should you reach for what?

| Use case | Best choice | Why it fits |
|----------|-------------|-------------|
| Tokenize a Tiferet source file | `TiferetLexer().tokenize(text)` | Default config covers all Tiferet tokens |
| Add a new token type | Add constant + handler in `assets/lexer.py` | One file, grammar stays centralized |
| Build a stripped-down lexer variant | Compose a new `TOKENS` + `RULES` from existing constants | No new classes needed |
| Test individual token rules | `TiferetLexer().tokenize(snippet)` | 42 tests already validate every rule |
| Mock the lexer in event tests | Mock `LexerService.tokenize()` | Events depend on the interface, not the class |

## Quick examples to get you started

```python
from src.utils import TiferetLexer

# === Tokenize a snippet ===
lexer = TiferetLexer()
tokens = lexer.tokenize("class AddNumber(BasicCalcEvent):")

for tok in tokens:
    print(f"{tok['type']:20} {tok['value']!r}")
# CLASS                'class'
# IDENTIFIER           'AddNumber'
# LPAREN               '('
# IDENTIFIER           'BasicCalcEvent'
# RPAREN               ')'
# COLON                ':'

# === Tokenize artifact comments ===
tokens = lexer.tokenize("# *** events\n# ** event: add_number\n")

for tok in tokens:
    print(f"{tok['type']:25} {tok['value']!r}")
# ARTIFACT_START            '# *** events'
# NEWLINE                   '\n'
# ARTIFACT_SECTION          '# ** event: add_number'
# NEWLINE                   '\n'
```

## How the import chain works

The assets module reaches the lexer through a deliberate chain that follows the Tiferet `a` convention:

```
src/assets/__init__.py       →  from . import lexer
src/events/settings.py       →  from .. import assets as a
src/events/__init__.py       →  re-exports a
src/utils/lexer.py           →  from ..events import a
                                 tokens = a.lexer.TOKENS
                                 rules  = a.lexer.RULES
```

Normally in Tiferet, `a` points to `tiferet.assets` (the framework's assets). Here, `src/events/settings.py` redirects it to the project's own `src.assets` package instead. The framework's internal `a` references are unaffected — they're captured in closures at import time.

## The assets module: `src/assets/lexer.py`

Everything the lexer needs lives here, organized under `# *** constants`:

### Token name constants (one per token type)

```python
ARTIFACT_IMPORTS_START = 'ARTIFACT_IMPORTS_START'
CLASS = 'CLASS'
IDENTIFIER = 'IDENTIFIER'
DOUBLESTAR = 'DOUBLESTAR'
# ... 47 total
```

These exist as individual constants so you can compose different `TOKENS` tuples by selecting subsets.

### The `TOKENS` tuple

```python
TOKENS = (
    ARTIFACT_IMPORTS_START,
    ARTIFACT_IMPORT_GROUP,
    ARTIFACT_START,
    # ...
    NEWLINE,
    UNKNOWN,
)
```

**Important:** `TOKENS` must be defined _before_ the rule handlers in the module. Rule handlers reuse the same names (shadowing the strings), but Python evaluates sequentially — so `TOKENS` captures the string values before shadowing occurs.

### Rule handler constants

Two forms — both are just constants whose values happen to be functions or regex strings:

**Function rules** (for tokens needing logic or PLY docstring regex):

```python
def ARTIFACT_IMPORTS_START(self, t):
    r'\#\s*\*{3}\s+imports\s*'
    return t

def IDENTIFIER(self, t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value == 'class':
        t.type = 'CLASS'
    elif t.value in _python_keywords:
        t.type = 'PYTHON_KEYWORD'
    return t
```

**String rules** (simple regex):

```python
DOUBLESTAR = r'\*\*'
PLUS = r'\+'
LPAREN = r'\('
```

Rule handlers are named without any lexer-specific prefix — they're lexer-agnostic, identified by their regex. The PLY `t_` convention only appears in the `RULES` dict keys.

### The `RULES` mapping dict

This is the composable unit that ties everything together:

```python
RULES = {
    't_ARTIFACT_IMPORTS_START': ARTIFACT_IMPORTS_START,
    't_ARTIFACT_IMPORT_GROUP': ARTIFACT_IMPORT_GROUP,
    # ...
    't_DOUBLESTAR': DOUBLESTAR,
    't_PLUS': PLUS,
    # ...
    't_IDENTIFIER': IDENTIFIER,
    't_NEWLINE': NEWLINE,
}
```

The `t_` prefix exists _only_ here — it's the boundary between your lexer-agnostic constants and PLY's naming convention.

## How dynamic rule loading works

The `TiferetLexer.__init__` method does the heavy lifting:

```python
from types import MethodType

def __init__(self):
    # Load rules dynamically from the assets mapping.
    for name, rule in a.lexer.RULES.items():
        if callable(rule):
            setattr(self, name, MethodType(rule, self))
        else:
            setattr(self, name, rule)

    # Build the PLY lexer from this module's token rules.
    self.lexer = lex.lex(module=self)
```

Two things happen per rule:

- **Callable (function rule):** Bound to the instance using `MethodType`. This is necessary because PLY calls function rules as `func(t)`, but the function signature is `(self, t)`. Python's descriptor protocol only auto-binds `self` for _class_ attributes — instance attributes set via `setattr` are stored as plain functions. `MethodType` creates the binding explicitly.

- **String (regex rule):** Set directly as an instance attribute. PLY reads it via `getattr()` and uses it as a regex pattern.

After loading, `lex.lex(module=self)` inspects the instance via `dir()` and `getattr()`, finding both class attributes (`tokens`, `t_ignore`, `t_error`) and the dynamically loaded instance attributes.

## What stays on the class (and why)

Three things are _not_ sourced from assets:

| Attribute | Why it stays |
|-----------|-------------|
| `tokens = a.lexer.TOKENS` | PLY requires this at class level; sourced from assets but assigned statically |
| `t_ignore = ' \t'` | PLY infrastructure — defines whitespace handling, not grammar |
| `t_error(self, t)` | PLY infrastructure — defines what happens when _no_ rule matches |

These are properties of the lexer host, not the grammar. Grammar authors shouldn't need to think about them.

## Composing a new lexer variant

To build a new dialect, compose a new `TOKENS` + `RULES` from existing constants:

```python
# src/assets/lexer_minimal.py
from .lexer import (
    IDENTIFIER, STRING_LITERAL, NUMBER_LITERAL,
    PLUS, MINUS, STAR, SLASH,
    LPAREN, RPAREN, COMMA, COLON, EQUALS,
    NEWLINE, UNKNOWN,
)
from . import lexer as _lex

TOKENS_MINIMAL = (
    IDENTIFIER, STRING_LITERAL, NUMBER_LITERAL,
    PLUS, MINUS, STAR, SLASH,
    LPAREN, RPAREN, COMMA, COLON, EQUALS,
    NEWLINE, UNKNOWN,
)

RULES_MINIMAL = {
    't_IDENTIFIER': _lex.IDENTIFIER,
    't_STRING_LITERAL': _lex.STRING_LITERAL,
    't_NUMBER_LITERAL': _lex.NUMBER_LITERAL,
    't_PLUS': _lex.PLUS,
    't_MINUS': _lex.MINUS,
    't_STAR': _lex.STAR,
    't_SLASH': _lex.SLASH,
    't_LPAREN': _lex.LPAREN,
    't_RPAREN': _lex.RPAREN,
    't_COMMA': _lex.COMMA,
    't_COLON': _lex.COLON,
    't_EQUALS': _lex.EQUALS,
    't_NEWLINE': _lex.NEWLINE,
}
```

The `TiferetLexer` class itself needs no changes. A future enhancement could accept `TOKENS` and `RULES` as constructor parameters for even more flexibility.

## Testing tip (very common pattern)

```python
from src.events import DomainEvent
from src.interfaces import LexerService
from unittest import mock

def test_perform_lexical_analysis_success(sample_tokens):
    mock_lexer = mock.Mock(spec=LexerService)
    mock_lexer.tokenize.return_value = sample_tokens

    result = DomainEvent.handle(
        PerformLexicalAnalysis,
        dependencies={'lexer_service': mock_lexer},
        validated_blocks=[{'name': 'test', 'text': 'class Foo:\n    pass'}],
    )

    assert result['token_count'] == len(sample_tokens)
    mock_lexer.tokenize.assert_called_once()
```

Events depend on the `LexerService` interface, not `TiferetLexer` directly. Mock the interface in event tests; use the real lexer in utility tests.

## Quick reminders – key design points

- Grammar is data — token names, regex patterns, and function handlers are all constants in `assets/lexer.py`
- `TOKENS` is defined before rule handlers (captures string values before shadowing)
- Rule handler names are lexer-agnostic — `t_` prefix lives only in `RULES` keys
- Function rules need `MethodType` binding (descriptor protocol doesn't apply to instance attributes)
- `t_error` and `t_ignore` stay on the class — they're PLY infrastructure, not grammar
- New dialects = new `TOKENS` tuple + new `RULES` dict, same constants

## Related reading

- [LEXICAL_SPEC.md](../../../LEXICAL_SPEC.md) – formal lexical specification for all token types
- [AGENTS.md](../../../agents.md) – AI agent codebase index
- [docs/core/events.md](https://github.com/greatstrength/tiferet/blob/main/docs/core/events.md) – domain events & testing patterns
- [docs/core/interfaces.md](https://github.com/greatstrength/tiferet/blob/main/docs/core/interfaces.md) – service interface conventions
- [docs/core/code_style.md](https://github.com/greatstrength/tiferet/blob/main/docs/core/code_style.md) – formatting & artifact comments