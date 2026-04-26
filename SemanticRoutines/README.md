# Semantic Routines

This directory contains the source code and reference outputs for the semantic analysis phase of the Tiferet Command Parser compiler. The implementation spans AST construction, symbol table building, name resolution, and type checking.

For running the full pipeline (lexing → parsing → semantic analysis → type checking), see the project [README](../README.md).

## Source Files

### AST

| File | Classes / Functions | Purpose |
|------|---------------------|---------|
| `ast_domain.py` | `Declaration`, `Statement`, `Expression`, `Type`, `ParamList`, `TypeKind`, `ExprKind`, `StatementKind` | Pydantic domain objects defining the AST node structures |
| `ast_mapper.py` | `TypeAggregate`, `ParamListAggregate`, `ExpressionAggregate`, `DeclarationAggregate`, `StatementAggregate` | Aggregate mappers with `new_*()` static factory methods for building the AST |

**Domain models** (`ast_domain.py`):

- **`Declaration`** — A named AST node representing a module, class, function, attribute, or artifact.
  - `name` — The identifier (e.g., class name `"Ping"`, method name `"execute"`, module name).
  - `type` — Optional `Type` describing what this declaration is (a class type, function type, primitive type, or artifact marker).
  - `metadata` — Freeform dict for parser-level annotations (e.g., `{"type": "ARTIFACT_MEMBER"}` for artifact wrappers, or `{"type": "***"}` for top-level sections).
  - `doc_string` — The declaration's docstring, if present.
  - `value` — Optional `Expression` for declarations that hold a value (e.g., attribute assignments like `count: int`).
  - `code` — Optional `Statement` chain representing the body (class members, method body, module-level statements).
  - `next` — Linked-list pointer to the next sibling declaration (e.g., chained artifact members within a class).

- **`Statement`** — A code unit within a declaration body.
  - `kind` — `StatementKind` enum discriminating the statement type.
  - `decl` — The associated `Declaration` for `decl`-kind statements (e.g., the class or function being declared) and for `artifact`-kind statements (the section header).
  - `init_expr` — The source module expression in `import_from` statements (e.g., the `.settings` in `from .settings import X`).
  - `expr` — The primary expression: the imported names in imports, the condition in `if_else`, the returned value in `return`, the assigned/called expression in `expr` statements.
  - `body` — Nested `Statement` chain for compound statements (artifact body, snippet body, loop body, if-body).
  - `else_body` — The else branch for `if_else` statements.
  - `next` — Linked-list pointer to the next sibling statement in sequence.

- **`Expression`** — A value, variable reference, operator, or function call.
  - `kind` — `ExprKind` enum discriminating the expression type (e.g., `add`, `name`, `str_val`, `assign`, `call`).
  - `value` — Literal text for value expressions (`"'pong'"` for `str_val`, `"42"` for `int_val`, `"+"` for operators).
  - `name` — Identifier string for `name` expressions (e.g., `"self.count"`, `"DomainEvent"`, `".settings"`).
  - `left` — Left sub-expression: the target in assignments, the left operand in binary ops, the callee in calls, the module in `import_as`.
  - `right` — Right sub-expression: the value in assignments, the right operand in binary ops, the arguments in calls, the alias in `import_as`.

- **`Type`** — Describes the type associated with a declaration.
  - `kind` — `TypeKind` enum (e.g., `class`, `func`, `int`, `str`, `artifact`).
  - `name` — Class name when `kind=class` (e.g., `"Ping"`, `"DomainEvent"`); absent for primitives.
  - `subtype` — Nested `Type` for inheritance chains (base class) or container element types (e.g., list element type).
  - `return_type` — Nested `Type` for function return types (e.g., `{"kind": "str"}` on a function that returns `str`).
  - `params` — Optional `ParamList` linked list for function parameter signatures.

