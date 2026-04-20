# Utilities – Output

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`src/utils/output.py` consolidates every pipeline-terminal output concern behind a single module. It exposes four public surfaces:

- **`OutputWriter`** — file I/O with format auto-detection (YAML, JSON, keter).
- **`OutputPrinter`** — console diagnostics (semantic errors, AST post-order traversal, symbol table).
- **`ResultPayloadBuilder`** — per-stage payload builders (scan, parse, semantic, ir, codegen).
- **`emit(payload, output=None, output_format='auto')`** — convenience helper that writes the payload when `output` is set and always returns it.

These utilities are consumed by the unified `EmitResult` domain event in `src/events/output.py`, which replaces the former `EmitScanResult`, `EmitParseResult`, `EmitSemanticResult`, `EmitIRResult`, and `EmitCodegenResult` events.

**File:** `src/utils/output.py`

## OutputWriter

Static utility for writing pipeline result payloads to file.

### Static Methods

**`detect_format(output_path, output_format='auto') -> str`**

Resolves the output format. If `output_format` is `'auto'`, detects from file extension:
- `.json` → `'json'`
- `.keter` → `'keter'`
- anything else → `'yaml'`

An explicit `output_format` is returned unchanged.

**`write(result, output_path, output_format='auto') -> None`**

Writes a payload to file:
- **JSON** — `json.dump()` with `indent=2`
- **YAML** — `yaml.dump()` with `default_flow_style=False, sort_keys=False`
- **Keter** — writes the string verbatim (or `str(result)` when not a string)

```python
from src.utils import OutputWriter

# Auto-detect format from extension.
OutputWriter.write(result_dict, 'output.json')   # → JSON
OutputWriter.write(result_dict, 'output.yaml')   # → YAML
OutputWriter.write(keter_text,  'output.keter')  # → plain text
```

**`parse_extract_names(extract) -> Optional[List[str]]`**

Parses a comma-separated extract filter string into a list of stripped names. Returns `None` when the input is falsy.

```python
OutputWriter.parse_extract_names('add_error, get_error')
# ['add_error', 'get_error']
```

## OutputPrinter

Static utility for console diagnostics. Used by `EmitResult` for semantic errors, AST post-order traversal, and symbol table output.

### Static Methods

- **`print_semantic_errors(errors)`** — Prints each descriptor in the list (`error_code`, `scope_path`, `message`, optional `lineno`/`col`). No-op when the list is empty/`None`.
- **`print_ast(ast)`** — Prints the module `Declaration` tree with a section header, using post-order traversal (children before parent).
- **`print_symbol_table(symbol_table)`** — Prints the scope hierarchy produced by `SymbolTableBuilder.build()` with symbols and children per scope.
- **`print_declaration`**, **`print_statement`**, **`print_expression`**, **`print_type`**, **`print_param_list`** — Public recursive helpers used by `print_ast` and available directly for custom traversal scenarios.

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

## ResultPayloadBuilder

Static utility that builds the per-stage result payloads consumed by `EmitResult`.

### Static Methods

- **`build_envelope(event_type, source_file)`** — Shared `{event_type, timestamp, source_file}` envelope used by the scan, parse, and semantic stages.
- **`build_scan_payload(source_file, tokens)`** — `TokensScanned` envelope with serialized `tokens` list and `token_count`.
- **`build_parse_payload(source_file, ast, tokens=None, extract=None, include_tokens=False)`** — `ParseCompleted` envelope with serialized AST; optionally includes `extracted_artifacts` and the tokens list.
- **`build_semantic_payload(source_file, semantic, semantic_errors=None, ast=None, tokens=None, include_tokens=False, include_ast=False)`** — `SemanticAnalysisCompleted` envelope. When `semantic_errors` is non-empty, `symbol_table` and `resolution` are omitted from the payload.
- **`build_ir_payload(ir)`** — Delegates to `ir.to_keter()` and returns the keter DSL string.
- **`build_codegen_payload(codegen, semantic_errors=None)`** — Passes the codegen dict through unchanged.

## emit()

Module-level convenience helper.

```python
from src.utils import emit

# Always returns the payload; also writes to file when `output` is provided.
payload = emit({'event_type': 'TokensScanned', ...}, output='result.yaml')
```

`output_format` defaults to `'auto'` and honors the extension of `output` when detection is requested.

## Relationship to EmitResult

`EmitResult` (`src/events/output.py`) is the single terminal event for every feature in `config.yml`. Its `execute()` method:

1. Resolves a pipeline stage from an explicit `stage` hint or auto-detects from supplied inputs in priority order **codegen > ir > semantic > parse > scan**.
2. Prints `semantic_errors` via `OutputPrinter.print_semantic_errors` for the semantic and codegen stages.
3. Delegates payload assembly to the matching `ResultPayloadBuilder.build_<stage>_payload`.
4. For the semantic stage (when no output file is set), optionally prints the AST via `OutputPrinter.print_ast` and prints the symbol table via `OutputPrinter.print_symbol_table`.
5. Invokes `emit(payload, output, output_format)` to write to file and always returns the payload.

## Testing

Output utility tests: `src/utils/tests/test_output.py` (19 tests covering `OutputWriter`, `ResultPayloadBuilder`, and `emit`).

Event-level dispatch tests: `src/events/tests/test_output.py` (14 tests covering stage auto-detection, per-stage dispatch, explicit stage overrides, and file writes).

```bash
python -m pytest src/utils/tests/test_output.py src/events/tests/test_output.py -v
```

## Related reading

- [parser.md](parser.md) — TiferetParser utility (produces the AST consumed by `OutputPrinter.print_ast`)
- [semantic.md](semantic.md) — SymbolTableBuilder / NameResolver (produce the symbol tables consumed by `OutputPrinter.print_symbol_table`)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
