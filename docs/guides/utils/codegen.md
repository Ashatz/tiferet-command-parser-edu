# Utilities – TiferetGenerator (Code Generation)

**Project:** Tiferet Command Parser — Educational Compiler Front-End
**Version:** 0.3.2

## Overview

`TiferetGenerator` is the concrete implementation of `CodegenService` that walks an `IREventGroup` and produces a structured dict conforming to the `codegen/schema.yml` specification. This is the final stage in the compiler pipeline — it transforms the intermediate representation into a format suitable for downstream code generation or tooling consumption.

**Files:**
- `src/utils/codegen.py` — `TiferetGenerator`
- `src/interfaces/codegen.py` — `CodegenService` abstract interface
- `src/events/codegen.py` — `GenerateCode` and `OptimizeCode` domain events
- `src/events/output.py` — `EmitResult` (terminal pipeline event)


## CodegenService Interface

```python
class CodegenService(Service):
    @abstractmethod
    def generate(self, ir: IREventGroup) -> Dict[str, Any]:
        '''Transform an IREventGroup into a schema-conforming output dict.'''
        raise NotImplementedError()
```


## TiferetGenerator

### Generation Process

The `generate()` method builds a top-level `evt_grp` dict:

1. **Module metadata** — `name` and optional `desc` from the IR root
2. **Imports** — `build_imports()` produces an `impt` dict keyed by category (`core`, `app`, `infra`), each containing a list of `{src, tgts}` dicts. Imports sharing the same `module_path` are collapsed.
3. **Events** — `build_events()` produces an `evts` dict keyed by artifact name, each containing the event structure

### Event Structure

Each event dict contains:
- `name` — class name
- `desc` — docstring (if present)
- `attributes` — list of compact `{name: type}` dicts
- `injections` — list of encoded injection dicts with `name:type:required:default:description` keys and optional `assign` entries
- `execute` — dict with `params`, `returns`, and `snpt` (snippets)
- `methods` — dict keyed by method name, each with `params`, `returns`, `snpt`

### Compact Encoding

Parameters and returns are encoded as colon-delimited strings:
- Params: `name:type:required:default:description`
- Returns: `type_name:description`

Snippets are encoded as `{coms: [...], stmt: [...]}` dicts, where `coms` are comment strings and `stmt` are encoded expression strings.

### Example Output

```yaml
evt_grp:
  name: add_error
  desc: Domain events for error management
  impt:
    core:
      - src: typing
        tgts: [List, Any]
    app:
      - src: .settings
        tgts: [DomainEvent, a]
  evts:
    add_error:
      name: AddError
      desc: Event to add a new error configuration.
      attributes:
        - error_service: ErrorService
      injections:
        - error_service:ErrorService:true:::The error service.:
            assign:
              - target: error_service
                value: error_service
      execute:
        params:
          - id:str:true:::The error identifier.
          - name:str:true:::The error name.
        returns:
          - Error:The created error.
        snpt:
          - coms: [Check if error already exists.]
            stmt: [Assign(exists, Call(self.error_service.exists, id))]
```


## Pipeline Integration

The codegen stage is wired as the `codegen.event` pipeline in `config.yml`:

1. **PerformLexicalAnalysis** — tokenizes source file
2. **PerformSyntacticAnalysis** — parses tokens into AST
3. **PerformSemanticAnalysis** — builds symbol table and resolves names
4. **GenerateIR** — produces `IREventGroup`
5. **GenerateCode** — calls `codegen_service.generate(ir)` → structured dict
6. **OptimizeCode** — at `-O O1` applies YAML anchor/alias deduplication
7. **EmitResult** — auto-detects the `codegen` stage and writes the codegen dict to YAML/JSON via `emit()`

```yaml
# config.yml (attrs section)
codegen_service:
  module_path: src.utils.codegen
  class_name: TiferetGenerator
```


## Testing

Codegen utility tests: `src/utils/tests/test_codegen.py` (10 tests)
Codegen event tests: `src/events/tests/test_codegen.py` (4 tests)

```bash
python -m pytest src/utils/tests/test_codegen.py -v
python -m pytest src/events/tests/test_codegen.py -v
```


## Related reading

- [ir.md](ir.md) — DocstringParser and IRGenerator (upstream, produces the IR consumed by codegen)
- [output.md](output.md) — Unified output utilities (used by `EmitResult` to emit the codegen dict)
- [AGENTS.md](../../../AGENTS.md) — AI agent codebase index
