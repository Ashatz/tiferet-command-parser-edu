# Tiferet Command Parser — Educational Compiler Front-End

**Repository:** tiferet-command-parser-edu
**Version:** 0.3.2
**Branch:** ece-506-submission
**Framework:** Tiferet (DDD, Domain Events) + Pydantic (AST domain objects)
**Python:** >= 3.10
**Purpose:** Educational compiler for ECE 506 (Compiler Design) — performs lexical scanning, syntactic parsing, semantic analysis, type checking, IR generation, AST-level constant folding, AST-level strength reduction, AST-level return analysis (unreachable-code detection), code generation, and output optimization on Python source files written in the Tiferet framework's Domain Event dialect.

## Architecture

This project has two layers:

1. **Tiferet pipeline layer** (`src/`) — A Tiferet application using Domain Events wired via `config.yml` and executed through the Tiferet CLI context. Handles the full compiler pipeline: lexical analysis, syntactic parsing, semantic analysis, type checking, IR generation, AST-level constant folding, AST-level strength reduction, AST-level return analysis, code generation, and output optimization.
2. **Semantic routines layer** (`SemanticRoutines/`) — A standalone Pydantic-based AST domain model and mapper layer. Consumes the JSON AST output from the Tiferet pipeline and provides typed domain objects for semantic analysis (e.g., symbol table construction, name resolution).

### Bounded Contexts

- **Lexical scanning** (`src/events/lexer.py`) — Source file reading, tokenization via PLY, INDENT/DEDENT injection via `BlockTracker`.
- **Syntactic parsing** (`src/events/parser.py`) — Token stream parsing into a Pydantic AST via PLY yacc with PEMDAS-correct arithmetic precedence.
- **Semantic analysis** (`src/events/semantic.py`, `src/utils/semantic.py`) — Symbol table construction and name resolution from the parsed AST. Standalone domain/mapper copies in `SemanticRoutines/`.
- **Type checking** (`src/events/typecheck.py`, `src/utils/typecheck.py`) — Structural artifact validation and type checking against the symbol table. Validates import groups, section-class name concordance, artifact member types, method signatures, and assignment/operation type compatibility.
- **IR generation** (`src/events/ir.py`) — Walks the parsed AST to produce a keter IR conforming to the schema in `IntermediateRepresentation/schema.txt`.
- **Code generation** (`src/events/codegen.py`, `src/utils/codegen.py`) — Transforms the IR into a structured YAML-conforming output dict via `TiferetGenerator`, conforming to `CodeGen/schema.yml`.
- **AST optimization** (`src/events/optimizer.py`, `src/utils/optimizer.py`) — `FoldConstants` applies `ConstantFolder` (implements `ASTOptimizerService`) to fold constant numeric sub-expressions, and `ReduceStrength` applies `StrengthReducer` (implements `ASTStrengthReducerService`) to rewrite multiplication/division by a power of two into shifts and `x ** 2` into `x * x`. Both run at `-O O1` before IR generation.
- **Return analysis** (`src/events/optimizer.py`, `src/utils/optimizer.py`) — `AnalyzeReturns` applies `ReturnAnalyzer` (implements `ReturnAnalyzerService`) to walk the AST and collect `UNREACHABLE_AFTER_RETURN` warnings for statements that follow a `return` within the same scope. Diagnostic-only (does not mutate the AST). Runs at `-O O1` before IR generation.
- **Output optimization** (`src/events/optimizer.py`, `src/utils/optimizer.py`) — `OptimizeCode` applies `YamlAnchorOptimizer` (implements `OptimizerService`) to deduplicate repeated params/returns for YAML anchor/alias emission at `-O O2`.
- **Output** (`src/events/output.py`, `src/utils/output.py`) — Terminal pipeline stage. The single `EmitResult` domain event dispatches per-stage payload assembly via `ResultPayloadBuilder`, handles console diagnostics via `OutputPrinter`, and writes files via `OutputWriter` / `emit()`.

### Unified Output Event

Every feature terminates in `EmitResult` (`src/events/output.py`). The event resolves a pipeline stage from an explicit `stage` hint or auto-detects from the supplied inputs in priority order **codegen > ir > semantic > parse > scan**. It then:
1. Prints `semantic_errors` via `OutputPrinter.print_semantic_errors` (semantic / codegen stages).
2. Builds the stage-specific payload via `ResultPayloadBuilder.build_<stage>_payload`.
3. For the semantic stage, optionally prints the AST (`include_ast`) and symbol table via `OutputPrinter`.
4. Writes the payload to `output` (when set) via the `emit()` helper and always returns the payload.

### Pipeline (Feature: `scan.event`)

Defined in `config.yml`. Two chained commands:

1. **PerformLexicalAnalysis** — Reads the source file via `tiferet.File`, tokenizes the full text via `LexerService` (which internally uses `BlockTracker` for INDENT/DEDENT injection). Returns `List[TokenAggregate]`.
2. **EmitResult** — Auto-detects the `scan` stage from `tokens` and assembles a `TokensScanned` envelope.

### Pipeline (Feature: `parse.event`)

Defined in `config.yml`. Three chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Parses token stream via `ParserService` (PLY yacc). Produces a `DeclarationAggregate` AST root.
3. **EmitResult** — Auto-detects the `parse` stage from `ast` and assembles a `ParseCompleted` envelope; honors `include_tokens` and `extract`.

