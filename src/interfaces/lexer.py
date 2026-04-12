"""Scanner Lexer Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import List, Dict, Any

# ** infra
from tiferet.interfaces.settings import Service

# ** app
from ..mappers import TokenAggregate

# *** interfaces

# ** interface: lexer_service
class LexerService(Service):
    '''
    Abstract interface for lexical analysis of Tiferet dialect source text.
    '''

    # * method: tokenize
    @abstractmethod
    def tokenize(self, text: str) -> List[TokenAggregate]:
        '''
        Tokenize a block of source text.

        :param text: A block of source text to tokenize.
        :type text: str
        :return: A list of token aggregates.
        :rtype: List[TokenAggregate]
        '''

        raise NotImplementedError()
