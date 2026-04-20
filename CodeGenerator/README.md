# Code Generator — Code Generation Phase for the Tiferet Domain Event Dialect

**Project:** Tiferet Event Parser (Educational Compiler Front-End)
**Course:** ECE 506 — Compiler Design
**University of Arizona**
**Date:** April 2026

**Author:** Andrew Shatz
**Co-Author:** Oz (oz-agent@warp.dev)

## 1. Purpose

This directory contains the deliverables for the **code generation** phase of the Tiferet compiler. The code generator walks the **Intermediate Representation (IR)** produced by the earlier phases (lex → parse → semantic analysis → IR generation) and produces a structured, schema-conforming **YAML document** that represents the compiled form of a Tiferet Domain Event source file.

Unlike the Scanner and Parser deliverable folders — which bundle standalone scripts — this deliverable consists of the **schema definition**, **reference sample outputs**, and this README, which points to the parts of the live application (under `src/`) that perform each step of the process. The Tiferet application already implements a complete, testable code generator; this folder documents it.

## 2. Deliverable Checklist

The ECE 506 Code Generator deliverable requires the following artifacts. Each is satisfied by an existing, tested component in the main application.

| # | Requirement | Where it lives in the app |
|---|---|---|
| 1 | Print the AST (or IR) into a file | `src/events/parser.py`, `src/events/ir.py`, `src/utils/output.py`, `src/domain/ir.py` |
| 2 | Read the IR file in a different script | `src/events/codegen.py` (`LoadFromKeter`, `LoadFromAST`) |
| 3 | Reconstruct the AST from the file | `src/mappers/ir.py` (`KeterIREventGroup.from_data`), `src/events/codegen.py` (`LoadFromAST`) |
| 4 | Call the function to print the AST (testing) | `src/utils/printer.py` (`ASTPrinter`); wired in `src/events/semantic.py` (`EmitSemanticResult`) |
| 5 | Generate code for an expression | `src/utils/codegen.py` (`TiferetGenerator.build_snippets` / `.build_snippet`) consumes the IR expression strings produced by `src/utils/ir.py` (`IRGenerator.encode_expr`) |
| 6 | Test your code | Reference outputs in `CodeGenerator/samples/*.yaml` round-trip from the paired `samples/*.py` sources (see §10) |
| 7 | Update the main method to call the code generator after parsing | `compiler.py` + `config.yml` — the `compile event` feature chains parsing → semantic → IR → codegen → optimize → emit |
| 8 | Document this module | This README |

The rest of the document expands each row with file, class, and method references.

## 3. Pipeline Overview

The code generator is the second-to-last stage of the `compile event` feature declared in `config.yml`. It is wired into the Tiferet domain-event pipeline and receives an `IREventGroup` instance (from `GenerateIR`) as input:

```
Source File (.py)
    │
    ▼  PerformLexicalAnalysis        → tokens
    ▼  PerformSyntacticAnalysis      → ast (DeclarationAggregate)
    ▼  PerformSemanticAnalysis       → symbol table + resolution
    ▼  PerformTypeCheck              → semantic errors
    ▼  GenerateIR                    → ir (IREventGroup)
┌──────────────────────────┐
│ GenerateCode             │  TiferetGenerator.generate(ir)  →  codegen dict
└──────────────────────────┘
┌──────────────────────────┐
│ OptimizeCode             │  YamlAnchorOptimizer.optimize(codegen)
└──────────────────────────┘
┌──────────────────────────┐
│ EmitCodegenResult        │  ScanOutputWriter.write(codegen, path, format)
└──────────────────────────┘  → output.yaml / output.json
```

Two sibling sub-features reuse the back half of the pipeline when the source is already compiled to an earlier form:

- `compile keter` — starts from a `.keter` IR file via `LoadFromKeter`.
- `compile ast` — starts from a JSON AST file via `LoadFromAST`, then re-runs semantic analysis, type checking, and IR generation before entering the codegen stages.

All three sub-features are declared in `config.yml` under the `compile:` feature group and share the same `GenerateCode → OptimizeCode → EmitCodegenResult` tail.

## 4. Folder Contents

