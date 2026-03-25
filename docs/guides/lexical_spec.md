# Scanner Part 1 — Lexical Specification

## Input Language

The input language is the **Tiferet Domain Event dialect**, a highly structured subset of **Python 3.10+** used within the Tiferet framework to implement domain-driven events following Clean Architecture and Domain-Driven Design (DDD) principles.

In DDD, a Domain Event represents a discrete, well-defined operation within the domain — a focused action that changes or queries domain state in response to a business requirement. Tiferet's `DomainEvent` base class formalizes this concept: each event class encapsulates a single operation, receives dependencies via constructor injection, validates inputs declaratively through the `@DomainEvent.parameters_required` decorator, and enforces domain rules via `self.verify(...)` calls.

The dialect is characterized by:
- Strict use of artifact comments (`# ***`, `# **`, `# *`) to mark architectural sections, events, methods, and attributes
- Event classes inheriting from `DomainEvent`
- Dependency injection via `__init__`
- A single `execute` method containing ordered business logic
- Declarative parameter validation via `@DomainEvent.parameters_required([...])`
- Standard Python syntax for function signatures, type annotations, calls, lists, dicts, etc.

The scanner is **not** a complete Python lexer — it recognizes only the tokens necessary to identify domain structure, annotation markers, operators, and execution flow for later AST-based extraction.


## Token Categories/Types

### Artifact Comments (Tiferet-specific structural markers)

- ARTIFACT_IMPORTS_START `# *** imports`
- ARTIFACT_IMPORT_GROUP  `# ** core`, `# ** app`, etc.
- ARTIFACT_START         `# *** …`     (major sections: imports, events, etc.)
- ARTIFACT_SECTION       `# ** …`      (subsections: event names, import groups)
- ARTIFACT_MEMBER        `# * …`       (members: method: execute, attribute: xxx_service)

### Annotation Markers

- OBSOLETE               `# - obsolete: …` or `# -- obsolete: …`  (marks deprecated artifact members)
- TODO                   `# + todo: …` or `# ++ todo: …`           (marks in-progress artifact members)

### Documentation & Conventional Comments

- DOCSTRING              Triple-quoted string literals used as class/method docstrings
- LINE_COMMENT           Single-line `# …` comments not matching artifact or annotation patterns

### Control & Structural Keywords

- CLASS                  `class`
- DEF                    `def`
- INIT                   `__init__`     (dependency injection point)
- RETURN                 `return`

### Self Reference

- SELF                   `self`

### Generic Python Structural Tokens

- PYTHON_KEYWORD         Python reserved words: `from`, `import`, `if`, `else`, `for`, `True`, `False`, `None`, `is`, `not`, `in`, `and`, `or`, `as`, `with`, etc.
- IDENTIFIER             Letter/_ followed by letters/digits/_
- STRING_LITERAL         `'…'`, `"…"`, `'''…'''`, `"""…"""`
- NUMBER_LITERAL         Integer or float

### Operators

- DOUBLESTAR             `**`
- PLUS                   `+`
- MINUS                  `-`
- STAR                   `*`
- SLASH                  `/`
- DOUBLESLASH            `//`
- PERCENT                `%`
- PIPE                   `|`
- AMPERSAND              `&`
- TILDE                  `~`
- CARET                  `^`
- LSHIFT                 `<<`
- RSHIFT                 `>>`
- EQEQ                   `==`
- NOTEQ                  `!=`
- LTEQ                   `<=`
- GTEQ                   `>=`
- LT                     `<`
- GT                     `>`
- AT                     `@`

### Punctuation & Delimiters

- LPAREN                 `(`
- RPAREN                 `)`
- LBRACK                 `[`
- RBRACK                 `]`
- LBRACE                 `{`
- RBRACE                 `}`
- COMMA                  `,`
- COLON                  `:`
- ARROW                  `->`
- DOT                    `.`
- EQUALS                 `=`

### Layout & Error Tokens

- NEWLINE                `\n`
- UNKNOWN                Any unmatched character or sequence (for error reporting)


## Formal Specification

(using basic regular expression notation as taught in class)

