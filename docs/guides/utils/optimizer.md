# Utilities – YamlAnchorOptimizer, ConstantFolder, StrengthReducer, and ReturnAnalyzer

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

The optimizer module provides four concrete utilities that together implement the compiler's optimization levels:

- **`YamlAnchorOptimizer`** — codegen-level pass that deduplicates repeated `params` / `returns` lists so PyYAML can emit anchors and aliases automatically. Runs at `-O O2`.
- **`ConstantFolder`** — AST-level pass that folds binary arithmetic expressions with two numeric-literal operands into a single literal. Runs at `-O O1` and `-O O2`.
- **`StrengthReducer`** — AST-level pass that rewrites a small set of expensive arithmetic operations into cheaper equivalents (shifts and self-multiplication). Runs at `-O O1` and `-O O2` immediately after `ConstantFolder`.
- **`ReturnAnalyzer`** — AST-level analysis pass that detects statements appearing after a `return` within the same scope and emits diagnostic `UNREACHABLE_AFTER_RETURN` warnings. Runs at `-O O1` and `-O O2` and does not mutate the AST.

Each utility implements a dedicated service interface and is driven by a single-purpose domain event, keeping each optimization independently injectable, testable, and wirable.

**Files:**
- `src/utils/settings.py` — `ASTTraversal` shared traversal base class
- `src/utils/optimizer.py` — `YamlAnchorOptimizer`, `ConstantFolder`, `StrengthReducer`, `ReturnAnalyzer`
- `src/interfaces/optimizer.py` — `OptimizerService`, `ASTOptimizerService`, `ASTStrengthReducerService`, `ReturnAnalyzerService` abstract interfaces
- `src/events/optimizer.py` — `FoldConstants`, `ReduceStrength`, `OptimizeCode`, `AnalyzeReturns` domain events

## Service Interfaces

### OptimizerService

```python
class OptimizerService(Service):
    @abstractmethod
    def optimize(self, codegen: Dict[str, Any]) -> Dict[str, Any]:
        '''Deduplicate repeated structures in the codegen output dict.'''
        raise NotImplementedError()
```

### ASTOptimizerService

```python
class ASTOptimizerService(Service):
    @abstractmethod
    def fold(self, ast: Declaration) -> Declaration:
        '''Apply constant folding to the AST rooted at *ast*.'''
        raise NotImplementedError()
```

### ASTStrengthReducerService

```python
class ASTStrengthReducerService(Service):
    @abstractmethod
    def reduce(self, ast: Declaration) -> Declaration:
        '''Apply strength reduction to the AST rooted at *ast*.'''
        raise NotImplementedError()
```

### ReturnAnalyzerService

```python
class ReturnAnalyzerService(Service):
    @abstractmethod
    def analyze(self, ast: Declaration) -> List[Dict]:
        '''Return warnings for statements following a return in scope.'''
        raise NotImplementedError()
```

## ASTTraversal

Base class in `src/utils/settings.py` that provides the shared declaration and statement traversal skeleton for AST transformation passes.

Both `ConstantFolder` and `StrengthReducer` extend `ASTTraversal` alongside their respective service interfaces, inheriting `traverse_declaration` and `traverse_statement` and overriding the `transform_expression` hook to route into their own expression-level rewrite logic.

### Public Methods

- **`traverse_declaration(decl)`** — walks a `Declaration` chain: transforms `decl.value`, recurses into `decl.code` via `traverse_statement`, then follows `decl.next`.
- **`traverse_statement(stmt)`** — walks a `Statement` chain: recurses into `stmt.decl`, transforms `stmt.expr` and `stmt.init_expr`, recurses into `stmt.body` and `stmt.else_body`, then follows `stmt.next`.
- **`transform_expression(expr)`** — hook called by the traversal for every expression field encountered. Default returns `expr` unchanged. Subclasses override to apply per-expression rewrites.

### Extending ASTTraversal

To write a new AST transformation pass, extend `ASTTraversal`, override `transform_expression` to apply your rewrite after children are handled, and call `traverse_declaration(ast)` as the entry point:

```python path=null start=null
class MyPass(ASTTraversal):
    def transform_expression(self, expr):
        return self.my_rewrite(expr)  # your expression-level logic

    def my_rewrite(self, expr):
        if expr is None:
            return None
        if expr.left:  expr.left  = self.my_rewrite(expr.left)
        if expr.right: expr.right = self.my_rewrite(expr.right)
        # ... apply rewrite and return
        return expr
```

