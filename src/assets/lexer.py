"""Scanner Lexer Assets"""

# *** imports

# ** core
import re

# *** constants

# ** constant: artifact_imports_start
ARTIFACT_IMPORTS_START = 'ARTIFACT_IMPORTS_START'

# ** constant: artifact_import_group
ARTIFACT_IMPORT_GROUP = 'ARTIFACT_IMPORT_GROUP'

# ** constant: artifact_start
ARTIFACT_START = 'ARTIFACT_START'

# ** constant: artifact_section
ARTIFACT_SECTION = 'ARTIFACT_SECTION'

# ** constant: artifact_member
ARTIFACT_MEMBER = 'ARTIFACT_MEMBER'

# ** constant: docstring
DOCSTRING = 'DOCSTRING'

# ** constant: line_comment
LINE_COMMENT = 'LINE_COMMENT'

# ** constant: class
CLASS = 'CLASS'

# ** constant: def
DEF = 'DEF'

# ** constant: init
INIT = 'INIT'

# ** constant: return
RETURN = 'RETURN'

# ** constant: self
SELF = 'SELF'

# ** constant: python_keyword
PYTHON_KEYWORD = 'PYTHON_KEYWORD'

# ** constant: identifier
IDENTIFIER = 'IDENTIFIER'

# ** constant: string_literal
STRING_LITERAL = 'STRING_LITERAL'

# ** constant: number_literal
NUMBER_LITERAL = 'NUMBER_LITERAL'

# ** constant: lparen
LPAREN = 'LPAREN'

# ** constant: rparen
RPAREN = 'RPAREN'

# ** constant: lbrack
LBRACK = 'LBRACK'

# ** constant: rbrack
RBRACK = 'RBRACK'

# ** constant: lbrace
LBRACE = 'LBRACE'

# ** constant: rbrace
RBRACE = 'RBRACE'

# ** constant: comma
COMMA = 'COMMA'

# ** constant: colon
COLON = 'COLON'

# ** constant: arrow
ARROW = 'ARROW'

# ** constant: dot
DOT = 'DOT'

# ** constant: equals
EQUALS = 'EQUALS'

# ** constant: newline
NEWLINE = 'NEWLINE'

# ** constant: unknown
UNKNOWN = 'UNKNOWN'

# ** constant: tokens
TOKENS = (
    # Artifact comments
    ARTIFACT_IMPORTS_START,
    ARTIFACT_IMPORT_GROUP,
    ARTIFACT_START,
    ARTIFACT_SECTION,
    ARTIFACT_MEMBER,

    # Documentation & comments
    DOCSTRING,
    LINE_COMMENT,

    # Structural keywords
    CLASS,
    DEF,
    INIT,
    RETURN,

    # Self reference
    SELF,

    # Generic tokens
    PYTHON_KEYWORD,
    IDENTIFIER,
    STRING_LITERAL,
    NUMBER_LITERAL,

    # Punctuation & delimiters
    LPAREN,
    RPAREN,
    LBRACK,
    RBRACK,
    LBRACE,
    RBRACE,
    COMMA,
    COLON,
    ARROW,
    DOT,
    EQUALS,

    # Layout
    NEWLINE,
    UNKNOWN,
)

# ** constant: _python_keywords
_python_keywords = {
    'and', 'as', 'assert', 'break', 'continue', 'del',
    'elif', 'else', 'except', 'False', 'finally', 'for',
    'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
    'None', 'nonlocal', 'not', 'or', 'pass', 'raise',
    'True', 'try', 'while', 'with', 'yield',
}

# ** constant: artifact_imports_start
def ARTIFACT_IMPORTS_START(self, t):
    r'\#\s*\*{3}\s+imports\s*'
    return t

# ** constant: artifact_import_group
def ARTIFACT_IMPORT_GROUP(self, t):
    r'\#\s*\*{2}\s+(core|app|infra)\b.*'
    return t

# ** constant: artifact_start
def ARTIFACT_START(self, t):
    r'\#\s*\*{3}\s+.*'
    return t

# ** constant: artifact_section
def ARTIFACT_SECTION(self, t):
    r'\#\s*\*{2}\s+.*'
    return t

# ** constant: artifact_member
def ARTIFACT_MEMBER(self, t):
    r'\#\s*\*\s+.*'
    return t

# ** constant: docstring
def DOCSTRING(self, t):
    r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')'
    t.lexer.lineno += t.value.count('\n')
    return t

# ** constant: line_comment
def LINE_COMMENT(self, t):
    r'\#[^*\n].*'
    return t

# ** constant: string_literal
def STRING_LITERAL(self, t):
    r'(\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\')'
    return t

# ** constant: arrow
def ARROW(self, t):
    r'->'
    return t

# ** constant: number_literal
def NUMBER_LITERAL(self, t):
    r'[0-9]+(\.[0-9]+)?([a-zA-Z_][a-zA-Z0-9_]*)?'

    # If trailing identifier characters are present, emit as UNKNOWN.
    if re.search(r'[a-zA-Z_]', t.value):
        t.type = 'UNKNOWN'

    return t

# ** constant: identifier
def IDENTIFIER(self, t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'

    # Check for structural keywords first.
    if t.value == 'class':
        t.type = 'CLASS'
    elif t.value == 'def':
        t.type = 'DEF'
    elif t.value == '__init__':
        t.type = 'INIT'
    elif t.value == 'return':
        t.type = 'RETURN'
    elif t.value == 'self':
        t.type = 'SELF'
    elif t.value in _python_keywords:
        t.type = 'PYTHON_KEYWORD'

    return t

# ** constant: lparen
LPAREN = r'\('

# ** constant: rparen
RPAREN = r'\)'

# ** constant: lbrack
LBRACK = r'\['

# ** constant: rbrack
RBRACK = r'\]'

# ** constant: lbrace
LBRACE = r'\{'

# ** constant: rbrace
RBRACE = r'\}'

# ** constant: comma
COMMA = r','

# ** constant: colon
COLON = r':'

# ** constant: dot
DOT = r'\.'

# ** constant: equals
EQUALS = r'='

# ** constant: newline
def NEWLINE(self, t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# ** constant: rules
RULES = {
    't_ARTIFACT_IMPORTS_START': ARTIFACT_IMPORTS_START,
    't_ARTIFACT_IMPORT_GROUP': ARTIFACT_IMPORT_GROUP,
    't_ARTIFACT_START': ARTIFACT_START,
    't_ARTIFACT_SECTION': ARTIFACT_SECTION,
    't_ARTIFACT_MEMBER': ARTIFACT_MEMBER,
    't_DOCSTRING': DOCSTRING,
    't_LINE_COMMENT': LINE_COMMENT,
    't_STRING_LITERAL': STRING_LITERAL,
    't_ARROW': ARROW,
    't_NUMBER_LITERAL': NUMBER_LITERAL,
    't_IDENTIFIER': IDENTIFIER,
    't_LPAREN': LPAREN,
    't_RPAREN': RPAREN,
    't_LBRACK': LBRACK,
    't_RBRACK': RBRACK,
    't_LBRACE': LBRACE,
    't_RBRACE': RBRACE,
    't_COMMA': COMMA,
    't_COLON': COLON,
    't_DOT': DOT,
    't_EQUALS': EQUALS,
    't_NEWLINE': NEWLINE,
}
