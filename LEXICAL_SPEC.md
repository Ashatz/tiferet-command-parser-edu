# Scanner part 1 - Lexical Specification

## Input language: 

The input language is the **Tiferet Domain Event dialect**, a highly structured subset of **Python 3.10+** used within the Tiferet framework to implement domain-driven events following Clean Architecture and Domain-Driven Design (DDD) principles.

In DDD, a Domain Event represents a discrete, well-defined operation within the domain — a focused action that changes or queries domain state in response to a business requirement. Tiferet's `DomainEvent` base class formalizes this concept: each event class encapsulates a single operation, receives dependencies via constructor injection, validates inputs declaratively through the `@DomainEvent.parameters_required` decorator, and enforces domain rules via `self.verify(...)` calls.

The dialect is characterized by:
- Strict use of artifact comments (`# ***`, `# **`, `# *`) to mark architectural sections, events, methods, and attributes
- Event classes inheriting from `DomainEvent`
- Dependency injection via `__init__`
- A single `execute` method containing ordered business logic
- Declarative parameter validation via `@DomainEvent.parameters_required([...])`
- Ubiquitous use of `self.verify(...)`, `self.*_service.*(...)`, domain object factories `*.new(...)`, and domain constants `a.const.*`
- Standard Python syntax for function signatures, type annotations, calls, lists, dicts, etc.

The scanner is **not** a complete Python lexer — it recognizes only the tokens necessary to identify domain structure, validation patterns, service interactions, and execution flow for later AST-based extraction.


## Token Categories/Types:

### Artifact Comments (Tiferet-specific structural markers)

- ARTIFACT_START         `# *** …`     (major sections: imports, events, etc.)
- ARTIFACT_SECTION       `# ** …`      (subsections: event names, import groups)
- ARTIFACT_MEMBER        `# * …`       (members: method: execute, attribute: xxx_service)
- ARTIFACT_IMPORTS_START `# *** imports`
- ARTIFACT_IMPORT_GROUP  `# ** core`, `# ** app`, etc.

### Documentation & Conventional Comments

- DOCSTRING              Triple-quoted string literals used as class/method docstrings
- LINE_COMMENT           Single-line `# …` comments not matching artifact patterns

### Control & Structural Keywords (Tiferet-specific high-value names)

- CLASS                  `class`
- DEF                    `def`
- EXECUTE                `execute`     (the core business method)
- INIT                   `__init__`     (dependency injection point)
- RETURN                 `return`

### Domain Idioms & Patterns (core semantic carriers)

- PARAMETERS_REQUIRED    `@DomainEvent.parameters_required(`  (declarative parameter validation decorator)
- VERIFY                 `self.verify(`
- SERVICE_CALL           `self.<ident>_service.<ident>(`   (service method invocation)
- FACTORY_CALL           `<ident>.new(`                    (domain factory invocation)
- CONST_REF              `a.const.<ident>`

### Self Reference

- SELF                   `self`

### Generic Python Structural Tokens

- PYTHON_KEYWORD         Python reserved words: `from`, `import`, `if`, `else`, `for`, `True`, `False`, `None`, `is`, `not`, `in`, `and`, `or`, `as`, `with`, etc.
- IDENTIFIER             Letter/_ followed by letters/digits/_
- STRING_LITERAL         `'…'`, `"…"`, `'''…'''`, `"""…"""`
- NUMBER_LITERAL         Integer, float, or simple scientific notation

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


## Formal Specification:

(using basic regular expression notation as taught in class)

### Artifact Comments
```
ARTIFACT_START          #\s*\*{3}.*
ARTIFACT_SECTION        #\s*\*{2}\s+.*
ARTIFACT_MEMBER         #\s*\*\s+.*
ARTIFACT_IMPORTS_START  #\s*\*{3}\s+imports\s*
ARTIFACT_IMPORT_GROUP   #\s*\*{2}\s+(core|app|infra)
```

### Documentation & Comments
```
DOCSTRING               (""".*?""")   
LINE_COMMENT            #.*$                        (not starting with * after #)
```

### Structural & Domain Keywords (longest match first)
```
CLASS                   class
DEF                     def
INIT                    __init__
RETURN                  return
PARAMETERS_REQUIRED     @DomainEvent\.parameters_required\(
VERIFY                  self\.verify\(
SERVICE_CALL            self\.[a-zA-Z_][a-zA-Z0-9_]*_service\.[a-zA-Z_][a-zA-Z0-9_]*\(
FACTORY_CALL            [a-zA-Z_][a-zA-Z0-9_]*\.new\(
CONST_REF               a\.const\.[A-Z_][A-Z_]*
SELF                    self
```

### Generic Tokens
```
PYTHON_KEYWORD          (and|as|assert|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield)
IDENTIFIER              [a-zA-Z_][a-zA-Z0-9_]*
STRING_LITERAL          ("([^"\\]|\\.)*")|('([^'\\]|\\.)*')|('''.*?''')
NUMBER_LITERAL          [0-9]+(\.[0-9]+)?
```

### Punctuation & Delimiters (single characters / short fixed strings)
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

**Note:** The lexer should use longest-match-first priority and prefer domain-specific patterns (PARAMETERS_REQUIRED, SERVICE_CALL, etc.) over generic IDENTIFIER or PYTHON_KEYWORD.


## Examples: 

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

### Class & Method Structure
```python
class AddError(DomainEvent):
    def __init__(self, error_service: ErrorService):
        self.error_service = error_service

    @DomainEvent.parameters_required(['id', 'name', 'message'])
    def execute(self, id: str, name: str, message: str, **kwargs) -> None:
```

### Domain Idioms & Validation
```python
    @DomainEvent.parameters_required(['id', 'name', 'message'])
    def execute(self, id: str, name: str, message: str, **kwargs):

        exists = self.error_service.exists(id)
        self.verify(
            expression=exists is False,
            error_code=a.const.ERROR_ALREADY_EXISTS_ID,
            message=f'An error with ID {id} already exists.'
        )
```

### Factory & Return
```python
        new_error = Aggregate.new(ErrorAggregate, id=id, name=name, message=error_messages)
        self.error_service.save(new_error)
        return new_error
```

### Type Annotations & Collections
```python
    def execute(self,
            id: str,
            additional_messages: List[Dict[str, Any]] = []
        ) -> None:
```