## YamlAnchorOptimizer

Codegen-level optimizer that inspects every event's `execute` and `methods` sections, collects their `params` and `returns` lists, and replaces any list appearing two or more times with a single shared Python object. A top-level `vars` key is added to hold the canonical objects so PyYAML emits anchor declarations (`&…`) there and aliases (`*…`) everywhere else.

### Public Methods

- **`optimize(codegen)`** — entry point. Walks the dict, builds a fingerprint map of `(kind, tuple(values)) → [(parent, key), …]`, and patches each duplicate location to reference the same list object. Returns the original dict unchanged when no duplicates are found.
- **`collect_lists(codegen)`** — walks every event and delegates to `collect_from_callable` for the `execute` and each `method` dict.
- **`collect_from_callable(callable_dict, collected)`** — records the `params` and `returns` lists for a single callable into the fingerprint map.

### Example Output

When three events share the same `params` and two of them share the same `returns`:

```yaml
vars:
  - &id001
    - a:int:true::
    - b:int:true::
  - &id002
    - int:
evt_grp:
  evts:
    add:
      execute:
        params: *id001
        returns: *id002
    subtract:
      execute:
        params: *id001
        returns: *id002
    divide:
      execute:
        params: *id001
        returns:
          - float:
```

## ConstantFolder

AST-level optimizer that performs a post-order walk over the module declaration tree. For each binary arithmetic node whose both operands are numeric literals, it replaces the node with a single literal carrying the computed value. Variable references, calls, comparisons, and mixed constant / variable expressions are left untouched.

### Supported Operators

`ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `EXP` (defined in `ARITHMETIC_OPS`).

### Numeric Literal Kinds

`INT_VAL` and `NUM_VAL` are unambiguously numeric (`NUMERIC_KINDS`). `STR_VAL` is also accepted when its string value parses as a number — this matches the parser convention of storing raw token values as `STR_VAL`.

### Public Methods

- **`is_numeric(expr)`** — returns True when *expr* is a foldable numeric literal (including numeric `STR_VAL`).
- **`fold(ast)`** — entry point. Calls `traverse_declaration(ast)` (inherited from `ASTTraversal`) and returns the (mutated) root.
- **`transform_expression(expr)`** — overrides the `ASTTraversal` hook; routes directly into `fold_expression`.
- **`fold_expression(expr)`** — post-order: recurses into left and right children (via itself), then attempts to collapse the current node.
- **`evaluate(expr)`** — computes the result of a binary arithmetic node with two numeric-literal children.

`traverse_declaration` and `traverse_statement` are inherited from `ASTTraversal` and are no longer defined on `ConstantFolder` directly.

### Result Kind Rules

- Division always yields `NUM_VAL` (even for whole-number quotients).
- Non-division operations that produce a whole number yield `INT_VAL` when both operands were `INT_VAL` / `NUM_VAL`, otherwise `STR_VAL` (matching the parser's raw-token convention).
- Non-division operations that produce a non-integer yield `NUM_VAL`.

### Example

```python
# Before:  return (3 * 5) * 2
# After:   return 30  (INT_VAL)

# Before:  return 10 / 4
# After:   return 2.5  (NUM_VAL)