### Pipeline (Feature: `semantic.event`)

Defined in `config.yml`. Five chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Same as `parse.event`.
3. **PerformSemanticAnalysis** — Builds symbol table and resolves names from the AST.
4. **PerformTypeCheck** — Runs `TypeChecker` against the AST and symbol table; returns a list of type error descriptors.
5. **EmitResult** — Auto-detects the `semantic` stage; prints `semantic_errors`, omits symbol table/resolution from the payload when errors exist, optionally includes the AST, and invokes `OutputPrinter` for console output.

### Pipeline (Feature: `ir.event`)

Defined in `config.yml`. Nine chained commands:

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Same as `parse.event`.
3. **PerformSemanticAnalysis** — Same as `semantic.event`.
4. **PerformTypeCheck** — Same as `semantic.event`.
5. **AnalyzeReturns** — Applies `ReturnAnalyzer` (injected as `ReturnAnalyzerService`) to the AST and stores `dead_code_warnings` (list of `UNREACHABLE_AFTER_RETURN` warning dicts). Non-mutating; runs before any AST rewrite so warnings reference original source positions.
6. **FoldConstants** — Applies `ConstantFolder` (injected as `ASTOptimizerService`) to fold constant numeric sub-expressions in the AST in place.
7. **ReduceStrength** — Applies `StrengthReducer` (injected as `ASTStrengthReducerService`) to rewrite `x * 2**k` / `x / 2**k` / `x ** 2` into `x << k` / `x >> k` / `x * x`.
8. **GenerateIR** — Walks the (folded and reduced) AST via `IRGenerator` (injected as `IRService`) and produces an `IREventGroup`.
9. **EmitResult** — Auto-detects the `ir` stage; calls `ir.to_keter()` to produce the keter DSL string.

### Pipeline (Feature: `compile.event`)

Defined in `config.yml`. Eleven chained commands (full source-to-YAML pipeline):

1. **PerformLexicalAnalysis** — Same as `scan.event`.
2. **PerformSyntacticAnalysis** — Same as `parse.event`.
3. **PerformSemanticAnalysis** — Same as `semantic.event`.
4. **PerformTypeCheck** — Same as `semantic.event`.
5. **AnalyzeReturns** — Same as `ir.event`.
6. **FoldConstants** — Same as `ir.event`.
7. **ReduceStrength** — Same as `ir.event`.
8. **GenerateIR** — Same as `ir.event`.
9. **GenerateCode** — Walks the IR via `TiferetGenerator` (injected as `CodegenService`) and produces a schema-conforming output dict.
10. **OptimizeCode** — At `-O O2`, applies `YamlAnchorOptimizer` (injected as `OptimizerService`) to deduplicate repeated structures. `-O O0` and `-O O1` pass through unchanged.
11. **EmitResult** — Auto-detects the `codegen` stage; prints `semantic_errors`, prints `dead_code_warnings`, and passes the codegen dict through to `emit()`.

### Pipeline (Feature: `compile.keter`)

Defined in `config.yml`. Four chained commands (keter IR to YAML):

1. **LoadFromKeter** — Reads a `.keter` file and parses it into an `IREventGroup` via `KeterIREventGroup.from_data()`.
2. **GenerateCode** — Same as `compile.event`.
3. **OptimizeCode** — Same as `compile.event`.
4. **EmitResult** — Same as `compile.event`.

### Pipeline (Feature: `compile.ast`)

Defined in `config.yml`. Ten chained commands (JSON AST to YAML):

1. **LoadFromAST** — Reads a JSON AST file and reconstructs the `DeclarationAggregate` via Pydantic `model_validate()`.
2. **PerformSemanticAnalysis** — Same as `semantic.event`.
3. **PerformTypeCheck** — Same as `semantic.event`.
4. **AnalyzeReturns** — Same as `ir.event`.
5. **FoldConstants** — Same as `ir.event`.
6. **ReduceStrength** — Same as `ir.event`.
7. **GenerateIR** — Same as `ir.event`.
8. **GenerateCode** — Same as `compile.event`.
9. **OptimizeCode** — Same as `compile.event` (YAML dedup at `-O O2`).
10. **EmitResult** — Same as `compile.event`.

## Project Structure

