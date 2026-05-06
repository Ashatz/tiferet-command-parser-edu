# Part 3: Optimization — Video Script

**Estimated duration: 5–7 minutes**

**Input file:** `Presentation/samples/pass_all_optimizations.py`
**Output files:**
- IR (unoptimized) → `Presentation/results/ir/pass_all_optimizations_O0.keter`
- IR (optimized) → `Presentation/results/ir/pass_all_optimizations_O1.keter`
- Codegen (unoptimized) → `Presentation/results/dsl/pass_all_optimizations_O0.yaml`
- Codegen (optimized + anchors) → `Presentation/results/opt/pass_all_optimizations_O2.yaml`

---

## 3.0 — Introduction (~30 seconds)

> This is Part 3. We'll demonstrate how our compiler applies three required optimizations — constant folding, strength reduction, and dead code detection/elimination — plus one optional optimization: YAML anchor/alias deduplication.
>
> Our sample program has four event classes, each designed to trigger a specific optimization. All four events share the same parameter signature `(value: int, **kwargs)`, which will also demonstrate the optional anchor/alias optimization.

**[SHOW: `Presentation/samples/pass_all_optimizations.py` — full file]**

> We'll compare the unoptimized output (`-O O0`) against the optimized output (`-O O1` and `-O O2`) to see each transformation.

---

## 3.1 — Constant Folding (~1.5 minutes)

> **Purpose**: Evaluate pure-literal arithmetic sub-expressions at compile time, replacing them with a single constant.

**[SHOW: `Presentation/samples/pass_all_optimizations.py`, lines 16–26 — the `FoldConstants` event:]**
```python
        return value + (3 * 5) - (2 + 6)
```

> Before optimization, the IR shows the full expression tree:
> ```
> Return(Sub(Add(value, Mul(3, 5)), Add(2, 6)))
> ```

> After optimization at `-O O1`, it becomes:
> ```
> Return(Sub(Add(value, 15), 8))
> ```

**[SHOW side-by-side: `Presentation/results/ir/pass_all_optimizations_O0.keter` line ~30 vs `pass_all_optimizations_O1.keter` line ~30]**

> `Mul(3, 5)` folded to `15`, and `Add(2, 6)` folded to `8`. The sub-expression `value + ...` is left untouched because `value` is a variable, not a constant.

**[SHOW: `src/utils/optimizer.py`, lines 151–166 — `ConstantFolder` class docstring and ARITHMETIC_OPS]**

> The implementation is in `ConstantFolder` (`src/utils/optimizer.py`, line 152). It extends `ASTTraversal` and performs a **post-order walk** — children are folded before their parent. The method `fold_expression` (line 246) recurses into left and right children, then checks: if the current node is an arithmetic operator and **both** children are numeric literals, it calls `evaluate` (line 283) to compute the result and replace the subtree with a single literal node.

**[SHOW: `src/utils/optimizer.py`, lines 269–280 — the folding decision in `fold_expression`]**

> The key check is at lines 270–277: `expr.kind in ARITHMETIC_OPS` and `is_numeric(expr.left)` and `is_numeric(expr.right)`. Only when both sides are constant does folding occur.

---

## 3.2 — Strength Reduction (~1.5 minutes)

> **Purpose**: Replace expensive arithmetic operations with cheaper equivalents when one operand is a power of two.

**[SHOW: `Presentation/samples/pass_all_optimizations.py`, lines 42–49 — the three patterns in `ReduceStrength`:]**
```python
        scaled = value * 8       # -> value << 3
        halved = value / 4       # -> value >> 2
        squared = value ** 2     # -> value * value
```

> Before optimization:
> ```
> Assign(scaled, Mul(value, 8))
> Assign(halved, Div(value, 4))
> Assign(squared, Exp(value, 2))
> ```

> After optimization at `-O O1`:
> ```
> Assign(scaled, Shl(value, 3))
> Assign(halved, Shr(value, 2))
> Assign(squared, Mul(value, value))
> ```

**[SHOW side-by-side: the three statements in `pass_all_optimizations_O0.keter` vs `pass_all_optimizations_O1.keter`]**

> Three textbook patterns implemented in `StrengthReducer` (`src/utils/optimizer.py`, line 341):

> **Pattern 1** — `try_reduce_mul` (line 554): `x * 2^k` → `x << k`. The method `is_power_of_two_literal` (line 371) uses the classic bit trick `n & (n-1) == 0` to detect powers of two, then returns the exponent `k`. Either operand can be the literal since multiplication is commutative.

> **Pattern 2** — `try_reduce_div` (line 598): `x / 2^k` → `x >> k`. Only the divisor (right operand) is checked, since division is not commutative.

> **Pattern 3** — `try_reduce_exp` (line 629): `x ** 2` → `x * x`. The method `is_literal_two` (line 413) guards this to the exact exponent `2`. The left operand is deep-copied via `deep_copy_expr` (line 427) so the synthesized `Mul(value, value)` has two distinct AST nodes.

