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

# ** constant: obsolete
OBSOLETE = 'OBSOLETE'

# ** constant: todo
TODO = 'TODO'

# ** constant: docstring
DOCSTRING = 'DOCSTRING'

# ** constant: line_comment
LINE_COMMENT = 'LINE_COMMENT'

# ** constant: from
FROM = 'FROM'

# ** constant: import
IMPORT = 'IMPORT'

# * constant: as
AS = 'AS'

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

# ** constant: doublestar
DOUBLESTAR = 'DOUBLESTAR'

# ** constant: plus
PLUS = 'PLUS'

# ** constant: minus
MINUS = 'MINUS'

# ** constant: star
STAR = 'STAR'

# ** constant: slash
SLASH = 'SLASH'

# ** constant: doubleslash
DOUBLESLASH = 'DOUBLESLASH'

# ** constant: percent
PERCENT = 'PERCENT'

# ** constant: pipe
PIPE = 'PIPE'

# ** constant: ampersand
AMPERSAND = 'AMPERSAND'

# ** constant: tilde
TILDE = 'TILDE'

# ** constant: caret
CARET = 'CARET'

# ** constant: lshift
LSHIFT = 'LSHIFT'

# ** constant: rshift
RSHIFT = 'RSHIFT'

# ** constant: eqeq
EQEQ = 'EQEQ'

# ** constant: noteq
NOTEQ = 'NOTEQ'

# ** constant: lteq
LTEQ = 'LTEQ'

# ** constant: gteq
GTEQ = 'GTEQ'

# ** constant: lt
LT = 'LT'

# ** constant: gt
GT = 'GT'

# ** constant: at
AT = 'AT'

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

# ** constant: indent
INDENT = 'INDENT'

# ** constant: dedent
DEDENT = 'DEDENT'

# ** constant: tokens
TOKENS = (
    # Artifact comments
    ARTIFACT_IMPORTS_START,
    ARTIFACT_IMPORT_GROUP,
    ARTIFACT_START,
    ARTIFACT_SECTION,
    ARTIFACT_MEMBER,
    OBSOLETE,
    TODO,

    # Documentation & comments
    DOCSTRING,
    LINE_COMMENT,

    # Import statements
    FROM,
    IMPORT,
    AS,

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

    # Operators
    DOUBLESTAR,
    PLUS,
    MINUS,
    STAR,
    SLASH,
    DOUBLESLASH,
    PERCENT,
    PIPE,
    AMPERSAND,
    TILDE,
    CARET,
    LSHIFT,
    RSHIFT,
    EQEQ,
    NOTEQ,
    LTEQ,
    GTEQ,
    LT,
    GT,
    AT,

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

    # Indentation (synthetic — injected by IndentInjector, not produced by PLY lexer)
    INDENT,
    DEDENT,
)

# ** constant: _python_keywords
_python_keywords = {
    'and',  'assert', 'break', 'continue', 'del',
    'elif', 'else', 'except', 'False', 'finally', 'for',
    'global', 'if', 'in', 'is', 'lambda',
    'None', 'nonlocal', 'not', 'or', 'pass', 'raise',
    'True', 'try', 'while', 'with', 'yield',
}

# ** constant: artifact_imports_start
def T_ARTIFACT_IMPORTS_START(self, t):
    r'\#\s*\*{3}\s+imports[^\S\n]*'
    return t

# ** constant: artifact_import_group
def T_ARTIFACT_IMPORT_GROUP(self, t):
    r'\#\s*\*{2}\s+(core|app|infra)\b.*'
    return t

# ** constant: artifact_start
def T_ARTIFACT_START(self, t):
    r'\#\s*\*{3}\s+.*'
    return t

# ** constant: artifact_section
def T_ARTIFACT_SECTION(self, t):
    r'\#\s*\*{2}\s+.*'
    return t

# ** constant: artifact_member
def T_ARTIFACT_MEMBER(self, t):
    r'\#\s*\*\s+.*'
    return t

# ** constant: obsolete
def T_OBSOLETE(self, t):
    r'\#\s*-{1,2}\s+obsolete:[^\n]+'
    return t

# ** constant: todo
def T_TODO(self, t):
    r'\#\s*\+{1,2}\s+todo:[^\n]+'
    return t

# ** constant: docstring
def T_DOCSTRING(self, t):
    r'(\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\')'
    t.lexer.lineno += t.value.count('\n')
    return t

# ** constant: line_comment
def T_LINE_COMMENT(self, t):
    r'\#[^*\n].*'
    return t

# ** constant: string_literal
def T_STRING_LITERAL(self, t):
    r'(\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\')'
    return t

# ** constant: arrow
def T_ARROW(self, t):
    r'->'
    return t

