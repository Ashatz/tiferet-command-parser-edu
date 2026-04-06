"""Scanner Parser Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import List, Dict, Any

# ** infra
from tiferet.interfaces.settings import Service

# *** interfaces

# ** interface: parser_service
class ParserService(Service):
    '''
    Abstract interface for syntactic analysis of tokenized Tiferet Domain Event dialect input.
    '''

    # * method: parse
    @abstractmethod
    def parse(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        '''
        Parse a list of tokens into a structured AST reflecting the three-tier artifact hierarchy.

        :param tokens: Token stream from lexer + IndentInjector (including synthetic INDENT/DEDENT).
        :type tokens: List[Dict[str, Any]]
        :return: Root Module AST node.
        :rtype: Dict[str, Any]
        '''

        raise NotImplementedError()
