# Optimizer — Optimization Phase for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)
**Course:** ECE 506 — Compiler Design
**University of Arizona**
**Date:** April 2026

**Author:** Andrew Shatz
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

This directory contains the deliverables for the **optimization** phase of the Tiferet compiler. The optimizer exposes three AST-level rewrite passes, one non-mutating AST-level diagnostic pass, and one post-codegen structural deduplication pass, each implemented as an injectable Tiferet `Service` and driven by a dedicated Tiferet `DomainEvent`. Together the passes provide the optimization coverage expected of a teaching compiler:

1. **Constant Folding** — compile-time evaluation of numeric arithmetic sub-expressions.
2. **Strength Reduction** — three textbook rewrites replacing expensive operators with cheaper equivalents.
3. **Dead Code Detection AND Elimination (Unreachable-After-Return)** — a diagnostic warning pass paired with a mutating elimination pass that physically removes statements following a `return` in the same scope.
4. **YAML Anchor / Alias Aliasing** — a post-codegen dedup pass that turns repeated `params` / `returns` lists into YAML `&anchor` / `*alias` references.

Like the Code Generator deliverable, this folder contains only **documentation and reference sample outputs**. The implementation itself lives in the production source tree under [`src/utils/optimizer.py`](../src/utils/optimizer.py), [`src/events/optimizer.py`](../src/events/optimizer.py), and [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py), and is wired into the pipeline by [`config.yml`](../config.yml).

## 2. Deliverable Checklist

| # | Requirement | Where it lives in the app |
|---|---|---|
| 1 | Constant folding on the AST | `ConstantFolder` in `src/utils/optimizer.py`; driven by `FoldConstants` in `src/events/optimizer.py` |
| 2 | Three types of strength reduction | `StrengthReducer` in `src/utils/optimizer.py`; driven by `ReduceStrength` in `src/events/optimizer.py` |
| 3a | Dead code detection (unreachable-after-return) | `ReturnAnalyzer` in `src/utils/optimizer.py`; driven by `AnalyzeReturns` in `src/events/optimizer.py` |
| 3b | Dead code elimination (mutates the AST) | `DeadCodeEliminator` in `src/utils/optimizer.py`; driven by `EliminateDeadCode` in `src/events/optimizer.py` |
| 4 | YAML anchor/alias deduplication | `YamlAnchorOptimizer` in `src/utils/optimizer.py`; driven by `OptimizeCode` in `src/events/optimizer.py` |
| 5 | Wiring into the compilation pipeline | `config.yml` — `compile event`, `compile keter`, `compile ast`, and `ir event` feature chains |
| 6 | Tests and CLI examples reproducing every effect | `src/utils/tests/test_optimizer.py` (41 tests), `src/events/tests/test_optimizer.py` (20 tests), plus the sample round-trips in §10 |
| 7 | Document this module | This README |

## 3. Pipeline Overview

All five optimizer components are wired into the three `compile` sub-features (`event`, `keter`, `ast`) and into the `ir event` feature in [`config.yml`](../config.yml). The passes interleave between the existing stages as follows:

```
Source File (.py)
    │
    ▼  PerformLexicalAnalysis          → tokens
    ▼  PerformSyntacticAnalysis        → ast (DeclarationAggregate)
    ▼  PerformSemanticAnalysis         → symbol table + resolution
    ▼  PerformTypeCheck                → semantic errors
┌────────────────────────┐
│ AnalyzeReturns           │  ReturnAnalyzer.analyze(ast)            (diagnostic-only)
└────────────────────────┘
┌────────────────────────┐
│ EliminateDeadCode        │  DeadCodeEliminator.eliminate(ast)      (mutates AST)
└────────────────────────┘
┌────────────────────────┐
│ FoldConstants            │  ConstantFolder.fold(ast)
└────────────────────────┘
┌────────────────────────┐
│ ReduceStrength           │  StrengthReducer.reduce(ast)
└────────────────────────┘
    ▼  GenerateIR                      → ir (IREventGroup)
    ▼  GenerateCode                    → codegen dict
┌────────────────────────┐
│ OptimizeCode             │  YamlAnchorOptimizer.optimize(codegen)  (O2 only)
└────────────────────────┘
    ▼  EmitResult                      → output.yaml / output.json
```

