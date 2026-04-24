# Optimizer — Optimization Phase for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)
**Course:** ECE 506 — Compiler Design
**University of Arizona**
**Date:** April 2026

**Author:** Andrew Shatz
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

This directory contains the deliverables for the **optimization** phase of the Tiferet compiler. The optimizer exposes two AST-level rewrite passes, one non-mutating AST-level diagnostic pass, and one post-codegen structural deduplication pass, each implemented as an injectable Tiferet `Service` and driven by a dedicated Tiferet `DomainEvent`. Together the four passes provide the optimization coverage expected of a teaching compiler:

1. **Constant Folding** — compile-time evaluation of numeric arithmetic sub-expressions.
2. **Strength Reduction** — three textbook rewrites replacing expensive operators with cheaper equivalents.
3. **Dead Code Detection (Unreachable-After-Return)** — a diagnostic-only warning pass that flags statements following a `return` in the same scope.
4. **YAML Anchor / Alias Aliasing** — a post-codegen dedup pass that turns repeated `params` / `returns` lists into YAML `&anchor` / `*alias` references.

Like the Code Generator deliverable, this folder contains only **documentation and reference sample outputs**. The implementation itself lives in the production source tree under [`src/utils/optimizer.py`](../src/utils/optimizer.py), [`src/events/optimizer.py`](../src/events/optimizer.py), and [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py), and is wired into the pipeline by [`config.yml`](../config.yml).

## 2. Deliverable Checklist

| # | Requirement | Where it lives in the app |
|---|---|---|
| 1 | Constant folding on the AST | `ConstantFolder` in `src/utils/optimizer.py`; driven by `FoldConstants` in `src/events/optimizer.py` |
| 2 | Three types of strength reduction | `StrengthReducer` in `src/utils/optimizer.py`; driven by `ReduceStrength` in `src/events/optimizer.py` |
| 3 | Dead code detection (unreachable-after-return) | `ReturnAnalyzer` in `src/utils/optimizer.py`; driven by `AnalyzeReturns` in `src/events/optimizer.py` |
| 4 | YAML anchor/alias deduplication | `YamlAnchorOptimizer` in `src/utils/optimizer.py`; driven by `OptimizeCode` in `src/events/optimizer.py` |
| 5 | Wiring into the compilation pipeline | `config.yml` — `compile event`, `compile keter`, `compile ast`, and `ir event` feature chains |
| 6 | Tests and CLI examples reproducing every effect | `src/utils/tests/test_optimizer.py` (33 tests), `src/events/tests/test_optimizer.py` (16 tests), plus the sample round-trips in §8 |
| 7 | Document this module | This README |

## 3. Pipeline Overview

All four optimizer components are wired into the three `compile` sub-features (`event`, `keter`, `ast`) and into the `ir event` feature in [`config.yml`](../config.yml). The four passes interleave between the existing stages as follows:

```
Source File (.py)
    │
    ▼  PerformLexicalAnalysis          → tokens
    ▼  PerformSyntacticAnalysis        → ast (DeclarationAggregate)
    ▼  PerformSemanticAnalysis         → symbol table + resolution
    ▼  PerformTypeCheck                → semantic errors
┌──────────────────────────┐
│ AnalyzeReturns           │  ReturnAnalyzer.analyze(ast)            (diagnostic-only)
└──────────────────────────┘
┌──────────────────────────┐
│ FoldConstants            │  ConstantFolder.fold(ast)
└──────────────────────────┘
┌──────────────────────────┐
│ ReduceStrength           │  StrengthReducer.reduce(ast)
└──────────────────────────┘
    ▼  GenerateIR                      → ir (IREventGroup)
    ▼  GenerateCode                    → codegen dict
┌──────────────────────────┐
│ OptimizeCode             │  YamlAnchorOptimizer.optimize(codegen)  (O2 only)
└──────────────────────────┘
    ▼  EmitResult                      → output.yaml / output.json
```

The three AST-level passes (`AnalyzeReturns`, `FoldConstants`, `ReduceStrength`) run at **-O O1** and above. The post-codegen `OptimizeCode` pass runs at **-O O2** and above. At `-O O0` every optimizer pass is a pure pass-through, so the `-O` flag alone selects which optimizations are active.

### 3.1 Optimization level summary

| Level | AnalyzeReturns | FoldConstants | ReduceStrength | OptimizeCode |
|-------|-----------------|---------------|-----------------|---------------|
| `-O O0` | passthrough (no warnings emitted) | passthrough | passthrough | passthrough |
| `-O O1` | active (warnings emitted) | active | active | passthrough |
| `-O O2` | active | active | active | active (YAML anchors) |

