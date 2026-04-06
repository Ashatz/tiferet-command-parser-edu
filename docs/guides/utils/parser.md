# Parser Utility — TiferetParser

## Overview

`TiferetParser` is a PLY yacc-based syntactic parser for the Tiferet Domain Event dialect. It implements the `ParserService` interface and dynamically loads grammar rules from `src/assets/parser.py`, exactly mirroring the `TiferetLexer` pattern for lexical analysis.

The parser consumes a token stream produced by `TiferetLexer` (with synthetic `INDENT`/`DEDENT` tokens injected by `IndentInjector`) and produces a structured AST reflecting the three-tier artifact comment hierarchy:

- **Tier 1** — Module / Artifact Groups (`# ***`)
- **Tier 2** — Artifact Sections (`# **`)
- **Tier 3** — Artifact Members (`# *`)

**Files:**
- `src/utils/parser.py` — `TiferetParser` utility class, `TokenStream` adapter, `PLYToken`, semantic actions, and helpers
- `src/interfaces/parser.py` — `ParserService` abstract interface
- `src/assets/parser.py` — Grammar constants: `TOKENS`, `precedence`, `RULES` mapping, and AST builder helpers


## ParserService Interface

`ParserService` extends Tiferet's `Service` (ABC) and defines a single abstract method:

```python
class ParserService(Service):
    @abstractmethod
    def parse(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        '''Parse a list of tokens into a structured AST.'''
        raise NotImplementedError()
```

`TiferetParser` is the concrete implementation. Domain events depend on the `ParserService` interface, keeping domain logic decoupled from the PLY infrastructure.


## Dynamic Grammar Loading

`TiferetParser.__init__` dynamically attaches grammar rules from `src/assets/parser.py` — the same pattern used by `TiferetLexer` for lexer rules:

1. **Token list and precedence** are sourced directly from `a.parser.TOKENS` and `a.parser.precedence`.
2. **Grammar rules** are loaded from `a.parser.RULES`, a dict mapping PLY rule function names (e.g., `p_module`, `p_group`) to either:
   - **String BNF rules** — wrapped with a semantic action function resolved from the `_SEMANTIC_ACTIONS` dispatch table.
   - **Callable rules** — bound directly as methods on the parser instance.
3. PLY's `yacc.yacc()` builds the LALR parser with `module=self`, `start='module'`, `debug=False`, and `write_tables=False`.

This design keeps grammar definitions (BNF productions + AST builders) in the assets layer, while `TiferetParser` serves as a generic PLY host.


## Grammar Assets (`src/assets/parser.py`)

The grammar assets module defines the complete context-free grammar for the Tiferet Domain Event dialect:

- **`TOKENS`** — re-exported from `src/assets/lexer.py` (all 53 token types)
- **`precedence`** — PLY precedence tuple resolving structural boundary ambiguities (`COLON`, `ARROW`, artifact markers, `DEDENT`)
- **`RULES`** — dict of 69 production rules organized by tier:
  - Tier 1: Module / Artifact Groups (rules 1–6)
  - Tier 2: Artifact Sections (rules 7–16)
  - Section Body / Imports (rules 17–22)
  - Class Definition (rules 23–27)
  - Tier 3: Artifact Members (rules 28–34)
  - Method Definition (rules 35–43)
  - Function Definition (rules 44–47)
  - Body / Snippets (rules 48–57)
  - Token Sequence (rules 58–68)
  - Token Catch-All (rule 69)
- **AST builder helpers** — `build_module`, `build_group`, `build_section`, `build_class_def`, `build_member`, `build_method_def`, `build_func_def`, `build_snippet`, `build_stmt`, `build_enclosed`, etc.

See [grammar_spec.md](../grammar_spec.md) for the formal grammar definition, LR(1) automaton, and LALR verification.


## Usage

### Basic Usage

```python
from src.utils import TiferetLexer, TiferetParser
from src.utils import ArtifactBlockParser, IndentInjector

# 1. Read source file
with open('samples/add_error_event.py', 'r') as f:
    source = f.read()

# 2. Extract artifact blocks (imports + events)
blocks = ArtifactBlockParser.extract_artifact_blocks(source, 'event')
imports = ArtifactBlockParser.extract_imports_block(source)

# 3. Tokenize each block
lexer = TiferetLexer()
all_tokens = []
for block in [imports] + blocks:
    tokens = lexer.tokenize(block['text'])
    tokens = IndentInjector.inject(tokens)
    all_tokens.extend(tokens)

# 4. Parse token stream into AST
parser = TiferetParser()
ast = parser.parse(all_tokens)
```

### Pipeline Integration

In the Tiferet application, the parser is wired as part of the `parse.event` pipeline in `config.yml`:

1. **ExtractText** — reads source file, extracts artifact blocks
2. **LexerInitialized** — validates extracted text blocks
3. **PerformLexicalAnalysis** — tokenizes blocks via `LexerService` + `IndentInjector`
4. **ParserInitialized** — validates `ParserService` readiness
5. **PerformSyntacticAnalysis** — parses token stream via `ParserService`
6. **EmitParseResult** — assembles output payload with AST

