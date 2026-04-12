"""Parser Domain Events"""

# *** imports

# ** core
from datetime import datetime, timezone
from typing import List, Dict, Any

# ** app
from ..interfaces import ParserService
from ..mappers import TokenAggregate
from ..utils import ScanOutputWriter
from .settings import DomainEvent, a

# *** events

# ** event: perform_syntactic_analysis
class PerformSyntacticAnalysis(DomainEvent):
    '''
    Core analytical event that performs syntactic parsing on the
    tokenized input using the injected ParserService.
    '''

    # * attribute: parser_service
    parser_service: ParserService

    # * init
    def __init__(self, parser_service: ParserService):
        '''
        Initialize with injected parser service.

        :param parser_service: The parser service for syntactic analysis.
        :type parser_service: ParserService
        '''

        # Set the parser service dependency.
        self.parser_service = parser_service

    # * method: execute
    @DomainEvent.parameters_required(['tokens'])
    def execute(self,
            tokens: List[TokenAggregate],
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Parse token stream and produce structured AST.

        :param tokens: List of token aggregates from PerformLexicalAnalysis.
        :type tokens: List[TokenAggregate]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: AST dict with Module root.
        :rtype: Dict[str, Any]
        '''

        # Execute syntactic parsing via the injected parser service.
        ast = self.parser_service.parse(tokens)

        # Validate the AST root structure is a Module.
        self.verify(
            expression=isinstance(ast, dict) and ast.get('type') == 'Module',
            error_code='INVALID_AST_STRUCTURE',
            message='Syntactic parser did not return a valid Module AST',
            ast_type=str(type(ast)),
        )

        # Return the AST for downstream events.
        return ast

# ** event: emit_parse_result
class EmitParseResult(DomainEvent):
    '''
    Final event in the parse.event pipeline.
    Assembles the result payload with syntactic AST and delegates to output writer.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Dict[str, Any],
            tokens: List[TokenAggregate] = None,
            source_file: str = None,
            extract: str = None,
            summary_only: bool = False,
            with_metrics: bool = False,
            output_format: str = 'yaml',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble and emit the parse result payload.

        :param ast: The syntactic AST from PerformSyntacticAnalysis.
        :type ast: Dict[str, Any]
        :param source_file: Original source file path.
        :type source_file: str
        :param tokens: List of token aggregates from PerformLexicalAnalysis.
        :type tokens: List[TokenAggregate]
        :param extract: Original -x filter string.
        :type extract: str
        :param summary_only: If truthy, omit tokens and include metrics.
        :type summary_only: bool
        :param with_metrics: If truthy, include metrics alongside tokens.
        :type with_metrics: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param output: File path to write output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The assembled parse result payload.
        :rtype: Dict[str, Any]
        '''

        # Default analysis if missing.
        analysis = {
            'tokens': tokens,
            'token_count': len(tokens),
            'metrics': {},
        }

        # Build base payload with AST.
        result = {
            'event_type': 'ParseCompleted',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'token_count': analysis['token_count'],
            'ast': ast,
        }

        # Include extracted artifact names if -x was used.
        extracted_names = ScanOutputWriter.parse_extract_names(extract)
        if extracted_names:
            result['extracted_artifacts'] = extracted_names

        # Include metrics if requested.
        if with_metrics or summary_only:
            result['metrics'] = analysis['metrics']

        # Include tokens unless summary-only.
        if not summary_only:
            result['tokens'] = analysis['tokens']

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)

        # Return the result payload.
        return result