- **`ParamList`** — A linked-list node for function parameters.
  - `name` — Parameter name (e.g., `"self"`, `"kwargs"`, `"a"`).
  - `type` — Optional `Type` annotation (e.g., `{"kind": "int"}` for `a: int`, `{"kind": "dict"}` for `**kwargs`).
  - `required` — `true` if the parameter has no default value; `false` if it does.
  - `default` — Optional `Expression` for the default value (e.g., `None`, a literal).
  - `next` — Pointer to the next parameter in the signature.

- **`TypeKind`** — Enum: `unknown`, `None`, `bool`, `str`, `int`, `float`, `list`, `dict`, `class`, `func`, `artifact`, `module`.
- **`ExprKind`** — Enum: `add`, `sub`, `mul`, `div`, `mod`, `exp`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `name`, `num_val`, `int_val`, `str_val`, `bool_val`, `assign`, `args_list`, `call`, `import`, `import_as`, `import_multi`, `artifact`, `comment`.
- **`StatementKind`** — Enum: `decl`, `expr`, `if_else`, `for`, `while`, `print`, `return`, `block`, `import`, `import_from`, `artifact`, `comment`, `snippet`.

Key AST builder functions (in `ast_mapper.py`):

- `DeclarationAggregate.new_module_decl()` — Create a module root declaration
- `DeclarationAggregate.new_class_decl()` — Create a class declaration with base classes
- `DeclarationAggregate.new_func_decl()` — Create a function/method declaration
- `DeclarationAggregate.new_attr_decl()` — Create an attribute declaration
- `DeclarationAggregate.new_artifact_decl()` — Create an artifact section header
- `DeclarationAggregate.new_member_decl()` — Create an artifact member wrapper
- `StatementAggregate.new_import_stmt_from()` — Create an import-from statement
- `StatementAggregate.new_decl_stmt()` — Create a declaration statement
- `StatementAggregate.new_artifact_stmt()` — Create an artifact statement
- `StatementAggregate.new_return_stmt()` — Create a return statement
- `StatementAggregate.new_snippet_stmt()` — Create a snippet statement
- `ExpressionAggregate.new_name_expr()` — Create a name reference expression
- `ExpressionAggregate.new_name_or_literal_expr()` — Create a literal expression
- `ExpressionAggregate.new_operator_expr()` — Create a binary operator expression
- `ExpressionAggregate.new_assign_expr()` — Create an assignment expression
- `ExpressionAggregate.new_call_expr()` — Create a call expression
- `TypeAggregate.new_class_type()` — Create a class type
- `TypeAggregate.new_func_type()` — Create a function type with params and return type

### AST Printing (Post-Order Traversal)

| File | Class | Purpose |
|------|-------|---------|
| `../src/utils/output.py` | `OutputPrinter` | Static methods for console printing of AST post-order traversal, symbol tables, and semantic errors |

Functions:

- `OutputPrinter.print_ast(ast)` — Print the AST with a section header then post-order traversal
- `OutputPrinter.print_declaration(decl)` — Print a Declaration tree (post-order)
- `OutputPrinter.print_statement(stmt)` — Print a Statement chain (post-order)
- `OutputPrinter.print_expression(expr)` — Print an Expression tree (post-order)
- `OutputPrinter.print_type(type_node)` — Print a Type tree (post-order)
- `OutputPrinter.print_param_list(param)` — Print a ParamList linked list (post-order)
- `OutputPrinter.print_symbol_table(symbol_table)` — Print the symbol table in readable format
- `OutputPrinter.print_semantic_errors(errors)` — Print type/semantic error descriptors to the console

### Symbol Table

| File | Classes | Purpose |
|------|---------|---------|
| `semantic_domain.py` | `Symbol`, `Scope`, `SymbolKind`, `ResolvedName`, `UnresolvedName`, `ResolutionResult` | Domain objects for the symbol table (symbols stored in hash tables within scopes; scopes managed as a stack) |
| `semantic_mapper.py` | `ScopeAggregate` | Aggregate with static factories (`new_module_scope`, `new_class_scope`, `new_method_scope`) and mutation methods (`add_symbol`, `add_child`, `has_symbol`, `get_symbol`) |
| `semantic_utils.py` | `SymbolTableBuilder`, `NameResolver` | Utilities for building the symbol table and resolving name references |

