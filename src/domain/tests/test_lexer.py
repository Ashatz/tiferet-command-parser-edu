"""Domain - Lexer Domain Objects Tests"""

# *** imports

# ** core
import pytest
from pydantic import ValidationError

# ** app
from ..lexer import Token

# *** fixtures

# ** fixture: minimal_token
@pytest.fixture
def minimal_token() -> Token:
    '''
    Returns a minimal valid Token with all required fields.

    :return: A fully populated Token instance for basic testing.
    :rtype: Token
    '''

    return Token(
        type='IDENTIFIER',
        value='error_service',
        lineno=42,
        lexpos=156,
        column=8,
    )

# ** fixture: artifact_token
@pytest.fixture
def artifact_token() -> Token:
    '''
    Returns a Token representing an artifact comment member.

    :return: A Token instance with ARTIFACT_MEMBER type.
    :rtype: Token
    '''

    return Token(
        type='ARTIFACT_MEMBER',
        value='# * method: execute',
        lineno=17,
        lexpos=289,
        column=0,
    )

# ** fixture: complex_token
@pytest.fixture
def complex_token() -> Token:
    '''
    Returns a Token with realistic values from a typical Tiferet event.

    :return: A Token instance representing a method call.
    :rtype: Token
    '''

    return Token(
        type='IDENTIFIER',
        value='self.verify',
        lineno=28,
        lexpos=672,
        column=12,
    )

# *** tests

# ** test: token_creation_and_access
def test_token_creation_and_access(
        minimal_token: Token,
        artifact_token: Token,
    ) -> None:
    '''
    Happy path: Token objects can be instantiated and all fields are accessible.

    :param minimal_token: Fixture providing a basic token.
    :type minimal_token: Token
    :param artifact_token: Fixture providing an artifact token.
    :type artifact_token: Token
    '''

    # Minimal token checks.
    assert minimal_token.type == 'IDENTIFIER'
    assert minimal_token.value == 'error_service'
    assert minimal_token.lineno == 42
    assert minimal_token.lexpos == 156

    # Artifact token checks.
    assert artifact_token.type == 'ARTIFACT_MEMBER'
    assert artifact_token.value == '# * method: execute'
    assert artifact_token.lineno == 17
    assert artifact_token.lexpos == 289

# ** test: token_field_validation
def test_token_field_validation() -> None:
    '''
    All required fields must be present; missing fields raise ValidationError.
    '''

    # Missing type.
    with pytest.raises(ValidationError):
        Token(
            value='foo',
            lineno=1,
            lexpos=0,
        )

    # Missing value.
    with pytest.raises(ValidationError):
        Token(
            type='IDENTIFIER',
            lineno=1,
            lexpos=0,
        )

    # Missing lineno.
    with pytest.raises(ValidationError):
        Token(
            type='IDENTIFIER',
            value='foo',
            lexpos=0,
        )

    # Missing lexpos.
    with pytest.raises(ValidationError):
        Token(
            type='IDENTIFIER',
            value='foo',
            lineno=1,
        )

# ** test: token_string_representation
def test_token_string_representation(minimal_token: Token) -> None:
    '''
    Token has a useful __repr__ for debugging (Pydantic v2 default).

    :param minimal_token: Fixture providing a token.
    :type minimal_token: Token
    '''

    repr_str = repr(minimal_token)
    assert 'Token' in repr_str
    assert "type='IDENTIFIER'" in repr_str
    assert "value='error_service'" in repr_str
    assert 'lineno=42' in repr_str
    assert 'lexpos=156' in repr_str

# ** test: token_immutability_after_creation
def test_token_immutability_after_creation(minimal_token: Token) -> None:
    '''
    Pydantic BaseModel (v2) allows mutation by default unless model_config = {"frozen": True}.

    :param minimal_token: Fixture providing a token.
    :type minimal_token: Token
    '''

    # Fields are readable.
    assert minimal_token.type == 'IDENTIFIER'

    # Mutation is currently allowed (model is not frozen).
    minimal_token.type = 'NEW_TYPE'
    assert minimal_token.type == 'NEW_TYPE'

# ** test: token_with_edge_values
def test_token_with_edge_values() -> None:
    '''
    Token accepts edge-case values (empty string value, lineno=1, lexpos=0, column=0).
    '''

    token = Token(
        type='NEWLINE',
        value='',
        lineno=1,
        lexpos=0,
    )

    assert token.type == 'NEWLINE'
    assert token.value == ''
    assert token.lineno == 1
    assert token.lexpos == 0

# ** test: token_with_long_value
def test_token_with_long_value() -> None:
    '''
    Token correctly stores long string values (e.g., multi-word artifact comments).
    '''

    long_value = '# * method: execute(self, id: str, name: str) -> None:'

    token = Token(
        type='ARTIFACT_MEMBER',
        value=long_value,
        lineno=35,
        lexpos=1247,
        column=4,
    )

    assert token.value == long_value
    assert len(token.value) > 50