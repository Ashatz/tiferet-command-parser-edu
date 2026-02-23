"""Lexer Utility Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..lexer import TiferetLexer

# *** fixtures

# ** fixture: lexer
@pytest.fixture
def lexer() -> TiferetLexer:
    '''
    Create a fresh TiferetLexer instance for each test.
    '''

    return TiferetLexer()

# *** helpers

def token_types(lexer, text):
    '''Return a list of token type strings for the given text.'''

    return [t['type'] for t in lexer.tokenize(text)]


def first_token(lexer, text):
    '''Return the first token dict for the given text.'''

    tokens = lexer.tokenize(text)
    assert len(tokens) > 0, f'No tokens produced for: {text!r}'
    return tokens[0]

# *** tests

# ** test: artifact_imports_start
def test_artifact_imports_start(lexer: TiferetLexer) -> None:
    '''
    Test that # *** imports is recognized as ARTIFACT_IMPORTS_START.
    '''

    tok = first_token(lexer, '# *** imports')
    assert tok['type'] == 'ARTIFACT_IMPORTS_START'


# ** test: artifact_start
def test_artifact_start(lexer: TiferetLexer) -> None:
    '''
    Test that # *** commands is recognized as ARTIFACT_START.
    '''

    tok = first_token(lexer, '# *** commands')
    assert tok['type'] == 'ARTIFACT_START'


# ** test: artifact_import_group_core
def test_artifact_import_group_core(lexer: TiferetLexer) -> None:
    '''
    Test that # ** core is recognized as ARTIFACT_IMPORT_GROUP.
    '''

    tok = first_token(lexer, '# ** core')
    assert tok['type'] == 'ARTIFACT_IMPORT_GROUP'


# ** test: artifact_import_group_app
def test_artifact_import_group_app(lexer: TiferetLexer) -> None:
    '''
    Test that # ** app is recognized as ARTIFACT_IMPORT_GROUP.
    '''

    tok = first_token(lexer, '# ** app')
    assert tok['type'] == 'ARTIFACT_IMPORT_GROUP'


# ** test: artifact_import_group_infra
def test_artifact_import_group_infra(lexer: TiferetLexer) -> None:
    '''
    Test that # ** infra is recognized as ARTIFACT_IMPORT_GROUP.
    '''

    tok = first_token(lexer, '# ** infra')
    assert tok['type'] == 'ARTIFACT_IMPORT_GROUP'


# ** test: artifact_section
def test_artifact_section(lexer: TiferetLexer) -> None:
    '''
    Test that # ** command: add_error is recognized as ARTIFACT_SECTION.
    '''

    tok = first_token(lexer, '# ** command: add_error')
    assert tok['type'] == 'ARTIFACT_SECTION'


# ** test: artifact_member
def test_artifact_member(lexer: TiferetLexer) -> None:
    '''
    Test that # * method: execute is recognized as ARTIFACT_MEMBER.
    '''

    tok = first_token(lexer, '# * method: execute')
    assert tok['type'] == 'ARTIFACT_MEMBER'


# ** test: docstring
def test_docstring(lexer: TiferetLexer) -> None:
    '''
    Test that triple-quoted strings are recognized as DOCSTRING.
    '''

    tok = first_token(lexer, "'''This is a docstring.'''")
    assert tok['type'] == 'DOCSTRING'

    tok2 = first_token(lexer, '"""Another docstring."""')
    assert tok2['type'] == 'DOCSTRING'


# ** test: docstring_multiline
def test_docstring_multiline(lexer: TiferetLexer) -> None:
    '''
    Test that multiline triple-quoted strings are recognized as DOCSTRING.
    '''

    text = "'''\n    A multiline\n    docstring.\n    '''"
    tok = first_token(lexer, text)
    assert tok['type'] == 'DOCSTRING'


# ** test: line_comment
def test_line_comment(lexer: TiferetLexer) -> None:
    '''
    Test that regular comments (non-artifact) are recognized as LINE_COMMENT.
    '''

    tok = first_token(lexer, '# This is a regular comment')
    assert tok['type'] == 'LINE_COMMENT'


# ** test: class_keyword
def test_class_keyword(lexer: TiferetLexer) -> None:
    '''
    Test that the class keyword is recognized as CLASS.
    '''

    tok = first_token(lexer, 'class')
    assert tok['type'] == 'CLASS'


# ** test: def_keyword
def test_def_keyword(lexer: TiferetLexer) -> None:
    '''
    Test that the def keyword is recognized as DEF.
    '''

    tok = first_token(lexer, 'def')
    assert tok['type'] == 'DEF'


# ** test: init_keyword
def test_init_keyword(lexer: TiferetLexer) -> None:
    '''
    Test that __init__ is recognized as INIT.
    '''

    tok = first_token(lexer, '__init__')
    assert tok['type'] == 'INIT'


# ** test: execute_keyword
def test_execute_keyword(lexer: TiferetLexer) -> None:
    '''
    Test that execute is recognized as EXECUTE.
    '''

    tok = first_token(lexer, 'execute')
    assert tok['type'] == 'EXECUTE'


# ** test: return_keyword
def test_return_keyword(lexer: TiferetLexer) -> None:
    '''
    Test that return is recognized as RETURN.
    '''

    tok = first_token(lexer, 'return')
    assert tok['type'] == 'RETURN'


# ** test: self_reference
def test_self_reference(lexer: TiferetLexer) -> None:
    '''
    Test that self is recognized as SELF.
    '''

    tok = first_token(lexer, 'self')
    assert tok['type'] == 'SELF'


# ** test: parameters_required
def test_parameters_required(lexer: TiferetLexer) -> None:
    '''
    Test that @DomainEvent.parameters_required( is recognized as PARAMETERS_REQUIRED.
    '''

    tok = first_token(lexer, '@DomainEvent.parameters_required(')
    assert tok['type'] == 'PARAMETERS_REQUIRED'


# ** test: verify_call
def test_verify_call(lexer: TiferetLexer) -> None:
    '''
    Test that self.verify( is recognized as VERIFY.
    '''

    tok = first_token(lexer, 'self.verify(')
    assert tok['type'] == 'VERIFY'


# ** test: service_call
def test_service_call(lexer: TiferetLexer) -> None:
    '''
    Test that self.error_service.save( is recognized as SERVICE_CALL.
    '''

    tok = first_token(lexer, 'self.error_service.save(')
    assert tok['type'] == 'SERVICE_CALL'


# ** test: factory_call
def test_factory_call(lexer: TiferetLexer) -> None:
    '''
    Test that Error.new( is recognized as FACTORY_CALL.
    '''

    tok = first_token(lexer, 'Error.new(')
    assert tok['type'] == 'FACTORY_CALL'


# ** test: const_ref
def test_const_ref(lexer: TiferetLexer) -> None:
    '''
    Test that a.const.ERROR_ALREADY_EXISTS_ID is recognized as CONST_REF.
    '''

    tok = first_token(lexer, 'a.const.ERROR_ALREADY_EXISTS_ID')
    assert tok['type'] == 'CONST_REF'


# ** test: python_keywords
def test_python_keywords(lexer: TiferetLexer) -> None:
    '''
    Test that Python reserved words are recognized as PYTHON_KEYWORD.
    '''

    keywords = ['from', 'import', 'if', 'else', 'for', 'True', 'False', 'None', 'is', 'not', 'in', 'and', 'or', 'as', 'with']
    for kw in keywords:
        tok = first_token(lexer, kw)
        assert tok['type'] == 'PYTHON_KEYWORD', f'{kw} should be PYTHON_KEYWORD, got {tok["type"]}'


# ** test: identifier
def test_identifier(lexer: TiferetLexer) -> None:
    '''
    Test that regular identifiers are recognized as IDENTIFIER.
    '''

    tok = first_token(lexer, 'my_variable')
    assert tok['type'] == 'IDENTIFIER'
    assert tok['value'] == 'my_variable'


# ** test: string_literal_single
def test_string_literal_single(lexer: TiferetLexer) -> None:
    '''
    Test that single-quoted strings are recognized as STRING_LITERAL.
    '''

    tok = first_token(lexer, "'hello world'")
    assert tok['type'] == 'STRING_LITERAL'


# ** test: string_literal_double
def test_string_literal_double(lexer: TiferetLexer) -> None:
    '''
    Test that double-quoted strings are recognized as STRING_LITERAL.
    '''

    tok = first_token(lexer, '"hello world"')
    assert tok['type'] == 'STRING_LITERAL'


# ** test: number_literal_integer
def test_number_literal_integer(lexer: TiferetLexer) -> None:
    '''
    Test that integers are recognized as NUMBER_LITERAL.
    '''

    tok = first_token(lexer, '42')
    assert tok['type'] == 'NUMBER_LITERAL'
    assert tok['value'] == '42'


# ** test: number_literal_float
def test_number_literal_float(lexer: TiferetLexer) -> None:
    '''
    Test that floats are recognized as NUMBER_LITERAL.
    '''

    tok = first_token(lexer, '3.14')
    assert tok['type'] == 'NUMBER_LITERAL'
    assert tok['value'] == '3.14'


# ** test: punctuation
def test_punctuation(lexer: TiferetLexer) -> None:
    '''
    Test that all punctuation and delimiters are recognized correctly.
    '''

    cases = {
        '(': 'LPAREN',
        ')': 'RPAREN',
        '[': 'LBRACK',
        ']': 'RBRACK',
        '{': 'LBRACE',
        '}': 'RBRACE',
        ',': 'COMMA',
        ':': 'COLON',
        '.': 'DOT',
        '=': 'EQUALS',
    }
    for char, expected_type in cases.items():
        tok = first_token(lexer, char)
        assert tok['type'] == expected_type, f'{char!r} should be {expected_type}, got {tok["type"]}'


# ** test: arrow
def test_arrow(lexer: TiferetLexer) -> None:
    '''
    Test that -> is recognized as ARROW.
    '''

    tok = first_token(lexer, '->')
    assert tok['type'] == 'ARROW'


# ** test: newline
def test_newline(lexer: TiferetLexer) -> None:
    '''
    Test that newlines are recognized as NEWLINE.
    '''

    types = token_types(lexer, 'a\nb')
    assert 'NEWLINE' in types


# ** test: unknown_token
def test_unknown_token(lexer: TiferetLexer) -> None:
    '''
    Test that unrecognized characters produce UNKNOWN tokens.
    '''

    tok = first_token(lexer, '@')
    assert tok['type'] == 'UNKNOWN'


# ** test: unknown_tokens_various
def test_unknown_tokens_various(lexer: TiferetLexer) -> None:
    '''
    Test that various unrecognized characters produce UNKNOWN tokens.
    '''

    for char in ['@', '$', '`', '~', '!', '%', '^', '&']:
        tok = first_token(lexer, char)
        assert tok['type'] == 'UNKNOWN', f'{char!r} should be UNKNOWN, got {tok["type"]}'


# ** test: column_tracking
def test_column_tracking(lexer: TiferetLexer) -> None:
    '''
    Test that column positions are correctly computed.
    '''

    tokens = lexer.tokenize('class AddError')
    assert tokens[0]['column'] == 0
    assert tokens[1]['column'] == 6


# ** test: line_tracking
def test_line_tracking(lexer: TiferetLexer) -> None:
    '''
    Test that line numbers are correctly tracked across newlines.
    '''

    tokens = lexer.tokenize('class\ndef')
    class_tok = [t for t in tokens if t['type'] == 'CLASS'][0]
    def_tok = [t for t in tokens if t['type'] == 'DEF'][0]
    assert class_tok['line'] == 1
    assert def_tok['line'] == 2


# ** test: full_command_snippet
def test_full_command_snippet(lexer: TiferetLexer) -> None:
    '''
    Test tokenization of a complete Tiferet command snippet.
    '''

    text = '''# ** command: add_error
class AddError(DomainEvent):
    def __init__(self, error_service: ErrorService):
        self.error_service = error_service

    @DomainEvent.parameters_required(['id', 'name'])
    def execute(self, id: str, **kwargs):
        exists = self.error_service.exists(id)
        self.verify(
            expression=exists is False,
            error_code=a.const.ERROR_ALREADY_EXISTS_ID,
        )
        new_error = Error.new(id=id, name=name)
        self.error_service.save(new_error)
        return new_error
'''

    tokens = lexer.tokenize(text)
    types = [t['type'] for t in tokens]

    # Verify key domain tokens are present.
    assert 'ARTIFACT_SECTION' in types
    assert 'CLASS' in types
    assert 'INIT' in types
    assert 'EXECUTE' in types
    assert 'PARAMETERS_REQUIRED' in types
    assert 'VERIFY' in types
    assert 'SERVICE_CALL' in types
    assert 'FACTORY_CALL' in types
    assert 'CONST_REF' in types
    assert 'RETURN' in types


# ** test: empty_input
def test_empty_input(lexer: TiferetLexer) -> None:
    '''
    Test that empty input produces no tokens.
    '''

    tokens = lexer.tokenize('')
    assert tokens == []


# ** test: whitespace_only
def test_whitespace_only(lexer: TiferetLexer) -> None:
    '''
    Test that whitespace-only input produces no tokens.
    '''

    tokens = lexer.tokenize('   \t  ')
    assert tokens == []
