"""Tiferet Compiler Lexer Mapper Objects"""

# *** imports

# ** app
from ..domain import Token

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