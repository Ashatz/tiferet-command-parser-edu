# *** imports

# ** core
from abc import abstractmethod
from typing import List, Dict, Any

# ** infra
from tiferet.interfaces.settings import Service

# *** interfaces

# ** interface: lexer_service
class LexerService(Service):
    '''
    Service interface for lexical analysis of Tiferet source files.
    '''

    # * method: tokenize
    @abstractmethod
    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        '''
        Tokenize a block of source text.

        :param text: A block of source text to tokenize.
        :type text: str
        :return: A list of token dictionaries with type, value, line, and column.
        :rtype: List[Dict[str, Any]]
        '''

        raise NotImplementedError()