# Before:  result = x + (4 * 5)
# After:   result = x + 20  (outer ADD preserved; constant subtree folded)
```

## StrengthReducer

AST-level optimizer that rewrites three textbook strength-reduction patterns. The pass is designed to run **after** `ConstantFolder` so that expressions like `(2 * 4) * x` first fold to `8 * x` and then reduce to `x << 3`.

### Supported Patterns

1. **Multiplication by a positive integer power of two** (`MUL`): `x * 2**k` or `2**k * x` becomes `x << k` (multiplication is commutative, so the literal may be on either side).
2. **Division by a positive integer power of two** (`DIV`): `x / 2**k` becomes `x >> k`. Division is *not* commutative, so only the divisor (right operand) is examined; `2**k / x` is left alone.
3. **Exponentiation by two** (`EXP`): `x ** 2` becomes `x * x`. The left operand is deep-copied so the two `MUL` children are distinct nodes.

Anything that does not match one of these patterns — non-integer literals, zero or negative literals, non-power-of-two literals, exponents other than `2`, identity cases like `x * 1` — is left untouched.

### Public Methods

- **`is_power_of_two_literal(expr)`** — returns the exponent `k` when *expr* is a positive integer literal equal to `2**k`, otherwise `None`. Accepts `INT_VAL`, `NUM_VAL`, and numeric `STR_VAL` nodes.
- **`is_literal_two(expr)`** — guard used by the exponentiation rewrite; returns True iff *expr* is the literal `2`.
- **`deep_copy_expr(expr)`** — recursive structural clone of an `Expression` tree into a fresh `ExpressionAggregate`. Used only for the `x ** 2` rewrite.
- **`make_int_literal(value, lineno, col)`** — helper that builds an `INT_VAL` node carrying the shift amount.
- **`reduce(ast)`** — entry point. Calls `traverse_declaration(ast)` (inherited from `ASTTraversal`) and returns the (mutated) root.
- **`transform_expression(expr)`** — overrides the `ASTTraversal` hook; routes directly into `reduce_expression`.
- **`reduce_expression(expr)`** — post-order: recurses into left and right children (via itself), then attempts the three strength-reduction rewrites.
- **`try_reduce_mul(expr)`** / **`try_reduce_div(expr)`** / **`try_reduce_exp(expr)`** — per-pattern rewrite helpers.

`traverse_declaration` and `traverse_statement` are inherited from `ASTTraversal` and are no longer defined on `StrengthReducer` directly.

### Position Preservation

Replacement `SHL`, `SHR`, and self-multiplication `MUL` nodes inherit `lineno` / `col` from the outer expression they replace, so downstream IR generation and error reporting continue to point at the correct source location.

### Example

```python
# Before (after constant folding):
#   scaled = value * 8
#   halved = value / 4
#   squared = value ** 2