The four AST-level passes (`AnalyzeReturns`, `EliminateDeadCode`, `FoldConstants`, `ReduceStrength`) run at **-O O1** and above. The post-codegen `OptimizeCode` pass runs at **-O O2** and above. At `-O O0` every optimizer pass is a pure pass-through, so the `-O` flag alone selects which optimizations are active.

`EliminateDeadCode` runs immediately after `AnalyzeReturns` and before `FoldConstants` so that subsequent stages (folding, strength reduction, IR generation, codegen) operate on an AST whose unreachable branches have already been physically removed.

### 3.1 Optimization level summary

| Level | AnalyzeReturns | EliminateDeadCode | FoldConstants | ReduceStrength | OptimizeCode |
|-------|-----------------|---------------------|---------------|-----------------|---------------|
| `-O O0` | passthrough (no warnings emitted) | passthrough (dead code retained in output) | passthrough | passthrough | passthrough |
| `-O O1` | active (warnings emitted) | active (dead code removed from AST) | active | active | passthrough |
| `-O O2` | active | active | active | active | active (YAML anchors) |

### 3.2 Feature chains that include optimization

- `ir event` — runs all four AST-level passes (analysis + elimination + fold + reduce) before IR generation.
- `compile event` — runs all four AST-level passes, then generates code, then optionally applies YAML anchor dedup.
- `compile keter` — skips all AST-level passes (starts from IR) and optionally applies YAML anchor dedup.
- `compile ast` — starts from a JSON AST, then runs semantic/type-check, all four AST-level passes, IR, codegen, and optional YAML anchor dedup.

## 4. Folder Contents

| File | Purpose |
|------|---------|
| `samples/pass_constant_folding_event.yaml` | `compile event -O O1` output for `samples/pass_constant_folding_event.py` — demonstrates AST-level constant folding. |
| `samples/pass_constant_folding_event.O0.yaml` | `compile event -O O0` baseline of the same source — the folded arithmetic appears here **unfolded**. |
| `samples/pass_strength_reduction_event.yaml` | `compile event -O O1` output for `samples/pass_strength_reduction_event.py` — demonstrates all three strength-reduction patterns. |
| `samples/pass_strength_reduction_event.O0.yaml` | `compile event -O O0` baseline — `Mul`/`Div`/`Exp` remain in their original, un-reduced form. |
| `samples/pass_dead_code_after_return.yaml` | `compile event -O O1` output for `samples/pass_dead_code_after_return.py` — emits the three `UNREACHABLE_AFTER_RETURN` warnings on stderr **and** the `EliminateDeadCode` pass physically removes the unreachable snippets, so the YAML body contains only the reachable `Return(...)` statements. |
| `samples/pass_dead_code_after_return.O0.yaml` | `compile event -O O0` baseline — no analysis runs, no warnings are emitted, and the unreachable `Assign(...)` statements still appear in the output. The diff between this file and the O1 file above is the proof that elimination ran. |
| `samples/pass_multiple_operator_events.yaml` | `compile event -O O2` output — the canonical demonstration of YAML anchor/alias deduplication (`&id001`/`*id001`). |
| `samples/pass_minimal_event.yaml` | `compile event -O O2` output — no duplicate structures, so the `vars:` section is omitted entirely (demonstrates the no-op path). |
| `samples/pass_minimal_injection_event.yaml` | `compile event -O O2` output — small sample with a single event and injections; no dedup triggered. |
| `samples/pass_helper_method_event.yaml` | `compile event -O O2` output — helper method path; no duplicates across `execute` and `methods` to dedup. |
| `samples/pass_imports_only.yaml` | `compile event -O O2` output — imports-only module; no events to analyze. |

No new source scripts are added here. All implementation is referenced from [`src/`](../src).

## 5. Deliverable 1 — Constant Folding on the AST

### 5.1 Overview

Constant folding evaluates constant numeric sub-expressions at compile time, replacing subtrees like `3 * 5 * penalty` with `15 * penalty`. The pass shrinks the IR / codegen output and gives downstream consumers fewer nodes to walk.

### 5.2 Implementation

