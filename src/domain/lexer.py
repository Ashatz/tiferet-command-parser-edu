"""Tiferet Compiler Lexer Domain Objects"""

# *** imports

# ** infra
from pydantic import BaseModel, Field

# *** objects

# ** object: token
class Token(BaseModel):
    '''A token produced by the TiferetLexer, representing a lexical unit in the source text.'''

    # * attribute: type
    type: str = Field(..., description='The type of the token (e.g., IDENTIFIER, KEYWORD)')

    # * attribute: value
    value: str = Field(..., description='The string value of the token')

    # * attribute: lineno
    lineno: int = Field(..., description='The line number where the token was found')

    # * attribute: lexpos
    lexpos: int = Field(..., description='The position of the token in the input text')