### 3.2 Feature chains that include optimization

- `ir event` — runs all three AST-level passes before IR generation.
- `compile event` — runs all three AST-level passes, then generates code, then optionally applies YAML anchor dedup.
- `compile keter` — skips all AST-level passes (starts from IR) and optionally applies YAML anchor dedup.
- `compile ast` — starts from a JSON AST, then runs semantic/type-check, all three AST-level passes, IR, codegen, and optional YAML anchor dedup.

## 4. Folder Contents

| File | Purpose |
|------|---------|
| `samples/pass_constant_folding_event.yaml` | `compile event -O O1` output for `samples/pass_constant_folding_event.py` — demonstrates AST-level constant folding. |
| `samples/pass_constant_folding_event.O0.yaml` | `compile event -O O0` baseline of the same source — the folded arithmetic appears here **unfolded**. |
| `samples/pass_strength_reduction_event.yaml` | `compile event -O O1` output for `samples/pass_strength_reduction_event.py` — demonstrates all three strength-reduction patterns. |
| `samples/pass_strength_reduction_event.O0.yaml` | `compile event -O O0` baseline — `Mul`/`Div`/`Exp` remain in their original, un-reduced form. |
| `samples/pass_dead_code_after_return.yaml` | `compile event -O O1` output for `samples/pass_dead_code_after_return.py` — trigger for the `UNREACHABLE_AFTER_RETURN` diagnostic. |
| `samples/pass_dead_code_after_return.O0.yaml` | `compile event -O O0` baseline — the unreachable statements still appear in the output, and no warnings are emitted. |
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

## 7. Deliverable 3 — Dead Code Detection (Unreachable-After-Return)

### 7.1 Overview

The return analyzer detects the simplest and most common form of dead code in the Tiferet dialect: statements that follow a `return` in the same scope. It is a **non-mutating diagnostic pass** — the AST is left unchanged, and the warnings are surfaced both on the console (via `OutputPrinter`) and through the `dead_code_warnings` data key in the feature pipeline.

### 7.2 Implementation

- **Service interface:** `ReturnAnalyzerService` in [`src/interfaces/optimizer.py`](../src/interfaces/optimizer.py).
- **Concrete utility:** `ReturnAnalyzer` in [`src/utils/optimizer.py`](../src/utils/optimizer.py).
- **Domain event:** `AnalyzeReturns` in [`src/events/optimizer.py`](../src/events/optimizer.py).
- **Container wiring:** `return_analyzer_service` + `analyze_returns_event` in [`config.yml`](../config.yml).
- **Constants:** `UNREACHABLE_AFTER_RETURN_CODE` and `UNREACHABLE_AFTER_RETURN_MESSAGE` in [`src/utils/optimizer.py`](../src/utils/optimizer.py).

### 7.3 Algorithm

`ReturnAnalyzer.analyze(ast)` walks the declaration tree with a scope stack that is pushed on `CLASS` / `FUNC` declarations and popped on the way out, so every warning carries a dotted `scope_path` (e.g. `module.ClassifyScore.describe`). Within each statement chain:

- `SNIPPET` / `BLOCK` container statements are flattened transparently via `iter_effective_statements`, so the parser's habit of grouping consecutive source lines into a snippet does not hide a terminator from a sibling snippet.
- `COMMENT` statements are ignored for control-flow purposes — they are neither terminators nor reportable as unreachable code.
- A direct `RETURN` statement becomes the terminator for the remainder of the chain.
- An `IF_ELSE` statement whose `body` **and** `else_body` both always return (determined recursively by `block_always_returns`) also becomes a terminator.
- Every statement encountered after the terminator is flagged as `UNREACHABLE_AFTER_RETURN`, preserving its `lineno` / `col` and the terminator's position (as `return_lineno` / `return_col`).

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

Source [`samples/pass_dead_code_after_return.py`](../samples/pass_dead_code_after_return.py) has one unreachable statement in `execute` and two unreachable statements in `describe`. Running the `compile event` pipeline at `-O O1` emits three warnings to the console and still writes the full (unchanged) YAML to disk:

```bash path=null start=null
$ python compiler.py compile event samples/pass_dead_code_after_return.py -O O1 -o out.yaml
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.execute (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 31, col 8]
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 51, col 8]
Warning [UNREACHABLE_AFTER_RETURN] in module.ClassifyScore.describe (line 0, col 0): \
  Statement is unreachable (follows a return statement) [after return at line 51, col 8]
```