- **Service interface:** `ASTOptimizerService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `ConstantFolder` in [`src/utils/optimizer.py`](../src/utils/optimizer.py) — extends `ASTTraversal` (from [`src/utils/settings.py`](../src/utils/settings.py)) to inherit the shared declaration and statement traversal skeleton.
- **Domain event:** `FoldConstants` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `ast_optimizer_service` (concrete `ConstantFolder`) + `fold_constants_event` (domain event) in [`config.yml`](../config.yml).

### 5.3 Algorithm

`ConstantFolder.fold(ast)` calls `traverse_declaration(ast)` (inherited from `ASTTraversal`), which visits every declaration and statement node and calls `transform_expression` on each expression field. `ConstantFolder.transform_expression` delegates to `fold_expression`, which performs a **post-order walk** across the expression tree:

- Recursively folds children of each `Expression` node.
- Attempts to fold the current node only when its `kind` is in `ARITHMETIC_OPS = {ADD, SUB, MUL, DIV, MOD, EXP}` **and** both child expressions return `True` from `is_numeric(expr)` (INT_VAL, NUM_VAL, or STR_VAL whose value parses as a number — the latter accommodates the parser's habit of storing raw integer tokens as STR_VAL).
- Evaluates the operator via Python float arithmetic in `evaluate(expr)`, then promotes whole-number results to INT_VAL / STR_VAL (matching the source kinds) and non-whole results to NUM_VAL. Division always returns NUM_VAL.
- Variable references, calls, comparisons, mixed constant/variable expressions, and non-arithmetic operators are left untouched.

### 5.4 Source / output example

Source [`samples/pass_constant_folding_event.py`](../samples/pass_constant_folding_event.py):

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/samples/pass_constant_folding_event.py start=29
# Subtract the scaled penalty: 3 * 5 is a constant sub-expression.
adjusted = base_score - 3 * 5 * penalty

# Return the score with a fixed bonus: 4 * 5 is a constant sub-expression.
return adjusted + 4 * 5
```

O0 (unfolded) form in [`samples/pass_constant_folding_event.O0.yaml`](samples/pass_constant_folding_event.O0.yaml):

```yaml path=null start=null
stmt:
- Assign(adjusted, Sub(base_score, Mul(Mul(3, 5), penalty)))
...
stmt:
- Return(Add(adjusted, Mul(4, 5)))
```

O1 (folded) form in [`samples/pass_constant_folding_event.yaml`](samples/pass_constant_folding_event.yaml):

```yaml path=null start=null
stmt:
- Assign(adjusted, Sub(base_score, Mul(15, penalty)))
...
stmt:
- Return(Add(adjusted, 20))
```

The `Mul(3, 5)` subtree became `15`; the `Mul(4, 5)` subtree became `20`.

## 6. Deliverable 2 — Three Types of Strength Reduction

### 6.1 Overview

Strength reduction replaces expensive arithmetic with cheaper equivalents. The Tiferet optimizer recognizes the three textbook patterns that map cleanly onto shifts and self-multiplication.

### 6.2 Implementation

- **Service interface:** `ASTStrengthReducerService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `StrengthReducer` in [`src/utils/optimizer.py`](../src/utils/optimizer.py) — extends `ASTTraversal` (from [`src/utils/settings.py`](../src/utils/settings.py)) to inherit the shared declaration and statement traversal skeleton.
- **Domain event:** `ReduceStrength` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `ast_strength_reducer_service` + `reduce_strength_event` in [`config.yml`](../config.yml).

### 6.3 Supported patterns

| # | Pattern | Rewrite | Commutative? | Implementation method |
|---|---------|---------|---------------|-----------------------|
| 1 | `x * 2**k` (or `2**k * x`) | `x << k` | Yes — either operand may be the literal | `try_reduce_mul` |
| 2 | `x / 2**k` | `x >> k` | No — only the divisor may be the literal | `try_reduce_div` |
| 3 | `x ** 2` | `x * x` (left operand is deep-copied so the two MUL children are distinct nodes) | N/A — only the exact literal 2 triggers | `try_reduce_exp` |

Power-of-two detection is centralized in `is_power_of_two_literal(expr)`, which accepts INT_VAL, NUM_VAL, and numeric STR_VAL, and returns the exponent `k` (or `None`). `is_literal_two(expr)` is a thin wrapper used by the exponentiation case.

### 6.4 Source / output example

Source [`samples/pass_strength_reduction_event.py`](../samples/pass_strength_reduction_event.py):

```python path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/samples/pass_strength_reduction_event.py start=28
# Multiplication by a power of two: `value * 8` reduces to `value << 3`.
scaled = value * 8

# Division by a power of two: `value / 4` reduces to `value >> 2`.
halved = value / 4

