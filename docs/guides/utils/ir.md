# Utilities – DocstringParser and IRGenerator

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`DocstringParser` is a static utility for extracting structured information from RST-formatted docstrings. `IRGenerator` is the concrete implementation of `IRService` that walks a `DeclarationAggregate` AST and produces an `IREventGroup` conforming to the keter IR schema.

**Files:**
- `src/utils/ir.py` — `DocstringParser` and `IRGenerator`
- `src/interfaces/ir.py` — `IRService` abstract interface
- `src/domain/ir.py` — Pydantic IR domain objects (`IREventGroup`, `IREvent`, `IRImportGroup`, `IRAttribute`, `IRInjection`, `IRParam`, `IRReturn`, `IRSnippet`, `IRExecute`, `IRMethod`, etc.)
- `src/mappers/ir.py` — `IREventGroupAggregate` with mutation helpers


## DocstringParser

Static utility with three methods for extracting information from RST-formatted docstrings:

- **`strip(raw)`** — removes triple-quote delimiters and surrounding whitespace
- **`parse_param_descriptions(raw)`** — extracts `:param name: description` entries into a `Dict[str, str]`
- **`parse_return_descriptions(raw)`** — extracts `:return:` / `:returns:` entries into a `List[str]`

```python
from src.utils.ir import DocstringParser

raw = '''
    Add a new Error.

    :param id: The error identifier.
    :type id: str
    :return: The created error.
    :rtype: Error
'''

DocstringParser.strip(raw)
# 'Add a new Error.\n\n    :param id: ...'

DocstringParser.parse_param_descriptions(raw)
# {'id': 'The error identifier.'}

DocstringParser.parse_return_descriptions(raw)
# ['The created error.']
```


## IRGenerator

Implements `IRService` and walks the module-level `DeclarationAggregate` AST to produce an `IREventGroup`.

### IRService Interface

```python
class IRService(Service):
    @abstractmethod
    def generate(self, ast: Any, symbol_table: Optional[Dict[str, Any]] = None) -> IREventGroup:
        raise NotImplementedError()
```

### Generation Process

The `generate()` method:
1. Extracts module name and description from the AST root
2. Walks the top-level statement chain, dispatching by artifact group name:
   - `imports` group → `build_import_groups()` → `IRImportGroups`
   - All other groups → `build_events()` → `IREvents`
3. Returns an `IREventGroup` containing both collections

### Event Construction

For each event class found in the AST, `build_event()` walks the `ARTIFACT_MEMBER` chain and dispatches by member role:

- `attribute` → `build_attributes()` → `IRAttributes` (name + type)
- `init` → `build_injections()` → `IRInjections` (name, type, description, assign)
- `method` named `execute` → `build_execute()` → `IRExecute` (params, returns, snippets)
- Other `method` → `build_method()` → `IRMethod` (params, returns, snippets)

### Expression Encoding

`encode_expr()` recursively encodes expression nodes to string:
- Name → `'name'`
- Assignment → `'Assign(left, right)'`
- Arithmetic → `'Add(left, right)'`, `'Sub(...)'`, `'Mul(...)'`, etc.
- Call → `'Call(callee, args)'`
- Return statement → `'Return(expr)'`

### Keter IR Output

Each IR domain object has a `to_keter()` method for serializing to the keter DSL format (defined in `IntermediateRepresentation/schema.txt`).

```python
from src.utils.ir import IRGenerator

generator = IRGenerator()
ir = generator.generate(ast_root, symbol_table=None)
keter_text = ir.to_keter()
```


## Pipeline Integration

The IR generator is wired into the `ir.event` pipeline in `config.yml`:

1. **PerformLexicalAnalysis** — tokenizes source file
2. **PerformSyntacticAnalysis** — parses tokens into AST
3. **PerformSemanticAnalysis** — builds symbol table and resolves names
4. **PerformTypeCheck** — validates artifact structure and types against the symbol table
5. **GenerateIR** — calls `ir_service.generate(ast, symbol_table)` → `IREventGroup`
6. **EmitResult** — auto-detects the `ir` stage, calls `ir.to_keter()` via `ResultPayloadBuilder.build_ir_payload`, and emits the keter DSL

```yaml
# config.yml (attrs section)
ir_service:
  module_path: src.utils.ir
  class_name: IRGenerator
```


## Testing

IR utility tests: `src/utils/tests/test_ir.py` (19 tests)
IR event tests: `src/events/tests/test_ir.py` (3 tests)
IR domain tests: `src/domain/tests/test_ir.py` (12 tests)
IR mapper tests: `src/mappers/tests/test_ir.py` (4 tests)

```bash
python -m pytest src/utils/tests/test_ir.py -v
```


## Related reading

- [semantic.md](semantic.md) — SymbolTableBuilder and NameResolver (upstream of IR generation)
- [codegen.md](codegen.md) — TiferetGenerator (downstream, consumes IR)
- [parser.md](parser.md) — TiferetParser (produces the AST consumed by IRGenerator)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