| File | Purpose |
|------|---------|
| `schema.yml` | Formal schema definition for the codegen output dict — the target language of the Tiferet code generator. |
| `samples/` | Pre-computed YAML outputs produced by the pipeline for each sample source file in `samples/` at the project root. |
| `README.md` | This document. |

No new source scripts are added. All implementation is referenced from the live Tiferet application under `src/`.

## 5. Deliverable 1 — Printing the AST / IR into a File

The pipeline produces three persistable artifacts, each of which is written to disk by a dedicated emit event.

### 5.1 AST → JSON file

- **Event:** `EmitParseResult` in `src/events/parser.py`
- **Writer:** `ScanOutputWriter.write` in `src/utils/output.py`
- **Serialization:** the parser returns a `DeclarationAggregate` (Pydantic model) which is serialized with `model_dump(exclude_none=True, exclude_unset=True)` and written as JSON or YAML.
- **CLI:** `python compiler.py parse event <source> -o output.json`

### 5.2 IR → keter file

- **Event:** `EmitIRResult` in `src/events/ir.py`
- **Serializer:** `IREventGroup.to_keter()` in `src/domain/ir.py` (every IR node class — `IRImport`, `IRImportGroup`, `IREvent`, `IRExecute`, `IRMethod`, `IRParam`, `IRReturn`, `IRSnippet`, `IRStatement`, `IRComment`, etc. — implements its own `to_keter(indent)` method; the root calls them recursively).
- **Writer:** `ScanOutputWriter.write` (auto-detects `.keter` extension and writes as plain text).
- **CLI:** `python compiler.py ir event <source> -o output.keter`

### 5.3 Codegen dict → YAML file

- **Event:** `EmitCodegenResult` in `src/events/codegen.py`
- **Writer:** `ScanOutputWriter.write` (auto-detects `.yaml` / `.json`).
- **CLI:** `python compiler.py compile event <source> -o output.yaml`

Pre-generated examples of all three artifact types live in `Parser/samples/` (AST), `IntermediateRepresentation/samples/` (IR), and `CodeGenerator/samples/` (codegen) respectively.

## 6. Deliverable 2 — Reading the IR File in a Different Script

The code generator is intentionally decoupled from the IR producer. Two dedicated loader events read previously-printed IR/AST artifacts from disk and feed them into the codegen pipeline.

- **`LoadFromKeter`** in `src/events/codegen.py`
  - Reads a `.keter` file via `tiferet.File`.
  - Delegates parsing to `KeterIREventGroup.from_data(text)`.
  - Raises `INVALID_KETER_SYNTAX` (declared in `config.yml`) on malformed input.
  - CLI: `python compiler.py compile keter <file>.keter -o output.yaml`

- **`LoadFromAST`** in `src/events/codegen.py`
  - Reads a JSON AST file via `tiferet.Json`.
  - Reconstructs the `DeclarationAggregate` directly via Pydantic's `model_validate()`.
  - CLI: `python compiler.py compile ast <file>.json -o output.yaml`

Both events satisfy the deliverable requirement that the IR file be read from **a different script than the one that produced it** — they are separate domain events, wired into separate `compile keter` / `compile ast` features in `config.yml`.

## 7. Deliverable 3 — Reconstructing the AST / IR from the File

Reconstruction is performed by dedicated **transfer objects** in `src/mappers/ir.py`. The keter DSL is tokenized by a minimal custom lexer (`KeterLexer`) and a recursive-descent parser built from composable `KeterIR*` transfer objects.

Key classes in `src/mappers/ir.py`:

- `KeterLexer` — tokenizes the keter DSL string into `(type, value)` tuples (keywords, identifiers, quoted strings, delimiters).
- `KeterTransferObject` — base class providing `consume`, `peek`, `skip_comma`, `collect_balanced`, `decode_param_spec`, `decode_return_spec`.
- `KeterIREventGroup.from_data(text)` — root entry point. Tokenizes the input and dispatches to child transfer objects (`KeterIRImportGroups`, `KeterIREvents`, etc.) to rebuild the full `IREventGroup` tree.
- Inner transfer objects: `KeterIRImport`, `KeterIRImportGroup`, `KeterIRImportGroups`, `KeterIREvent`, `KeterIREvents`, `KeterIRAttribute`, `KeterIRAttributes`, `KeterIRAssign`, `KeterIRInjection`, `KeterIRInjections`, `KeterIRExecute`, `KeterIRMethod`, `KeterIRMethods`, `KeterIRParam`, `KeterIRParams`, `KeterIRReturn`, `KeterIRReturns`, `KeterIRSnippet`, `KeterIRSnippets`, `KeterIRComment`, `KeterIRComments`, `KeterIRStatement`, `KeterIRStatements`.