# Exponentiation by two: `value ** 2` reduces to `value * value`.
squared = value ** 2
```

O0 (un-reduced) form in [`samples/pass_strength_reduction_event.O0.yaml`](samples/pass_strength_reduction_event.O0.yaml):

```yaml path=null start=null
- Assign(scaled, Mul(value, 8))
- Assign(halved, Div(value, 4))
- Assign(squared, Exp(value, 2))
```

O1 (reduced) form in [`samples/pass_strength_reduction_event.yaml`](samples/pass_strength_reduction_event.yaml):

```yaml path=null start=null
- Assign(scaled, Shl(value, 3))
- Assign(halved, Shr(value, 2))
- Assign(squared, Mul(value, value))
```

All three patterns trigger: `Mul → Shl`, `Div → Shr`, `Exp → Mul(x, x)`.

### 6.5 Ordering with constant folding

`ReduceStrength` runs **after** `FoldConstants` in every feature chain. This ordering matters because constant folding reduces patterns like `x * (2 ** 3)` into `x * 8` *before* the strength reducer has to analyze the operand. The reducer itself intentionally does not attempt to fold `2 ** 3` on the fly; constant folding is treated as a prerequisite pass.

## 7. Deliverable 3 — Dead Code Detection AND Elimination (Unreachable-After-Return)

### 7.1 Overview

The Tiferet optimizer satisfies the dead-code requirement with two cooperating passes that share a single definition of "terminator":

- **Detection** — `ReturnAnalyzer` walks the AST without mutating it and collects descriptive `UNREACHABLE_AFTER_RETURN` warnings with file positions and a dotted scope path. Warnings are printed on stderr by `OutputPrinter` and surfaced via the `dead_code_warnings` pipeline data key.
- **Elimination** — `DeadCodeEliminator` (a subclass of `ReturnAnalyzer`) walks the same AST a second time and physically detaches every statement that follows a terminator within the same scope, so downstream stages (constant folding, strength reduction, IR generation, codegen) never see the unreachable code.

Both passes recognize the same three terminator patterns (direct `return`, `if/else` whose both branches always return, and a `snippet` / `block` whose body always returns), so detection and elimination always agree on what is dead.

### 7.2 Implementation

#### Detection
- **Service interface:** `ReturnAnalyzerService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `ReturnAnalyzer` in [`src/utils/optimizer.py`](../src/utils/optimizer.py).
- **Domain event:** `AnalyzeReturns` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `return_analyzer_service` + `analyze_returns_event` in [`config.yml`](../config.yml).
- **Constants:** `UNREACHABLE_AFTER_RETURN_CODE` and `UNREACHABLE_AFTER_RETURN_MESSAGE` in [`src/utils/optimizer.py`](../src/utils/optimizer.py).

