# Part 2: AST and Symbol Table — Video Script

**Estimated duration: 5–7 minutes**

**Input file:** `Presentation/samples/pass_scopes_and_types.py`
**Output files:**
- AST → `Presentation/results/ast/pass_scopes_and_types.json`
- Semantic → `Presentation/results/ast/pass_scopes_and_types_semantic.json`

---

## 2.0 — Introduction (~30 seconds)

> This is Part 2. We'll look at how the compiler builds an AST for a program with multiple scopes and data types, constructs a symbol table, resolves names across scopes, and performs type checking.
>
> Our sample program defines a `ScoreCalculator` event with two class-level attributes of different types (`base_points: int`, `multiplier: float`), a helper method `apply_bonus`, and an `execute` method. The methods declare local variables, use cross-scope references via `self.`, and include a function call statement.

**[SHOW: `Presentation/samples/pass_scopes_and_types.py` — full file]**

> Key elements to watch for:
> - **Two attribute types**: `base_points: int` (line 13), `multiplier: float` (line 16).
> - **Two scopes**: `apply_bonus` has its own local `bonus` (line 29); `execute` has locals `adjusted`, `bonus_points`, `weighted` (lines 47, 50, 53).
> - **Cross-scope expressions**: `self.base_points + amount` (line 47), `self.multiplier * adjusted` (line 53).
> - **Function call**: `self.apply_bonus(amount)` (line 50).

---

## 2.1 — AST (~1.5–2 minutes)

> Let's start with the AST.

**[RUN on screen:]**
```bash
python compiler.py parse event Presentation/samples/pass_scopes_and_types.py \
    -o Presentation/results/ast/pass_scopes_and_types.json
```

**[SHOW: `Presentation/results/ast/pass_scopes_and_types.json`]**

> The AST is a tree of Pydantic nodes connected by `.next` sibling links and `.body`/`.code` child links. Let's walk through the main constructs:

> **Class declaration** — The `ScoreCalculator` node has `kind: "class"` with a `subtype` referencing `DomainEvent` as its base class. Its `code` field chains the member declarations.

> **Attribute declarations** — Each attribute is wrapped in an `ARTIFACT_MEMBER` declaration. Inside, we find a bare declaration node. For `base_points`, the type is `kind: "int"` (line 13). For `multiplier`, it's `kind: "float"` (line 16). These carry no code bodies — they're pure type declarations.

> **Method declarations** — `apply_bonus` and `execute` are `kind: "func"` nodes. Each has:
> - A `params` linked list — `self` → `points: int` for `apply_bonus`; `self` → `amount: int` → `**kwargs: dict` for `execute`.
> - A `return_type` — `int` for `apply_bonus`, `float` for `execute`.
> - A `code` body of snippet statements.

> **Assignment expressions** — Inside `execute`, the statement `adjusted = self.base_points + amount` (line 47) becomes an `assign` expression node. Its `left` is a `name` node with value `"adjusted"`, and its `right` is an `add` node whose children are `name "self.base_points"` and `name "amount"`.

> **Function call** — `self.apply_bonus(amount)` (line 50) becomes a `call` expression: `left` is `name "self.apply_bonus"`, `right` is an `args_list` containing `name "amount"`.

> The AST captures the full structure but has no notion of types for variables or scope resolution — that's the semantic analyzer's job.

---

## 2.2 — Symbol Table (~2 minutes)

> Now let's see how the symbol table is built.

**[RUN on screen:]**
```bash
python compiler.py semantic event Presentation/samples/pass_scopes_and_types.py \
    -o Presentation/results/ast/pass_scopes_and_types_semantic.json --include-ast true
```

> The symbol table is constructed by `SymbolTableBuilder` in `src/utils/semantic.py` (line 30). It performs a single-pass walk of the AST and builds a flat registry of scopes, each containing its symbols.

**[SHOW: semantic output — the `symbol_table.scopes` section]**

> The builder creates four scopes for this program:

> **1. `module`** — The top-level module scope.
> - `DomainEvent` → `kind: import`, `source_module: tiferet.events`
> - `ScoreCalculator` → `kind: class_def`, `type_annotation: DomainEvent`

> **2. `module.ScoreCalculator`** — The class scope.
> - `base_points` → `kind: attribute`, `type_annotation: int`
> - `multiplier` → `kind: attribute`, `type_annotation: float`
> - `apply_bonus` → `kind: method`, `type_annotation: int` (return type)
> - `execute` → `kind: method`, `type_annotation: float`

> **3. `module.ScoreCalculator.apply_bonus`** — The method scope.
> - `self` → `kind: parameter`
> - `points` → `kind: parameter`, `type_annotation: int`
> - `bonus` → `kind: variable`, `type_annotation: int` (inferred from literal `10`)