```
compiler.py              — Entry point: loads Tiferet CLI app from config.yml
config.yml               — Tiferet app configuration (attrs, features, errors, cli, interfaces)
pyproject.toml           — Project metadata, dependencies (tiferet, ply, pyyaml, pydantic)
PROJECT_PROPOSAL.md      — ECE 506 project proposal
PROJECT_SUMMARY.md       — ECE 506 project summary
README.md                — Project readme

docs/
  guides/
    lexical_spec.md      — Formal lexical specification for all token types
    grammar_spec.md      — Context-free grammar specification
    utils/
      codegen.md         — Code generation utility guide (TiferetGenerator, schema)
      ir.md              — IR generator utility guide (DocstringParser, IRGenerator)
      lexer.md           — Lexer utility guide
      optimizer.md       — Optimizer utilities guide (YamlAnchorOptimizer, ConstantFolder, StrengthReducer)
      output.md          — Output utilities guide (OutputWriter, OutputPrinter, ResultPayloadBuilder, emit)
      parser.md          — Parser utility guide (TiferetParser, AST structure)
      semantic.md        — Semantic analysis utility guide (SymbolTableBuilder, NameResolver)

samples/                 — End-to-end sample Tiferet source files for all pipeline stages (25 files)
  pass_imports_only.py               — Imports-only module (success case)
  pass_minimal_event.py              — Minimal event with no injection (success case)
  pass_minimal_injection_event.py    — Event with service injection (success case)
  pass_multiple_operator_events.py   — Multi-event module with operators (success case)
  pass_helper_method_event.py        — Event with helper method and chained arithmetic (success case)
  pass_constant_folding_event.py     — Event with constant numeric sub-expressions demonstrating constant folding (success case)
  pass_strength_reduction_event.py   — Event demonstrating multiplication/division by a power of two and exponentiation by 2 reduced to shifts and self-multiplication at -O O1 (success case)
  pass_dead_code_after_return.py     — Event demonstrating direct post-return unreachable statements flagged as UNREACHABLE_AFTER_RETURN at -O O1 (success case)
  fail_bare_function.py              — Top-level function outside artifact structure (failure case)
  fail_class_bare_attribute.py       — Class attribute without member artifact (failure case)
  fail_class_bare_method.py          — Class method without member artifact (failure case)
  fail_class_no_section.py           — Class without section artifact (failure case)
  fail_import_no_group.py            — Import without group comment (failure case)
  fail_missing_group_header.py       — Content without top-level header (failure case)
  fail_missing_member_artifact.py    — Member without artifact annotation (failure case)
  fail_unresolved_attribute.py       — Undefined attribute reference (semantic failure)
  fail_unresolved_import.py          — Unresolved import reference (semantic failure)
  fail_attribute_is_function.py      — Attribute member is a function declaration (type check failure)
  fail_event_class_mismatch.py       — Section name doesn't match class name (type check failure)
  fail_event_missing_execute.py      — Event class missing execute method (type check failure)
  fail_import_with_class.py          — Import section with non-import statements (type check failure)
  fail_invalid_import_group.py       — Invalid import group name (type check failure)
  fail_method_member_not_func.py     — Method member is not a function (type check failure)
  fail_multiple_artifact_errors.py   — Multiple structural errors (type check failure)
  fail_type_mismatch.py              — Type mismatch in assignment/operation (type check failure)

Scanner/                 — Standalone scanner deliverable (ECE 506 submission)
  LEXICAL_SPEC.md        — Lexical specification document
  SCANNER_PROCESS.md     — Scanner design process document
  lexer.py               — Standalone PLY lexer implementation
  lexer_assets.py        — Standalone lexer token constants and rules
  samples/               — Pre-computed scanner JSON outputs (pass cases)

Parser/                  — Standalone parser deliverable (ECE 506 submission)
  README.md              — Parser documentation
  grammar_specification.md — Grammar specification document
  parser.py              — Standalone PLY yacc parser implementation
  parser_assets.py       — Standalone parser grammar constants and AST builders
  test_parser.py         — Parser unit tests
  samples/               — Pre-computed parser JSON outputs (pass cases)

IntermediateRepresentation/
  schema.txt             — Keter IR schema definition (EventGroup, Events, Params, Returns, etc.)
  samples/               — Pre-computed keter IR outputs (.keter files)

CodeGen/                 — Code generation deliverable (ECE 506 submission)
  schema.yml             — Codegen output schema definition (evt_grp, impt, evts, etc.)
  samples/               — Pre-computed codegen YAML outputs (pass cases)

Optimizer/               — Optimizer deliverable (ECE 506 submission)
  samples/               — Pre-computed optimized YAML outputs with anchor/alias (pass cases)

SemanticRoutines/        — Semantic analysis layer (ECE 506 submission)
  ast_domain.py          — Pydantic AST domain objects (Type, Expression, Declaration, Statement, ParamList)
  ast_mapper.py          — Pydantic AST mapper aggregates with mutation methods
  samples/               — Pre-computed JSON outputs (AST, symbol table, and failure cases)
    pass_imports_only.json
    pass_minimal_event.json
    pass_minimal_injection_event.json
    pass_multiple_operator_events.json
    pass_helper_method_event.json
    pass_constant_folding_event.json
    fail_unresolved_attribute.json
    fail_unresolved_import.json

src/
  __init__.py            — Package exports and version (0.3.2)
  assets/
    __init__.py          — Exports `lexer` and `parser` asset modules
    lexer.py             — Token constants (58 types), rule handlers, RULES mapping dict
    parser.py            — Grammar precedence (PEMDAS hierarchy), AST builder helpers (build_module, build_group, etc.)
  domain/
    __init__.py          — Exports: TypeKind, ExprKind, StatementKind, Type, ParamList, Expression, Declaration, Statement, Token, SymbolKind, Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult, and all IR domain objects
    ast.py               — Pydantic AST domain objects with lineno/col position tracking (TypeKind, ExprKind, StatementKind enums; Type, ParamList, Expression, Declaration, Statement models)
    ir.py                — Pydantic IR domain objects (IRImport, IRImportGroup, IRAttribute, IRInjection, IRParam, IRReturn, IRSnippet, IRExecute, IRMethod, IREvent, IREventGroup, etc.) each with to_keter() serialization
    lexer.py             — Pydantic Token domain object (type, value, lineno, lexpos)
    semantic.py          — Pydantic symbol table domain objects (SymbolKind enum; Symbol, Scope, ResolvedName, UnresolvedName, ResolutionResult models)
    tests/
      test_ast.py        — 13 tests for AST domain object instantiation and validation
      test_ir.py         — 12 tests for IR domain objects and to_keter() output
      test_lexer.py      — 6 tests for Token domain object
      test_semantic.py   — 9 tests for symbol table domain objects
  events/
    __init__.py          — Exports: DomainEvent, TiferetError, a (assets)
    settings.py          — Re-exports DomainEvent, TiferetError from tiferet; imports local assets as `a`
    lexer.py             — Lexer domain event: PerformLexicalAnalysis
    parser.py            — Parser domain event: PerformSyntacticAnalysis
    semantic.py          — Semantic domain event: PerformSemanticAnalysis
    typecheck.py         — Type checking domain event: PerformTypeCheck
    ir.py                — IR domain event: GenerateIR (injects IRService, produces IREventGroup)
    codegen.py           — Codegen domain events: GenerateCode, LoadFromKeter, LoadFromAST
    optimizer.py         — Optimizer domain events: FoldConstants (injects ASTOptimizerService), ReduceStrength (injects ASTStrengthReducerService), AnalyzeReturns (injects ReturnAnalyzerService), OptimizeCode (injects OptimizerService)
    output.py            — Unified output domain event: EmitResult (stage auto-detection, payload dispatch, console + file emission)
    tests/
      test_lexer.py      — 2 tests for PerformLexicalAnalysis
      test_parser.py     — 4 tests for PerformSyntacticAnalysis
      test_ir.py         — 3 tests for GenerateIR
      test_codegen.py    — 4 tests for GenerateCode + LoadFromKeter/AST
      test_optimizer.py  — 14 tests for FoldConstants + ReduceStrength + OptimizeCode + AnalyzeReturns
      test_output.py     — 14 tests for EmitResult (stage detection, per-stage dispatch, overrides, file writes)
  interfaces/
    __init__.py          — Exports: LexerService, ParserService, IRService, CodegenService, OptimizerService, ASTOptimizerService, ASTStrengthReducerService, ReturnAnalyzerService
    lexer.py             — LexerService(Service): abstract `tokenize(text) -> List[TokenAggregate]`
    parser.py            — ParserService(Service): abstract `parse(tokens) -> Dict[str, Any]`
    ir.py                — IRService(Service): abstract `generate(ast, symbol_table) -> IREventGroup`
    codegen.py           — CodegenService(Service): abstract `generate(ir) -> Dict[str, Any]`
    optimizer.py         — OptimizerService: abstract `optimize(codegen)`; ASTOptimizerService: abstract `fold(ast)`; ASTStrengthReducerService: abstract `reduce(ast)`; ReturnAnalyzerService: abstract `analyze(ast) -> List[Dict]`
  mappers/
    __init__.py          — Exports: KeterTransferObject, TokenAggregate/Tok, DeclarationAggregate/Decl, ExpressionAggregate/Expr, StatementAggregate/Stmt, TypeAggregate/Type, ParamListAggregate/ParamList, ScopeAggregate/SymbolScope, IREventGroupAggregate, KeterIREventGroup
    settings.py          — KeterTransferObject base class + KT_* token-type constants (KT_KEYWORD, KT_STRING, KT_IDENT, KT_LPAREN, KT_RPAREN, KT_COMMA) shared by all keter transfer objects
    ast.py               — AST mappers: TypeAggregate, ParamListAggregate, ExpressionAggregate, DeclarationAggregate, StatementAggregate — all with mutation methods and static factories
    ir.py                — IREventGroupAggregate (mutation helpers) + all keter transfer objects (KeterIREventGroup, KeterIREvent, KeterIRMethod, KeterIRAttribute, etc.) consolidated under a single # *** mappers section; references the KT_* constants and KeterTransferObject from .settings; KeterIREventGroup.from_data lazy-imports KeterLexer from ..utils.lexer_keter to avoid a circular package import
    lexer.py             — TokenAggregate: extends Token with factory methods (new, new_indent, new_dedent)
    semantic.py          — ScopeAggregate: extends Scope with static factories (new_module_scope, new_class_scope, new_method_scope) and mutation methods (add_symbol, add_child, remove_child, has_symbol, get_symbol)
    tests/
      test_ir.py         — 4 tests for IREventGroupAggregate mutation helpers
      test_lexer.py      — 9 tests for TokenAggregate mapper
      test_semantic.py   — 9 tests for ScopeAggregate factories and mutation
      test_settings.py   — 13 tests for KeterTransferObject consume/peek/skip_comma/collect_balanced/decode_* helpers
  utils/
    __init__.py          — Exports: ASTTraversal, TiferetLexer, TiferetParser, OutputWriter, OutputPrinter, ResultPayloadBuilder, emit, SymbolTableBuilder, NameResolver, TypeChecker, DocstringParser, IRGenerator, TiferetGenerator, YamlAnchorOptimizer, ConstantFolder, StrengthReducer, ReturnAnalyzer (KeterLexer is intentionally NOT re-exported here; import it directly via `from src.utils.lexer_keter import KeterLexer`)
    settings.py          — ASTTraversal base class providing the shared declaration/statement traversal skeleton for AST transformation passes (traverse_declaration, traverse_statement, transform_expression hook)
    ir.py                — DocstringParser (static RST extraction) + IRGenerator (implements IRService; walks AST via public build_* methods)
    lexer.py             — BlockTracker (INDENT/DEDENT state machine) + TiferetLexer (PLY lexer host implementing LexerService)
    lexer_keter.py       — KeterLexer (minimal lexer for the keter IR DSL) + KETER_KEYWORDS constant; consumed by KeterIREventGroup via a lazy import
    output.py            — OutputWriter (file I/O with format auto-detection), OutputPrinter (AST/symbol-table/error console output), ResultPayloadBuilder (per-stage payload assembly), and emit() helper
    parser.py            — TokenStream (PLY adapter) + ParserBase + TiferetParser (PLY yacc parser implementing ParserService)
    semantic.py          — SymbolTableBuilder (single-pass AST walker for scope/symbol construction) + NameResolver (second-pass name resolution against scope registry)
    typecheck.py         — TypeChecker: AST walker for structural artifact validation and type checking against the symbol table
    codegen.py           — TiferetGenerator (implements CodegenService; walks IR to produce structured YAML-conforming output dict)
    optimizer.py         — YamlAnchorOptimizer (implements OptimizerService; YAML anchor/alias deduplication); ConstantFolder (extends ASTTraversal + ASTOptimizerService; post-order constant folding of numeric AST sub-expressions); StrengthReducer (extends ASTTraversal + ASTStrengthReducerService; post-order rewrite of multiplication/division by a power of two to shifts and `x ** 2` to `x * x`); ReturnAnalyzer (implements ReturnAnalyzerService; non-mutating scope-aware walk that flags statements following a return as `UNREACHABLE_AFTER_RETURN`)
    tests/
      test_ir.py         — 19 tests for DocstringParser and IRGenerator
      test_lexer.py      — 13 tests for TiferetLexer and BlockTracker
      test_lexer_keter.py — 8 tests for KeterLexer tokenization and KETER_KEYWORDS
      test_output.py     — 19 tests for OutputWriter, ResultPayloadBuilder, and emit()
      test_parser.py     — 51 tests for TiferetParser grammar rules and AST structure
      test_semantic.py   — 26 tests for SymbolTableBuilder and NameResolver
      test_codegen.py    — 10 tests for TiferetGenerator
      test_optimizer.py  — 32 tests for YamlAnchorOptimizer + ConstantFolder + StrengthReducer + ReturnAnalyzer
```