The parser service is injected into `ParserInitialized` and `PerformSyntacticAnalysis` events via the Tiferet DI container:

```yaml
# config.yml (attrs section)
parser_service:
  module_path: src.utils.parser
  class_name: TiferetParser
```


## TokenStream Adapter

PLY's `yacc.parser.parse()` expects a lexer-like object with a `.token()` method. `TokenStream` provides this adapter:

```python
stream = TokenStream(tokens)  # tokens = List[Dict[str, Any]]
parser.parser.parse(lexer=stream)
```

`TokenStream` iterates over the token dictionaries and wraps each into a `PLYToken` object with `.type`, `.value`, `.lineno`, and `.lexpos` attributes that PLY expects.


## AST Structure

The parser produces a nested dict-based AST. Each node has a `type` key indicating its kind:

- **`Module`** — root node containing a `groups` list
- **`Group`** — `header` (artifact group token value) + `sections` list
- **`Section`** — `header` + `annotations` list + `body` (ClassDef, FuncDef, or ImportBlock)
- **`ClassDef`** — `name`, `bases`, `docstring`, `members` list
- **`Member`** — `kind` (attribute/method/init), `annotations`, `body` (AttrDecl or MethodDef)
- **`MethodDef`** — `name`, `params`, `return_type`, `decorator`, `docstring`, `body` (list of Snippets)
- **`FuncDef`** — same shape as MethodDef but without `SELF` requirement
- **`Snippet`** — `comment` (optional LINE_COMMENT) + `statements` list
- **`Stmt`** — `tokens` (flat token sequence) + optional `block` (compound statement body)
- **`Enclosed`** — `open`, `items`, `close` (matched bracket group)
- **`ImportBlock`** — `statements` list of ImportStmt nodes
- **`ImportStmt`** — `keyword` + `tokens`
- **`AttrDecl`** — `name` + `type_annotation`
- **`Annot`** — `kind` (OBSOLETE/TODO) + `text`
- **`Decorator`** — `tokens` list
- **`Body`** — `docstring` + `snippets` list

### Example AST Fragment

For a simple event class with one method:

```yaml
type: Module
groups:
  - type: Group
    header: "# *** events"
    sections:
      - type: Section
        header: "# ** event: add_error"
        annotations: []
        body:
          type: ClassDef
          name: AddError
          bases: [DomainEvent]
          docstring: "Command to add a new Error..."
          members:
            - type: Member
              kind: method
              annotations: []
              body:
                type: MethodDef
                name: execute
                params: [...]
                return_type: null
                decorator: null
                docstring: "Add a new Error..."
                body:
                  - type: Snippet
                    comment: "# Check if error exists."
                    statements:
                      - type: Stmt
                        tokens: [...]
                        block: null
```


## Error Handling

The parser reports syntax errors via `p_error`, raising a `SyntaxError` with context about the unexpected token and expected artifact hierarchy structure. Domain events (`PerformSyntacticAnalysis`) wrap parsing in a `verify` call to produce structured `TiferetError` instances when the AST root is invalid.


## Semantic Actions

Semantic actions translate PLY productions into AST nodes. They are organized in `src/utils/parser.py` as module-level functions dispatched via the `_SEMANTIC_ACTIONS` dict:

- **Tier 1 actions** — `_action_module`, `_action_group`, `_action_group_header`
- **Tier 2 actions** — `_action_section`, `_action_section_annotated`, annotation builders
- **Section body actions** — import block, class def, function def builders
- **Tier 3 actions** — `_action_member`, `_action_member_annotated`, attribute/method builders
- **Body/snippet actions** — body, snippet, and statement builders
- **Token sequence actions** — token seq, enclosed, inner item handlers
- **List helpers** — `_collect_list` (left-recursive accumulation), `_empty_list` (base case)

String-based BNF rules from assets are wrapped by `_build_semantic_action`, which resolves the correct action from the dispatch table and sets `__doc__` to the production string (required by PLY).


## Relationship to Other Utilities

- **`TiferetLexer`** — produces the token stream consumed by `TiferetParser`
- **`IndentInjector`** — injects synthetic `INDENT`/`DEDENT` tokens that the parser uses as block delimiters
- **`ArtifactBlockParser`** — extracts artifact blocks from source files; the parser operates on the combined token stream from all extracted blocks
- **`ScanOutputWriter`** — used by `EmitParseResult` to write the final payload (including AST) to file


## Testing

Parser utility tests live in `src/utils/tests/test_parser.py` (16 tests). Parser event tests live in `src/events/tests/test_parser.py` (9 tests).

```bash
# Run parser utility tests
python -m pytest src/utils/tests/test_parser.py -v

# Run parser event tests
python -m pytest src/events/tests/test_parser.py -v
```

Tests use mock `ParserService` instances for event isolation and real `TiferetParser` instances for utility integration tests.