> **4. `module.ScoreCalculator.execute`** — The method scope.
> - `self` → `kind: parameter`
> - `amount` → `kind: parameter`, `type_annotation: int`
> - `kwargs` → `kind: parameter`, `type_annotation: dict`
> - `adjusted` → `kind: variable`, `type_annotation: int` (inferred from `self.base_points + amount`)
> - `bonus_points` → `kind: variable` (type not inferred — RHS is a function call)
> - `weighted` → `kind: variable`, `type_annotation: float` (inferred from `self.multiplier * adjusted`)

**[SHOW: `src/utils/semantic.py`, lines 459–538 — `handle_expr_stmt` method]**

> The builder registers local variables when it encounters bare assignments like `bonus = 10` inside a method scope. The method `handle_expr_stmt` (line 460) detects assignment expressions and:
> 1. Checks for `self.X` patterns — routes those to the class scope.
> 2. For bare locals, checks for duplicate definitions in the same scope (would emit `DUPLICATE_VARIABLE_SAME_SCOPE`).
> 3. Checks if the name shadows an outer scope (would emit `VARIABLE_SHADOWS_OUTER_SCOPE`).
> 4. Infers the type via `infer_local_type` (line 586) — this resolves literals directly (`10` → `int`), looks up name types through `self.X` resolution, and propagates arithmetic types (`float * int` → `float`).

> The key point: `weighted = self.multiplier * adjusted` infers `float` because `self.multiplier` resolves to `float` in the class scope and `float * int` yields `float`.

---

## 2.3 — Name Resolution and Scope Lookup (~30 seconds)

**[SHOW: semantic output — the `resolution` section]**

> After building the symbol table, the `NameResolver` (line 704 of `src/utils/semantic.py`) performs a second pass over the AST. For each name reference, it walks the scope chain from the current scope upward:

> - `points` in `apply_bonus` → resolved to `module.ScoreCalculator.apply_bonus` (local parameter).
> - `bonus` in `apply_bonus` → resolved to `module.ScoreCalculator.apply_bonus` (local variable).
> - `self.base_points` in `execute` → resolved to `module.ScoreCalculator` (class attribute).
> - `amount` in `execute` → resolved to `module.ScoreCalculator.execute` (local parameter).
> - `self.apply_bonus` in `execute` → resolved to `module.ScoreCalculator` (class method).
> - `self.multiplier` in `execute` → resolved to `module.ScoreCalculator` (class attribute).
> - `adjusted` in `execute` → resolved to `module.ScoreCalculator.execute` (local variable).

> All names resolve successfully — `unresolved: []`.

> The `self.X` resolution is handled by `resolve_self_attr` (line 988), which walks the scope stack to find the enclosing class scope and checks if `X` exists there.

---

## 2.4 — Type Checking (~1.5 minutes)

> The final stage is type checking, implemented by `TypeChecker` in `src/utils/typecheck.py` (line 24). It walks the AST a third time with the symbol table and checks two categories of rules:

> **Structural validation** — The type checker validates the Tiferet artifact structure:
> - Import groups must be named `core`, `infra`, or `app` (`check_import_group`, line 376).
> - Section names must match class names in PascalCase (`check_section_class_name`, line 438) — e.g., section `score_calculator` expects class `ScoreCalculator`.
> - Event classes must declare an `execute` method (`class_has_method`, line 507).
> - Attribute members must be variable declarations, not functions (`check_attribute_member`, line 592).
> - Method members must have `self` as the first parameter (`check_method_member`, line 634).

**[SHOW: `src/utils/typecheck.py`, lines 769–842 — `check_assignment` and `check_binary_op`]**

> **Type compatibility** — For assignments and binary operations:
> - `check_assignment` (line 770) looks up the declared type of the target variable, infers the type of the right-hand side, and compares them via `types_compatible`.
> - `check_binary_op` (line 806) infers both operand types and validates they are compatible — numeric with numeric for arithmetic, str with str for addition (concatenation).
>
> Type inference in `infer_type` (line 845) follows the same logic as the builder: literals map directly, names are looked up in the scope chain, and arithmetic propagates types (`float` wins over `int`).

> For our sample program, all types are compatible:
> - `adjusted = self.base_points + amount` → `int + int = int` ✓
> - `weighted = self.multiplier * adjusted` → `float * int = float` ✓
> - `return points + bonus` → `int + int = int` ✓
>
> No type errors are produced.

> To see what a type error looks like, consider if we had `bonus = 'ten'` instead of `bonus = 10`. The assignment `return points + bonus` would fail with `TYPE_MISMATCH_OPERATION`: unsupported operand types for `add`: `int` and `str`.

---

**[TRANSITION: "Next, in Part 3, we'll examine how the optimizer applies constant folding, strength reduction, and dead code detection."]**