**Domain models** (`semantic_domain.py`):

- **`Symbol`** — An entry in a scope's symbol hash table.
  - `name` — The symbol identifier (e.g., `"DomainEvent"`, `"execute"`, `"count"`).
  - `kind` — `SymbolKind` enum classifying the symbol (import, class_def, method, attribute, parameter, variable). Method-local assignments register as **`variable`** symbols with the type inferred from the right-hand side (literal kind, name lookup, or arithmetic propagation).
  - `type_annotation` — Lightweight type hint string recorded during parsing (e.g., `"str"`, `"int"`, `"DomainEvent"`). Used by the type checker for compatibility checks.
  - `scope_path` — Fully qualified path of the scope where this symbol is defined (e.g., `"module"`, `"module.Ping.execute"`).
  - `source_module` — For import symbols only: the originating module path (e.g., `".settings"`, `"tiferet.events"`). `None` for non-imports.

- **`Scope`** — A lexical scope node in the symbol table.
  - `name` — The scope segment name (e.g., `"module"`, `"Ping"`, `"execute"`).
  - `kind` — `SymbolKind` indicating what created this scope: `module`, `class_def`, or `method`.
  - `path` — Fully qualified dot-separated path (e.g., `"module.Ping.execute"`).
  - `symbols` — `Dict[str, Symbol]`: hash table mapping symbol names to `Symbol` objects within this scope.
  - `children` — `Dict[str, str]`: maps child scope names to their fully qualified paths (e.g., `{"Ping": "module.Ping"}`).
  - `parent_path` — Path of the enclosing scope (`None` for the module root).

- **`SymbolKind`** — Enum: `module`, `import`, `class_def`, `method`, `attribute`, `parameter`, `variable`.

- **`ResolvedName`** — A name reference that was successfully looked up.
  - `name` — The referenced name (e.g., `"DomainEvent"`, `"self.message"`).
  - `scope_path` — Where the reference occurred (e.g., `"module.Ping.execute"`).
  - `resolved_to` — The scope where the matching symbol was found (e.g., `"module"` for a module-level import).

- **`UnresolvedName`** — A name reference with no matching symbol in any enclosing scope.
  - `name` — The unresolved name (e.g., `"self.logger.info"`).
  - `scope_path` — Where the reference occurred.

- **`ResolutionResult`** — The aggregate output of the name resolution pass.
  - `resolved` — List of `ResolvedName` entries for all successfully resolved references.
  - `unresolved` — List of `UnresolvedName` entries for all failed lookups.

Key functions:

- `SymbolTableBuilder.build(module_decl)` — Single-pass AST walk; constructs scopes and registers symbols; returns `{module_name, scopes, root_scope_path}`. Method-local assignments (`x = ...` inside a method scope) are registered as `VARIABLE` symbols whose `type_annotation` is inferred via `infer_local_type` (literal types, looked-up names, propagated arithmetic). Re-assigning the same local name in one scope emits `DUPLICATE_VARIABLE_SAME_SCOPE`, and a local that shadows an outer class attribute, parameter, or import emits `VARIABLE_SHADOWS_OUTER_SCOPE`. Both errors are accumulated on `builder.errors` and surfaced through the `PerformSemanticAnalysis` event.
- `NameResolver.resolve(module_decl)` — Second-pass AST walk; resolves name references against the scope registry; returns `ResolutionResult` with resolved and unresolved lists.

### Type Checking

| File | Class | Purpose |
|------|-------|---------|
| `typecheck_utils.py` | `TypeChecker` | AST walker that validates structural artifacts and checks type compatibility |

Key function:

- `TypeChecker.check(module_decl)` — Walk the AST and return a list of error dicts

Error codes generated (≥2 required):