### Artifact Comments
```
ARTIFACT_IMPORTS_START  #\s*\*{3}\s+imports\s*
ARTIFACT_IMPORT_GROUP   #\s*\*{2}\s+(core|app|infra)
ARTIFACT_START          #\s*\*{3}.*
ARTIFACT_SECTION        #\s*\*{2}\s+.*
ARTIFACT_MEMBER         #\s*\*\s+.*
```

### Annotation Markers
```
OBSOLETE                #\s*-{1,2}\s+obsolete:[^\n]+
TODO                    #\s*\+{1,2}\s+todo:[^\n]+
```

### Documentation & Comments
```
DOCSTRING               (""".*?""")
LINE_COMMENT            #.*$                        (not starting with * after #)
```

### Structural Keywords
```
CLASS                   class
DEF                     def
INIT                    __init__
RETURN                  return
SELF                    self
```

### Generic Tokens
```
PYTHON_KEYWORD          (and|as|assert|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield)
IDENTIFIER              [a-zA-Z_][a-zA-Z0-9_]*
STRING_LITERAL          ("([^"\\]|\\.)*")|('([^'\\]|\\.)*')|('''.*?''')
NUMBER_LITERAL          [0-9]+(\.[0-9]+)?
```

### Operators (longest match first)
```
DOUBLESTAR              \*\*
DOUBLESLASH             //
LSHIFT                  <<
RSHIFT                  >>
EQEQ                    ==
NOTEQ                   !=
LTEQ                    <=
GTEQ                    >=
PLUS                    \+
MINUS                   -
STAR                    \*
SLASH                   /
PERCENT                 %
PIPE                    \|
AMPERSAND               &
TILDE                   ~
CARET                   \^
LT                      <
GT                      >
AT                      @
```

### Punctuation & Delimiters
```
LPAREN                  \(
RPAREN                  \)
LBRACK                  \[
RBRACK                  \]
LBRACE                  \{
RBRACE                  \}
COMMA                   ,
COLON                   :
ARROW                   ->
DOT                     \.
EQUALS                  =
```

### Layout
```
NEWLINE                 \n
UNKNOWN                 .
```

**Ignored characters:** spaces and tabs (`t_ignore = ' \t'`).

**Note:** Multi-character operators (`**`, `//`, `<<`, `>>`, `==`, `!=`, `<=`, `>=`) use longest-match-first priority over their single-character counterparts.

### Keyword Resolution Rules

When the lexer matches an `IDENTIFIER` pattern (`[a-zA-Z_][a-zA-Z0-9_]*`), it checks the matched text against a keyword table and promotes the token to a more specific type:

- `class` → `CLASS`
- `def` → `DEF`
- `__init__` → `INIT`
- `return` → `RETURN`
- `self` → `SELF`
- Any Python reserved word (`from`, `import`, `if`, `else`, `for`, `True`, `False`, `None`, `is`, `not`, `in`, `and`, `or`, `as`, `with`, `yield`, etc.) → `PYTHON_KEYWORD`

If the identifier does not match any keyword, it remains `IDENTIFIER`.


## Examples

### Artifact Comments & Structure
```python
# *** imports

# ** core
from typing import List, Dict, Any

# ** app
from .settings import DomainEvent, a
from ..domain import Error
from ..interfaces import ErrorService
from ..mappers import ErrorAggregate

# *** events

# ** event: add_error
class AddError(DomainEvent):
```

### Annotation Markers
```python
# -- obsolete: replaced by ErrorAggregate.new in v0.2.0
def _build_error(self, id, name):
    ...

# ++ todo: inject CacheService for result caching
def execute(self, id: str, **kwargs):
    ...
```

### Class & Method Structure
```python
class AddError(DomainEvent):
    def __init__(self, error_service: ErrorService):
        self.error_service = error_service

    @DomainEvent.parameters_required(['id', 'name', 'message'])
    def execute(self, id: str, name: str, message: str, **kwargs) -> None:
```

### Type Annotations & Collections
```python
    def execute(self,
            id: str,
            additional_messages: List[Dict[str, Any]] = []
        ) -> None:
```
