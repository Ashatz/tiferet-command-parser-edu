# Utilities – ScanOutputWriter

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`ScanOutputWriter` is a static utility for writing pipeline result payloads to file. It supports YAML, JSON, and keter DSL output formats with auto-detection from file extension.

**File:** `src/utils/output.py`


## Static Methods

### `detect_format(output_path, output_format='auto') -> str`

Resolves the output format. If `output_format` is `'auto'`, detects from the file extension:
- `.json` → `'json'`
- `.keter` → `'keter'`
- Anything else → `'yaml'`

If `output_format` is explicitly provided, returns it unchanged.

### `write(result, output_path, output_format='auto') -> None`

Writes a result payload to file:
- **JSON** — `json.dump()` with `indent=2`
- **YAML** — `yaml.dump()` with `default_flow_style=False, sort_keys=False`
- **Keter** — writes as plain text (string or `str()` conversion)

```python
from src.utils import ScanOutputWriter

# Auto-detect format from extension
ScanOutputWriter.write(result_dict, 'output.json')   # → JSON
ScanOutputWriter.write(result_dict, 'output.yaml')   # → YAML
ScanOutputWriter.write(keter_text, 'output.keter')    # → plain text
```

### `parse_extract_names(extract) -> Optional[List[str]]`

Parses a comma-separated extract filter string into a list of stripped names. Returns `None` if the input is falsy.

```python
ScanOutputWriter.parse_extract_names('add_error, get_error')
# ['add_error', 'get_error']
```


## Usage in Pipeline

`ScanOutputWriter` is used by all `Emit*Result` domain events across the pipeline:
- `EmitScanResult` — writes token list / metrics
- `EmitParseResult` — writes AST
- `EmitSemanticResult` — writes symbol table and resolution results
- `EmitIRResult` — writes keter IR
- `EmitCodegenResult` — writes codegen output


## Testing

Output utility tests: `src/utils/tests/test_output.py` (11 tests)

```bash
python -m pytest src/utils/tests/test_output.py -v
```


## Related reading

- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
