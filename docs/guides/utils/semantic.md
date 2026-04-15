# Utilities – SymbolTableBuilder and NameResolver

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`SymbolTableBuilder` and `NameResolver` are the two semantic analysis utilities. Together they implement a classic two-pass approach:

1. **SymbolTableBuilder** — single-pass AST walker that constructs scopes and populates symbol entries (imports, classes, methods, attributes, parameters).
2. **NameResolver** — second-pass AST walker that resolves name references in expressions against the built scope registry.

Both utilities operate on the Pydantic AST produced by `TiferetParser` and use `ScopeAggregate` (from `src/mappers/semantic.py`) for scope management.

**Files:**
- `src/utils/semantic.py` — `SymbolTableBuilder` and `NameResolver`
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


## Pipeline Integration

The semantic utilities are wired into the `semantic.event` pipeline in `config.yml`:

1. **PerformLexicalAnalysis** — tokenizes source file
2. **PerformSyntacticAnalysis** — parses tokens into AST
3. **PerformSemanticAnalysis** — builds symbol table via `SymbolTableBuilder`, resolves names via `NameResolver`
4. **EmitSemanticResult** — assembles output payload


## Testing

Semantic utility tests: `src/utils/tests/test_semantic.py` (9 tests)
Semantic mapper tests: `src/mappers/tests/test_semantic.py` (9 tests)
Semantic domain tests: `src/domain/tests/test_semantic.py` (9 tests)

```bash
python -m pytest src/utils/tests/test_semantic.py -v
```


## Related reading

- [parser.md](parser.md) — TiferetParser utility guide (produces the AST consumed by semantic analysis)
- [ir.md](ir.md) — IRGenerator utility guide (consumes the symbol table)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
