"""Mappers - KeterTransferObject Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..settings import KeterTransferObject
from ...utils.lexer_keter import KeterLexer

# *** tests — consume

# ** test: consume_advances_position_and_returns_token
def test_consume_advances_position_and_returns_token():
    '''
    consume returns the current token and advances the cursor.
    '''

    tokens = [(KeterLexer.KEYWORD, 'EventGroup'), (KeterLexer.LPAREN, '(')]
    pos = [0]

    tok = KeterTransferObject.consume(tokens, pos)

    assert tok == (KeterLexer.KEYWORD, 'EventGroup')
    assert pos[0] == 1


# ** test: consume_asserts_type
def test_consume_asserts_type():
    '''
    consume raises ValueError when the token type does not match.
    '''

    tokens = [(KeterLexer.IDENT, 'foo')]
    pos = [0]

    with pytest.raises(ValueError):
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD)


# ** test: consume_asserts_value
def test_consume_asserts_value():
    '''
    consume raises ValueError when the token value does not match.
    '''

    tokens = [(KeterLexer.KEYWORD, 'Events')]
    pos = [0]

    with pytest.raises(ValueError):
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'EventGroup')


# ** test: consume_raises_at_end_of_input
def test_consume_raises_at_end_of_input():
    '''
    consume raises ValueError when the cursor is past the end of the token list.
    '''

    with pytest.raises(ValueError):
        KeterTransferObject.consume([], [0])


# *** tests — peek

# ** test: peek_returns_current_token_without_advancing
def test_peek_returns_current_token_without_advancing():
    '''
    peek returns the token at the cursor and does not advance.
    '''

    tokens = [(KeterLexer.IDENT, 'x')]
    pos = [0]

    assert KeterTransferObject.peek(tokens, pos) == (KeterLexer.IDENT, 'x')
    assert pos[0] == 0


# ** test: peek_returns_none_past_end
def test_peek_returns_none_past_end():
    '''
    peek returns None when the cursor is past the end.
    '''

    assert KeterTransferObject.peek([], [0]) is None


# *** tests — skip_comma

# ** test: skip_comma_advances_when_on_comma
def test_skip_comma_advances_when_on_comma():
    '''
    skip_comma advances the cursor past a COMMA token.
    '''

    tokens = [(KeterLexer.COMMA, ','), (KeterLexer.IDENT, 'x')]
    pos = [0]

    KeterTransferObject.skip_comma(tokens, pos)

    assert pos[0] == 1


# ** test: skip_comma_noop_when_not_on_comma
def test_skip_comma_noop_when_not_on_comma():
    '''
    skip_comma leaves the cursor unchanged when the current token is not a comma.
    '''

    tokens = [(KeterLexer.IDENT, 'x')]
    pos = [0]

    KeterTransferObject.skip_comma(tokens, pos)

    assert pos[0] == 0


# *** tests — collect_balanced

# ** test: collect_balanced_flat_expression
def test_collect_balanced_flat_expression():
    '''
    collect_balanced reconstructs a flat expression with no nested parens.
    '''

    tokens = KeterLexer.tokenize('a, b)')
    pos = [0]

    result = KeterTransferObject.collect_balanced(tokens, pos)

    assert result == 'a, b'


# ** test: collect_balanced_respects_nested_parens
def test_collect_balanced_respects_nested_parens():
    '''
    collect_balanced tracks paren depth and stops at the matching closer.
    '''

    tokens = KeterLexer.tokenize('Add(a, b))')
    pos = [0]

    result = KeterTransferObject.collect_balanced(tokens, pos)

    assert result == 'Add(a, b)'


# *** tests — decode specs

# ** test: decode_param_spec_full
def test_decode_param_spec_full():
    '''
    decode_param_spec splits all five fields and coerces required to a boolean.
    '''

    spec = 'value:int:true:0:The input value'
    fields = KeterTransferObject.decode_param_spec(spec)

    assert fields == dict(
        name='value',
        type='int',
        required=True,
        default='0',
        description='The input value',
    )


# ** test: decode_param_spec_defaults_for_missing_fields
def test_decode_param_spec_defaults_for_missing_fields():
    '''
    decode_param_spec fills missing trailing fields with empty defaults.
    '''

    fields = KeterTransferObject.decode_param_spec('name')

    assert fields['name'] == 'name'
    assert fields['type'] == ''
    assert fields['required'] is True
    assert fields['default'] == ''
    assert fields['description'] == ''


# ** test: decode_return_spec
def test_decode_return_spec():
    '''
    decode_return_spec splits on the first colon only, preserving colons in the description.
    '''

    fields = KeterTransferObject.decode_return_spec('str:The greeting: hello')

    assert fields == dict(type_name='str', description='The greeting: hello')
