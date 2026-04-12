"""Mappers - Lexer Mapper Objects Tests"""

# *** imports

# ** core
import pytest
from pydantic import ValidationError

# ** app
from ...domain import Token
from ..lexer import TokenAggregate, a

# *** fixtures

# ** fixture: minimal_token_aggregate
@pytest.fixture
def minimal_token_aggregate() -> TokenAggregate:
    '''
    Returns a minimal TokenAggregate created via the canonical .new() factory.

    :return: A TokenAggregate instance.
    :rtype: TokenAggregate
    '''

    return TokenAggregate.new(
        type='IDENTIFIER',
        value='error_service',
        lineno=42,
        lexpos=156,
    )

# ** fixture: artifact_token_aggregate
@pytest.fixture
def artifact_token_aggregate() -> TokenAggregate:
    '''
    Returns a TokenAggregate representing an artifact comment member.

    :return: A TokenAggregate instance.
    :rtype: TokenAggregate
    '''

    return TokenAggregate.new(
        type='ARTIFACT_MEMBER',
        value='# * method: execute',
        lineno=17,
        lexpos=289,
    )

# *** tests

# ** test: token_aggregate_creation_via_new
def test_token_aggregate_creation_via_new(
        minimal_token_aggregate: TokenAggregate,
        artifact_token_aggregate: TokenAggregate,
    ) -> None:
    '''
    TokenAggregate.new() correctly creates instances with all fields.

    :param minimal_token_aggregate: Fixture providing a basic aggregate.
    :type minimal_token_aggregate: TokenAggregate
    :param artifact_token_aggregate: Fixture providing an artifact aggregate.
    :type artifact_token_aggregate: TokenAggregate
    '''

    # Minimal aggregate checks.
    assert minimal_token_aggregate.type == 'IDENTIFIER'
    assert minimal_token_aggregate.value == 'error_service'
    assert minimal_token_aggregate.lineno == 42
    assert minimal_token_aggregate.lexpos == 156

    # Artifact aggregate checks.
    assert artifact_token_aggregate.type == 'ARTIFACT_MEMBER'
    assert artifact_token_aggregate.value == '# * method: execute'
    assert artifact_token_aggregate.lineno == 17
    assert artifact_token_aggregate.lexpos == 289


# ** test: token_aggregate_inherits_from_token
def test_token_aggregate_inherits_from_token() -> None:
    '''
    TokenAggregate properly inherits all fields and behavior from Token.
    '''

    agg = TokenAggregate.new(
        type='CLASS',
        value='class',
        lineno=5,
        lexpos=23,
    )

    assert isinstance(agg, Token)
    assert isinstance(agg, TokenAggregate)
    assert agg.type == 'CLASS'
    assert agg.value == 'class'


# ** test: token_aggregate_new_requires_all_params
def test_token_aggregate_new_requires_all_params() -> None:
    '''
    TokenAggregate.new() (which delegates to Token(BaseModel)) requires all four fields.
    Missing a required parameter raises TypeError from the constructor.
    Passing None (or any invalid value) for a required field raises ValidationError from pydantic.
    '''

    with pytest.raises(TypeError):
        TokenAggregate.new(
            type='IDENTIFIER',
            value='foo',
            lineno=1,
            # missing lexpos
        )

    with pytest.raises(ValidationError):
        TokenAggregate.new(
            type='IDENTIFIER',
            value='foo',
            lineno=None,
            lexpos=None,
        )


# ** test: token_aggregate_column_default
def test_token_aggregate_column_default() -> None:
    '''
    Token model no longer defines a column field (it was removed when switching from schematics to pydantic).
    This test is kept as documentation that no extra column attribute exists.
    '''

    agg = TokenAggregate.new(
        type='NEWLINE',
        value='',
        lineno=10,
        lexpos=0,
    )

    # Explicit check that no .column attribute exists
    assert not hasattr(agg, 'column')


# ** test: token_aggregate_mutation
def test_token_aggregate_mutation(minimal_token_aggregate: TokenAggregate) -> None:
    '''
    TokenAggregate (backed by pydantic BaseModel) is mutable by default.

    :param minimal_token_aggregate: Fixture providing an aggregate.
    :type minimal_token_aggregate: TokenAggregate
    '''

    assert minimal_token_aggregate.type == 'IDENTIFIER'

    # Mutation is permitted (BaseModel is not frozen by default).
    minimal_token_aggregate.type = 'PYTHON_KEYWORD'
    minimal_token_aggregate.value = 'self'
    assert minimal_token_aggregate.type == 'PYTHON_KEYWORD'
    assert minimal_token_aggregate.value == 'self'


# ** test: token_aggregate_with_edge_values
def test_token_aggregate_with_edge_values() -> None:
    '''
    TokenAggregate.new() correctly handles edge-case values.
    '''

    agg = TokenAggregate.new(
        type='NEWLINE',
        value='',
        lineno=1,
        lexpos=0,
    )

    assert agg.type == 'NEWLINE'
    assert agg.value == ''
    assert agg.lineno == 1
    assert agg.lexpos == 0


# ** test: token_aggregate_with_long_value
def test_token_aggregate_with_long_value() -> None:
    '''
    TokenAggregate.new() correctly stores long string values.
    '''

    long_value = '# * method: execute(self, id: str, name: str, message: str) -> None:'

    agg = TokenAggregate.new(
        type='ARTIFACT_MEMBER',
        value=long_value,
        lineno=35,
        lexpos=1247,
    )

    assert agg.value == long_value
    assert len(agg.value) > 50


# ** test: token_aggregate_new_indent
def test_token_aggregate_new_indent() -> None:
    '''
    TokenAggregate.new_indent() correctly creates an INDENT token using the canonical factory.
    '''

    agg = TokenAggregate.new_indent(lineno=10, lexpos=4)

    assert agg.type == a.lexer.INDENT
    assert agg.value == ''
    assert agg.lineno == 10
    assert agg.lexpos == 4


# ** test: token_aggregate_new_dedent
def test_token_aggregate_new_dedent() -> None:
    '''
    TokenAggregate.new_dedent() correctly creates a DEDENT token (defaults lineno/lexpos to 0).
    '''

    agg = TokenAggregate.new_dedent()

    assert agg.type == a.lexer.DEDENT
    assert agg.value == ''
    assert agg.lineno == 0
    assert agg.lexpos == 0

    agg2 = TokenAggregate.new_dedent(lineno=25, lexpos=120)

    assert agg2.lineno == 25
    assert agg2.lexpos == 120