At `-O O0` the same command emits **no** warnings because `AnalyzeReturns.execute` returns an empty list when the level is `O0`. The output YAML itself does not change between the two levels for this sample — the unreachable code is still emitted into the codegen output either way, since return analysis is diagnostic-only. Compare:

- [`samples/pass_dead_code_after_return.O0.yaml`](samples/pass_dead_code_after_return.O0.yaml) (no warnings)
- [`samples/pass_dead_code_after_return.yaml`](samples/pass_dead_code_after_return.yaml) (three warnings on the console)

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

The four optimization services and four driving events are declared as Tiferet container attributes in the top `attrs:` block of [`config.yml`](../config.yml):

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
```

### 9.2 Feature chain

The `compile event` feature chains the optimization stages between type-checking and IR generation (for AST passes) and between codegen and emit (for the YAML anchor pass):

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/config.yml start=142
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

```yaml path=/Users/ashatz/Documents/GitHub/tiferet-command-parser-edu/config.yml start=450
- name_or_flags:
    - -O
  default: O0
  description: "Optimization level: O0 (none, default), O1 (AST constant folding + strength reduction), O2 (constant folding + strength reduction + YAML anchor/alias deduplication)."
```

Each driving event normalizes the flag value (`.strip().upper()`) and branches internally — `FoldConstants` / `ReduceStrength` / `AnalyzeReturns` pass through at `O0` and activate at `O1+`, `OptimizeCode` passes through at `O0`/`O1` and activates at `O2+`.

## 10. Deliverable 6 — Tests and CLI Examples

### 10.1 Unit tests

Total: **49 tests** across two modules.

| File | Count | Coverage |
|------|-------|----------|
| [`src/utils/tests/test_optimizer.py`](../src/utils/tests/test_optimizer.py) | 33 | Unit tests for `YamlAnchorOptimizer` (params/returns dedup, vars omitted when no duplicates), `ConstantFolder` (simple add, multiply, divide → NUM_VAL, nested sub-expressions), `StrengthReducer` (all three patterns plus non-matching operands), and `ReturnAnalyzer` (direct-return, if/else-always-returns, comment-only chains, scope-stack correctness). |
| [`src/events/tests/test_optimizer.py`](../src/events/tests/test_optimizer.py) | 16 | Domain event tests for `FoldConstants` / `ReduceStrength` / `AnalyzeReturns` / `OptimizeCode` — delegation to injected service, `O0` pass-through behavior, real-service integration with a parser-produced AST, and `parameters_required` validation. |

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

# Dead-code detection (O1 prints three warnings; O0 prints none).
python compiler.py compile event samples/pass_dead_code_after_return.py -O O1 \
  -o /tmp/pass_dead_code_after_return.yaml
python compiler.py compile event samples/pass_dead_code_after_return.py -O O0 \
  -o /tmp/pass_dead_code_after_return.O0.yaml

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

# Re-compile from a pre-generated JSON AST (all four passes apply).
python compiler.py compile ast <file>.json -O O2 -o out.yaml

# Run the IR feature (includes all three AST-level passes, skips codegen).
python compiler.py ir event <source>.py -O O1 -o out.keter
```

## 11. Summary

The Tiferet optimizer is implemented as four cleanly-separated Tiferet domain events, each backed by a concrete utility class that implements an injectable service interface:

- **`FoldConstants` → `ConstantFolder` → `ASTOptimizerService` + `ASTTraversal`** — compile-time arithmetic on numeric literals. Inherits the shared declaration/statement traversal from `ASTTraversal`; overrides `transform_expression` to route into `fold_expression`.
- **`ReduceStrength` → `StrengthReducer` → `ASTStrengthReducerService` + `ASTTraversal`** — three textbook strength-reduction rewrites (`* 2**k`, `/ 2**k`, `** 2`). Inherits the shared traversal from `ASTTraversal`; overrides `transform_expression` to route into `reduce_expression`.
- **`AnalyzeReturns` → `ReturnAnalyzer` → `ReturnAnalyzerService`** — non-mutating unreachable-code detection.
- **`OptimizeCode` → `YamlAnchorOptimizer` → `OptimizerService`** — post-codegen YAML anchor/alias deduplication.

`ASTTraversal` (defined in `src/utils/settings.py`) provides the shared `traverse_declaration` and `traverse_statement` skeleton consumed by both `ConstantFolder` and `StrengthReducer`, eliminating duplicated traversal code between the two passes.

The four passes are wired into [`config.yml`](../config.yml) and executed from [`compiler.py`](../compiler.py) via the standard `-O` flag. This folder supplies only the **documentation** and the **reference YAML outputs** — satisfying the deliverable while keeping the single source of truth in the production code under [`src/`](../src).
