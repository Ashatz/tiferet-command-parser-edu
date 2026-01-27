# tiferet-command-parser-edu

Educational parser and static analysis tool for the Tiferet Command pattern — extracts structured YAML metadata and dependency graphs from domain-driven Python command code. Built for ECE 506: Compiler Design at the University of Arizona.

### Project Abstract

This project develops a domain-specific compiler front-end for analyzing Python code written in the Tiferet framework’s Command pattern — a highly regular dialect that embodies Domain-Driven Design (DDD) principles and Clean Architecture layering. In enterprise software development, domain experts define critical business requirements that must be faithfully translated into features and then reliably implemented, tested, and maintained by cross-functional teams of developers and QA engineers. DDD addresses this challenge by establishing a shared ubiquitous language, which Tiferet realizes through interdependent object-oriented design patterns and a consistent set of guidelines governing their structure and interaction within an application.
This project focuses exclusively on Commands, which reside at the heart of every working application. As illustrated in the [calculator app](https://github.com/greatstrength/tiferet-calculator-app) example, Commands encapsulate operations essential for both core application behavior and feature workflow orchestration, while interacting with infrastructural components to persist, distribute, or transform model state. The Command dialect is defined by a precise syntactic language: artifact comments serve as domain documentation, Command inheritance establishes the service boundary, execute methods orchestrate transactional use cases, injected service contracts provide infrastructure abstraction, model factories act as aggregate roots, and error codes form part of the shared domain vocabulary.
The compiler applies lexical analysis to recognize Tiferet idioms (artifact sections, import groups, validation keywords), syntactic analysis via Python’s ast module to extract Command classes and ordered execute snippets, and semantic analysis to resolve dependencies while enforcing DDD architectural rules. The resulting intermediate representation — a single consolidated YAML file capturing parameter contracts, ordered execution flow, and aggregated domain dependencies — serves as a semantically rich context store. This IR enables enhanced, AI-assisted generation of high-quality dependency visualizations in Mermaid and Graphviz DOT formats, where the depth of context significantly improves layout clarity, edge labeling, and relational insight beyond what generic extraction can achieve. The implementation demonstrates core compiler design methodologies — phase separation, domain-specific tokenization, AST-based analysis, semantic resolution, and multi-target code generation — applied to a production DDD framework. A public repository (tiferet-command-parser-edu) documents the process for the Command pattern only, serving as an educational artifact while preserving broader extensions for future inquiry.

### Project Overview (1.5–2 page summary)

For the full project narrative — including detailed motivation (DDD & Clean Architecture context), scope, deliverables, compiler pipeline, educational outcomes, and future inquiry — see:

→ **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**

### Quick Start / Usage

(Coming soon — once the prototype is ready)

### Development Status

- **Current branch**: `prototype/command-parser`  
- **Focus**: Command pattern only (error-management suite as demonstration)  
- **License**: MIT (educational reuse encouraged)

### Acknowledgments

ECE 506: Compiler Design – University of Arizona  
Inspired by real-world DDD frameworks and the need for tools that preserve domain fidelity in large codebases.

Questions, feedback, or contributions welcome — especially for educational purposes!
