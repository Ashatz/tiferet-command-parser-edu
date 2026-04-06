"""Parser Domain Events"""

# *** imports

# ** core
from typing import List, Dict, Any

# ** app
from .settings import DomainEvent, a
from ..interfaces import ParserService

# *** events

# ** event: parser_initialized
class ParserInitialized(DomainEvent):
    '''
    Validation gate event that verifies the TiferetParser service
    is properly instantiated before syntactic analysis.
    '''

    # * attribute: parser
    parser: ParserService

    # * init
    def __init__(self, parser: ParserService):
        '''
        Initialize with injected parser service.

        :param parser: The parser service for syntactic analysis.
        :type parser: ParserService
        '''

        # Set the parser service dependency.
        self.parser = parser

    # * method: execute
    @DomainEvent.parameters_required([])
    def execute(self, **kwargs) -> ParserService:
        '''
        Verify parser service readiness.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The validated parser service.
        :rtype: ParserService
        '''

        # Verify the parser service is not None.
        self.verify(
            expression=self.parser is not None,
            error_code='PARSER_NOT_INITIALIZED',
            message='TiferetParser service failed to initialize',
        )

        # Return the validated parser service.
        return self.parser


# ** event: perform_syntactic_analysis
class PerformSyntacticAnalysis(DomainEvent):
    '''
    Core analytical event that performs syntactic parsing on the
    tokenized input using the injected ParserService.
    '''

    # * attribute: parser
    parser: ParserService

    # * init
    def __init__(self, parser: ParserService):
        '''
        Initialize with injected parser service.

        :param parser: The parser service for syntactic analysis.
        :type parser: ParserService
        '''

        # Set the parser service dependency.
        self.parser = parser

    # * method: execute
    @DomainEvent.parameters_required(['tokens'])
    def execute(self,
            tokens: List[Dict[str, Any]],
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Parse token stream and produce structured AST.

        :param tokens: Token stream from PerformLexicalAnalysis (post-IndentInjector).
        :type tokens: List[Dict[str, Any]]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: AST dict with Module root.
        :rtype: Dict[str, Any]
        '''

        # Execute syntactic parsing via the injected parser service.
        ast = self.parser.parse(tokens)

        # Validate the AST root structure is a Module.
        self.verify(
            expression=isinstance(ast, dict) and ast.get('type') == 'Module',
            error_code='INVALID_AST_STRUCTURE',
            message='Syntactic parser did not return a valid Module AST',
            ast_type=str(type(ast)),
        )

        # Return the AST for downstream events.
        return ast


# ** event: syntactic_analysis_completed
class SyntacticAnalysisCompleted(DomainEvent):
    '''
    Terminal parser event that finalizes the AST and prepares it
    for result emission.
    '''

    # * method: execute
    def execute(self,
            ast: Dict[str, Any] = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Finalize syntactic analysis result.

        :param ast: AST produced by PerformSyntacticAnalysis.
        :type ast: Dict[str, Any]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Enriched result payload.
        :rtype: Dict[str, Any]
        '''

        # Ensure a valid AST was received.
        self.verify(
            expression=ast is not None,
            error_code='MISSING_AST',
            message='No AST received from syntactic analysis',
        )

        # Return enriched payload.
        return {
            'event_type': 'SyntacticAnalysisCompleted',
            'ast': ast,
            'group_count': len(ast.get('groups', [])),
        }
