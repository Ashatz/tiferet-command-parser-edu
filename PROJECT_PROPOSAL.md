# Compiler Project – Initial Definition

## 1. Student Information
- **Name:** Andrew Shatz and Lojain Syed
- **Program:** Electrical & Computer Engineering (ECE), College of Engineering, University of Arizona
- **Course:** Compiler Design (ECE 506)
- **Semester / Year:** Spring 2026

## 2. Project Overview
In enterprise software development, domain experts define critical business requirements that must be accurately translated into reliable, testable features by cross-functional teams. Domain-Driven Design (DDD) and Clean Architecture address this challenge by enforcing a shared ubiquitous language and strict separation of concerns. Large language models (LLMs) hold strong potential as enterprise-grade code generators, particularly when guided by structured technical documents and supplied with rich, high-fidelity initial context. Research on token-efficient context provisioning—including patterns inspired by Model Context Protocol (MCP)—shows that LLMs generate significantly fewer errors and exhibit stronger long-horizon reasoning when provided with dense, semantically rich, low-redundancy context at the beginning of a session.

This project builds a domain-specific compiler front-end that analyzes Python code written in the highly structured Tiferet Command pattern—a dialect that embodies DDD and Clean Architecture principles through artifact comments, strict Command inheritance, dependency-injected services, ordered execute snippets, model factories, and domain constants. The compiler parses command modules to extract metadata, execution flow, and dependencies into a consolidated YAML file optimized as token-efficient context material for LLMs. By leveraging YAML anchors (`&`) and aliases (`*`) during an optimization phase, the output dramatically reduces token count while preserving full domain fidelity—enabling more effective AI-driven tasks such as code summarization, refactoring suggestions, test generation, and dependency-aware reasoning.

**Demonstration target:** the error-management command suite from the core Tiferet framework itself (`tiferet/commands/error.py`). This project has the compiler applied to the framework’s own production-grade code, proving immediate practical utility within the Tiferet ecosystem. Among available command suites, the error commands represent the simplest yet most complete bounded context — offering clear artifact structure, moderate validation/dependency complexity, and abundant repetition (service calls, constants, patterns) — making them ideal for validating the full compiler pipeline without unnecessary scope.

The compiler is implemented entirely in **Python**.

## 3. Source Language
- **Name of the source code language:** Tiferet Command dialect (a structured subset of Python 3 with domain-specific idioms: artifact comments `# *** commands`, `# ** command: xxx`, `# * method: execute`, service injections, `verify*` calls, model factories, and constant references)

## 4. Target / Output Language
- **Output of the compiler:** A single, consolidated YAML file per analyzed command suite (e.g., `error_commands_context.yaml`). The YAML is initially emitted in human-readable form, then optimized with anchors/aliases for maximum token efficiency when used as LLM context.
- **Reason for choosing this output language:** YAML is human-readable, structurally rich, and natively supports anchors (`&`) + aliases (`*`) for de-duplication of repeated elements (services, models, constants, validation patterns). Tokenizer benchmarks show YAML with anchors can save 40–55% tokens vs equivalent JSON or raw source when fed to frontier LLMs. The output is designed as high-fidelity context suitable for direct prompt usage or injection into MCP-compatible resource workflows.

## 5. Compiler Features (Planned)
- Lexical analysis (custom recognition of Tiferet artifact comments, keywords like `verify_parameter`, `verify`, `self.xxx_service.`, constant refs, etc.)
- Syntax analysis (AST-based parsing using Python’s built-in `ast` module to extract `Command` classes, `__init__` injections, `execute` method bodies with ordered snippets/comments)
- Semantic analysis (resolve service method calls, model usages, constant references, enforce basic DDD rules like proper service injection and no direct infrastructure coupling)
- Intermediate representation (internal structured data model capturing commands, parameters, validation steps, core logic, dependencies)
- Optimizations (deduplication via YAML anchors/aliases for repeated scalars/structures; optional minification of non-essential prose)
- Code generation (emit verbose YAML → apply optimization pass → final dense YAML using PyYAML)

## 6. Tools and Libraries
- Python 3.10+ standard library (`ast`, `inspect`, `re` for lexical patterns)
- PyYAML (for safe, structured YAML emission with anchor/alias support)
- pytest (for unit/integration testing of each phase)
- No external parser generators (ANTLR/Bison/etc.) — we use Python’s `ast` module directly for syntactic analysis, keeping the project lightweight and educational

## 7. Repository Information
- **Repository hosting service:** GitHub
- **Repository URL:** https://github.com/Ashatz/tiferet-command-parser-edu (public)

## 8. Project Status
- [x] Repository created
- [x] README file added
- [ ] Initial project structure committed  
  (planned: `src/commands/` with `lexer.py`, `parser.py`, `semantic.py`, `intrep.py`, `optimize.py`, `codegen.py`; `tests/`, `samples/` with error commands input)

## 9. Additional Notes
- The project focuses exclusively on the **Command pattern** (no models, contexts, or services yet — keeps scope tight for ECE 506).
- Demonstration input: error-management command suite from the core Tiferet framework (`tiferet/commands/error.py`).
- We plan to create lightweight assets: regex patterns for token/idiom recognition and a small set of domain constants (e.g., error codes) embedded in the command analysis logic.
- The optimization phase draws inspiration from MCP-related research on token-efficient context provisioning, but the tool itself produces static YAML files (not a live MCP server).
- Future extensions (post-course): analysis of Models/Contracts, cross-bounded-context dependencies.
- Collaborators: Andrew Shatz (lead implementation) and Lojain Syed (co-development & testing).