For the JSON AST case, reconstruction is a one-liner: `Decl.model_validate(ast_dict)` in `LoadFromAST` (Pydantic handles the entire recursive rebuild because every AST node is a `BaseModel`).

## 8. Deliverable 4 — Calling the Function to Print the AST (Testing)

The `ASTPrinter` utility in `src/utils/printer.py` provides post-order, human-readable printing for AST trees, statement chains, expression trees, type trees, parameter lists, and symbol tables.

Public static methods:

- `ASTPrinter.print_ast(decl)` — print a `Declaration` tree.
- `ASTPrinter.print_statement(stmt)` — print a `Statement` chain.
- `ASTPrinter.print_expression(expr)` — print an `Expression` tree.
- `ASTPrinter.print_type(type_node)` — print a `Type` tree.
- `ASTPrinter.print_param_list(param)` — print a `ParamList` linked list.
- `ASTPrinter.print_symbol_table(symbol_table)` — print the symbol table in readable form.

The semantic emit stage (`EmitSemanticResult` in `src/events/semantic.py`) invokes these printers whenever no `-o` flag is supplied, so testing the printed tree is as simple as:

```bash
python compiler.py semantic event samples/pass_minimal_event.py --include-ast true
```

This prints the AST (post-order) and the symbol table directly to the console — demonstrating that the AST round-trips cleanly from parsing through any reconstruction step.

## 9. Deliverable 5 — Generating Code for an Expression

Expression code generation is a two-stage process:

### 9.1 AST → IR encoding

`IRGenerator.encode_expr` in `src/utils/ir.py` recursively encodes an AST `Expression` node into a string-form DSL expression suitable for the IR. It handles every `ExprKind`:

- **Literals:** `STR_VAL`, `INT_VAL`, `NUM_VAL`, `BOOL_VAL` → raw value text.
- **Names / dotted names:** `NAME` → `expr.name` (also detects the parser's `NAME`/`value="**"` encoding of exponentiation and rewrites it as `Exp(left, right)`).
- **Assignments:** `ASSIGN` → `Assign(<lhs>, <rhs>)`.
- **Arithmetic:** `ADD`/`SUB`/`MUL`/`DIV`/`MOD`/`EXP` → `Add(l,r)`, `Sub(l,r)`, `Mul(l,r)`, `Div(l,r)`, `Mod(l,r)`, `Exp(l,r)`.
- **Calls:** `CALL` → `Call(<callee>, <args>)` (or `Call(<callee>)` when no args).
- **Argument lists:** `ARGS_LIST` → `left, right` (recursively flattened).
- **Comments:** `COMMENT` → the raw comment text.

Sibling method `IRGenerator.encode_stmt` wraps statement-level nodes (`RETURN`, `EXPR`, `IF_ELSE`) into `Return(...)`, inline expressions, and `If(cond, body)` respectively.

Example expression round-trip:

```python
# Source
return a + b * 3 ** 2
```

```
# Encoded IR expression string
Return(Add(a, Mul(b, Exp(3, 2))))
```

### 9.2 IR → YAML codegen

`TiferetGenerator` in `src/utils/codegen.py` consumes the IR and emits the schema-conforming dict. Its entry method is `generate(ir: IREventGroup) -> Dict[str, Any]`, which delegates to:

- `build_imports` / `build_import_group` — collapses shared module paths into `{src, tgts}` entries.
- `build_events` / `build_event` — assembles the `evts` map with per-event keys.
- `build_attributes` — compact `[{name: type}, ...]`.
- `build_injections` / `encode_injection` — compact colon-delimited spec strings with optional `assign:` lists.
- `build_execute` / `build_method` / `build_methods` — `params`, `returns`, `snpt` sections.
- `build_params` / `encode_param` — `name:type:required:default:description` strings.
- `build_returns` / `encode_return` — `type:description` strings.
- `build_snippets` / `build_snippet` — paired `coms` / `stmt` lists, preserving the IR's string-encoded expressions as-is (this is where the encoded expressions from §9.1 appear in the final YAML).

The output omits empty nodes entirely, per the `schema.yml` rule.

### 9.3 Optional optimization pass

`YamlAnchorOptimizer` in `src/utils/optimizer.py` implements `OptimizerService.optimize`. At `-O O1`, it deduplicates repeated `params`/`returns` lists across events by sharing a single Python list object, which PyYAML then emits as `&anchor` / `*alias` pairs. `-O O0` (the default) passes the dict through unchanged.

## 10. Deliverable 6 — Testing via Sample Round-Trips

Rather than lean on isolated unit tests, the code generator is validated end-to-end by running the live `compile event` pipeline against the project's `samples/*.py` source files and comparing the YAML output to the pre-committed reference files in `CodeGenerator/samples/`. Every pass-case source has a paired YAML output that demonstrates the codegen handles that feature correctly.

### 10.1 Source → YAML pairings

| Source sample (`samples/*.py`) | Reference output (`CodeGenerator/samples/*.yaml`) | Feature demonstrated |
|---|---|---|
| [`pass_imports_only.py`](../samples/pass_imports_only.py) | [`pass_imports_only.yaml`](samples/pass_imports_only.yaml) | Multi-category imports (`core`, `app`), collapsing shared module paths, `evts` omitted when there are no events. |
| [`pass_minimal_event.py`](../samples/pass_minimal_event.py) | [`pass_minimal_event.yaml`](samples/pass_minimal_event.yaml) | Single event with only `execute`; string literal expression emitted as `Return('pong')`; empty `attributes`/`injections`/`methods` omitted. |
| [`pass_minimal_injection_event.py`](../samples/pass_minimal_injection_event.py) | [`pass_minimal_injection_event.yaml`](samples/pass_minimal_injection_event.yaml) | Class-level `attributes`, constructor `injections` with `assign:` mappings, attribute access expression (`Return(self.pong)`). |
| [`pass_multiple_operator_events.py`](../samples/pass_multiple_operator_events.py) | [`pass_multiple_operator_events.yaml`](samples/pass_multiple_operator_events.yaml) | Every arithmetic operator encoded: `Return(Add(a, b))`, `Sub`, `Mul`, `Div`, `Mod`, `Exp`; repeated param / return shapes across six events. |
| [`pass_helper_method_event.py`](../samples/pass_helper_method_event.py) | [`pass_helper_method_event.yaml`](samples/pass_helper_method_event.yaml) | Helper `methods:` section alongside `execute`; call expressions (`Call(self.to_int, a)`); assignment statements; chained arithmetic `Return(Sub(Add(x, Mul(y, 3)), 2))` demonstrating PEMDAS-correct nesting. |
| [`pass_minimal_event.py`](../samples/pass_minimal_event.py) (compiled from keter) | [`pass_minimal_event_2.yaml`](samples/pass_minimal_event_2.yaml) | Output of `compile keter` on the pre-generated `.keter` IR — byte-identical to `pass_minimal_event.yaml`, proving the keter round-trip. |
| [`pass_minimal_event.py`](../samples/pass_minimal_event.py) (compiled from AST) | [`pass_minimal_event_3.yaml`](samples/pass_minimal_event_3.yaml) | Output of `compile ast` on the pre-generated JSON AST — byte-identical to `pass_minimal_event.yaml`, proving the AST round-trip. |

### 10.2 Reproducing the reference outputs

Each YAML in `CodeGenerator/samples/` can be regenerated from the paired source file and compared with `diff`:

```bash
source .venv/bin/activate

# End-to-end pipeline from Python source.
for name in pass_imports_only pass_minimal_event pass_minimal_injection_event \
            pass_multiple_operator_events pass_helper_method_event; do
    python compiler.py compile event samples/$name.py -o /tmp/$name.yaml
    diff -u CodeGenerator/samples/$name.yaml /tmp/$name.yaml
done

# Keter IR round-trip (produces pass_minimal_event_2.yaml).
python compiler.py compile keter IntermediateRepresentation/samples/pass_minimal_event.keter \
    -o /tmp/pass_minimal_event_2.yaml
diff -u CodeGenerator/samples/pass_minimal_event_2.yaml /tmp/pass_minimal_event_2.yaml

# JSON AST round-trip (produces pass_minimal_event_3.yaml).
python compiler.py compile ast Parser/samples/pass_minimal_event.json \
    -o /tmp/pass_minimal_event_3.yaml
diff -u CodeGenerator/samples/pass_minimal_event_3.yaml /tmp/pass_minimal_event_3.yaml
```

If the code generator is working correctly, every `diff` prints nothing — the live pipeline reproduces each committed reference output exactly.

### 10.3 What the sample round-trips prove

- **Correctness** — the YAML output conforms to `schema.yml` for every feature exercised by the sample suite.
- **Coverage** — collectively the samples exercise imports, attributes, injections, `execute`, helper methods, every arithmetic operator, literals, calls, dotted-name references, and assignments.
- **Idempotency** — the three `pass_minimal_event*.yaml` files all originate from the same source but enter the pipeline at three different stages (Python source, `.keter` IR, JSON AST) and produce byte-identical output, demonstrating that the code generator is a pure function of its IR input regardless of which upstream phase produced that IR.

## 11. Deliverable 7 — The Main Method Calls the Code Generator After Parsing

The main entry point is `compiler.py` at the project root:

```python
from tiferet import App

# Create new app (manager) instance.
app = App(dict(
    app_repo_params=dict(
        app_config_file='config.yml',
    )
))

# Load the CLI app instance.
cli = app.load_interface('compiler_cli')

# Run the CLI app.
if __name__ == '__main__':
    cli.run()
```

It loads the `compiler_cli` interface (declared in `config.yml`) which dispatches to the `compile event` feature. That feature — also in `config.yml` — is a sequence of domain events that performs parsing first and codegen **after**:

```yaml
compile:
  event:
    commands:
      - attribute_id: perform_lexical_analysis_event
      - attribute_id: perform_syntactic_analysis_event       # ← parse
      - attribute_id: perform_semantic_analysis_event
      - attribute_id: perform_type_check_event
      - attribute_id: generate_ir_event
      - attribute_id: generate_code_event                    # ← codegen
        params:
          codegen_service: codegen_service
        data_key: codegen
      - attribute_id: optimize_code_event
        params:
          optimizer_service: optimizer_service
        data_key: codegen
      - attribute_id: emit_codegen_result_event              # ← emit YAML
```

Three CLI entry points drive the code generator:

```bash
# End-to-end: source .py → YAML
python compiler.py compile event samples/pass_helper_method_event.py -o out.yaml

# From pre-generated keter IR
python compiler.py compile keter IntermediateRepresentation/samples/pass_helper_method_event.keter -o out.yaml

# From pre-generated JSON AST
python compiler.py compile ast Parser/samples/pass_helper_method_event.json -o out.yaml

# With optimization
python compiler.py compile event samples/pass_multiple_operator_events.py -O O1 -o out.yaml
```

## 12. Schema

`schema.yml` in this directory is the formal target-language definition. Every YAML artifact in `samples/` conforms to it. Key rules:

- Top-level wrapper: `evt_grp` (or `cmd_grp` for commands).
- Imports grouped by category (`core`, `infra`, `app`), collapsing entries that share a module path.
- Events keyed by their lowercase artifact name; each event has `name`, optional `desc`, and optional `attributes`, `injections`, `execute`, `methods` sections.
- `params` / `returns` encoded as compact colon-delimited strings (`name:type:required:default:description` and `type:description`).
- Snippets are always paired `coms` / `stmt` dicts preserving IR statement strings.
- **Empty nodes are omitted entirely** — never serialized as empty lists or empty dicts.

## 13. Summary

The Tiferet code generator is implemented as a set of injectable Tiferet domain events and service utilities, wired together in `config.yml` and executed from `compiler.py`. This folder supplies only the **schema**, **sample outputs**, and this **README** — satisfying the deliverable while keeping the single source of truth in the production code under `src/`.
