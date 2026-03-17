"""Scanner Lexer Utility"""

# *** imports

# ** core
from types import MethodType
from typing import List, Dict, Any

# ** infra
import ply.lex as lex

# ** app
from ..events import a
from ..interfaces import LexerService

# *** utils

# ** util: tiferet_lexer
class TiferetLexer(LexerService):
    '''
    PLY-based lexer for the Tiferet Command dialect.
    Implements LexerService to tokenize Tiferet source text
    according to the lexical specification.
    '''

    # * attribute: lexer
    lexer: Any

    # * attribute: tokens
    tokens = a.lexer.TOKENS

    # * attribute: t_ignore
    t_ignore = ' \t'

    # * init
    def __init__(self):
        '''
        Initialize the TiferetLexer and build the PLY lexer instance.
        '''

        # Load rules dynamically from the assets mapping.
        for name, rule in a.lexer.RULES.items():
            if callable(rule):
                setattr(self, name, MethodType(rule, self))
            else:
                setattr(self, name, rule)

        # Build the PLY lexer from this module's token rules.
        self.lexer = lex.lex(module=self)

    # * rule: t_error
    def t_error(self, t):
        '''
        Handle unrecognized characters by emitting UNKNOWN tokens.
        '''

        t.type = 'UNKNOWN'
        t.value = t.value[0]
        t.lexer.skip(1)
        return t

    # -- Public interface

    # * method: tokenize
    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        '''
        Tokenize the provided source text into a list of token dictionaries.

        :param text: The source text to tokenize.
        :type text: str
        :return: A list of token dicts with keys: type, value, line, column.
        :rtype: List[Dict[str, Any]]
        '''

        # Reset lexer state for fresh tokenization.
        self.lexer.lineno = 1
        self.lexer.input(text)

        # Collect all tokens.
        tokens = []
        for tok in self.lexer:
            tokens.append({
                'type': tok.type,
                'value': tok.value,
                'line': tok.lineno,
                'column': self._find_column(text, tok),
            })

        # Return the collected tokens.
        return tokens

    # * method: _find_column
    def _find_column(self, text: str, token: Any) -> int:
        '''
        Compute the 0-based column position of a token.

        :param text: The full source text.
        :type text: str
        :param token: The PLY token object.
        :type token: Any
        :return: The column position.
        :rtype: int
        '''

        # Find the last newline before the token position.
        last_newline = text.rfind('\n', 0, token.lexpos)

        # Return the column offset.
        if last_newline < 0:
            return token.lexpos
        return token.lexpos - last_newline - 1
