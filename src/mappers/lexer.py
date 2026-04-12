"""Tiferet Compiler Lexer Mapper Objects"""

# *** imports

# ** app
from ..domain import Token
from ..events import a

# *** mappers

# ** mapper: TokenAggregate
class TokenAggregate(Token):

    # * method: new
    @staticmethod
    def new(type: str, value: str, lineno: int, lexpos: int) -> 'TokenAggregate':
        '''
        Create a new TokenAggregate instance from the provided token attributes.

        :param type: The type of the token (e.g., IDENTIFIER, KEYWORD).
        :type type: str
        :param value: The string value of the token.
        :type value: str
        :param lineno: The line number where the token was found.
        :type lineno: int
        :param lexpos: The position of the token in the input text.
        :type lexpos: int
        :return: A new TokenAggregate instance with the provided attributes.
        :rtype: TokenAggregate
        '''

        return TokenAggregate(
            type=type,
            value=value,
            lineno=lineno,
            lexpos=lexpos
        )
    
    # * method: new_indent
    @staticmethod
    def new_indent(lineno: int, lexpos: int) -> 'TokenAggregate':
        '''
        Create a new INDENT token with the given line number and lex position.

        :param lineno: The line number for the INDENT token.
        :type lineno: int
        :param lexpos: The lex position for the INDENT token.
        :type lexpos: int
        :return: A new TokenAggregate representing an INDENT token.
        :rtype: TokenAggregate
        '''

        return TokenAggregate.new(
            type=a.lexer.INDENT,
            value='',
            lineno=lineno,
            lexpos=lexpos
        )
    
    # * method: new_dedent
    @staticmethod
    def new_dedent(lineno: int = 0, lexpos: int = 0) -> 'TokenAggregate':
        '''
        Create a new DEDENT token with the given line number and lex position.

        :param lineno: The line number for the DEDENT token (default is 0).
        :type lineno: int
        :param lexpos: The lex position for the DEDENT token (default is 0).
        :type lexpos: int
        :return: A new TokenAggregate representing a DEDENT token.
        :rtype: TokenAggregate
        '''

        return TokenAggregate.new(
            type=a.lexer.DEDENT,
            value='',
            lineno=lineno,
            lexpos=lexpos
        )