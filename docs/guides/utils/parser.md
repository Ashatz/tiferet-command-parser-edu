# Utilities – TiferetParser

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`TiferetParser` is a PLY yacc-based syntactic parser for the Tiferet Domain Event dialect. It extends `ParserBase` (which implements the `ParserService` interface) and dynamically loads grammar rules from `src/assets/parser.py`, mirroring the `TiferetLexer` pattern for lexical analysis.

The parser consumes a token stream produced by `TiferetLexer` (with synthetic `INDENT`/`DEDENT` tokens injected by `BlockTracker`) and produces a **Pydantic-based AST** using `DeclarationAggregate`, `StatementAggregate`, and `ExpressionAggregate` mapper classes.

**Files:**
- `src/utils/parser.py` — `TokenStream`, `ParserBase`, `TiferetParser`
- `src/interfaces/parser.py` — `ParserService` abstract interface
- `src/assets/parser.py` — Grammar constants: `TOKENS`, `precedence`, and AST builder helpers
- `src/mappers/ast.py` — Pydantic AST mapper aggregates (`Decl`, `Stmt`, `Expr`, `Type`, `ParamList`)


## ParserService Interface

`ParserService` extends Tiferet's `Service` (ABC) and defines a single abstract method:

```python
class ParserService(Service):
    @abstractmethod
    def parse(self, module_name: str, tokens: List[TokenAggregate]) -> Dict[str, Any]:
        '''Parse a list of tokens into a structured AST.'''
        raise NotImplementedError()
```

`ParserBase` implements this method. `TiferetParser` extends `ParserBase` with the full grammar.


## Class Hierarchy

### ParserBase

Base class providing shared infrastructure:
- **Token list and precedence** sourced from `a.parser.TOKENS` and `a.parser.precedence`
- **`parse(module_name, tokens)`** — converts tokens to a `TokenStream`, invokes PLY yacc, returns the AST
- **Static helpers** — `parse_artifact_header()`, `parse_member_kind()`, `get_attribute_type()`
- **`p_error()`** — structured syntax error reporting using Tiferet artifact hierarchy terminology

### TiferetParser

Extends `ParserBase` with the complete grammar implemented as `p_*` methods (PLY convention). Grammar rules build Pydantic AST nodes via the mapper aggregates in semantic actions.


## Pydantic AST Model

The parser builds a typed AST using Pydantic `BaseModel` classes. AST nodes use **linked-list chaining** via `.next` fields rather than Python lists.

### Core mapper aggregates (from `src/mappers/ast.py`)

- **`Decl` / `DeclarationAggregate`** — module, class, function, and attribute declarations
- **`Stmt` / `StatementAggregate`** — statements: artifact, import, decl, expr, snippet, comment, return, etc.
- **`Expr` / `ExpressionAggregate`** — expressions: name, literal, assignment, binary ops, call, import, etc.
- **`Type` / `TypeAggregate`** — type annotations with `TypeKind` enum (str, int, float, class, func, artifact, etc.)
- **`ParamList` / `ParamListAggregate`** — linked-list parameter chain with name, type, default, required

### Static factories

Mapper aggregates provide static factory methods for node construction:
- `Decl.new_module_decl()`, `Decl.new_class_decl()`, `Decl.new_func_decl()`
- `Stmt.new_artifact_stmt()`, `Stmt.new_import_from_stmt()`, `Stmt.new_snippet_stmt()`
- `Expr.new_name_expr()`, `Expr.new_assign_expr()`, `Expr.new_call_expr()`

### Mutation methods

- `set_next()`, `set_left()`, `set_right()`, `set_return_type()`, `set_code()`

### Serialization

The AST root (`DeclarationAggregate`) is serialized to dict via:
```python
ast.model_dump(exclude_none=True, exclude_unset=True)
```


## TokenStream Adapter

PLY's `yacc.parser.parse()` expects a lexer-like object with a `.token()` method. `TokenStream` provides this adapter:

```python
stream = TokenStream(tokens)  # tokens = List[TokenAggregate]
parser.parser_service.parse(lexer=stream)
```

`TokenStream` wraps each `TokenAggregate` into a `PLYToken` object with `.type`, `.value`, `.lineno`, and `.lexpos` attributes.


## Grammar Assets (`src/assets/parser.py`)

- **`TOKENS`** — re-exported from `src/assets/lexer.py` (all 53 token types)
- **`precedence`** — PLY precedence tuple resolving structural boundary ambiguities
- **AST builder helpers** — functions used by `TiferetParser` grammar rules to construct AST nodes

See [grammar_spec.md](../grammar_spec.md) for the formal grammar definition, LR(1) automaton, and LALR verification.


## Usage

### Basic Usage

```python
from src.utils import TiferetLexer, TiferetParser

# 1. Tokenize (includes INDENT/DEDENT via BlockTracker)
lexer = TiferetLexer()
tokens = lexer.tokenize(source_text)

# 2. Parse into Pydantic AST
parser = TiferetParser()
ast = parser.parse('my_module', tokens)

# 3. Serialize to dict
ast_dict = ast.model_dump(exclude_none=True, exclude_unset=True)
```

### Pipeline Integration

In the Tiferet application, the parser is wired as part of the `parse.event` pipeline in `config.yml`:

1. **PerformLexicalAnalysis** — reads source file, tokenizes via `LexerService` (with `BlockTracker`)
2. **PerformSyntacticAnalysis** — parses token stream via `ParserService`, returns serialized AST dict
3. **EmitParseResult** — assembles output payload with AST

The parser service is injected via the Tiferet DI container:

```yaml
# config.yml (attrs section)
parser_service:
  module_path: src.utils.parser
  class_name: TiferetParser
```


## Error Handling

`ParserBase.p_error()` raises a `SyntaxError` with context about the unexpected token and expected artifact hierarchy structure. Domain events (`PerformSyntacticAnalysis`) wrap parsing in a `verify` call to produce structured `TiferetError` instances when the AST root is invalid.


## Relationship to Other Utilities

- **`TiferetLexer`** — produces the token stream consumed by `TiferetParser`
- **`BlockTracker`** — injects synthetic `INDENT`/`DEDENT` tokens that the parser uses as block delimiters (integrated into `TiferetLexer.tokenize()`)
- **`ArtifactBlockParser`** — extracts artifact blocks from source files for preprocessing
- **`ScanOutputWriter`** — used by `EmitParseResult` to write the final payload (including AST) to file


## Testing

Parser utility tests: `src/utils/tests/test_parser.py` (51 tests)
Parser event tests: `src/events/tests/test_parser.py` (6 tests)

```bash
python -m pytest src/utils/tests/test_parser.py -v
python -m pytest src/events/tests/test_parser.py -v
```

Tests use mock `ParserService` instances for event isolation and real `TiferetParser` instances for utility integration tests.


## Related reading

- [grammar_spec.md](../grammar_spec.md) — formal grammar definition and LALR verification
- [lexer.md](lexer.md) — TiferetLexer and BlockTracker utility guide
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
