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
            source_file: str,
            tokens: List[TokenAggregate],
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Parse token stream and produce structured AST.

        :source_file: The original source file path.
        :type source_file: str
        :param tokens: List of token aggregates from PerformLexicalAnalysis.
        :type tokens: List[TokenAggregate]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: AST dict with Module root.
        :rtype: Dict[str, Any]
        '''

        # Find the module name from the source file path for context (optional).
        module_name = source_file.rsplit('/', 1)[-1].rsplit('.', 1)[0] if source_file else 'unknown_module'

        # Execute syntactic parsing via the injected parser service.
        ast = self.parser_service.parse(module_name, tokens)

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
            include_tokens: bool = False,
            output_format: str = 'auto',
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
        :param include_tokens: If truthy, include tokens in the output.
        :type include_tokens: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param output: File path to write output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The assembled parse result payload.
        :rtype: Dict[str, Any]
        '''

        # Build base payload with AST.
        result = {
            'event_type': 'ParseCompleted',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'ast': ast,
        }

        # Include extracted artifact names if -x was used.
        extracted_names = ScanOutputWriter.parse_extract_names(extract)
        if extracted_names:
            result['extracted_artifacts'] = extracted_names

        # Include tokens if requested.
        if include_tokens:
            result['tokens'] = [token.dump_model() for token in tokens] if tokens else []
            result['token_count'] = len(tokens) if tokens else 0

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)
            return ''
        else:
            # Otherwise, return the result payload.
            return result