## Key Concepts

### AST Domain Model (Pydantic)

The AST is built from Pydantic `BaseModel` classes defined in `src/domain/ast.py` and extended with mutation methods in `src/mappers/ast.py`. This is separate from the Tiferet framework's `schematics`-based DomainObject system.

- **TypeKind** — Enum: `unknown`, `None`, `bool`, `str`, `int`, `float`, `list`, `dict`, `class`, `func`, `artifact`, `module`
- **ExprKind** — Enum: `add`, `sub`, `mul`, `div`, `mod`, `exp`, `shl`, `shr`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `name`, `num_val`, `int_val`, `str_val`, `bool_val`, `assign`, `args_list`, `call`, `import`, `import_as`, `import_multi`, `artifact`, `comment`
- **StatementKind** — Enum: `decl`, `expr`, `if_else`, `for`, `while`, `print`, `return`, `block`, `import`, `import_from`, `artifact`, `comment`, `snippet`

AST nodes use linked-list chaining via `.next` fields (not Python lists). Mapper aggregates provide `set_next()`, `set_left()`, `set_right()`, `set_return_type()`, and static factories like `Decl.new_module_decl()`, `Stmt.new_artifact_stmt()`, `Expr.new_name_expr()`, etc.

### SemanticRoutines Layer

`SemanticRoutines/` contains a parallel copy of the AST domain/mapper files (`ast_domain.py`, `ast_mapper.py`) that mirrors `src/domain/ast.py` and `src/mappers/ast.py` but is importable as a standalone package for semantic analysis work. It also contains:

