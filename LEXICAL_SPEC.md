# Scanner part 1 - Lexical Specification

## Input language: 

The input language is the **Tiferet Command dialect**, a highly structured subset of **Python 3.10+** used within the Tiferet framework to implement domain-driven events via the Command pattern classes following Clean Architecture and Domain-Driven Design principles.

The dialect is characterized by:
- Strict use of artifact comments (`# ***`, `# **`, `# *`) to mark architectural sections, commands, methods, and attributes
- Command classes inheriting from `Command`
- Dependency injection via `__init__`
- A single `execute` method containing ordered business logic
- Ubiquitous use of `self.verify_parameter(...)`, `self.verify(...)`, `self.*_service.*(...)`, domain object factories `*.new(...)`, and domain constants `a.const.*`
- Standard Python syntax for function signatures, type annotations, calls, lists, dicts, etc.

The scanner is **not** a complete Python lexer — it recognizes only the tokens necessary to identify domain structure, validation patterns, service interactions, and execution flow for later AST-based extraction.


## Token Categories/Types:

### Artifact Comments (Tiferet-specific structural markers)

- ARTIFACT_START         `# *** …`     (major sections: imports, commands, etc.)
- ARTIFACT_SECTION       `# ** …`      (subsections: command names, import groups)
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

- VERIFY_PARAMETER       `self.verify_parameter(`
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

- INDENT                 Increase in leading whitespace (optional – may be deferred to AST phase)
- DEDENT                 Decrease in leading whitespace (optional)
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
ARTIFACT_IMPORT_GROUP   #\s*\*{2}\s+(core|app|infra|adapters|...)
```

### Documentation & Comments
```
DOCSTRING               (""".*?""")|('''.*?''')    (non-greedy, multiline)
LINE_COMMENT            #.*$                        (not starting with * after #)
```

### Structural & Domain Keywords (longest match first)
```
CLASS                   class
DEF                     def
INIT                    __init__
RETURN                  return
VERIFY_PARAMETER        self\.verify_parameter\(
VERIFY                  self\.verify\(
SERVICE_CALL            self\.[a-zA-Z_][a-zA-Z0-9_]*_service\.[a-zA-Z_][a-zA-Z0-9_]*\(
FACTORY_CALL            [a-zA-Z_][a-zA-Z0-9_]*\.new\(
CONST_REF               a\.const\.[a-zA-Z_][a-zA-Z0-9_]*
SELF                    self
```

### Generic Tokens
```
PYTHON_KEYWORD          (and|as|assert|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield)
IDENTIFIER              [a-zA-Z_][a-zA-Z0-9_]*
STRING_LITERAL          ("([^"\\]|\\.)*")|('([^'\\]|\\.)*')|(""".*?""")|('''.*?''')
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
INDENT                  (handled by tracking leading whitespace – optional)
DEDENT                  (handled by tracking leading whitespace – optional)
NEWLINE                 \n
UNKNOWN                 .
```

**Note:** The lexer should use longest-match-first priority and prefer domain-specific patterns (VERIFY_PARAMETER, SERVICE_CALL, etc.) over generic IDENTIFIER or PYTHON_KEYWORD.


## Examples: 

### Artifact Comments & Structure
```python
# *** imports

# ** core
from typing import List, Dict, Any

# ** app
from .settings import Command, a
from ..models import Error

# *** commands

# ** command: add_error
class AddError(Command):
```

### Class & Method Structure
```python
class AddError(Command):
    def __init__(self, error_service: ErrorService):
        self.error_service = error_service

    def execute(self, id: str, name: str) -> None:
```

### Domain Idioms & Validation
```python
        self.verify_parameter(parameter=id, parameter_name='id', command_name='AddError')
        
        exists = self.error_service.exists(id)
        self.verify(
            expression=exists is False,
            error_code=a.const.ERROR_ALREADY_EXISTS_ID,
            message=f'An error with ID {id} already exists.'
        )
```

### Factory & Return
```python
        new_error = Error.new(id=id, name=name, message=[{'lang': 'en_US', 'text': message}])
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
