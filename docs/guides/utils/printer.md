# Utilities – ASTPrinter (AST and Symbol Table Printer)

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`ASTPrinter` is a diagnostic utility for visualizing AST trees and symbol tables produced by the compiler pipeline. It performs post-order traversal of the linked-list AST (Declaration → Statement → Expression → Type → ParamList) and prints each node with indentation reflecting tree depth. It also provides a formatted printer for symbol table output from `SymbolTableBuilder`.

All methods are static — no instantiation is required.

**Files:**
- `src/utils/printer.py` — `ASTPrinter`


## ASTPrinter

### Static Methods

**`print_ast(decl, indent=0)`** — Entry point for AST visualization. Walks the `Declaration` linked list using post-order traversal (children before parent). For each declaration node:
1. Visits `code` (statement chain), `value` (expression), and `type` sub-trees
2. Prints the declaration node with name, type kind, and truncated docstring
3. Follows the `.next` chain for sibling declarations

**`print_statement(stmt, indent=0)`** — Prints a `Statement` node. Post-order visits: `body`, `else_body`, `decl`, `init_expr`, `expr`, then prints the statement kind and follows `.next`.

**`print_expression(expr, indent=0)`** — Prints an `Expression` node. Post-order visits: `left`, `right` sub-expressions, then prints kind, name, and value.

**`print_type(type_node, indent=0)`** — Prints a `Type` node. Post-order visits: `subtype`, `return_type`, `params`, then prints kind and name.

**`print_param_list(param, indent=0)`** — Prints a `ParamList` linked list. Post-order visits: `default` (expression), `type`, then prints name and required/optional status. Follows `.next` chain.

**`print_symbol_table(symbol_table)`** — Prints the symbol table dict (as returned by `SymbolTableBuilder.build()`) in a readable hierarchical format. For each scope: prints path, kind, parent, symbols (with kind, type annotation, source module), and children.


### Output Format

AST output uses two-space indentation per depth level with bracketed node types:

```
  [Statement] kind=artifact
    [Declaration] name=AddError : class
      [Statement] kind=decl
        [Expression] kind=name name=error_service
      [Declaration] name=execute : func
  [Declaration] name=add_error : module
```

Symbol table output uses a flat scope listing:

```
=== Symbol Table: add_error ===

Scope: module [module]
  Symbols:
    DomainEvent [import] from=tiferet.events
  Children:
    AddError -> module.AddError

Scope: module.AddError [class_def] (parent: module)
  Symbols:
    error_service [attribute] type=ErrorService
  Children:
    execute -> module.AddError.execute
```


## Usage

```python
from src.utils import ASTPrinter

# Print the full AST tree (post-order)
ASTPrinter.print_ast(module_decl)

# Print a symbol table
ASTPrinter.print_symbol_table(symbol_table)
```

The printer is intended for debugging and educational demonstration — it writes directly to stdout via `print()`.


## Related reading

- [parser.md](parser.md) — TiferetParser utility guide (produces the AST consumed by the printer)
- [semantic.md](semantic.md) — SymbolTableBuilder (produces the symbol table consumed by the printer)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
