# Part 1: Arithmetic Expressions — Video Script

**Estimated duration: 5–7 minutes**

**Expression:** `1 + 3 - (4 / 2) * 5 + 6`

**Input file:** `Presentation/samples/pass_simple_expression.py`
**Output files:**
- Tokens → `Presentation/results/token/pass_simple_expression.yaml`
- AST → `Presentation/results/ast/pass_simple_expression.json`
- IR → `Presentation/results/ir/pass_simple_expression.keter`
- Codegen → `Presentation/results/dsl/pass_simple_expression.yaml`

---

## 1.0 — Introduction (~30 seconds)

> This is Part 1 of our compiler walkthrough. We'll trace how a single arithmetic expression moves through every stage of the compiler, from raw text to final output.
>
> Our input language is the Tiferet Domain Event dialect — a structured subset of Python. The compiler uses PLY for lexing and parsing, and Pydantic for the AST model.
>
> Our sample program places the expression `1 + 3 - (4 / 2) * 5 + 6` inside a return statement on line 23.

**[SHOW: `Presentation/samples/pass_simple_expression.py`, highlighting line 23:]**
```python
        return 1 + 3 - (4 / 2) * 5 + 6
```

---

## 1.1 — Scanner / Lexical Analysis (~1–1.5 minutes)

> Let's start with how the scanner tokenizes this expression.

**[RUN on screen:]**
```bash
python compiler.py scan event Presentation/samples/pass_simple_expression.py \
    -o Presentation/results/token/pass_simple_expression.yaml
```

> The scanner is implemented in `src/utils/lexer.py` as `TiferetLexer`, which wraps PLY's lexer engine. Token rules live in `src/assets/lexer.py` as regex patterns — each operator gets its own named rule.

**[SHOW: `src/assets/lexer.py`, lines 82–93 — PLUS, MINUS, STAR, SLASH constants:]**

> `T_PLUS` is `\+`, `T_MINUS` is `-`, `T_STAR` is `\*`, `T_SLASH` is `/`. Numbers are matched by `T_NUMBER_LITERAL` at line 331, which uses the pattern `[0-9]+(\.[0-9]+)?` to capture both integers and floats. Parentheses are matched by `T_LPAREN` and `T_RPAREN`.

> Now let's look at what the scanner actually produces for line 23. The full file yields 61 tokens, but the expression itself generates these 14:

**[SHOW: `Presentation/results/token/pass_simple_expression.yaml`, lines 211–266 — the expression tokens]**

| Token Type       | Value | Lexpos |
|------------------|-------|--------|
| RETURN           | return| 596    |
| NUMBER_LITERAL   | 1     | 603    |
| PLUS             | +     | 605    |
| NUMBER_LITERAL   | 3     | 607    |
| MINUS            | -     | 609    |
| LPAREN           | (     | 611    |
| NUMBER_LITERAL   | 4     | 612    |
| SLASH            | /     | 614    |
| NUMBER_LITERAL   | 2     | 616    |
| RPAREN           | )     | 617    |
| STAR             | *     | 619    |
| NUMBER_LITERAL   | 5     | 621    |
| PLUS             | +     | 623    |
| NUMBER_LITERAL   | 6     | 625    |

> The scanner treats all of these equally — it doesn't know that `*` binds tighter than `+`. It just classifies each character sequence and records its position. That's the parser's job.

---

## 1.2 — Parser / Syntax Analysis (~1.5–2 minutes)

> The parser takes this flat token stream and builds a tree that encodes operator precedence and associativity.

**[RUN on screen:]**
```bash
python compiler.py parse event Presentation/samples/pass_simple_expression.py \
    -o Presentation/results/ast/pass_simple_expression.json
```

> The parser is implemented in `src/utils/parser.py` as `TiferetParser`. It enforces **PEMDAS** precedence through a chain of grammar rules — each level can only contain expressions of equal or higher precedence:

**[SHOW: `src/utils/parser.py` — walk through the expression hierarchy:]**

> **Level 1 — `p_primary_expr`** (lines 1120–1131): The atoms. This is where literals live, and where parenthesized expressions re-enter the chain. The rule `LPAREN operation_expr RPAREN` at line 1128 means anything inside parens gets parsed as a full expression, giving parentheses the highest effective precedence.
>
> **Level 2 — `p_exponential_expr`** (line 1108): Handles `**`, right-associative.
>
> **Level 3 — `p_multiplicative_expr`** (lines 1094–1105): Handles `*`, `/`, `%`, left-associative. This is where `(4 / 2) * 5` gets grouped — division and multiplication at the same level, evaluated left to right.
>
> **Level 4 — `p_additive_expr`** (lines 1081–1091): Handles `+` and `-`, left-associative. This is the lowest arithmetic precedence.

> So for `1 + 3 - (4 / 2) * 5 + 6`, the parser builds the tree bottom-up:
>
> 1. The parenthesized `(4 / 2)` is parsed at the primary level — the parens force it to be fully reduced before anything outside sees it.
> 2. At the multiplicative level, `(4 / 2) * 5` is grouped into a `mul` node.
> 3. At the additive level, the parser works left to right:
>    - `1 + 3` becomes an `add` node.
>    - That result minus `(4/2)*5` becomes a `sub` node.
>    - That result plus `6` becomes the outermost `add` node.

