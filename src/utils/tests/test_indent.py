"""Indent Injector Utility Tests"""

# *** imports

# ** app
from ..indent import IndentInjector

# *** helpers

def tok(type, value='', line=1, column=0):
    '''Build a minimal token dict for test input.'''
    return {'type': type, 'value': value, 'line': line, 'column': column}

def types_of(tokens):
    '''Return a list of token type strings.'''
    return [t['type'] for t in tokens]

# *** tests — basic cases

# ** test: empty_input
def test_empty_input() -> None:
    '''
    Test that an empty token list returns an empty list.
    '''

    # Inject into an empty stream.
    result = IndentInjector.inject([])

    # Assert empty list returned.
    assert result == []


# ** test: no_method_bodies
def test_no_method_bodies() -> None:
    '''
    Test that a token stream with no artifact member tokens
    produces no INDENT or DEDENT tokens.
    '''

    # Tokens with no artifact members.
    tokens = [
        tok('CLASS', 'class', 1, 0),
        tok('IDENTIFIER', 'Foo', 1, 6),
        tok('NEWLINE', '\n', 1, 9),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert no indentation tokens injected.
    assert 'INDENT' not in result_types
    assert 'DEDENT' not in result_types


# ** test: attribute_member_no_body
def test_attribute_member_no_body() -> None:
    '''
    Test that a non-method artifact member (e.g. attribute) does not
    open a method body and produces no INDENT or DEDENT tokens.
    '''

    # Tokens for an attribute member.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * attribute: error_service', 1, 4),
        tok('NEWLINE', '\n', 1, 32),
        tok('IDENTIFIER', 'error_service', 2, 4),
        tok('COLON', ':', 2, 17),
        tok('IDENTIFIER', 'ErrorService', 2, 19),
        tok('NEWLINE', '\n', 2, 31),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert no indentation tokens injected.
    assert 'INDENT' not in result_types
    assert 'DEDENT' not in result_types


# ** test: tokens_preserved
def test_tokens_preserved() -> None:
    '''
    Test that all original tokens are present in the output in their
    original order, with only INDENT/DEDENT tokens added.
    '''

    # Tokens for a simple method body.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('RETURN', 'return', 3, 8),
        tok('IDENTIFIER', 'value', 3, 15),
        tok('NEWLINE', '\n', 3, 20),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)

    # Assert all original tokens are present in the same order.
    non_synthetic = [t for t in result if t['type'] not in ('INDENT', 'DEDENT')]
    assert non_synthetic == tokens

# *** tests — method body open and close