# After strength reduction (-O O1):
#   scaled = value << 3
#   halved = value >> 2
#   squared = value * value
```

## ReturnAnalyzer

AST-level analyzer that performs a non-mutating walk of the declaration tree, maintaining a scope stack so findings carry a qualified `scope_path`. For every function or method body it walks the statement chain left-to-right; as soon as a `return` statement is seen, all remaining statements on the same chain are recorded as `UNREACHABLE_AFTER_RETURN` warnings. Each statement's inner bodies (e.g. `body`, `else_body`) are always analyzed independently so dead code inside an earlier branch is still caught.

### Warning Shape

Warnings are plain dicts, following the same pattern as `TypeChecker` errors:

```python
{
    'warning_code': 'UNREACHABLE_AFTER_RETURN',
    'message': 'Statement is unreachable (follows a return statement)',
    'scope_path': 'module.ClassifyScore.describe',
    'lineno': 11,
    'col': 8,
    'return_lineno': 10,
    'return_col': 8,
}
```

The warning code and message strings live as module-level constants `UNREACHABLE_AFTER_RETURN_CODE` and `UNREACHABLE_AFTER_RETURN_MESSAGE` in `src/utils/optimizer.py` so they can be referenced consistently from tests and consumers.

### Branch Awareness (AST level)

The analyzer also treats an `if/else` statement whose `body` and `else_body` chains both provably end in a `return` as a terminator for its enclosing chain, so a sibling statement that follows it is flagged. This branch path is validated at the AST level — it is currently not exercised from source because the parser's INDENT/DEDENT injection does not yet fully support nested `if/else` blocks. The sample file (`samples/pass_dead_code_after_return.py`) therefore demonstrates only the direct post-return case; the branch-aware case is tested via direct AST construction in `src/utils/tests/test_optimizer.py`.

### Public Methods

- **`analyze(ast)`** — entry point. Resets internal state and returns the collected warnings list.
- **`walk_declaration(decl)`** — pushes/pops a named scope on `CLASS` / `FUNC` declarations and recurses into their bodies.
- **`scan_block(stmt)`** — walks a statement chain, tracking the current terminator and flagging subsequent siblings.
- **`descend(stmt)`** — recurses into a statement's inner bodies and inline declarations.
- **`flag_unreachable(stmt, terminator)`** — records an `UNREACHABLE_AFTER_RETURN` warning.
- **`block_always_returns(stmt)`** — helper used to decide whether an `if/else` trailing a chain terminates it.

### Example

```python
# Source (method body):
return 'label: ' + label
trailing = 'trailing assignment'   # flagged as UNREACHABLE_AFTER_RETURN
extra = 'another trailing assignment'  # flagged as UNREACHABLE_AFTER_RETURN
```

## Domain Events

The four utilities are driven by four sibling domain events. Each event takes an `-O` level parameter (`'O0'`, `'O1'`, or `'O2'`) and passes through unchanged at the inapplicable levels.

- **`FoldConstants`** — injects `ASTOptimizerService`; at `O1+` calls `fold(ast)`; at `O0` returns the AST unchanged.
- **`ReduceStrength`** — injects `ASTStrengthReducerService`; at `O1+` calls `reduce(ast)`; at `O0` returns the AST unchanged.
- **`AnalyzeReturns`** — injects `ReturnAnalyzerService`; at `O1+` calls `analyze(ast)` and returns the warning list; at `O0` returns an empty list. Does not mutate the AST.
- **`OptimizeCode`** — injects `OptimizerService`; at `O2+` calls `optimize(codegen)`; at `O0` and `O1` returns the codegen dict unchanged.

### Level Semantics

- `-O O0` — no optimization (pipelines still run the events, but each is a passthrough).
- `-O O1` — `FoldConstants`, `ReduceStrength`, and `AnalyzeReturns`. `OptimizeCode` is a passthrough.
- `-O O2` — `FoldConstants`, `ReduceStrength`, `AnalyzeReturns`, then (after codegen) `OptimizeCode` for YAML anchor/alias deduplication.

### Test Invocation

All three events are invoked via `DomainEvent.handle`:

```python
result = DomainEvent.handle(
    ReduceStrength,
    dependencies={'ast_strength_reducer_service': StrengthReducer()},
    ast=module_decl,
)
```

## Pipeline Integration

The AST-level events run in a fixed order immediately before IR generation, and the codegen-level event runs immediately after codegen. The full AST-optimization order is `AnalyzeReturns` → `FoldConstants` → `ReduceStrength` → `GenerateIR` → `GenerateCode` → `OptimizeCode`. `AnalyzeReturns` is placed before `FoldConstants` so warnings refer to original source positions, before any AST-mutating pass runs.

The `ir.event`, `compile.event`, and `compile.ast` features all wire this order. The `compile.keter` feature skips the AST stages because it loads an IR directly.

### config.yml attrs

```yaml
# Codegen-level optimizer (O2 YAML anchor/alias deduplication).
optimizer_service:
  module_path: src.utils.optimizer
  class_name: YamlAnchorOptimizer
optimize_code_event:
  module_path: src.events.optimizer
  class_name: OptimizeCode

# AST-level constant folder (O1+).
ast_optimizer_service:
  module_path: src.utils.optimizer
  class_name: ConstantFolder
fold_constants_event:
  module_path: src.events.optimizer
  class_name: FoldConstants

# AST-level strength reducer (O1+).
ast_strength_reducer_service:
  module_path: src.utils.optimizer
  class_name: StrengthReducer
reduce_strength_event:
  module_path: src.events.optimizer
  class_name: ReduceStrength

# AST-level return analyzer (O1+; diagnostic, non-mutating).
return_analyzer_service:
  module_path: src.utils.optimizer
  class_name: ReturnAnalyzer
analyze_returns_event:
  module_path: src.events.optimizer
  class_name: AnalyzeReturns
```

## Testing

Optimizer utility tests: `src/utils/tests/test_optimizer.py` (now covers all four classes)
Optimizer event tests: `src/events/tests/test_optimizer.py` (now covers all four events)

```bash
python -m pytest src/utils/tests/test_optimizer.py -v
python -m pytest src/events/tests/test_optimizer.py -v
```

## Related reading

- [ir.md](ir.md) — IRGenerator (downstream consumer of the folded and reduced AST; also emits `Shl(...)` / `Shr(...)` for the new `ExprKind.SHL` / `SHR` nodes)
- [codegen.md](codegen.md) — TiferetGenerator (produces the codegen dict that `YamlAnchorOptimizer` deduplicates)
- [parser.md](parser.md) — TiferetParser (parses `<<` and `>>` shift operators via the `shift_expr` grammar rule, allowing authors to write shifts directly in source)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
