# ECE 506 Final Project Overview  
**Domain-Driven Parser for Tiferet Command Dialect: Metadata Extraction and Token-Efficient Context Generation**

## Motivation

In enterprise software development, domain experts define critical business requirements that must be accurately translated into reliable, testable features by cross-functional teams. Domain-Driven Design (DDD) and Clean Architecture address this challenge by enforcing a shared ubiquitous language and strict separation of concerns. Large language models (LLMs) hold strong potential as enterprise-grade code generators, particularly when guided by structured technical documents and supplied with rich, high-fidelity initial context. Research on token-efficient context provisioning—including patterns inspired by Model Context Protocol (MCP)—shows that LLMs generate significantly fewer errors and exhibit stronger long-horizon reasoning when provided with dense, semantically rich, low-redundancy context at the beginning of a session.

The Tiferet framework realizes this ubiquitous language through a rigorously layered object model aligned with Clean Architecture principles. At its core lies the Command pattern — the primary transactional use-case handler that orchestrates application behavior and feature workflows. This project treats the Tiferet Command dialect as a first-class input language: artifact comments serve as domain documentation, Command inheritance defines service boundaries, execute methods capture ordered business logic, injected service contracts abstract infrastructure, model factories act as aggregate gateways, and domain constants form part of the shared vocabulary.

## Project Scope

The compiler front-end processes Python source files written in the Tiferet Command dialect.

**Demonstration target:** the error-management command suite from the core Tiferet framework itself (`tiferet/commands/error.py`).  

This project applies the compiler directly to the framework’s own production-grade code, demonstrating immediate practical utility within the Tiferet ecosystem. Among available command suites, the error commands represent the simplest yet most complete bounded context — offering clear artifact structure, moderate validation and dependency complexity, and abundant repetition (service calls, constants, validation patterns) — making them ideal for validating the full compiler pipeline without unnecessary scope expansion.

## Deliverables

1. Public educational repository (`tiferet-command-parser-edu`) documenting the development process for the Command pattern only. It includes:
   - Source code for the lexer, AST-based extractor, dependency resolver, YAML serializer, and optimization phase
   - README with sequential development phases, usage instructions, and sample outputs
   - Sample input (core framework error commands) and outputs (optimized YAML context file)
   - MIT license for educational reuse

2. Primary output produced by the tool:
   - A single consolidated YAML file (`error_commands_context.yaml`) capturing:
     - Per-command metadata (parameters, descriptions, return types)
     - Ordered execution flow (snippets preserving comment intent and statement sequencing)
     - Aggregated domain dependencies (`used_service_methods`, `used_constants`, `used_domain_objects`)
     - Optimized structure using YAML anchors (`&`) and aliases (`*`) for maximum token efficiency when used as LLM context material

No graph visualizations (Mermaid or Graphviz) are produced — focus remains solely on high-fidelity, low-token-count context suitable for LLM/agentic workflows.

## Compiler Pipeline Summary

- Lexical analysis → tokenization of Tiferet’s ubiquitous language elements (artifact comments, verify calls, service refs, constants)
- Syntactic analysis → AST traversal to preserve domain intent in `execute` bodies
- Semantic analysis → dependency resolution and basic DDD rule enforcement
- Intermediate representation → structured data model
- Optimization → deduplication via YAML anchors/aliases + optional prose minification
- Code generation → final dense YAML output using PyYAML

## Educational Outcomes

The project demonstrates core compiler design methodologies — phase separation, domain-specific tokenization, AST-based structural analysis, semantic dependency tracking, and output optimization — applied to extract and externalize the ubiquitous language of a production DDD framework. It illustrates how compiler techniques can serve as a bridge between structured domain code and modern LLM research, particularly in token-efficient context provisioning.

## Future Inquiry

- Analysis of Contracts (service interfaces) and Models (domain entities)  
- Broader intra-bounded-context dependency tracking  
- Integration with live MCP resource servers  
- Cross-language translation studies (especially C# and C++)