# ** test: init_body_opens
def test_init_body_opens() -> None:
    '''
    Test that an init artifact member opens a method body,
    injecting INDENT at the first body line and DEDENT at EOF.
    '''

    # Tokens for an init body.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * init', 1, 4),
        tok('NEWLINE', '\n', 1, 12),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('SELF', 'self', 2, 8),
        tok('RPAREN', ')', 2, 12),
        tok('COLON', ':', 2, 13),
        tok('NEWLINE', '\n', 2, 14),
        tok('SELF', 'self', 3, 8),
        tok('DOT', '.', 3, 12),
        tok('IDENTIFIER', 'x', 3, 13),
        tok('NEWLINE', '\n', 3, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert one INDENT and one DEDENT are present.
    assert result_types.count('INDENT') == 1
    assert result_types.count('DEDENT') == 1

    # Assert INDENT appears before the first body SELF (after the signature).
    indent_idx = result_types.index('INDENT')
    body_self_idx = next(
        i for i, t in enumerate(result)
        if t['type'] == 'SELF' and t['column'] == 8 and i > indent_idx
    )
    assert indent_idx < body_self_idx


# ** test: method_body_opens
def test_method_body_opens() -> None:
    '''
    Test that a method artifact member opens a method body,
    injecting INDENT at the first body line and DEDENT at EOF.
    '''

    # Tokens for a method body.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('LINE_COMMENT', '# do something', 3, 8),
        tok('NEWLINE', '\n', 3, 22),
        tok('RETURN', 'return', 4, 8),
        tok('NEWLINE', '\n', 4, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert one INDENT and one DEDENT are present.
    assert result_types.count('INDENT') == 1
    assert result_types.count('DEDENT') == 1

    # Assert INDENT precedes the first body token (LINE_COMMENT at col=8).
    indent_idx = result_types.index('INDENT')
    comment_idx = result_types.index('LINE_COMMENT')
    assert indent_idx < comment_idx


# ** test: body_closed_by_artifact_member
def test_body_closed_by_artifact_member() -> None:
    '''
    Test that a subsequent artifact member closes the open body,
    emitting DEDENT before it, and opens a new body if it is a method.
    '''

    # Two method members in sequence.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('RETURN', 'return', 3, 8),
        tok('NEWLINE', '\n', 3, 14),
        tok('ARTIFACT_MEMBER', '# * method: other', 4, 4),
        tok('NEWLINE', '\n', 4, 21),
        tok('DEF', 'def', 5, 4),
        tok('LPAREN', '(', 5, 7),
        tok('RPAREN', ')', 5, 8),
        tok('COLON', ':', 5, 9),
        tok('NEWLINE', '\n', 5, 10),
        tok('RETURN', 'return', 6, 8),
        tok('NEWLINE', '\n', 6, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert one INDENT and DEDENT per method body.
    assert result_types.count('INDENT') == 2
    assert result_types.count('DEDENT') == 2

    # Assert DEDENT precedes the second ARTIFACT_MEMBER.
    first_dedent_idx = result_types.index('DEDENT')
    second_member_idx = next(
        i for i, t in enumerate(result)
        if t['type'] == 'ARTIFACT_MEMBER' and 'other' in t['value']
    )
    assert first_dedent_idx < second_member_idx


# ** test: body_closed_by_artifact_section
def test_body_closed_by_artifact_section() -> None:
    '''
    Test that an artifact section token closes the open method body,
    emitting DEDENT before the section token.
    '''

    # Method body followed by a new artifact section.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('RETURN', 'return', 3, 8),
        tok('NEWLINE', '\n', 3, 14),
        tok('ARTIFACT_SECTION', '# ** event: other', 4, 0),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert INDENT and DEDENT are present.
    assert 'INDENT' in result_types
    assert 'DEDENT' in result_types

    # Assert DEDENT precedes ARTIFACT_SECTION.
    dedent_idx = result_types.index('DEDENT')
    section_idx = result_types.index('ARTIFACT_SECTION')
    assert dedent_idx < section_idx


# ** test: body_closed_at_eof
def test_body_closed_at_eof() -> None:
    '''
    Test that a method body still open at end of stream is closed
    with a DEDENT as the final token.
    '''

    # Method body with no explicit close.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('RETURN', 'return', 3, 8),
        tok('NEWLINE', '\n', 3, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)

    # Assert the final token is DEDENT.
    assert result[-1]['type'] == 'DEDENT'

# *** tests — indentation depth

# ** test: nested_indent
def test_nested_indent() -> None:
    '''
    Test that deeper nesting within a method body emits a second
    INDENT, and returning to the baseline emits a DEDENT.
    '''

    # Method body with one level of nesting.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),
        tok('RPAREN', ')', 2, 8),
        tok('COLON', ':', 2, 9),
        tok('NEWLINE', '\n', 2, 10),
        tok('PYTHON_KEYWORD', 'if', 3, 8),    # col=8 → baseline INDENT
        tok('PYTHON_KEYWORD', 'True', 3, 11),
        tok('COLON', ':', 3, 15),
        tok('NEWLINE', '\n', 3, 16),
        tok('RETURN', 'return', 4, 12),        # col=12 → nested INDENT
        tok('NEWLINE', '\n', 4, 18),
        tok('PYTHON_KEYWORD', 'pass', 5, 8),   # col=8 < 12 → DEDENT back to baseline
        tok('NEWLINE', '\n', 5, 12),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert two INDENTs (baseline + nested) and two DEDENTs (nested exit + EOF).
    assert result_types.count('INDENT') == 2
    assert result_types.count('DEDENT') == 2


# ** test: paren_depth_guard
def test_paren_depth_guard() -> None:
    '''
    Test that newlines inside a multi-line function signature
    (paren depth > 0) do not trigger INDENT injection.
    '''

    # Method with a multi-line signature.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('DEF', 'def', 2, 4),
        tok('LPAREN', '(', 2, 7),             # paren_depth = 1
        tok('SELF', 'self', 2, 8),
        tok('COMMA', ',', 2, 12),
        tok('NEWLINE', '\n', 2, 13),           # paren_depth=1 → no indent check
        tok('IDENTIFIER', 'id', 3, 12),        # col=12 but paren_depth still 1
        tok('NEWLINE', '\n', 3, 14),           # paren_depth=1 → no indent check
        tok('RPAREN', ')', 4, 4),              # paren_depth = 0
        tok('COLON', ':', 4, 5),
        tok('NEWLINE', '\n', 4, 6),            # paren_depth=0 → indent check now active
        tok('RETURN', 'return', 5, 8),         # col=8 > 4 → INDENT here only
        tok('NEWLINE', '\n', 5, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert exactly one INDENT — only at the body, not inside the signature.
    assert result_types.count('INDENT') == 1

    # Assert INDENT appears immediately before RETURN.
    indent_idx = result_types.index('INDENT')
    return_idx = result_types.index('RETURN')
    assert indent_idx == return_idx - 1


# ** test: annotation_before_body_no_indent
def test_annotation_before_body_no_indent() -> None:
    '''
    Test that an OBSOLETE or TODO annotation at the member column
    appearing between the artifact member and the def line does not
    trigger a spurious INDENT.
    '''

    # Method with an OBSOLETE annotation before the def.
    tokens = [
        tok('ARTIFACT_MEMBER', '# * method: execute', 1, 4),
        tok('NEWLINE', '\n', 1, 23),
        tok('OBSOLETE', '# - obsolete: use v2 instead', 2, 4),  # col=4 = member_col
        tok('NEWLINE', '\n', 2, 32),
        tok('DEF', 'def', 3, 4),
        tok('LPAREN', '(', 3, 7),
        tok('RPAREN', ')', 3, 8),
        tok('COLON', ':', 3, 9),
        tok('NEWLINE', '\n', 3, 10),
        tok('RETURN', 'return', 4, 8),         # col=8 > 4 → INDENT here only
        tok('NEWLINE', '\n', 4, 14),
    ]

    # Inject into the stream.
    result = IndentInjector.inject(tokens)
    result_types = types_of(result)

    # Assert exactly one INDENT — only at the body entry.
    assert result_types.count('INDENT') == 1

    # Assert OBSOLETE appears before the INDENT.
    obsolete_idx = result_types.index('OBSOLETE')
    indent_idx = result_types.index('INDENT')
    assert obsolete_idx < indent_idx