1. `TYPE_MISMATCH_ASSIGNMENT` — RHS type incompatible with declared LHS type
2. `TYPE_MISMATCH_OPERATION` — binary operator applied to incompatible operand types
3. `INVALID_IMPORT_GROUP` — import section name not in `{core, infra, app}`
4. `INVALID_IMPORT_CONTENT` — non-import statement inside import section
5. `ARTIFACT_CLASS_NAME_MISMATCH` — section snake_case name ≠ class PascalCase name
6. `EVENT_MISSING_EXECUTE` — event class lacks an `execute` method
7. `INVALID_ATTRIBUTE_MEMBER_TYPE` — attribute member wraps a function/class
8. `INVALID_METHOD_MEMBER_TYPE` — method member wraps non-function
9. `METHOD_MISSING_SELF` — method's first param is not `self`
10. `INVALID_METHOD_RETURN_TYPE` — return type is not a valid TypeKind
11. `ATTRIBUTE_MEMBER_NAME_MISMATCH` — attribute member name ≠ inner declaration
12. `METHOD_MEMBER_NAME_MISMATCH` — method member name ≠ inner declaration

Additional structural diagnostics emitted by `SymbolTableBuilder` (merged into the same error list by `PerformTypeCheck`):

13. `DUPLICATE_VARIABLE_SAME_SCOPE` — a local variable name is assigned more than once in the same method scope
14. `VARIABLE_SHADOWS_OUTER_SCOPE` — a method-local variable shadows an enclosing class attribute, parameter, import, or other variable

### Parser Integration

The PLY yacc parser (`src/utils/parser.py` — `TiferetParser`) builds Pydantic AST nodes directly in its `p_*` grammar rule methods. Each grammar production calls the appropriate `*Aggregate.new_*()` factory to construct the AST during parsing.

## Running the Semantic Analysis

The `semantic event` CLI command runs the full pipeline: lexical analysis → syntactic parsing → semantic analysis → type checking.

```bash
# Write symbol table + name resolution + type errors to file
python compiler.py semantic event <source_file> -o output.json

# Include AST in file output
python compiler.py semantic event <source_file> -o output.json --include-ast true

# Print AST (post-order) and symbol table to console (no -o flag)
python compiler.py semantic event <source_file> --include-ast true
```

When no `-o` flag is provided, `EmitResult` (`src/events/output.py`) prints the AST (post-order traversal via `OutputPrinter.print_ast`) and the symbol table (via `OutputPrinter.print_symbol_table`) directly to the console.

Pre-computed outputs for all sample files are in `samples/`.

## Test Cases

### Test 1: Minimal Event (pass — declarations, types, statements, expressions)

**Input Source** (`samples/pass_minimal_event.py`):
```python
# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: ping
class Ping(DomainEvent):
    """A minimal event with no attributes and a single method."""

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Return a static response."""

        # Return pong.
        return 'pong'
```

**Printed AST** (JSON, abbreviated — full output in `samples/pass_minimal_event.json`):
```json
{
  "name": "pass_minimal_event",
  "code": {
    "kind": "artifact",
    "decl": { "name": "imports", "type": { "kind": "artifact" }, "metadata": { "type": "***" } },
    "body": {
      "kind": "artifact",
      "decl": { "name": "app", "type": { "kind": "artifact" }, "metadata": { "type": "**" } },
      "body": {
        "kind": "import_from",
        "init_expr": { "kind": "name", "name": ".settings" },
        "expr": { "kind": "name", "name": "DomainEvent" }
      }
    },
    "next": {
      "kind": "artifact",
      "decl": { "name": "events", "type": { "kind": "artifact" }, "metadata": { "type": "***" } },
      "body": {
        "kind": "artifact",
        "decl": { "name": "ping", "type": { "kind": "artifact" }, "metadata": { "type": "** event" } },
        "body": {
          "kind": "decl",
          "decl": {
            "name": "Ping",
            "type": { "kind": "class", "name": "Ping", "subtype": { "kind": "class", "name": "DomainEvent" } },
            "code": {
              "kind": "decl",
              "decl": {
                "name": "method", "type": { "kind": "artifact" }, "metadata": { "type": "ARTIFACT_MEMBER" },
                "code": {
                  "kind": "decl",
                  "decl": {
                    "name": "execute",
                    "type": { "kind": "func", "return_type": { "kind": "str" }, "params": { "name": "self", "next": { "name": "kwargs" } } },
                    "code": {
                      "kind": "snippet",
                      "body": {
                        "kind": "comment", "expr": { "kind": "comment", "value": "# Return pong." },
                        "next": { "kind": "return", "expr": { "kind": "str_val", "value": "'pong'" } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Printed Symbol Table:**
```
=== Symbol Table: pass_minimal_event ===

