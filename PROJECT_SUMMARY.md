# ECE 506 Final Project Overview  
**Domain-Driven Parser for Tiferet Command Dialect: Metadata Extraction and Dependency Visualization**

## Motivation

In large-scale enterprise software development, domain experts articulate critical business requirements that must be faithfully translated into reliable, testable features — then consistently implemented, validated, and maintained by cross-functional teams of software engineers and QA professionals. Domain-Driven Design (DDD) confronts this core challenge head-on by establishing and rigorously enforcing a shared ubiquitous language that bridges the gap between business intent and technical implementation.

The Tiferet framework embodies this ubiquitous language through a meticulously layered object model aligned with Clean Architecture principles. It cleanly separates the user interface / application layer, the domain/business layer, and the infrastructure layer. At the very center of the domain/business layer resides the Command pattern — the principal transactional use-case handler that drives application behavior and feature orchestration.

This project treats the Tiferet Command dialect as its own first-class input language: artifact comments serve as domain documentation, Command inheritance establishes the application service boundary, execute methods orchestrate use-case logic, injected service contracts abstract infrastructure concerns, model factories act as gateways to aggregate roots, and error codes form an integral part of the shared domain vocabulary. By constructing a domain-specific compiler front-end, the tool extracts, formalizes, and visualizes this embedded DDD dialect — creating a parser that speaks the same ubiquitous language as the code it analyzes and thereby empowering enterprise teams to maintain significantly stronger fidelity between business requirements and production code.

## Project Scope

The compiler front-end processes Python source files written in the Tiferet Command dialect. The primary demonstration target is the error-management command suite (`tiferet/commands/error.py`), which contains seven commands that together form a coherent bounded context for structured error handling.

The tool applies:
- lexical analysis (recognizing Tiferet idioms such as artifact sections, import groups, and validation keywords),
- syntactic analysis (via Python’s `ast` module to extract `Command` classes and ordered `execute` snippets),
- semantic analysis (resolving service dependencies, model factories, constant references, and enforcing DDD architectural rules).

## Deliverables

1. Public educational repository (`tiferet-command-parser-edu`) documenting the development process for the Command pattern only. It includes:
   - Source code for the lexer, AST-based extractor, dependency resolver, YAML serializer, and graph generator
   - README with sequential development phases, usage instructions, and sample outputs
   - Sample input (error commands excerpt) and outputs (YAML metadata + graphs)
   - MIT license for educational reuse

2. Two main outputs produced by the tool:
   - A single consolidated YAML file (`error_commands_metadata.yaml`) capturing:
     - Per-command metadata (ubiquitous-language-aligned parameters, descriptions, return types)
     - Ordered execution flow (snippets preserving comment intent and statement sequencing)
     - Aggregated domain dependencies (`used_service_methods`, `used_constants`, `used_domain_objects`)
   - Dependency graphs in two formats:
     - Mermaid markdown (`error_commands_dependency_graph.mmd`)
     - Graphviz DOT (`error_commands_dependency_graph.dot`)
     These visualizations are enhanced by the contextual richness of the YAML intermediate representation, enabling precise edge labeling, layout clarity, and relational insight (with AI-assisted generation as a supporting technique).

## Compiler Pipeline Summary

- Lexical analysis → tokenization of Tiferet’s ubiquitous language elements
- Syntactic analysis → AST traversal to preserve domain intent in `execute` bodies
- Semantic analysis → dependency resolution and DDD rule enforcement
- Intermediate representation & code generation → language-neutral YAML IR + dual-format graph outputs

## Educational Outcomes

The project demonstrates core compiler design methodologies — phase separation, domain-specific tokenization, AST-based structural analysis, semantic dependency tracking, and multi-target output generation — applied to extract and externalize the ubiquitous language of a production DDD framework. It illustrates how compiler techniques can serve as a mirror and guardian of domain modeling fidelity in large systems.

## Future Inquiry

• Analysis of **Contracts** (service interfaces) and **Models** (domain entities)  
• Broader intra-bounded-context dependency tracking  
• Cross-language translation studies (especially C# and C++)
