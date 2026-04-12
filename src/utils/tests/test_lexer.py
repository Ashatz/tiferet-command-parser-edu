"""Tests - BlockTracker and TiferetLexer"""

# *** imports

# ** core
import pytest
from pathlib import Path

# ** app
from ..lexer import TiferetLexer, BlockTracker, a
from ...mappers import TokenAggregate

# *** fixtures

# ** fixture: sample_text
@pytest.fixture
def sample_text() -> str:
    '''
    Returns the full add_error_event.py sample used throughout the project.

    :return: Content of samples/add_error_event.py
    :rtype: str
    '''
    return Path("samples/add_error_event.py").read_text(encoding="utf-8")


# ** fixture: minimal_class_text
@pytest.fixture
def minimal_class_text() -> str:
    '''
    Returns a minimal class + method example for testing basic indent injection.

    :return: Small Tiferet-style class with one method
    :rtype: str
    '''
    return '''# ** event: minimal
class Minimal(DomainEvent):
    """
    Class docstring.
    """

    # * method: execute
    def execute(self):
        """
        Method docstring.
        """
        pass
'''

# *** tests

# ** test: block_tracker_initial_state
def test_block_tracker_initial_state():
    '''
    BlockTracker starts with clean state after initialization.

    :rtype: None
    '''
    tracker = BlockTracker("")

    assert not tracker.in_class_body
    assert not tracker.in_method_body
    assert tracker.class_col is None
    assert tracker.member_col is None
    assert len(tracker.class_indent_stack) == 0
    assert len(tracker.method_indent_stack) == 0
    assert not tracker.saw_class
    assert not tracker.saw_method


# ** test: block_tracker_class_body_detection
def test_block_tracker_class_body_detection(minimal_class_text: str):
    '''
    After seeing CLASS followed by COLON, in_class_body becomes True.

    :param minimal_class_text: Minimal class example
    :type minimal_class_text: str
    :rtype: None
    '''
    tracker = BlockTracker(minimal_class_text)

    tokens = [
        TokenAggregate.new(type=a.lexer.CLASS, value="class", lineno=2, lexpos=0),
        TokenAggregate.new(type=a.lexer.COLON, value=":", lineno=2, lexpos=27),
    ]

    for tok in tokens:
        tracker.process_token(tok)

    assert tracker.in_class_body is True
    assert tracker.saw_class is False


# ** test: block_tracker_method_body_detection
def test_block_tracker_method_body_detection(minimal_class_text: str):
    '''
    After seeing DEF followed by COLON, in_method_body becomes True.

    :param minimal_class_text: Minimal class example
    :type minimal_class_text: str
    :rtype: None
    '''
    tracker = BlockTracker(minimal_class_text)

    tokens = [
        TokenAggregate.new(type=a.lexer.DEF, value="def", lineno=8, lexpos=100),
        TokenAggregate.new(type=a.lexer.COLON, value=":", lineno=8, lexpos=150),
    ]

    for tok in tokens:
        tracker.process_token(tok)

    assert tracker.in_method_body is True
    assert tracker.saw_method is False


# ** test: block_tracker_should_inject_class_indent
def test_block_tracker_should_inject_class_indent(minimal_class_text: str):
    '''
    First token on a new line after class colon with column > class_col triggers INDENT.

    :param minimal_class_text: Minimal class example
    :type minimal_class_text: str
    :rtype: None
    '''
    tracker = BlockTracker(minimal_class_text)

    # Simulate class declaration
    tracker.process_token(TokenAggregate.new(type=a.lexer.CLASS, value="class", lineno=2, lexpos=0))
    tracker.process_token(TokenAggregate.new(type=a.lexer.COLON, value=":", lineno=2, lexpos=27))

    # Token at column 4 should trigger class indent
    assert tracker.should_inject_class_indent(40) is True


# ** test: block_tracker_should_inject_method_indent
def test_block_tracker_should_inject_method_indent(minimal_class_text: str):
    '''
    First token on a new line after method colon with greater column triggers method INDENT.

    :param minimal_class_text: Minimal class example
    :type minimal_class_text: str
    :rtype: None
    '''
    tracker = BlockTracker(minimal_class_text)

    tracker.process_token(TokenAggregate.new(type=a.lexer.DEF, value="def", lineno=8, lexpos=100))
    tracker.process_token(TokenAggregate.new(type=a.lexer.COLON, value=":", lineno=8, lexpos=150))

    # Token at column 8 should trigger method indent
    assert tracker.should_inject_method_indent(160) is True


# ** test: tiferet_lexer_full_tokenize_includes_indents
def test_tiferet_lexer_full_tokenize_includes_indents(sample_text: str):
    '''
    Full lexer.tokenize() produces INDENT and DEDENT tokens at correct places.

    :param sample_text: Full sample source
    :type sample_text: str
    :rtype: None
    '''
    lexer = TiferetLexer()
    tokens = lexer.tokenize(sample_text)

    token_types = [t.type for t in tokens]

    assert "INDENT" in token_types
    assert "DEDENT" in token_types
    assert len(tokens) > 250


# ** test: tiferet_lexer_empty_text
def test_tiferet_lexer_empty_text():
    '''
    Empty text returns an empty list without error.

    :rtype: None
    '''
    lexer = TiferetLexer()
    tokens = lexer.tokenize("")
    assert tokens == []


# ** test: block_tracker_dedent_on_boundary
def test_block_tracker_dedent_on_boundary(sample_text: str):
    '''
    Hitting next artifact boundary flushes pending DEDENTs and closes bodies.

    :param sample_text: Full sample source
    :type sample_text: str
    :rtype: None
    '''
    tracker = BlockTracker(sample_text)

    # Simulate being inside a method body with indent levels
    tracker.in_method_body = True
    tracker.method_indent_stack = [8, 12]

    boundary = TokenAggregate.new(
        type=a.lexer.ARTIFACT_MEMBER,
        value="# * attribute: next_one",
        lineno=100,
        lexpos=1000
    )

    tracker.process_token(boundary)

    assert tracker.in_method_body is False
    assert len(tracker.method_indent_stack) == 0


# ** test: lexer_preserves_original_tokens
def test_lexer_preserves_original_tokens(sample_text: str):
    '''
    All original PLY tokens are still present in the final output.

    :param sample_text: Full sample source
    :type sample_text: str
    :rtype: None
    '''
    lexer = TiferetLexer()
    tokens = lexer.tokenize(sample_text)

    original_types = {t.type for t in tokens if t.type not in ('INDENT', 'DEDENT')}

    assert a.lexer.CLASS in original_types
    assert a.lexer.ARTIFACT_MEMBER in original_types
    assert a.lexer.DEF in original_types
    assert a.lexer.NEWLINE in original_types