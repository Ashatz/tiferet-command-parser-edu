# Utilities – SymbolTableBuilder, NameResolver, and TypeChecker

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`SymbolTableBuilder`, `NameResolver`, and `TypeChecker` are the three semantic analysis utilities. Together they implement a three-pass approach:

1. **SymbolTableBuilder** — single-pass AST walker that constructs scopes and populates symbol entries (imports, classes, methods, attributes, parameters).
2. **NameResolver** — second-pass AST walker that resolves name references in expressions against the built scope registry.
3. **TypeChecker** — third-pass AST walker that performs rudimentary type checking on assignments and binary operations, raising structured errors on mismatches.

All three utilities operate on the Pydantic AST produced by `TiferetParser` and use `ScopeAggregate` (from `src/mappers/semantic.py`) for scope management.

**Files:**
- `src/utils/semantic.py` — `SymbolTableBuilder`, `NameResolver`, and `TypeChecker`
- `src/domain/semantic.py` — `SymbolKind`, `Symbol`, `Scope`, `ResolvedName`, `UnresolvedName`, `ResolutionResult`
- `src/mappers/semantic.py` — `ScopeAggregate` with scope factories and mutation methods


## SymbolTableBuilder

### Purpose

Walks the module-level `DeclarationAggregate` AST and builds a flat registry of scopes, each containing its declared symbols.

### Key Behaviors

- **Scope stack** — maintains a stack of `ScopeAggregate` objects for nested scope entry/exit
- **Scope factories** — `ScopeAggregate.new_module_scope()`, `.new_class_scope()`, `.new_method_scope()`
- **Statement dispatch** — iterates `.next`-chained statement lists and dispatches by `StatementKind`:
  - `ARTIFACT` — transparent wrapper, recurses into body
  - `IMPORT_FROM` / `IMPORT` — registers imported names as `SymbolKind.IMPORT`
  - `DECL` — dispatches to class, function, or attribute handlers
  - `EXPR` — detects `self.X = ...` assignments and registers as attributes
  - `SNIPPET` — transparent wrapper, recurses into body
- **ARTIFACT_MEMBER unwrapping** — walks the `.next` chain of member declarations within a class

### Entry Point

```python
builder = SymbolTableBuilder()
symbol_table = builder.build(module_decl)
# Returns: { 'module_name': str, 'scopes': { path: scope_dict }, 'root_scope_path': 'module' }
```

### Output Structure

```python
{
    'module_name': 'add_error',
    'scopes': {
        'module': { 'name': 'add_error', 'kind': 'module', 'symbols': [...], 'children': {...} },
        'module.AddError': { 'name': 'AddError', 'kind': 'class_def', ... },
        'module.AddError.execute': { 'name': 'execute', 'kind': 'method', ... },
    },
    'root_scope_path': 'module',
}
```


## NameResolver

### Purpose

Walks the AST a second time, resolving name references against the pre-built scope registry. Produces a `ResolutionResult` containing resolved and unresolved name lists.

### Key Behaviors

- **Scope chain resolution** — for each name reference, walks from the current scope up through the stack to find a matching symbol
- **`self.X` handling** — resolves `self.X` references by looking up `X` in the nearest enclosing class scope
- **Skip patterns** — ignores `self` (implicit), import statements (definitions, not references), and literal expressions
- **Expression tree walk** — recursively resolves names in assignments (right side only), binary operations, and calls

### Entry Point

```python
resolver = NameResolver(scopes)  # scopes = Dict[str, ScopeAggregate]
result = resolver.resolve(module_decl)
# Returns: ResolutionResult(resolved=[...], unresolved=[...])
```

### Output Structure

```python
ResolutionResult(
    resolved=[
        ResolvedName(name='ErrorService', scope_path='module.AddError.__init__', resolved_to='module'),
        ResolvedName(name='self.error_service', scope_path='module.AddError.execute', resolved_to='module.AddError'),
    ],
    unresolved=[
        UnresolvedName(name='UndefinedType', scope_path='module.AddError'),
    ],
)
```


