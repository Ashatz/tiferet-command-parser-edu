"""Parser Domain Events"""

# *** imports

# ** core
import os
from typing import List, Dict, Any

# ** infra
from tiferet import File

# ** app
from ..interfaces import ParserService
from ..mappers import TokenAggregate, Decl
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

        # Read the source text for column position calculation.
        source_text = ''
        if source_file and os.path.exists(source_file):
            with File(source_file) as f:
                source_text = f.file.read()

        # Execute syntactic parsing via the injected parser service.
        ast: Decl = self.parser_service.parse(module_name, tokens, source_text=source_text)
        ast.set_name(module_name)

        # Return the AST for downstream events.
        return ast
