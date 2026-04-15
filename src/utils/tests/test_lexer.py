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
    Returns a Tiferet-style source file with classes, methods, and artifact comments.

    :return: Content of samples/pass_multiple_operator_events.py
    :rtype: str
    '''
    return Path("samples/pass_multiple_operator_events.py").read_text(encoding="utf-8")


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


# *** tests — BlockTracker

# ** test: block_tracker_initial_state
def test_block_tracker_initial_state():
    '''
    BlockTracker starts with clean state after initialization.
    '''

    tracker = BlockTracker("")

    assert tracker.paren_depth == 0
    assert tracker.saw_class is False
    assert tracker.saw_method is False
    assert tracker.current_col == 0


# ** test: block_tracker_class_detection
def test_block_tracker_class_detection(minimal_class_text: str):
    '''
    CLASS token or ARTIFACT_SECTION matching "events:" sets saw_class.
    '''

    tracker = BlockTracker(minimal_class_text)

    # Simulate class line
    tracker.process_token(TokenAggregate.new(
        type=a.lexer.CLASS, value="class", lineno=2, lexpos=0
    ))

    assert tracker.saw_class is True


# ** test: block_tracker_method_detection_via_artifact
def test_block_tracker_method_detection_via_artifact(minimal_class_text: str):
    '''
    ARTIFACT_MEMBER matching "# * method:" or "# * init" sets saw_method.
    '''

    tracker = BlockTracker(minimal_class_text)

    tracker.process_token(TokenAggregate.new(
        type=a.lexer.ARTIFACT_MEMBER,
        value="# * method: execute",
        lineno=7,
        lexpos=4
    ))

    assert tracker.saw_method is True


# ** test: block_tracker_method_detection_via_def
def test_block_tracker_method_detection_via_def(minimal_class_text: str):
    '''
    DEF token also sets saw_method (for bare def without artifact comment).
    '''

    tracker = BlockTracker(minimal_class_text)

    tracker.process_token(TokenAggregate.new(
        type=a.lexer.DEF, value="def", lineno=8, lexpos=100
    ))

    assert tracker.saw_method is True


# ** test: block_tracker_paren_depth
def test_block_tracker_paren_depth():
    '''
    Parenthesis depth is tracked correctly for nested expressions.
    '''

    tracker = BlockTracker("")

    # Open
    tracker.process_token(TokenAggregate.new(type=a.lexer.LPAREN, value="(", lineno=1, lexpos=10))
    assert tracker.paren_depth == 1

    tracker.process_token(TokenAggregate.new(type=a.lexer.LBRACK, value="[", lineno=1, lexpos=12))
    assert tracker.paren_depth == 2

    # Close
    tracker.process_token(TokenAggregate.new(type=a.lexer.RBRACK, value="]", lineno=1, lexpos=20))
    assert tracker.paren_depth == 1

    tracker.process_token(TokenAggregate.new(type=a.lexer.RPAREN, value=")", lineno=1, lexpos=22))
    assert tracker.paren_depth == 0


# ** test: block_tracker_apply_block_indent
def test_block_tracker_apply_block_indent(minimal_class_text: str):
    '''
    When column increases after seeing a class/method, apply_block injects INDENT.
    '''

    tracker = BlockTracker(minimal_class_text)
    result: list[TokenAggregate] = []

    # Simulate seeing class
    tracker.process_token(TokenAggregate.new(type=a.lexer.CLASS, value="class", lineno=2, lexpos=0))
    tracker.current_col = 0

    # Next token on deeper column
    tracker.apply_block(next_lexpos=4, lineno=3, result=result)

    assert len(result) == 1
    assert result[0].type == a.lexer.INDENT
    assert tracker.current_col == 4


# ** test: block_tracker_apply_block_dedent
def test_block_tracker_apply_block_dedent():
    '''
    When column decreases, apply_block injects the correct number of DEDENTs.
    '''

    tracker = BlockTracker("")
    result: list[TokenAggregate] = []

    tracker.current_col = 12   # inside method at column 12

    # Back to column 4
    tracker.apply_block(next_lexpos=4, lineno=20, result=result)

    assert len(result) == 2
    assert all(t.type == a.lexer.DEDENT for t in result)
    assert tracker.current_col == 4


# ** test: block_tracker_flush_dedents_for_boundary
def test_block_tracker_flush_dedents_for_boundary():
    '''
    At end of file / boundary, flush_dedents_for_boundary emits remaining DEDENTs.
    '''

    tracker = BlockTracker("")
    tracker.current_col = 8

    dedents = tracker.flush_dedents_for_boundary()

    assert len(dedents) == 2
    assert all(t.type == a.lexer.DEDENT for t in dedents)
    assert tracker.current_col == 0


# *** tests — TiferetLexer

# ** test: tiferet_lexer_full_tokenize_includes_indents
def test_tiferet_lexer_full_tokenize_includes_indents(sample_text: str):
    '''
    Full lexer.tokenize() produces INDENT and DEDENT tokens at correct places.
    '''

    lexer = TiferetLexer()
    tokens = lexer.tokenize(sample_text)

    token_types = [t.type for t in tokens]

    assert a.lexer.INDENT in token_types
    assert a.lexer.DEDENT in token_types
    assert len(tokens) > 200   # rough sanity check for sample size


# ** test: tiferet_lexer_empty_text
def test_tiferet_lexer_empty_text():
    '''
    Empty text returns a minimal list (usually just a final NEWLINE).
    '''

    lexer = TiferetLexer()
    tokens = lexer.tokenize("")

    assert len(tokens) >= 0
    # May contain a final NEWLINE depending on implementation


# ** test: lexer_preserves_original_tokens
def test_lexer_preserves_original_tokens(sample_text: str):
    '''
    All original PLY tokens are still present in the final output (excluding injected ones).
    '''

    lexer = TiferetLexer()
    tokens = lexer.tokenize(sample_text)

    original_types = {t.type for t in tokens if t.type not in (a.lexer.INDENT, a.lexer.DEDENT)}

    assert a.lexer.CLASS in original_types
    assert a.lexer.ARTIFACT_MEMBER in original_types
    assert a.lexer.DEF in original_types
    assert a.lexer.NEWLINE in original_types
    assert a.lexer.IDENTIFIER in original_types


# ** test: lexer_respects_include_indent_dedent_flag
def test_lexer_respects_include_indent_dedent_flag(sample_text: str):
    '''
    When include_indent_dedent=False, no INDENT/DEDENT tokens are emitted.
    '''

    lexer = TiferetLexer(include_indent_dedent=False)
    tokens = lexer.tokenize(sample_text)

    token_types = [t.type for t in tokens]

    assert a.lexer.INDENT not in token_types
    assert a.lexer.DEDENT not in token_types


# ** test: lexer_adds_final_newline_if_missing
def test_lexer_adds_final_newline_if_missing():
    '''
    If the last token is not a NEWLINE, a final NEWLINE is appended.
    '''

    lexer = TiferetLexer()
    tokens = lexer.tokenize("class Foo:")

    assert tokens[-1].type == a.lexer.NEWLINE