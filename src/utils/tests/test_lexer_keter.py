"""Tests - KeterLexer"""

# *** imports

# ** infra
import pytest

# ** app
from ..lexer_keter import KeterLexer, KETER_KEYWORDS

# *** tests — KeterLexer

# ** test: tokenize_empty_text
def test_tokenize_empty_text():
    '''
    Empty input produces an empty token list.
    '''

    assert KeterLexer.tokenize('') == []


# ** test: tokenize_whitespace_is_skipped
def test_tokenize_whitespace_is_skipped():
    '''
    Spaces, tabs, newlines and carriage returns are ignored.
    '''

    assert KeterLexer.tokenize(' \t\n\r') == []


# ** test: tokenize_delimiters
def test_tokenize_delimiters():
    '''
    Parens and commas are recognized as distinct token types.
    '''

    tokens = KeterLexer.tokenize('(,)')

    assert tokens == [
        (KeterLexer.LPAREN, '('),
        (KeterLexer.COMMA, ','),
        (KeterLexer.RPAREN, ')'),
    ]


# ** test: tokenize_keyword_vs_identifier
def test_tokenize_keyword_vs_identifier():
    '''
    Words in KETER_KEYWORDS emit KEYWORD; other words emit IDENT.
    '''

    tokens = KeterLexer.tokenize('EventGroup my_module')

    assert tokens == [
        (KeterLexer.KEYWORD, 'EventGroup'),
        (KeterLexer.IDENT, 'my_module'),
    ]


# ** test: tokenize_string_literal
def test_tokenize_string_literal():
    '''
    Double-quoted strings are captured without the surrounding quotes.
    '''

    tokens = KeterLexer.tokenize('"hello world"')

    assert tokens == [(KeterLexer.STRING, 'hello world')]


# ** test: tokenize_string_with_escape
def test_tokenize_string_with_escape():
    '''
    Backslash-escaped characters inside a string are skipped, not treated as terminators.
    '''

    tokens = KeterLexer.tokenize('"a\\"b"')

    assert len(tokens) == 1
    assert tokens[0][0] == KeterLexer.STRING


# ** test: tokenize_full_event_group_skeleton
def test_tokenize_full_event_group_skeleton():
    '''
    A minimal EventGroup DSL string round-trips into the expected token sequence.
    '''

    text = 'EventGroup(my_module, "desc")'
    tokens = KeterLexer.tokenize(text)

    assert tokens == [
        (KeterLexer.KEYWORD, 'EventGroup'),
        (KeterLexer.LPAREN, '('),
        (KeterLexer.IDENT, 'my_module'),
        (KeterLexer.COMMA, ','),
        (KeterLexer.STRING, 'desc'),
        (KeterLexer.RPAREN, ')'),
    ]


# ** test: keter_keywords_contains_expected_set
def test_keter_keywords_contains_expected_set():
    '''
    The KETER_KEYWORDS constant covers all top-level and nested DSL constructors.
    '''

    expected = {
        'EventGroup', 'ImportGroups', 'ImportGroup', 'Imports', 'Import',
        'Events', 'Event', 'Attributes', 'Attribute',
        'Injections', 'Injection', 'Assign',
        'Execute', 'Methods', 'Method',
        'Params', 'Param', 'Returns', 'Return',
        'Snippets', 'Snippet', 'Comments', 'Comment',
        'Statements', 'Statement',
    }

    assert KETER_KEYWORDS == expected