#### Elimination
- **Service interface:** `DeadCodeEliminatorService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `DeadCodeEliminator(ReturnAnalyzer, DeadCodeEliminatorService)` in [`src/utils/optimizer.py`](../src/utils/optimizer.py) — inherits `iter_effective_statements` and `block_always_returns` from `ReturnAnalyzer` so the two passes share their definition of "terminator".
- **Domain event:** `EliminateDeadCode` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `dead_code_eliminator_service` + `eliminate_dead_code_event` in [`config.yml`](../config.yml).

### 7.3 Algorithm

#### Detection (`ReturnAnalyzer.analyze`)
`ReturnAnalyzer.analyze(ast)` walks the declaration tree with a scope stack that is pushed on `CLASS` / `FUNC` declarations and popped on the way out, so every warning carries a dotted `scope_path` (e.g. `module.ClassifyScore.describe`). Within each statement chain:

- `SNIPPET` / `BLOCK` container statements are flattened transparently via `iter_effective_statements`, so the parser's habit of grouping consecutive source lines into a snippet does not hide a terminator from a sibling snippet.
- `COMMENT` statements are ignored for control-flow purposes — they are neither terminators nor reportable as unreachable code.
- A direct `RETURN` statement becomes the terminator for the remainder of the chain.
- An `IF_ELSE` statement whose `body` **and** `else_body` both always return (determined recursively by `block_always_returns`) also becomes a terminator.
- Every statement encountered after the terminator is flagged as `UNREACHABLE_AFTER_RETURN`, preserving its `lineno` / `col` and the terminator's position (as `return_lineno` / `return_col`).

#### Elimination (`DeadCodeEliminator.eliminate`)
`DeadCodeEliminator.eliminate(ast)` walks the declaration tree and, for every statement chain it encounters (method body, if/else branch, snippet body, etc.), iterates through the chain until it meets the first **chain terminator**, then sets that statement's `.next` to `None` to detach the rest of the chain. The chain terminator is determined by `is_chain_terminator`:

- A direct `RETURN` always terminates the chain.
- An `IF_ELSE` whose `body` and `else_body` both always return terminates the chain (so any sibling statement after the if/else is detached).
- A `SNIPPET` / `BLOCK` whose body always returns terminates the parent chain. This is what handles the common parser output where the source lines `return X` and `dead = ...` end up in two **sibling** snippet statements; the first snippet terminates and the second is dropped.

Before checking for a terminator, the eliminator recurses into nested structures (`body`, `else_body`, inline `decl`) so dead code inside `if`/`else` arms, loop bodies, and inline function declarations is removed independently of the enclosing chain. Terminators inside nested scopes do **not** propagate out to the parent chain, so scope boundaries are respected exactly the way `ReturnAnalyzer` does.

Each warning dict has the shape:

```json path=null start=null
{
  "warning_code": "UNREACHABLE_AFTER_RETURN",
  "message": "Statement is unreachable (follows a return statement)",
  "scope_path": "module.ClassifyScore.describe",
  "lineno": 55,
  "col": 8,
  "return_lineno": 51,
  "return_col": 8
}
```

### 7.4 Source / console example

Source [`samples/pass_dead_code_after_return.py`](../samples/pass_dead_code_after_return.py) has one unreachable assignment in `execute` and two unreachable assignments in `describe`. Running the `compile event` pipeline at `-O O1` emits three warnings to the console **and** physically removes the unreachable snippets from the codegen output:

```bash path=null start=null
$ python compiler.py compile event samples/pass_dead_code_after_return.py -O O1 -o out.yaml
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.execute (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 31, col 8]
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 51, col 8]
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 51, col 8]
```

At `-O O0` the same command emits **no** warnings because both `AnalyzeReturns.execute` and `EliminateDeadCode.execute` short-circuit, and the unreachable assignments survive into the YAML output. Compare:

- [`samples/pass_dead_code_after_return.O0.yaml`](samples/pass_dead_code_after_return.O0.yaml) — baseline; the `Assign(note, 'never reached')`, `Assign(trailing, 'trailing assignment')`, and `Assign(extra, 'another trailing assignment')` snippets are still present.
- [`samples/pass_dead_code_after_return.yaml`](samples/pass_dead_code_after_return.yaml) — O1 output; the three warnings appear on the console and the three unreachable snippets have been physically removed by `EliminateDeadCode`.

The O0 → O1 diff is the proof that elimination ran. For example, in `execute`:

```yaml path=null start=null
# O0 (baseline)
execute:
  ...
  snpt:
  - coms: [Return the label immediately.]
    stmt: [Return('score recorded')]
  - coms: [This statement is unreachable because it follows a return, ...]
    stmt: [Assign(note, 'never reached')]   # <-- unreachable, retained
```

```yaml path=null start=null
# O1 (after EliminateDeadCode)
execute:
  ...
  snpt:
  - coms: [Return the label immediately.]
    stmt: [Return('score recorded')]
  # the unreachable snippet is gone
```

## 8. Deliverable 4 — YAML Aliasing / Anchoring

### 8.1 Overview

The `YamlAnchorOptimizer` runs after `GenerateCode` and deduplicates repeated `params` and `returns` lists across events. Because PyYAML automatically emits `&anchor` / `*alias` references when the same Python object appears more than once in the serialized tree, the optimizer's job is simply to make the object-identity match for structurally-identical lists.

### 8.2 Implementation

- **Service interface:** `OptimizerService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `YamlAnchorOptimizer` in [`src/utils/optimizer.py`](../src/utils/optimizer.py).
- **Domain event:** `OptimizeCode` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `optimizer_service` + `optimize_code_event` in [`config.yml`](../config.yml).

### 8.3 Algorithm

`YamlAnchorOptimizer.optimize(codegen)` performs three steps:

