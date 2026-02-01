# tiferet-command-parser-edu

Educational compiler front-end for the Tiferet Command pattern — extracts token-efficient, LLM-optimized YAML context from domain-driven Python command code.  
Built for ECE 506: Compiler Design at the University of Arizona.

### Project Abstract

This project develops a domain-specific compiler front-end that analyzes Python code written in the highly structured **Tiferet Command dialect** — a production-ready pattern embodying Domain-Driven Design (DDD) and Clean Architecture principles. The dialect uses artifact comments, strict Command inheritance, dependency-injected services, ordered execute snippets, model factories, and domain constants to form a precise, ubiquitous-language-aligned representation of business use cases.

The compiler performs lexical, syntactic, and semantic analysis on command modules, producing a single consolidated YAML file optimized as high-fidelity, low-token-count context material for large language models (LLMs). By leveraging YAML anchors (`&`) and aliases (`*`) in an optimization phase, the output dramatically reduces token consumption (often 40–55% savings vs raw source or naive JSON) while preserving full semantic density — enabling more reliable AI-driven tasks such as code summarization, refactoring suggestions, test generation, and dependency-aware reasoning.

Research on token-efficient context provisioning — including patterns inspired by Model Context Protocol (MCP) — shows that LLMs exhibit significantly fewer errors and stronger long-horizon reasoning when given dense, semantically rich initial context. This tool explores how compiler techniques can extract and recontextualize structured DDD code to better serve modern LLM/agentic workflows.

### Why the Error Command Suite?

The parser targets the error-management command suite located directly in the core Tiferet framework (`tiferet/commands/error.py`).  

This demonstration applies the compiler to the framework’s own production-grade code, illustrating practical utility within the Tiferet ecosystem. Among available command suites, the error commands represent the simplest yet most complete bounded context: clear artifact structure, moderate validation and dependency complexity, and abundant repetition (service calls, constants, validation patterns) — making them ideal for validating the full compiler pipeline (lexical recognition, AST extraction, semantic resolution, and YAML optimization) without unnecessary scope.

### Key Deliverables
- Single optimized YAML file per command suite (e.g. `error_commands_context.yaml`)
- No graph outputs (Mermaid / Graphviz removed in favor of pure context optimization)

### Project Documentation
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** — Detailed course narrative: motivation, scope, pipeline, educational outcomes, future inquiry
- **[PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md)** — Completed ECE 506 initial project definition template

### Development Status
- **Current branch**: `main` (or `prototype/command-parser` during development)
- **Focus**: Command pattern only (error suite demonstration)
- **License**: MIT (educational reuse encouraged)

### Acknowledgments
ECE 506: Compiler Design – University of Arizona  
Inspired by the Tiferet framework[](https://github.com/greatstrength/tiferet) and research into token-efficient LLM context provisioning.

Questions, feedback, or contributions welcome — especially for educational purposes!