- `samples/` — Pre-computed JSON outputs from the parse and semantic pipelines, including both pass and fail cases (AST outputs, symbol table outputs, and unresolved name error cases)

### INDENT/DEDENT Injection

The `BlockTracker` class in `src/utils/lexer.py` handles indentation tracking. Unlike the previous `IndentInjector` (which was a separate post-processing step), `BlockTracker` is integrated directly into `TiferetLexer.tokenize()`. It:
- Tracks parenthesis depth to skip multi-line signatures
- Detects CLASS and METHOD boundaries via regex patterns on artifact tokens
- Computes column positions from `lexpos` against the original source text
- Injects `INDENT`/`DEDENT` `TokenAggregate` instances inline during tokenization

### Parser Architecture

`TiferetParser` extends `ParserBase` which implements `ParserService`. Grammar rules are defined as `p_*` methods directly on `TiferetParser` (PLY convention). The parser:
- Receives `List[TokenAggregate]` from the lexer
- Adapts them to PLY via `TokenStream` (wraps each in a `PLYToken`)
- Builds Pydantic `DeclarationAggregate` / `StatementAggregate` / `ExpressionAggregate` AST nodes in semantic actions
- Returns a `DeclarationAggregate` root (module declaration) which is serialized via `.model_dump(exclude_none=True, exclude_unset=True)`

## Key Files

### `src/events/lexer.py`
One domain event:
- **PerformLexicalAnalysis** — Injects `LexerService`, reads source file via `tiferet.File`, tokenizes full text. Returns `List[TokenAggregate]`.