1. **Collect** every `params` and `returns` list across every event's `execute` section and `methods` map, tagging each with `(kind, tuple(values))` as a fingerprint and recording the `(parent_dict, key)` location.
2. **Share** — for every fingerprint with more than one occurrence, build a single canonical `list(values)` and patch every recorded location to point at it. Single-occurrence lists are left alone.
3. **Emit** — if any canonical lists were created, return a new dict whose first key is `vars:` (the list of canonical lists) followed by the original `evt_grp`. PyYAML serializes the first occurrence as `&id001`, `&id002`, etc., and every subsequent reference as `*id001`, `*id002`.

When no duplicates exist the optimizer short-circuits and returns the original dict unchanged (no `vars:` section is emitted).

### 8.4 Source / output example

Source [`samples/pass_multiple_operator_events.py`](../samples/pass_multiple_operator_events.py) defines six events (`Add`, `Subtract`, `Multiply`, `Divide`, `Modulus`, `Exponentiate`) that all share the same `(a: int, b: int)` parameter list. Four of them also share the same `int` return type; the remaining two share `float`. The resulting dedup collapses the codegen output into three anchored lists plus six alias references:

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/Optimizer/samples/pass_multiple_operator_events.yaml start=1
vars:
- &id001
  - 'a:int:true::'
  - 'b:int:true::'
- &id002
  - 'int:'
- &id003
  - 'float:'
evt_grp:
  ...
  evts:
    add:
      ...
      execute:
        params: *id001
        returns: *id002
    ...
    divide:
      ...
      execute:
        params: *id001
        returns: *id003
```

### 8.5 No-op examples

The other four reference outputs in `samples/` demonstrate the short-circuit path — every one is the **O2** output for its source, but none contains duplicate params/returns, so none has a `vars:` section:

- [`samples/pass_imports_only.yaml`](samples/pass_imports_only.yaml) — imports-only (no events at all).
- [`samples/pass_minimal_event.yaml`](samples/pass_minimal_event.yaml) — single event with a single execute method.
- [`samples/pass_minimal_injection_event.yaml`](samples/pass_minimal_injection_event.yaml) — single event with injections.
- [`samples/pass_helper_method_event.yaml`](samples/pass_helper_method_event.yaml) — one event with a helper `methods` section whose signature differs from `execute`.

## 9. Deliverable 5 — Wiring Into the Compilation Event Workflow

### 9.1 Attribute declarations

The five optimization services and five driving events are declared as Tiferet container attributes in the top `attrs:` block of [`config.yml`](../config.yml):

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/config.yml start=32
optimizer_service:
  module_path: src.utils.optimizer
  class_name: YamlAnchorOptimizer
optimize_code_event:
  module_path: src.events.optimizer
  class_name: OptimizeCode
...
ast_optimizer_service:
  module_path: src.utils.optimizer
  class_name: ConstantFolder
fold_constants_event:
  module_path: src.events.optimizer
  class_name: FoldConstants
ast_strength_reducer_service:
  module_path: src.utils.optimizer
  class_name: StrengthReducer
reduce_strength_event:
  module_path: src.events.optimizer
  class_name: ReduceStrength
return_analyzer_service:
  module_path: src.utils.optimizer
  class_name: ReturnAnalyzer
analyze_returns_event:
  module_path: src.events.optimizer
  class_name: AnalyzeReturns
dead_code_eliminator_service:
  module_path: src.utils.optimizer
  class_name: DeadCodeEliminator
eliminate_dead_code_event:
  module_path: src.events.optimizer
  class_name: EliminateDeadCode
```

### 9.2 Feature chain

The `compile event` feature chains the optimization stages between type-checking and IR generation (for AST passes) and between codegen and emit (for the YAML anchor pass):

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/config.yml start=151
compile:
  event:
    ...
    commands:
      ...
      - attribute_id: perform_type_check_event
        name: Perform type checking against symbol table
        data_key: semantic_errors
      - attribute_id: analyze_returns_event
        name: Analyze unreachable code after return
        data_key: dead_code_warnings
      - attribute_id: eliminate_dead_code_event
        name: Eliminate unreachable post-return statements from AST
        data_key: ast
      - attribute_id: fold_constants_event
        name: Fold constant arithmetic sub-expressions in AST
        data_key: ast
      - attribute_id: reduce_strength_event
        name: Apply strength reduction to AST arithmetic
        data_key: ast
      - attribute_id: generate_ir_event
        ...
        data_key: ir
      - attribute_id: generate_code_event
        ...
        data_key: codegen
      - attribute_id: optimize_code_event
        name: Optimize codegen output
        params:
          optimizer_service: optimizer_service
        data_key: codegen
      - attribute_id: emit_result_event
        name: Assemble and emit result
