"""Output Domain Events

This module defines the terminal pipeline event ``EmitResult``, which
consolidates the previous per-stage emit events (scan/parse/semantic/ir/
codegen) into a single conditional event. It dispatches to the
appropriate ``ResultPayloadBuilder`` based on the supplied inputs (or an
explicit ``stage`` hint), prints diagnostic console output via
``OutputPrinter``, and writes the payload to a file when ``output`` is
set via the shared ``emit()`` helper.
"""

# *** imports

# ** core
from typing import Any, Dict, List, Optional

# ** app
from ..domain.ir import IREventGroup
from ..mappers import TokenAggregate, Decl
from ..utils.output import (
    OutputPrinter,
    ResultPayloadBuilder,
    emit,
)
from .settings import DomainEvent

# *** events

# ** event: emit_result
class EmitResult(DomainEvent):
    '''
    Terminal pipeline event that assembles a stage-appropriate result
    payload, prints any diagnostic console output, and optionally writes
    the payload to a file. Replaces the five per-stage emit events
    (EmitScanResult, EmitParseResult, EmitSemanticResult, EmitIRResult,
    EmitCodegenResult).
    '''

    # * method: execute
    def execute(self,
            stage: Optional[str] = None,
            source_file: Optional[str] = None,
            tokens: Optional[List[TokenAggregate]] = None,
            ast: Optional[Decl] = None,
            semantic: Optional[Dict[str, Any]] = None,
            semantic_errors: Optional[List[Dict[str, Any]]] = None,
            dead_code_warnings: Optional[List[Dict[str, Any]]] = None,
            ir: Optional[IREventGroup] = None,
            codegen: Optional[Dict[str, Any]] = None,
            extract: Optional[str] = None,
            include_tokens: bool = False,
            include_ast: bool = False,
            output: Optional[str] = None,
            output_format: str = 'auto',
            **kwargs,
        ) -> Any:
        '''
        Assemble and emit the pipeline result payload.

        :param stage: Optional explicit stage hint (``'scan'``, ``'parse'``,
            ``'semantic'``, ``'ir'``, or ``'codegen'``). When ``None``, the
            stage is auto-detected from the supplied inputs.
        :type stage: Optional[str]
        :param source_file: Original source file path.
        :type source_file: Optional[str]
        :param tokens: Optional list of token aggregates from
            ``PerformLexicalAnalysis``.
        :type tokens: Optional[List[TokenAggregate]]
        :param ast: Optional parsed AST from ``PerformSyntacticAnalysis``.
        :type ast: Optional[Decl]
        :param semantic: Optional semantic analysis result from
            ``PerformSemanticAnalysis``.
        :type semantic: Optional[Dict[str, Any]]
        :param semantic_errors: Optional list of type check error descriptors.
        :type semantic_errors: Optional[List[Dict[str, Any]]]
        :param dead_code_warnings: Optional list of dead-code warning
            descriptors from ``AnalyzeReturns``.
        :type dead_code_warnings: Optional[List[Dict[str, Any]]]
        :param ir: Optional IREventGroup from ``GenerateIR``.
        :type ir: Optional[IREventGroup]
        :param codegen: Optional codegen dict from ``GenerateCode`` /
            ``OptimizeCode``.
        :type codegen: Optional[Dict[str, Any]]
        :param extract: Comma-separated extract filter string (parse stage).
        :type extract: Optional[str]
        :param include_tokens: If truthy, include tokens in the payload.
        :type include_tokens: bool
        :param include_ast: If truthy, include the AST in the semantic payload.
        :type include_ast: bool
        :param output: Optional output file path.
        :type output: Optional[str]
        :param output_format: Output format (``'yaml'``, ``'json'``,
            ``'keter'``, or ``'auto'``).
        :type output_format: str
        :return: The assembled payload (dict or keter string).
        :rtype: Any
        '''

        # Resolve the stage, falling back to auto-detection.
        resolved_stage = stage or EmitResult.detect_stage(
            tokens=tokens,
            ast=ast,
            semantic=semantic,
            ir=ir,
            codegen=codegen,
        )

        # Verify a stage could be resolved.
        self.verify(
            expression=resolved_stage is not None,
            error_code='MISSING_EMIT_INPUT',
            message='EmitResult requires at least one of: tokens, ast, semantic, ir, codegen',
        )

        # Print semantic/type errors shared by the semantic and codegen stages.
        if resolved_stage in ('semantic', 'codegen'):
            OutputPrinter.print_semantic_errors(semantic_errors)

        # Print dead-code warnings on any stage that can carry them.
        if resolved_stage in ('semantic', 'ir', 'codegen'):
            OutputPrinter.print_dead_code_warnings(dead_code_warnings)

        # Assemble the stage-appropriate payload.
        payload = EmitResult.build_payload(
            stage=resolved_stage,
            source_file=source_file,
            tokens=tokens,
            ast=ast,
            semantic=semantic,
            semantic_errors=semantic_errors,
            dead_code_warnings=dead_code_warnings,
            ir=ir,
            codegen=codegen,
            extract=extract,
            include_tokens=include_tokens,
            include_ast=include_ast,
        )

        # Emit diagnostic console output for the semantic stage when not writing to file.
        if resolved_stage == 'semantic' and not output:
            if include_ast and isinstance(ast, Decl):
                OutputPrinter.print_ast(ast)
            if not semantic_errors and semantic is not None:
                OutputPrinter.print_symbol_table(semantic.get('symbol_table', {}))

        # Delegate the file write (if any) and return the payload.
        return emit(payload, output=output, output_format=output_format)

    # * method: detect_stage (static)
    @staticmethod
    def detect_stage(
            tokens: Optional[List[TokenAggregate]] = None,
            ast: Optional[Decl] = None,
            semantic: Optional[Dict[str, Any]] = None,
            ir: Optional[IREventGroup] = None,
            codegen: Optional[Dict[str, Any]] = None,
        ) -> Optional[str]:
        '''
        Infer the pipeline stage from which inputs are populated.
        The order (codegen > ir > semantic > parse > scan) matches the
        feature chain ordering in ``config.yml`` so the latest stage
        present wins.

        :param tokens: Optional list of token aggregates.
        :type tokens: Optional[List[TokenAggregate]]
        :param ast: Optional parsed AST.
        :type ast: Optional[Decl]
        :param semantic: Optional semantic analysis result.
        :type semantic: Optional[Dict[str, Any]]
        :param ir: Optional IREventGroup.
        :type ir: Optional[IREventGroup]
        :param codegen: Optional codegen output dict.
        :type codegen: Optional[Dict[str, Any]]
        :return: The detected stage name, or ``None`` if no inputs supplied.
        :rtype: Optional[str]
        '''

        # Most-complete stage wins.
        if codegen is not None:
            return 'codegen'
        if ir is not None:
            return 'ir'
        if semantic is not None:
            return 'semantic'
        if ast is not None:
            return 'parse'
        if tokens is not None:
            return 'scan'

        # No stage could be detected.
        return None

    # * method: build_payload (static)
    @staticmethod
    def build_payload(
            stage: str,
            source_file: Optional[str] = None,
            tokens: Optional[List[TokenAggregate]] = None,
            ast: Optional[Decl] = None,
            semantic: Optional[Dict[str, Any]] = None,
            semantic_errors: Optional[List[Dict[str, Any]]] = None,
            dead_code_warnings: Optional[List[Dict[str, Any]]] = None,
            ir: Optional[IREventGroup] = None,
            codegen: Optional[Dict[str, Any]] = None,
            extract: Optional[str] = None,
            include_tokens: bool = False,
            include_ast: bool = False,
        ) -> Any:
        '''
        Dispatch to the per-stage payload builder in ``ResultPayloadBuilder``.

        :param stage: Resolved pipeline stage.
        :type stage: str
        :param source_file: Original source file path.
        :type source_file: Optional[str]
        :param tokens: Optional list of token aggregates.
        :type tokens: Optional[List[TokenAggregate]]
        :param ast: Optional parsed AST.
        :type ast: Optional[Decl]
        :param semantic: Optional semantic analysis result.
        :type semantic: Optional[Dict[str, Any]]
        :param semantic_errors: Optional list of type check error descriptors.
        :type semantic_errors: Optional[List[Dict[str, Any]]]
        :param ir: Optional IREventGroup.
        :type ir: Optional[IREventGroup]
        :param codegen: Optional codegen output dict.
        :type codegen: Optional[Dict[str, Any]]
        :param extract: Optional extract filter string.
        :type extract: Optional[str]
        :param include_tokens: If truthy, include tokens in the payload.
        :type include_tokens: bool
        :param include_ast: If truthy, include the AST in the semantic payload.
        :type include_ast: bool
        :return: The assembled payload.
        :rtype: Any
        '''

        # Dispatch to the appropriate builder for the resolved stage.
        if stage == 'scan':
            return ResultPayloadBuilder.build_scan_payload(
                source_file=source_file,
                tokens=tokens,
            )

        if stage == 'parse':
            return ResultPayloadBuilder.build_parse_payload(
                source_file=source_file,
                ast=ast,
                tokens=tokens,
                extract=extract,
                include_tokens=include_tokens,
            )

        if stage == 'semantic':
            return ResultPayloadBuilder.build_semantic_payload(
                source_file=source_file,
                semantic=semantic or {},
                semantic_errors=semantic_errors,
                dead_code_warnings=dead_code_warnings,
                ast=ast,
                tokens=tokens,
                include_tokens=include_tokens,
                include_ast=include_ast,
            )

        if stage == 'ir':
            return ResultPayloadBuilder.build_ir_payload(ir)

        if stage == 'codegen':
            return ResultPayloadBuilder.build_codegen_payload(
                codegen=codegen,
                semantic_errors=semantic_errors,
                dead_code_warnings=dead_code_warnings,
            )

        # Unknown stage — return None (should be unreachable in practice).
        return None