### `src/events/parser.py`
One domain event:
- **PerformSyntacticAnalysis** — Injects `ParserService`, parses tokens into AST. Returns the `DeclarationAggregate` root.

### `src/events/output.py`
One domain event:
- **EmitResult** — Terminal pipeline event. Resolves a stage (explicit `stage` param or auto-detection over `codegen > ir > semantic > parse > scan`), delegates payload assembly to `ResultPayloadBuilder`, prints `semantic_errors` / AST / symbol table via `OutputPrinter`, and writes via `emit()`. Always returns the assembled payload.

### `src/utils/lexer.py`
Two classes:
- **BlockTracker** — State machine for INDENT/DEDENT injection. Tracks paren depth, CLASS/METHOD boundaries, column positions.
- **TiferetLexer** — PLY lexer host implementing `LexerService`. Loads token rules dynamically from `src/assets/lexer.py`. Integrates `BlockTracker` for layout token injection.

### `src/utils/parser.py`
Three classes:
- **TokenStream** — Adapter converting `List[TokenAggregate]` to PLY-compatible token stream.
- **ParserBase** — Base class with shared utilities (`parse_member_kind`, `get_attribute_type`, `p_error`). Loads precedence and tokens from `src/assets/parser.py`.
- **TiferetParser** — Full grammar implementation with `p_*` rule methods. Builds Pydantic AST nodes in semantic actions.

### `src/utils/ir.py`
Two classes:
- **DocstringParser** — Static methods: `strip()`, `parse_param_descriptions()`, `parse_return_descriptions()` for RST docstring extraction.
- **IRGenerator** — Implements `IRService`. Public `build_*` methods walk the `DeclarationAggregate` AST to produce an `IREventGroup`. `encode_expr()` encodes expression nodes to string.

### `src/utils/output.py`
Consolidated output utilities:
- **OutputWriter** (static methods: `detect_format`, `write`, `parse_extract_names`) — File I/O with format auto-detection (`yaml`, `json`, `keter`).
- **OutputPrinter** (static methods) — Console diagnostics: `print_semantic_errors`, `print_ast`, `print_symbol_table`, plus public traversal helpers (`print_declaration`, `print_statement`, `print_expression`, `print_type`, `print_param_list`).
- **ResultPayloadBuilder** (static methods: `build_envelope`, `build_scan_payload`, `build_parse_payload`, `build_semantic_payload`, `build_ir_payload`, `build_codegen_payload`) — Per-stage payload assembly consumed by `EmitResult`.
- **emit(payload, output=None, output_format='auto')** — Module-level helper that writes the payload when `output` is set and always returns the payload.

### `src/utils/typecheck.py`
One class:
- **TypeChecker** — AST walker that performs structural artifact validation and rudimentary type checking against the symbol table. Collects errors as descriptive dicts (with `error_code`, `message`, `lineno`, `col`). Validates import group names, section-class name concordance, artifact member types (attribute must be variable, method must be function), method signatures (self parameter, return type), event `execute` method requirement, and assignment/binary-operation type compatibility.

### `src/utils/codegen.py`
One class:
- **TiferetGenerator** — Implements `CodegenService`. Walks an `IREventGroup` and produces a structured dict conforming to `CodeGen/schema.yml`. Methods: `build_imports()`, `build_events()`, `build_event()`, `build_attributes()`, `build_injections()`, `build_execute()`, `build_methods()`, `build_params()`, `build_returns()`, `build_snippets()`.

### `src/utils/optimizer.py`
Module-level constants:
- **UNREACHABLE_AFTER_RETURN_CODE** / **UNREACHABLE_AFTER_RETURN_MESSAGE** — warning code and message emitted by `ReturnAnalyzer`. Defined under a `# *** constants` section at module scope so tests and consumers can import them directly.

Four classes:
- **YamlAnchorOptimizer** — Implements `OptimizerService`. Deduplicates repeated `params` and `returns` lists across events by sharing Python object references, enabling PyYAML to emit YAML anchors and aliases automatically. Adds a top-level `vars` section when shared structures exist.
- **ConstantFolder** — Implements `ASTOptimizerService`. Post-order walk of the AST that replaces binary arithmetic nodes whose both children are numeric literals (`INT_VAL`, `NUM_VAL`, or `STR_VAL` with numeric content) with a single folded literal. Uses `is_numeric()` to detect foldable operands and `evaluate()` to compute the result.
- **StrengthReducer** — Implements `ASTStrengthReducerService`. Post-order walk of the AST that rewrites three textbook strength-reduction patterns: multiplication by a positive integer power of two (`x * 2**k` → `x << k`, either operand), division by a positive integer power of two (`x / 2**k` → `x >> k`, divisor only), and exponentiation by 2 (`x ** 2` → `x * x` with a deep-copied left operand). Uses `is_power_of_two_literal()` to detect eligible literals, `is_literal_two()` for the `** 2` guard, and `deep_copy_expr()` to keep the synthesized `x * x` tree acyclic. Replacement nodes preserve `lineno` / `col` from the outer expression.
- **ReturnAnalyzer** — Implements `ReturnAnalyzerService`. Non-mutating scope-aware walker that collects `UNREACHABLE_AFTER_RETURN` warning dicts for statements that follow a `return` within the same scope. Transparently flattens `SNIPPET` / `BLOCK` container statements produced by the parser so grouped consecutive statements share a single terminator scope, skips `COMMENT` statements, maintains a scope stack that pushes on `CLASS` / `FUNC` declarations, and treats an `if/else` whose branches both always return as a terminator via `block_always_returns()`.

