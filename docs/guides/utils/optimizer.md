# Utilities – YamlAnchorOptimizer, ConstantFolder, and StrengthReducer

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

The optimizer module provides three concrete utilities that together implement the compiler's optimization levels:

- **`YamlAnchorOptimizer`** — codegen-level pass that deduplicates repeated `params` / `returns` lists so PyYAML can emit anchors and aliases automatically. Runs at `-O O2`.
- **`ConstantFolder`** — AST-level pass that folds binary arithmetic expressions with two numeric-literal operands into a single literal. Runs at `-O O1` and `-O O2`.
- **`StrengthReducer`** — AST-level pass that rewrites a small set of expensive arithmetic operations into cheaper equivalents (shifts and self-multiplication). Runs at `-O O1` and `-O O2` immediately after `ConstantFolder`.

Each utility implements a dedicated service interface and is driven by a single-purpose domain event, keeping each optimization independently injectable, testable, and wirable.

**Files:**
- `src/utils/optimizer.py` — `YamlAnchorOptimizer`, `ConstantFolder`, `StrengthReducer`
- `src/interfaces/optimizer.py` — `OptimizerService`, `ASTOptimizerService`, `ASTStrengthReducerService` abstract interfaces
- `src/events/optimizer.py` — `FoldConstants`, `ReduceStrength`, `OptimizeCode` domain events

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
- **`fold(ast)`** — entry point. Walks the entire declaration chain and returns the (mutated) root.
- **`fold_declaration(decl)`** — recurses into `decl.value` and `decl.code`, then into `decl.next`.
- **`fold_statement(stmt)`** — recurses into inline declarations, `expr`, `init_expr`, `body`, `else_body`, and `next`.
- **`fold_expression(expr)`** — post-order: folds left and right children first, then attempts to collapse the current node.
- **`evaluate(expr)`** — computes the result of a binary arithmetic node with two numeric-literal children.

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
- **`reduce(ast)`** — entry point. Walks the entire declaration chain and returns the (mutated) root.
- **`reduce_declaration(decl)`** / **`reduce_statement(stmt)`** / **`reduce_expression(expr)`** — mirror the traversal structure of `ConstantFolder.fold_*`.
- **`try_reduce_mul(expr)`** / **`try_reduce_div(expr)`** / **`try_reduce_exp(expr)`** — per-pattern rewrite helpers.

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

## Domain Events

The three utilities are driven by three sibling domain events. Each event takes an `-O` level parameter (`'O0'`, `'O1'`, or `'O2'`) and passes through unchanged at the inapplicable levels.

- **`FoldConstants`** — injects `ASTOptimizerService`; at `O1+` calls `fold(ast)`; at `O0` returns the AST unchanged.
- **`ReduceStrength`** — injects `ASTStrengthReducerService`; at `O1+` calls `reduce(ast)`; at `O0` returns the AST unchanged.
- **`OptimizeCode`** — injects `OptimizerService`; at `O2+` calls `optimize(codegen)`; at `O0` and `O1` returns the codegen dict unchanged.

### Level Semantics

- `-O O0` — no optimization (pipelines still run the three events, but each is a passthrough).
- `-O O1` — `FoldConstants` then `ReduceStrength`. `OptimizeCode` is a passthrough.
- `-O O2` — `FoldConstants`, then `ReduceStrength`, then (after codegen) `OptimizeCode` for YAML anchor/alias deduplication.

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

The two AST-level events run in a fixed order immediately before IR generation, and the codegen-level event runs immediately after codegen. The full AST-optimization order is `FoldConstants` → `ReduceStrength` → `GenerateIR` → `GenerateCode` → `OptimizeCode`.

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
```

## Testing

Optimizer utility tests: `src/utils/tests/test_optimizer.py` (26 tests covering all three classes)
Optimizer event tests: `src/events/tests/test_optimizer.py` (10 tests covering all three events)

```bash
python -m pytest src/utils/tests/test_optimizer.py -v
python -m pytest src/events/tests/test_optimizer.py -v
```

## Related reading

- [ir.md](ir.md) — IRGenerator (downstream consumer of the folded and reduced AST; also emits `Shl(...)` / `Shr(...)` for the new `ExprKind.SHL` / `SHR` nodes)
- [codegen.md](codegen.md) — TiferetGenerator (produces the codegen dict that `YamlAnchorOptimizer` deduplicates)
- [parser.md](parser.md) — TiferetParser (parses `<<` and `>>` shift operators via the `shift_expr` grammar rule, allowing authors to write shifts directly in source)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