```

The `ir event`, `compile keter`, and `compile ast` features are wired identically for the stages they include (see §3.2).

### 9.3 CLI `-O` flag

All three compile sub-commands accept a single `-O` flag declared in the `cli:` block of [`config.yml`](../config.yml):

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/config.yml start=465
- name_or_flags:
    - -O
  default: O0
  description: "Optimization level: O0 (none, default), O1 (dead-code elimination + AST constant folding + strength reduction), O2 (everything in O1 plus YAML anchor/alias deduplication)."
```

Each driving event normalizes the flag value (`.strip().upper()`) and branches internally — `AnalyzeReturns` / `EliminateDeadCode` / `FoldConstants` / `ReduceStrength` pass through at `O0` and activate at `O1+`, `OptimizeCode` passes through at `O0`/`O1` and activates at `O2+`.

## 10. Deliverable 6 — Tests and CLI Examples

### 10.1 Unit tests

Total: **61 tests** across two modules.

| File | Count | Coverage |
|------|-------|----------|
| [`src/utils/tests/test_optimizer.py`](../src/utils/tests/test_optimizer.py) | 41 | Unit tests for `YamlAnchorOptimizer` (params/returns dedup, vars omitted when no duplicates), `ConstantFolder` (simple add, multiply, divide → NUM_VAL, nested sub-expressions), `StrengthReducer` (all three patterns plus non-matching operands), `ReturnAnalyzer` (direct-return, if/else-always-returns, comment-only chains, scope-stack correctness), and `DeadCodeEliminator` (no-op when no terminator, single and multiple post-return drops, sibling-snippet drop matching the parser shape, in-snippet truncation, if/else terminator drop, and nested-scope isolation). |
| [`src/events/tests/test_optimizer.py`](../src/events/tests/test_optimizer.py) | 20 | Domain event tests for `FoldConstants` / `ReduceStrength` / `AnalyzeReturns` / `EliminateDeadCode` / `OptimizeCode` — delegation to injected service, `O0` pass-through behavior, real-service integration with a parser-produced AST, and `parameters_required` validation. |

Run them with:

```bash path=null start=null
source .venv/bin/activate
python -m pytest src/utils/tests/test_optimizer.py src/events/tests/test_optimizer.py -v
```

### 10.2 Sample round-trips

Every file in `Optimizer/samples/` can be regenerated by running the live pipeline on the paired source in [`samples/`](../samples):

```bash path=null start=null
source .venv/bin/activate

# Constant folding (O1) and its unfolded O0 baseline.
python compiler.py compile event samples/pass_constant_folding_event.py -O O1 \
  -o /tmp/pass_constant_folding_event.yaml
diff -u Optimizer/samples/pass_constant_folding_event.yaml \
        /tmp/pass_constant_folding_event.yaml

python compiler.py compile event samples/pass_constant_folding_event.py -O O0 \
  -o /tmp/pass_constant_folding_event.O0.yaml
diff -u Optimizer/samples/pass_constant_folding_event.O0.yaml \
        /tmp/pass_constant_folding_event.O0.yaml

# Strength reduction (O1) and its un-reduced O0 baseline.
python compiler.py compile event samples/pass_strength_reduction_event.py -O O1 \
  -o /tmp/pass_strength_reduction_event.yaml
diff -u Optimizer/samples/pass_strength_reduction_event.yaml \
        /tmp/pass_strength_reduction_event.yaml

python compiler.py compile event samples/pass_strength_reduction_event.py -O O0 \
  -o /tmp/pass_strength_reduction_event.O0.yaml
diff -u Optimizer/samples/pass_strength_reduction_event.O0.yaml \
        /tmp/pass_strength_reduction_event.O0.yaml

# Dead-code detection + elimination at O1 (three warnings on stderr,
# unreachable snippets removed) versus the O0 baseline (no warnings,
# unreachable snippets retained).
python compiler.py compile event samples/pass_dead_code_after_return.py -O O1 \
  -o /tmp/pass_dead_code_after_return.yaml
diff -u Optimizer/samples/pass_dead_code_after_return.yaml \
        /tmp/pass_dead_code_after_return.yaml

python compiler.py compile event samples/pass_dead_code_after_return.py -O O0 \
  -o /tmp/pass_dead_code_after_return.O0.yaml
diff -u Optimizer/samples/pass_dead_code_after_return.O0.yaml \
        /tmp/pass_dead_code_after_return.O0.yaml

# A diff between the two reference files shows the elimination effect:
diff -u Optimizer/samples/pass_dead_code_after_return.O0.yaml \
        Optimizer/samples/pass_dead_code_after_return.yaml

# YAML anchor dedup (O2) — anchored form matches the reference.
python compiler.py compile event samples/pass_multiple_operator_events.py -O O2 \
  -o /tmp/pass_multiple_operator_events.yaml
diff -u Optimizer/samples/pass_multiple_operator_events.yaml \
        /tmp/pass_multiple_operator_events.yaml
```