**[SHOW: `src/utils/optimizer.py`, lines 538–551 — the three pattern dispatches in `reduce_expression`]**

---

## 3.3 — Dead Code Detection and Elimination (~1 minute)

> **Purpose**: Detect statements that follow a `return` within the same scope and remove them from the AST.

**[SHOW: `Presentation/samples/pass_all_optimizations.py`, lines 68–72 — `EliminateDeadCode`:]**
```python
        return value + 1
        # Flagged as UNREACHABLE_AFTER_RETURN and pruned from the AST at O1.
        unused = 'never reached'
```

> Before optimization, the IR contains both snippets:
> ```
> Snippet(
>     Comments(Comment("Return immediately -- everything below this is unreachable.")),
>     Statements(Statement(Return(Add(value, 1)))),
> ),
> Snippet(
>     Comments(Comment("Flagged as UNREACHABLE_AFTER_RETURN and pruned...")),
>     Statements(Statement(Assign(unused, 'never reached'))),
> ),
> ```

> After optimization at `-O O1`, the dead snippet is removed entirely:
> ```
> Snippet(
>     Comments(Comment("Return immediately -- everything below this is unreachable.")),
>     Statements(Statement(Return(Add(value, 1)))),
> ),
> ```

**[SHOW side-by-side: `pass_all_optimizations_O0.keter` vs `pass_all_optimizations_O1.keter` — the eliminate_dead_code event section]**

> The console also emits a diagnostic warning:
> ```
> Warning [UNREACHABLE_AFTER_RETURN] in module.EliminateDeadCode.execute:
>   Statement is unreachable (follows a return statement) [after return at line 69, col 8]
> ```

> This is a two-pass process. First, `ReturnAnalyzer` (`src/utils/optimizer.py`, line 660) performs a non-mutating walk to collect warnings. It uses `scan_block` (line 762) to iterate statements, flattening `SNIPPET` containers so a return inside one snippet correctly terminates siblings in the next. When a `return` is seen, every subsequent non-comment statement is flagged.

> Then, `DeadCodeEliminator` (line 941) — which extends `ReturnAnalyzer` — performs the actual mutation via `eliminate_chain` (line 1007). It walks the same chain, and when it finds a terminator (return or an if/else whose both branches return), it sets `current.next = None` to detach everything after it.

---

## 3.4 — YAML Anchor/Alias Deduplication (Optional Optimization) (~1 minute)

> **Purpose**: When multiple events share identical parameter or return lists, deduplicate them in the YAML output using anchors (`&id`) and aliases (`*id`).

> All four events in our sample share the same `params` list: `[value:int:true::..., kwargs:dict:false::]`. At `-O O0`, each event repeats this list verbatim:

**[SHOW: `Presentation/results/dsl/pass_all_optimizations_O0.yaml`, lines 16–18 and 30–32 — repeated params]**

> At `-O O2`, the optimizer deduplicates them:

**[SHOW: `Presentation/results/opt/pass_all_optimizations_O2.yaml`, lines 1–4 and 19–20]**

> ```yaml
> vars:
> - &id001
>   - value:int:true::The input value.
>   - 'kwargs:dict:false::'
> ```
>
> The first event's `params` is defined as the anchor `&id001`, and all subsequent events reference it with `*id001`:
> ```yaml
>     fold_constants:
>       execute:
>         params: *id001
>     reduce_strength:
>       execute:
>         params: *id001
> ```

> The implementation is `YamlAnchorOptimizer` (`src/utils/optimizer.py`, line 38). The `optimize` method (line 46) collects all `params` and `returns` lists across events via `collect_lists` (line 90), fingerprints them by content, and when two or more lists match, creates one canonical Python list object that is shared by reference across all locations. PyYAML then automatically emits the anchor on the first occurrence and aliases for the rest. A top-level `vars` section is added so anchors are declared before they're referenced.

**[SHOW: `src/utils/optimizer.py`, lines 46–87 — `optimize` method]**

---

## 3.5 — Summary (~15 seconds)

> To recap the four optimizations:
> 1. **Constant Folding** — `Mul(3, 5)` → `15`, `Add(2, 6)` → `8`. Pure literals evaluated at compile time.
> 2. **Strength Reduction** — `Mul(value, 8)` → `Shl(value, 3)`, `Div(value, 4)` → `Shr(value, 2)`, `Exp(value, 2)` → `Mul(value, value)`. Expensive ops replaced with cheaper equivalents.
> 3. **Dead Code Elimination** — `Assign(unused, 'never reached')` removed after `Return`. Unreachable statements detected and pruned.
> 4. **Anchor/Alias Dedup** (optional) — Shared `params` lists collapsed to YAML `&id001` / `*id001`. Reduces output size.
>
> All optimizations are controlled by the `-O` flag: `O0` (none), `O1` (constant folding + strength reduction + dead code), `O2` (all of O1 + anchor/alias).

---

**[END: "That concludes our compiler walkthrough. Thank you."]**