### `src/events/semantic.py`
One domain event:
- **PerformSemanticAnalysis** — Validates the AST, builds a symbol table via `SymbolTableBuilder`, resolves names via `NameResolver`. Returns dict with `symbol_table` and `resolution`.

### `src/events/typecheck.py`
One domain event:
- **PerformTypeCheck** — Takes the AST and semantic analysis result, runs `TypeChecker` against the symbol table, returns a list of type error descriptors.

### `src/events/ir.py`
One domain event:
- **GenerateIR** — Injects `IRService`; receives `ast` and optional `semantic` from pipeline; calls `ir_service.generate(ast, symbol_table)`; returns `IREventGroup`.

### `src/events/codegen.py`
Three domain events:
- **GenerateCode** — Injects `CodegenService`; walks the IR to produce a schema-conforming output dict.
- **LoadFromKeter** — Reads a `.keter` file and parses it into an `IREventGroup` via `KeterIREventGroup.from_data()`.
- **LoadFromAST** — Reads a JSON AST file and reconstructs the `DeclarationAggregate` via Pydantic `model_validate()`.

### `src/events/optimizer.py`
Four domain events:
- **FoldConstants** — Injects `ASTOptimizerService`; calls `ast_optimizer_service.fold(ast)` and returns the optimized AST root. Runs after type checking and before IR generation at `-O O1`; passes through at `-O O0`.
- **ReduceStrength** — Injects `ASTStrengthReducerService`; calls `ast_strength_reducer_service.reduce(ast)` and returns the reduced AST root. Runs after constant folding and before IR generation at `-O O1`; passes through at `-O O0`.
- **AnalyzeReturns** — Injects `ReturnAnalyzerService`; at `-O O1+` calls `return_analyzer_service.analyze(ast)` and returns the warning list (stored as `dead_code_warnings` in the pipeline); at `-O O0` returns an empty list. Non-mutating; runs after type checking and before `FoldConstants`.
- **OptimizeCode** — Injects `OptimizerService`; at `-O O2` applies YAML anchor/alias deduplication; at `-O O0` and `-O O1` passes through unchanged.

### `src/mappers/settings.py`
Hosts the mapper base class and shared keter token-type constants:
- **KeterTransferObject** — Base class providing shared token-stream traversal helpers (`consume`, `peek`, `skip_comma`, `collect_balanced`, `decode_param_spec`, `decode_return_spec`) for keter parsing.
- **KT_KEYWORD / KT_STRING / KT_IDENT / KT_LPAREN / KT_RPAREN / KT_COMMA** — module-level token-type string constants that mirror the tags emitted by `KeterLexer`. Hosted here so `KeterTransferObject` and the keter transfer objects do not need to import `KeterLexer` at module load time.
### `src/mappers/ir.py`
Two categories of mapper classes, all under a single `# *** mappers` section:
- **IREventGroupAggregate** — Mutable aggregate extending `IREventGroup` with `add_event()` and `add_import_group()` mutation helpers.
- **KeterIR*** — All keter transfer objects (`KeterIRComment`, `KeterIRStatement`, `KeterIRSnippet`, `KeterIRParam`, `KeterIRReturn`, `KeterIRExecute`, `KeterIRMethod`, `KeterIRAttribute`, `KeterIRAssign`, `KeterIRInjection`, `KeterIRImport`, `KeterIRImportGroup`, `KeterIREvent`, `KeterIREventGroup`, plus collection variants). They reference the `KT_*` constants and `KeterTransferObject` from `.settings`. The root entry point `KeterIREventGroup.from_data(text)` lazy-imports `KeterLexer` from `..utils.lexer_keter` inside the method body to avoid triggering the utils package init at mapper module load time.
### `src/utils/lexer_keter.py`
Standalone module (intentionally NOT re-exported from `utils/__init__.py`):
- **KeterLexer** — Minimal lexer that tokenizes a keter DSL string into `(type, value)` tuples. Recognizes keywords, strings, identifiers, and delimiters via class-level token-type attributes whose string values match the `KT_*` constants in `mappers/settings.py`.
- **KETER_KEYWORDS** — Module-level set of DSL constructor names (`EventGroup`, `Events`, `Event`, `Params`, `Return`, etc.) distinguishing keywords from plain identifiers during tokenization.

### `src/utils/semantic.py`
Two classes:
- **SymbolTableBuilder** — Single-pass AST walker that constructs scopes (module, class, method) and populates symbol entries (imports, attributes, parameters, variables).
- **NameResolver** — Second-pass walker that resolves name references in expressions against the built scope registry, producing `ResolutionResult` with resolved and unresolved lists.