## TypeChecker

### Purpose

Walks the AST a third time, using the symbol table to perform rudimentary type checking. Verifies that typed variable assignments and binary arithmetic operations use compatible types. Raises `TiferetError` via `RaiseError.execute()` on the first mismatch encountered.

### Key Behaviors

- **Assignment checking** — if a variable (including `self.X`) has a declared `type_annotation` in the symbol table and the right-hand side infers to an incompatible type, raises `TYPE_MISMATCH_ASSIGNMENT`
- **Binary operation checking** — if operands of an arithmetic expression (`add`, `sub`, `mul`, `div`, `mod`, `exp`) have incompatible types, raises `TYPE_MISMATCH_OPERATION`
- **Type inference** — infers types from:
  - Literal expression kinds: `int_val` → `int`, `num_val` → `float`, `str_val` → `str`, `bool_val` → `bool`
  - Name references via symbol table lookup (walks scope chain)
  - `self.X` references via enclosing class scope lookup
  - Binary operation result types (recursive inference)
- **Compatibility rules:**
  - Numeric + numeric (`int`, `float`) is valid for all arithmetic operations
  - `str + str` is valid (concatenation)
  - `str * int` or `int * str` is valid (repetition)
  - `int` → `float` widening is allowed on assignment
  - All other combinations raise an error
- **Scope tracking** — maintains a scope stack identical to `NameResolver`, entering/exiting class and method scopes as it walks the AST

### Entry Point

```python
checker = TypeChecker(scopes)  # scopes = Dict[str, ScopeAggregate]
checker.check(module_decl)     # raises TiferetError on first mismatch
```

### Error Codes

Defined in `config.yml` under `errors:`:

- **`TYPE_MISMATCH_ASSIGNMENT`** — `Cannot assign {actual_type} to variable declared as {expected_type}`
- **`TYPE_MISMATCH_OPERATION`** — `Unsupported operand types for {operation}: {left_type} and {right_type}`

### Example Failure

Given the sample `samples/fail_type_mismatch.py`:

```python
class BadMath(DomainEvent):
    count: int

    def __init__(self, count: int):
        self.count = 'not_a_number'   # TYPE_MISMATCH_ASSIGNMENT: str → int

    def execute(self, a: int, b: int) -> int:
        return a + 'hello'            # TYPE_MISMATCH_OPERATION: int + str
```

Running:
```bash
python compiler.py semantic event samples/fail_type_mismatch.py
```
Produces:
```
{"error_code": "TYPE_MISMATCH_ASSIGNMENT", "message": "Cannot assign str to variable declared as int", "expected_type": "int", "actual_type": "str"}
```


## Pipeline Integration

The semantic utilities are wired into the `semantic.event` pipeline in `config.yml`:

1. **PerformLexicalAnalysis** — tokenizes source file
2. **PerformSyntacticAnalysis** — parses tokens into AST
3. **PerformSemanticAnalysis** — builds the symbol table via `SymbolTableBuilder` and resolves names via `NameResolver`
4. **PerformTypeCheck** — runs `TypeChecker` against the AST and symbol table; returns a list of type error descriptors
5. **EmitResult** — auto-detects the `semantic` stage, prints `semantic_errors` via `OutputPrinter`, and assembles a `SemanticAnalysisCompleted` envelope via `ResultPayloadBuilder.build_semantic_payload`


## Testing

Semantic utility tests: `src/utils/tests/test_semantic.py` (15 tests)
Semantic mapper tests: `src/mappers/tests/test_semantic.py` (9 tests)
Semantic domain tests: `src/domain/tests/test_semantic.py` (9 tests)

```bash
python -m pytest src/utils/tests/test_semantic.py -v
```


## Related reading

- [parser.md](parser.md) — TiferetParser utility guide (produces the AST consumed by semantic analysis)
- [ir.md](ir.md) — IRGenerator utility guide (consumes the symbol table)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