# ** constant: number_literal
def T_NUMBER_LITERAL(self, t):
    r'[0-9]+(\.[0-9]+)?([a-zA-Z_][a-zA-Z0-9_]*)?'

    # If trailing identifier characters are present, emit as UNKNOWN.
    if re.search(r'[a-zA-Z_]', t.value):
        t.type = 'UNKNOWN'

    return t

# ** constant: identifier
def T_IDENTIFIER(self, t):
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
    elif t.value == 'from':
        t.type = 'FROM'
    elif t.value == 'import':
        t.type = 'IMPORT'
    elif t.value == 'as':
        t.type = 'AS'
    elif t.value in _python_keywords:
        t.type = 'PYTHON_KEYWORD'

    return t

# ** constant: doublestar
T_DOUBLESTAR = r'\*\*'

# ** constant: doubleslash
T_DOUBLESLASH = r'//'

# ** constant: lshift
T_LSHIFT = r'<<'

# ** constant: rshift
T_RSHIFT = r'>>'

# ** constant: eqeq
T_EQEQ = r'=='

# ** constant: noteq
T_NOTEQ = r'!='

# ** constant: lteq
T_LTEQ = r'<='

# ** constant: gteq
T_GTEQ = r'>='

# ** constant: plus
T_PLUS = r'\+'

# ** constant: minus
T_MINUS = r'-'

# ** constant: star
T_STAR = r'\*'

# ** constant: slash
T_SLASH = r'/'

# ** constant: percent
T_PERCENT = r'%'

# ** constant: pipe
T_PIPE = r'\|'

# ** constant: ampersand
T_AMPERSAND = r'&'

# ** constant: tilde
T_TILDE = r'~'

# ** constant: caret
T_CARET = r'\^'

# ** constant: lt
T_LT = r'<'

# ** constant: gt
T_GT = r'>'

# ** constant: at
T_AT = r'@'

# ** constant: t_lparen
T_LPAREN = r'\('

# ** constant: t_rparen
T_RPAREN = r'\)'

# ** constant: t_lbrack
T_LBRACK = r'\['

# ** constant: t_rbrack
T_RBRACK = r'\]'

# ** constant: t_lbrace
T_LBRACE = r'\{'

# ** constant: t_rbrace
T_RBRACE = r'\}'

# ** constant: comma
T_COMMA = r','

# ** constant: colon
T_COLON = r':'

# ** constant: dot
T_DOT = r'\.'

# ** constant: equals
T_EQUALS = r'='

# ** constant: newline
def T_NEWLINE(self, t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# ** constant: rules
RULES = {
    't_ARTIFACT_IMPORTS_START': T_ARTIFACT_IMPORTS_START,
    't_ARTIFACT_IMPORT_GROUP': T_ARTIFACT_IMPORT_GROUP,
    't_ARTIFACT_START': T_ARTIFACT_START,
    't_ARTIFACT_SECTION': T_ARTIFACT_SECTION,
    't_ARTIFACT_MEMBER': T_ARTIFACT_MEMBER,
    't_OBSOLETE': T_OBSOLETE,
    't_TODO': T_TODO,
    't_DOCSTRING': T_DOCSTRING,
    't_LINE_COMMENT': T_LINE_COMMENT,
    't_STRING_LITERAL': T_STRING_LITERAL,
    't_ARROW': T_ARROW,
    't_NUMBER_LITERAL': T_NUMBER_LITERAL,
    't_IDENTIFIER': T_IDENTIFIER,
    't_DOUBLESTAR': T_DOUBLESTAR,
    't_DOUBLESLASH': T_DOUBLESLASH,
    't_LSHIFT': T_LSHIFT,
    't_RSHIFT': T_RSHIFT,
    't_EQEQ': T_EQEQ,
    't_NOTEQ': T_NOTEQ,
    't_LTEQ': T_LTEQ,
    't_GTEQ': T_GTEQ,
    't_PLUS': T_PLUS,
    't_MINUS': T_MINUS,
    't_STAR': T_STAR,
    't_SLASH': T_SLASH,
    't_PERCENT': T_PERCENT,
    't_PIPE': T_PIPE,
    't_AMPERSAND': T_AMPERSAND,
    't_TILDE': T_TILDE,
    't_CARET': T_CARET,
    't_LT': T_LT,
    't_GT': T_GT,
    't_AT': T_AT,
    't_LPAREN': T_LPAREN,
    't_RPAREN': T_RPAREN,
    't_LBRACK': T_LBRACK,
    't_RBRACK': T_RBRACK,
    't_LBRACE': T_LBRACE,
    't_RBRACE': T_RBRACE,
    't_COMMA': T_COMMA,
    't_COLON': T_COLON,
    't_DOT': T_DOT,
    't_EQUALS': T_EQUALS,
    't_NEWLINE': T_NEWLINE,
}