### `config.yml`
Tiferet YAML configuration defining:
- **attrs** — Container attributes for all pipeline events and services including `ir_service`, `codegen_service`, `optimizer_service`, `ast_optimizer_service`, `ast_strength_reducer_service`, `return_analyzer_service`, `generate_ir_event`, `generate_code_event`, `fold_constants_event`, `reduce_strength_event`, `analyze_returns_event`, `optimize_code_event`, `load_from_keter_event`, `load_from_ast_event`, `perform_type_check_event`, and the terminal `emit_result_event`
- **features** — `scan.event`, `parse.event`, `semantic.event`, `ir.event`, `compile.event`, `compile.keter`, and `compile.ast`
- **errors** — `TEXT_EXTRACTION_FAILED`, `LEXICAL_ERROR_DETECTED`, `PARSER_NOT_INITIALIZED`, `INVALID_AST_STRUCTURE`, `MISSING_AST`, `TYPE_MISMATCH_ASSIGNMENT`, `TYPE_MISMATCH_OPERATION`, `INVALID_KETER_SYNTAX`, `INVALID_CODEGEN_SCHEMA`, `INVALID_IMPORT_GROUP`, `INVALID_IMPORT_CONTENT`, `ARTIFACT_CLASS_NAME_MISMATCH`, `INVALID_ATTRIBUTE_MEMBER_TYPE`, `ATTRIBUTE_MEMBER_NAME_MISMATCH`, `INVALID_METHOD_MEMBER_TYPE`, `METHOD_MEMBER_NAME_MISMATCH`, `METHOD_MISSING_SELF`, `INVALID_METHOD_RETURN_TYPE`, `EVENT_MISSING_EXECUTE`
- **cli** — `scan event`, `parse event`, `semantic event`, `ir event`, `compile event`, `compile keter`, and `compile ast` commands
- **interfaces** — `compiler` (AppInterfaceContext) and `compiler_cli` (CliContext)

## CLI Usage

```bash
# Scan: tokenize and emit token list
python compiler.py scan event <source_file> -o output.yaml

# Parse: tokenize + parse into AST
python compiler.py parse event <source_file> -o output.json

# Semantic: lex + parse + type check + build symbol table
python compiler.py semantic event <source_file> -o output.json

# IR: lex + parse + semantic + type check + generate keter IR
python compiler.py ir event <source_file> -o output.keter

# Compile: full pipeline from source to structured YAML
python compiler.py compile event <source_file> -o output.yaml

# Compile from keter IR
python compiler.py compile keter <keter_file> -o output.yaml

# Compile from JSON AST
python compiler.py compile ast <ast_file> -o output.yaml
```

## Testing

```bash
python -m pytest src/ -v    # 303 tests total
```

Test breakdown:
- `src/domain/tests/test_ast.py` — 13 tests (AST domain objects)
- `src/domain/tests/test_ir.py` — 12 tests (IR domain objects, to_keter())
- `src/domain/tests/test_lexer.py` — 6 tests (Token domain object)
- `src/domain/tests/test_semantic.py` — 9 tests (Symbol table domain objects)
- `src/mappers/tests/test_ir.py` — 4 tests (IREventGroupAggregate mutation)
- `src/mappers/tests/test_lexer.py` — 9 tests (TokenAggregate mapper)
- `src/mappers/tests/test_semantic.py` — 9 tests (ScopeAggregate factories and mutation)
- `src/mappers/tests/test_settings.py` — 13 tests (KeterTransferObject consume/peek/skip_comma/collect_balanced/decode_* helpers)
- `src/utils/tests/test_ir.py` — 21 tests (DocstringParser + IRGenerator, including SHL/SHR encoding)
- `src/utils/tests/test_lexer.py` — 13 tests (TiferetLexer + BlockTracker)
- `src/utils/tests/test_lexer_keter.py` — 8 tests (KeterLexer tokenization + KETER_KEYWORDS)
- `src/utils/tests/test_output.py` — 19 tests (OutputWriter, ResultPayloadBuilder, emit)
- `src/utils/tests/test_parser.py` — 55 tests (TiferetParser grammar rules, including shift grammar)
- `src/utils/tests/test_semantic.py` — 26 tests (SymbolTableBuilder + NameResolver)
- `src/utils/tests/test_codegen.py` — 10 tests (TiferetGenerator)
- `src/utils/tests/test_optimizer.py` — 32 tests (YamlAnchorOptimizer + ConstantFolder + StrengthReducer + ReturnAnalyzer)
- `src/events/tests/test_lexer.py` — 2 tests (PerformLexicalAnalysis)
- `src/events/tests/test_parser.py` — 4 tests (PerformSyntacticAnalysis)
- `src/events/tests/test_ir.py` — 3 tests (GenerateIR)
- `src/events/tests/test_codegen.py` — 4 tests (GenerateCode + LoadFromKeter/AST)
- `src/events/tests/test_optimizer.py` — 14 tests (FoldConstants + ReduceStrength + OptimizeCode + AnalyzeReturns)
- `src/events/tests/test_output.py` — 14 tests (EmitResult stage detection + dispatch + overrides + file writes)

Tests use `DomainEvent.handle` for event invocation and mock `LexerService`/`ParserService`/`CodegenService`/`OptimizerService`/`ASTOptimizerService`/`ASTStrengthReducerService`/`ReturnAnalyzerService` for isolation. Utility tests validate lexing, parsing, output, codegen, and optimization logic (including return analysis) independently.

## Dependencies

- `tiferet>=1.9.5` — DDD framework (Domain Events, CLI context, DI container)
- `ply>=3.11` — Lexer and parser generator (PLY lex + yacc)
- `pyyaml>=6.0` — YAML output
- `pydantic` — AST domain objects and mappers (BaseModel, Field)
- `pytest>=7.0` — Testing (dev)