> Each binary operator node is created by `ExpressionAggregate.new_operator_expr()` in `src/mappers/ast.py` at line 468. This factory method takes the operator symbol (e.g., `+`, `-`, `*`, `/`), left and right child expressions, and the source position. It maps the symbol to the corresponding `ExprKind` enum — for example, `+` becomes `ExprKind.ADD`, `*` becomes `ExprKind.MUL` — and returns a new `ExpressionAggregate` node.

**[SHOW: `src/mappers/ast.py`, lines 466–521 — `new_operator_expr` factory method]**

---

## 1.3 — Abstract Syntax Tree (~1 minute)

> Let's look at the tree the parser actually produced.

**[SHOW: `Presentation/results/ast/pass_simple_expression.json`, lines 139–204 — the expression subtree]**

> Stripping away the event boilerplate, the return expression is this tree:

```
         (+)           ← outermost: ... + 6
        /   \
      (-)    6         ← middle: (1+3) - ((4/2)*5)
     /   \
   (+)   (*)           ← left: 1+3    right: (4/2)*5
  / \   /   \
 1   3 (/)   5         ← the parenthesized division
      / \
     4   2
```

> In the JSON, this reads as nested nodes. The root is `kind: "add"` with:
> - `left`: a `kind: "sub"` node, whose own left is `kind: "add"` (1+3) and right is `kind: "mul"` ((4/2)*5).
> - `right`: `kind: "int_val"`, value `"6"`.
>
> The `div` node for `4 / 2` sits inside the `mul` node's left child. Every leaf is a typed `int_val` literal, and every internal node is a binary operator carrying its source position (`lineno: 23`).
>
> This tree faithfully encodes the evaluation order: compute `4/2` first, multiply by `5`, compute `1+3`, subtract, then add `6`. The expected result is `1 + 3 - 10 + 6 = 0`.

---

## 1.4 — Intermediate Representation (~45 seconds)

> The IR stage walks the AST and produces a "keter" IR — a structured, text-based intermediate representation.

**[RUN on screen:]**
```bash
python compiler.py ir event Presentation/samples/pass_simple_expression.py \
    -o Presentation/results/ir/pass_simple_expression.keter -O O0
```

**[SHOW: `Presentation/results/ir/pass_simple_expression.keter`, focusing on lines 20–28 — the Snippets block:]**

> The keter IR is a constructor-based DSL. Inside the `Execute` block, the `Snippets` section contains our compiled code:
>
> ```
> Snippet(
>     Comments(
>         Comment("Evaluate and return the expression."),
>     ),
>     Statements(
>         Statement(Return(Add(Sub(Add(1, 3), Mul(Div(4, 2), 5)), 6))),
>     ),
> )
> ```
>
> The expression tree from the AST is now serialized as a prefix-notation string inside the `Statement`. You can read it directly: `Return(Add(Sub(Add(1, 3), Mul(Div(4, 2), 5)), 6))` — a return of the outermost `Add`, wrapping a `Sub` of `Add(1, 3)` minus `Mul(Div(4, 2), 5)`, plus `6`.
>
> This serialization is produced by the `encode_expr` method in `src/utils/ir.py` (line 704), which recursively walks each AST expression node and emits the corresponding constructor — `Add(...)`, `Sub(...)`, `Mul(...)`, `Div(...)` — with leaf literals emitted as bare values.

---

## 1.5 — Code Generation (~45 seconds)

> The final stage translates the IR into structured YAML — our target output.

**[RUN on screen:]**
```bash
python compiler.py compile event Presentation/samples/pass_simple_expression.py \
    -o Presentation/results/dsl/pass_simple_expression.yaml -O O0
```

> The code generator in `src/utils/codegen.py` (`TiferetGenerator`) walks the IR and builds the output dict.

**[SHOW: `Presentation/results/dsl/pass_simple_expression.yaml`, focusing on lines 17–21 — the snippet:]**

> ```yaml
> snpt:
> - coms:
>   - Evaluate and return the expression.
>   stmt:
>   - Return(Add(Sub(Add(1, 3), Mul(Div(4, 2), 5)), 6))
> ```
>
> This is the final serialized form of our expression. It reads as prefix notation: the outermost `Add` is the final `+ 6`. Inside it, `Sub` subtracts `Mul(Div(4, 2), 5)` from `Add(1, 3)`. You can trace the tree structure directly from this string — it mirrors the AST exactly.
>
> So the full journey for `1 + 3 - (4 / 2) * 5 + 6` was:
> 1. **Scanner** — flat stream of 14 tokens: numbers, operators, parens.
> 2. **Parser** — precedence-correct binary tree via the four-level grammar.
> 3. **AST** — Pydantic tree with typed `int_val` leaves and operator internal nodes.
> 4. **IR** — keter constructor DSL with the expression serialized as prefix notation inside `Statement(Return(...))`.
> 5. **Codegen** — YAML with the expression carried through as `Return(Add(Sub(Add(1, 3), Mul(Div(4, 2), 5)), 6))`.
>
> We skipped optimization for this part. That will be covered in Part 3.

---

**[TRANSITION: "Next, in Part 2, we'll examine a program with multiple scopes, variable types, and type checking."]**
