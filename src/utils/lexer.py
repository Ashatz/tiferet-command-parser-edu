"""Scanner Lexer Utility"""

# *** imports

# ** core
import re
from typing import List, Dict, Any

# ** infra
import ply.lex as lex

# ** app
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

    # * init
    def __init__(self):
        '''
        Initialize the TiferetLexer and build the PLY lexer instance.
        '''

        # Build the PLY lexer from this module's token rules.
        self.lexer = lex.lex(module=self)

    # -- PLY token list (order matters for longest-match priority)
    tokens = (
        # Artifact comments
        'ARTIFACT_IMPORTS_START',
        'ARTIFACT_IMPORT_GROUP',
        'ARTIFACT_START',
        'ARTIFACT_SECTION',
        'ARTIFACT_MEMBER',

        # Documentation & comments
        'DOCSTRING',
        'LINE_COMMENT',

        # Domain idioms (must precede generic tokens)
        'VERIFY_PARAMETER',
        'VERIFY',
        'SERVICE_CALL',
        'FACTORY_CALL',
        'CONST_REF',

        # Structural keywords
        'CLASS',
        'DEF',
        'INIT',
        'EXECUTE',
        'RETURN',

        # Self reference
        'SELF',

        # Generic tokens
        'PYTHON_KEYWORD',
        'IDENTIFIER',
        'STRING_LITERAL',
        'NUMBER_LITERAL',

        # Punctuation & delimiters
        'LPAREN',
        'RPAREN',
        'LBRACK',
        'RBRACK',
        'LBRACE',
        'RBRACE',
        'COMMA',
        'COLON',
        'ARROW',
        'DOT',
        'EQUALS',

        # Layout
        'NEWLINE',
        'UNKNOWN',
    )

    # -- Python reserved words for keyword detection
    _python_keywords = {
        'and', 'as', 'assert', 'break', 'continue', 'del',
        'elif', 'else', 'except', 'False', 'finally', 'for',
        'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'None', 'nonlocal', 'not', 'or', 'pass', 'raise',
        'True', 'try', 'while', 'with', 'yield',
    }

    # -- Ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # -- Artifact comment rules (longest match first, functions > strings)

    # * rule: artifact_imports_start
    def t_ARTIFACT_IMPORTS_START(self, t):
        r'\#\s*\*{3}\s+imports\s*'
        return t

    # * rule: artifact_import_group
    def t_ARTIFACT_IMPORT_GROUP(self, t):
        r'\#\s*\*{2}\s+(core|app|infra)\b.*'
        return t

    # * rule: artifact_start
    def t_ARTIFACT_START(self, t):
        r'\#\s*\*{3}\s+.*'
        return t

    # * rule: artifact_section
    def t_ARTIFACT_SECTION(self, t):
        r'\#\s*\*{2}\s+.*'
        return t

    # * rule: artifact_member
    def t_ARTIFACT_MEMBER(self, t):
        r'\#\s*\*\s+.*'
        return t

    # -- Documentation & comments

    # * rule: docstring (triple-quoted strings)
    def t_DOCSTRING(self, t):
        r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')'
        t.lexer.lineno += t.value.count('\n')
        return t

    # * rule: line_comment (non-artifact)
    def t_LINE_COMMENT(self, t):
        r'\#[^*\n].*'
        return t

    # -- Domain idiom rules (must precede IDENTIFIER)

    # * rule: verify_parameter
    def t_VERIFY_PARAMETER(self, t):
        r'self\.verify_parameter\('
        return t

    # * rule: verify
    def t_VERIFY(self, t):
        r'self\.verify\('
        return t

    # * rule: service_call
    def t_SERVICE_CALL(self, t):
        r'self\.[a-zA-Z_][a-zA-Z0-9_]*_service\.[a-zA-Z_][a-zA-Z0-9_]*\('
        return t

    # * rule: factory_call
    def t_FACTORY_CALL(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*\.new\('
        return t

    # * rule: const_ref
    def t_CONST_REF(self, t):
        r'a\.const\.[A-Z_][A-Z0-9_]*'
        return t

    # -- String literal (single/double quoted, before IDENTIFIER)

    # * rule: string_literal
    def t_STRING_LITERAL(self, t):
        r'(\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\')'
        return t

    # -- Arrow (before EQUALS and DOT)

    # * rule: arrow
    def t_ARROW(self, t):
        r'->'
        return t

    # -- Number literal (before DOT to avoid conflict)

    # * rule: number_literal
    def t_NUMBER_LITERAL(self, t):
        r'[0-9]+(\.[0-9]+)?'
        return t

    # -- Identifier and keyword resolution

    # * rule: identifier
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'

        # Check for structural keywords first.
        if t.value == 'class':
            t.type = 'CLASS'
        elif t.value == 'def':
            t.type = 'DEF'
        elif t.value == '__init__':
            t.type = 'INIT'
        elif t.value == 'execute':
            t.type = 'EXECUTE'
        elif t.value == 'return':
            t.type = 'RETURN'
        elif t.value == 'self':
            t.type = 'SELF'
        elif t.value in self._python_keywords:
            t.type = 'PYTHON_KEYWORD'

        return t

    # -- Punctuation & delimiters (simple string rules)
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACK = r'\['
    t_RBRACK = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_COMMA = r','
    t_COLON = r':'
    t_DOT = r'\.'
    t_EQUALS = r'='

    # -- Layout

    # * rule: newline
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    # * rule: unknown
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