Scope: module [module]
  Symbols:
    DomainEvent [import] from=.settings
    Ping [class_def] type=DomainEvent
  Children:
    Ping -> module.Ping

Scope: module.Ping [class_def] (parent: module)
  Symbols:
    execute [method] type=str
  Children:
    execute -> module.Ping.execute

Scope: module.Ping.execute [method] (parent: module.Ping)
  Symbols:
    self [parameter] type=unknown
    kwargs [parameter] type=dict
```

**Name Resolution:** `DomainEvent` → resolved to `module`
**Type Errors:** None

---

### Test 2: Multiple Operator Events (pass — multiple declarations, expressions, types)

**Input Source** (`samples/pass_multiple_operator_events.py`):
```python
"""This module demonstrates how to define multiple operator events in the Tiferet Dialect"""

# *** imports

# ** infra
from tiferet.events import DomainEvent

# *** events

# ** event: add
class Add(DomainEvent):
    """An event that performs addition of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the sum of a and b."""
        return a + b

# ** event: subtract
class Subtract(DomainEvent):
    """An event that performs subtraction of two numbers."""

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Return the difference of a and b."""
        return a - b

# ** event: multiply
class Multiply(DomainEvent):
    ...

# ** event: divide
class Divide(DomainEvent):
    ...

# ** event: modulus
class Modulus(DomainEvent):
    ...

# ** event: exponentiate
class Exponentiate(DomainEvent):
    ...
```

**Printed Symbol Table** (abbreviated — 6 classes, 6 method scopes):
```
=== Symbol Table: pass_multiple_operator_events ===

Scope: module [module]
  Symbols:
    DomainEvent [import] from=tiferet.events
    Add [class_def] type=DomainEvent
    Subtract [class_def] type=DomainEvent
    Multiply [class_def] type=DomainEvent
    Divide [class_def] type=DomainEvent
    Modulus [class_def] type=DomainEvent
    Exponentiate [class_def] type=DomainEvent
  Children:
    Add -> module.Add
    Subtract -> module.Subtract
    Multiply -> module.Multiply
    Divide -> module.Divide
    Modulus -> module.Modulus
    Exponentiate -> module.Exponentiate

Scope: module.Add.execute [method] (parent: module.Add)
  Symbols:
    self [parameter] type=unknown
    a [parameter] type=int
    b [parameter] type=int
```

**Name Resolution:** `DomainEvent` resolved × 6, `a` and `b` resolved in each `execute` method
**Type Errors:** None

---

### Test 3: Unresolved Attribute (fail — name resolution error)

**Input Source** (`samples/fail_unresolved_attribute.py`):
```python
"""Semantic failure: method body references self.logger, which is never declared as a class attribute."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: log_result
class LogResult(DomainEvent):
    """An event that references an attribute not declared on the class."""

    # * attribute: message
    message: str

    # * init
    def __init__(self, message: str):
        """Initialize with a message."""
        self.message = message

    # * method: execute
    def execute(self, **kwargs) -> str:
        """Attempt to log using an undeclared attribute."""
        self.logger.info(self.message)
        return self.message
```

**Printed Symbol Table:**
```
Scope: module.LogResult [class_def] (parent: module)
  Symbols:
    message [attribute] type=str
    __init__ [method] type=None
    execute [method] type=str
