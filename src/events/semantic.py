"""Semantic Analysis Domain Events"""

# *** imports

# ** core
from datetime import datetime, timezone
from typing import List, Dict, Any

# ** app
from ..mappers import TokenAggregate, Decl
from ..utils import ScanOutputWriter, SymbolTableBuilder, NameResolver
from .settings import DomainEvent, a

# *** events

# ** event: perform_semantic_analysis
class PerformSemanticAnalysis(DomainEvent):
    '''
    Core analytical event that performs semantic analysis on the
    parsed AST, building a symbol table and resolving name references.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Decl,
            source_file: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Build a symbol table from the AST and resolve name references.

        :param ast: The parsed AST DeclarationAggregate from PerformSyntacticAnalysis.
        :type ast: Decl
        :param source_file: The original source file path.
        :type source_file: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Semantic analysis result with symbol_table and resolution.
        :rtype: Dict[str, Any]
        '''

        # Validate that the AST is a DeclarationAggregate.
        self.verify(
            expression=ast and isinstance(ast, Decl),
            error_code='INVALID_AST_STRUCTURE',
            message='Semantic analysis requires a valid Module AST',
            ast_type=str(type(ast)),
        )

        # Build the symbol table from the AST.
        builder = SymbolTableBuilder()
        symbol_table = builder.build(ast)

        # Resolve name references against the symbol table.
        resolver = NameResolver(builder.scopes)
        resolution = resolver.resolve(ast)

        # Return the semantic analysis result.
        return {
            'symbol_table': symbol_table,
            'resolution': resolution.model_dump(exclude_none=True),
        }

# ** event: emit_semantic_result
class EmitSemanticResult(DomainEvent):
    '''
    Final event in the analyze.event pipeline.
    Assembles the result payload with semantic analysis data and delegates to output writer.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['semantic'])
    def execute(self,
            semantic: Dict[str, Any],
            ast: Decl = None,
            tokens: List[TokenAggregate] = None,
            source_file: str = None,
            include_tokens: bool = False,
            include_ast: bool = False,
            output_format: str = 'auto',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble and emit the semantic analysis result payload.

        :param semantic: The semantic analysis result from PerformSemanticAnalysis.
        :type semantic: Dict[str, Any]
        :param ast: The parsed AST DeclarationAggregate (optional, included if include_ast is True).
        :type ast: Decl
        :param tokens: List of token aggregates from PerformLexicalAnalysis.
        :type tokens: List[TokenAggregate]
        :param source_file: Original source file path.
        :type source_file: str
        :param include_tokens: If truthy, include tokens in the output.
        :type include_tokens: bool
        :param include_ast: If truthy, include the AST in the output.
        :type include_ast: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param output: File path to write output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The assembled semantic analysis result payload.
        :rtype: Dict[str, Any]
        '''

        # Build base payload with semantic analysis data.
        result = {
            'event_type': 'SemanticAnalysisCompleted',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'symbol_table': semantic.get('symbol_table', {}),
            'resolution': semantic.get('resolution', {}),
        }

        # Include AST if requested.
        if include_ast and ast and isinstance(ast, Decl):
            result['ast'] = ast.model_dump(exclude_none=True, exclude_unset=True)

        # Include tokens if requested.
        if include_tokens:
            result['tokens'] = [token.model_dump() for token in tokens] if tokens else []
            result['token_count'] = len(tokens) if tokens else 0

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)
            return ''
        else:
            # Otherwise, return the result payload.
            return result
