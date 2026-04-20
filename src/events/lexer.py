"""Scanner Domain Events"""

# *** imports

# ** core
from typing import List

# ** infra
from tiferet import File

# ** app
from .settings import DomainEvent
from ..interfaces import LexerService
from ..mappers import TokenAggregate

# *** events

# ** event: perform_lexical_analysis
class PerformLexicalAnalysis(DomainEvent):
    '''
    Core analytical event that tokenizes validated text blocks via
    an injected LexerService and computes aggregate domain metrics.
    '''

    # * attribute: lexer_service
    lexer_service: LexerService

    # * init
    def __init__(self, lexer_service: LexerService):
        '''
        Initialize the PerformLexicalAnalysis event.

        :param lexer_service: The lexer service for tokenization.
        :type lexer_service: LexerService
        '''

        # Set the lexer service dependency.
        self.lexer_service = lexer_service

    # * method: execute
    @DomainEvent.parameters_required(['source_file'])
    def execute(self,
            source_file: str,
            **kwargs,
        ) -> List[TokenAggregate]:
        '''
        Tokenize all validated blocks and compute domain metrics.

        :param source_file: The path to the source file to be tokenized.
        :type source_file: str
        :return: List of token aggregates.
        :rtype: List[TokenAggregate]
        '''

        with File(source_file) as f:
            text = f.file.read()

        # Tokenize the text using the injected lexer service and return the list of token aggregates.
        return self.lexer_service.tokenize(text)