```

**Name Resolution:**
- Resolved: `DomainEvent`, `message` (in `__init__`), `self.message` (in `execute`)
- **Unresolved: `self.logger.info`** — `logger` is never declared on `LogResult`

---

### Test 4: Type Mismatch (fail — type checking errors)

**Input Source** (`samples/fail_type_mismatch.py`):
```python
"""Semantic failure: assigns a str literal to an int-typed attribute and adds int + str."""

# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: bad_math
class BadMath(DomainEvent):
    """An event with type mismatches in assignment and operation."""

    # * attribute: count
    count: int

    # * init
    def __init__(self, count: int):
        """Initialize with a count."""
        self.count = 'not_a_number'

    # * method: execute
    def execute(self, a: int, b: int) -> int:
        """Attempt arithmetic with incompatible types."""
        return a + 'hello'
```

**Printed Symbol Table:**
```
Scope: module.BadMath [class_def] (parent: module)
  Symbols:
    count [attribute] type=int
    __init__ [method] type=None
    execute [method] type=int

Scope: module.BadMath.execute [method] (parent: module.BadMath)
  Symbols:
    self [parameter] type=unknown
    a [parameter] type=int
    b [parameter] type=int
```

**Type Errors (3 detected):**
```
Type Error [TYPE_MISMATCH_ASSIGNMENT] in module.BadMath.__init__ (line 22, col 19):
    Cannot assign str to variable declared as int

Type Error [TYPE_MISMATCH_OPERATION] in module.BadMath.execute (line 29, col 17):
    Unsupported operand types for add: int and str

Type Error [EVENT_MISSING_EXECUTE] in module (line 10, col 0):
    Event 'bad_math' class 'BadMath' must declare an 'execute' method
```

## Pre-Computed Samples

| Sample | Type | Content |
|--------|------|---------|
| `samples/pass_imports_only.json` | Pass | Imports only — module-level symbols |
| `samples/pass_minimal_event.json` | Pass | Single event class with one method |
| `samples/pass_minimal_injection_event.json` | Pass | Event with attribute injection and `__init__` |
| `samples/pass_multiple_operator_events.json` | Pass | Six arithmetic event classes |
| `samples/pass_helper_method_event.json` | Pass | Event with helper method and chained arithmetic |
| `samples/pass_constant_folding_event.json` | Pass | Constant numeric sub-expressions used to demonstrate AST folding |
| `samples/pass_arithmetic_parens.json` | Pass | Parenthesized arithmetic, including the canonical large arithmetic tree `5 * 8 - 6 + (11 - 9 * 7) + 3` |
| `samples/pass_variable_scopes.json` | Pass | Multiple methods, method-local variables of inferred types (`int`, `float`, `str`) across distinct scopes |
| `samples/fail_unresolved_attribute.json` | Fail | Unresolved `self.logger` reference |
| `samples/fail_unresolved_import.json` | Fail | Unresolved import reference |
| `samples/fail_type_mismatch.json` | Fail | Type mismatch in assignment and operation |
| `samples/fail_undefined_variable.json` | Fail | Reference to an undefined identifier (`UnresolvedName`) |
| `samples/fail_duplicate_same_scope.json` | Fail | Same-scope local redefinition (`DUPLICATE_VARIABLE_SAME_SCOPE`) |
| `samples/fail_shadow_outer_scope.json` | Fail | Local shadows enclosing class attribute (`VARIABLE_SHADOWS_OUTER_SCOPE`) |
| `samples/fail_assignment_type_mismatch.json` | Fail | `str` local assigned to an `int`-typed class attribute (`TYPE_MISMATCH_ASSIGNMENT`) |

When a sample emits any structural or type error, `PerformSemanticAnalysis` omits the `symbol_table` and `resolution` keys from the JSON envelope (errors are surfaced to the console instead). The AST is still included whenever `--include-ast true` is used, so the failure cases keep their full Pydantic AST for inspection.
