"""Utilities - KeterLexer for the keter IR DSL"""

# *** imports

# ** core
from typing import List, Tuple

# *** constants

# ** constant: KETER_KEYWORDS
KETER_KEYWORDS = {
    'EventGroup', 'ImportGroups', 'ImportGroup', 'Imports', 'Import',
    'Events', 'Event', 'Attributes', 'Attribute',
    'Injections', 'Injection', 'Assign',
    'Execute', 'Methods', 'Method',
    'Params', 'Param', 'Returns', 'Return',
    'Snippets', 'Snippet', 'Comments', 'Comment',
    'Statements', 'Statement',
}

# *** utils

# ** util: keter_lexer
class KeterLexer:
    '''
    Minimal lexer that tokenizes a keter DSL string into a flat
    stream of (type, value) tuples.
    '''

    # * attribute: KEYWORD
    KEYWORD = 'KEYWORD'

    # * attribute: STRING
    STRING = 'STRING'

    # * attribute: IDENT
    IDENT = 'IDENT'

    # * attribute: LPAREN
    LPAREN = 'LPAREN'

    # * attribute: RPAREN
    RPAREN = 'RPAREN'

    # * attribute: COMMA
    COMMA = 'COMMA'

    # * method: tokenize (static)
    @staticmethod
    def tokenize(text: str) -> List[Tuple[str, str]]:
        '''
        Tokenize a keter DSL string into a flat list of (type, value) tuples.

        :param text: The keter DSL string.
        :type text: str
        :return: List of (token_type, token_value) tuples.
        :rtype: List[Tuple[str, str]]
        '''

        # Initialize the token list and cursor.
        tokens: List[Tuple[str, str]] = []
        i = 0

        # Walk through the text character by character.
        while i < len(text):
            ch = text[i]

            # Skip whitespace.
            if ch in ' \t\n\r':
                i += 1
                continue

            # Match single-character delimiters.
            if ch == '(':
                tokens.append((KeterLexer.LPAREN, '('))
                i += 1
                continue
            if ch == ')':
                tokens.append((KeterLexer.RPAREN, ')'))
                i += 1
                continue
            if ch == ',':
                tokens.append((KeterLexer.COMMA, ','))
                i += 1
                continue

            # Match quoted string literals.
            if ch == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    if text[j] == '\\':
                        j += 1
                    j += 1
                tokens.append((KeterLexer.STRING, text[i + 1:j]))
                i = j + 1
                continue

            # Match identifiers and keywords.
            j = i
            while j < len(text) and text[j] not in ' \t\n\r(),"':
                j += 1
            word = text[i:j]
            tok_type = KeterLexer.KEYWORD if word in KETER_KEYWORDS else KeterLexer.IDENT
            tokens.append((tok_type, word))
            i = j

        # Return the flat token stream.
        return tokens
