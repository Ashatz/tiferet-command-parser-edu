"""Scanner Lexer Interface"""

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
    Abstract interface for lexical analysis of Tiferet dialect source text.
    '''

    # * method: tokenize
    @abstractmethod
    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        '''
        Tokenize the provided source text into a list of token dictionaries.

        :param text: The source text to tokenize.
        :type text: str
        :return: A list of token dictionaries with keys: type, value, line, column.
        :rtype: List[Dict[str, Any]]
        '''

        raise NotImplementedError()