Every `diff` should print nothing when the optimizer is working correctly.

### 10.3 Reproducing the warning output

The `UNREACHABLE_AFTER_RETURN` warnings are printed to **stderr** (via `OutputPrinter.print_dead_code_warnings` inside `EmitResult`) rather than written to the YAML file, so the quickest way to see them is to omit `-o` or redirect stderr:

```bash path=null start=null
source .venv/bin/activate

# Print warnings to the console alongside the codegen dict.
python compiler.py compile event samples/pass_dead_code_after_return.py -O O1

# Capture just the warnings.
python compiler.py compile event samples/pass_dead_code_after_return.py -O O1 \
  -o /tmp/dead.yaml 2>&1 | grep UNREACHABLE_AFTER_RETURN
```

Expected output (three warnings, one per unreachable statement):

```text path=null start=null
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.execute ...
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe ...
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe ...
```

### 10.4 CLI reference

```bash path=null start=null
# No optimization (default).
python compiler.py compile event <source>.py -O O0 -o out.yaml

# AST-level constant folding + strength reduction + dead-code warnings.
python compiler.py compile event <source>.py -O O1 -o out.yaml

# Everything above plus YAML anchor/alias deduplication.
python compiler.py compile event <source>.py -O O2 -o out.yaml

# Re-compile from a pre-generated keter IR (only YAML anchor dedup applies).
python compiler.py compile keter <file>.keter -O O2 -o out.yaml

# Re-compile from a pre-generated JSON AST (all five passes apply).
python compiler.py compile ast <file>.json -O O2 -o out.yaml

# Run the IR feature (includes all four AST-level passes, skips codegen).
python compiler.py ir event <source>.py -O O1 -o out.keter
```

## 11. Summary

The Tiferet optimizer is implemented as five cleanly-separated Tiferet domain events, each backed by a concrete utility class that implements an injectable service interface:

- **`FoldConstants` → `ConstantFolder` → `ASTOptimizerService` + `ASTTraversal`** — compile-time arithmetic on numeric literals. Inherits the shared declaration/statement traversal from `ASTTraversal`; overrides `transform_expression` to route into `fold_expression`.
- **`ReduceStrength` → `StrengthReducer` → `ASTStrengthReducerService` + `ASTTraversal`** — three textbook strength-reduction rewrites (`* 2**k`, `/ 2**k`, `** 2`). Inherits the shared traversal from `ASTTraversal`; overrides `transform_expression` to route into `reduce_expression`.
- **`AnalyzeReturns` → `ReturnAnalyzer` → `ReturnAnalyzerService`** — non-mutating unreachable-code detection that emits structured warnings.
- **`EliminateDeadCode` → `DeadCodeEliminator` → `DeadCodeEliminatorService`** — mutating unreachable-code elimination that detaches statements following a terminator. Subclasses `ReturnAnalyzer` so detection and elimination share their definition of "terminator".
- **`OptimizeCode` → `YamlAnchorOptimizer` → `OptimizerService`** — post-codegen YAML anchor/alias deduplication.

`ASTTraversal` (defined in `src/utils/settings.py`) provides the shared `traverse_declaration` and `traverse_statement` skeleton consumed by both `ConstantFolder` and `StrengthReducer`, eliminating duplicated traversal code between the two passes.

The five passes are wired into [`config.yml`](../config.yml) and executed from [`compiler.py`](../compiler.py) via the standard `-O` flag. This folder supplies only the **documentation** and the **reference YAML outputs** — satisfying the deliverable while keeping the single source of truth in the production code under [`src/`](../src).
