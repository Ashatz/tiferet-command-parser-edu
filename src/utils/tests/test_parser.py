"""Parser Utility Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..parser import TiferetParser

# *** helpers

def tok(type, value=None, line=1):
    '''Create a minimal token dict.'''
    return {'type': type, 'value': value or type, 'line': line}

# *** fixtures

# ** fixture: parser
@pytest.fixture
def parser() -> TiferetParser:
    '''
    Create a fresh TiferetParser instance for each test.
    '''

    return TiferetParser()

# ** fixture: minimal_import_tokens
@pytest.fixture
def minimal_import_tokens():
    '''
    Minimal valid token stream: one import group with a single import statement.
    Represents:
        # *** imports
        # ** core
        from typing import Any
    '''

    return [
        tok('ARTIFACT_IMPORTS_START', '# *** imports'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_IMPORT_GROUP', '# ** core'),
        tok('NEWLINE', '\n'),
        tok('PYTHON_KEYWORD', 'from'),
        tok('IDENTIFIER', 'typing'),
        tok('PYTHON_KEYWORD', 'import'),
        tok('IDENTIFIER', 'Any'),
        tok('NEWLINE', '\n'),
    ]

# ** fixture: minimal_event_tokens
@pytest.fixture
def minimal_event_tokens():
    '''
    Token stream for a minimal event class with one method member.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            # * method: execute
            def execute(self):
                return result
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        # Member: method
        tok('ARTIFACT_MEMBER', '# * method: execute'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('IDENTIFIER', 'execute'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        # Body: single snippet with return stmt
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'result'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# ** fixture: import_and_event_tokens
@pytest.fixture
def import_and_event_tokens(minimal_import_tokens, minimal_event_tokens):
    '''
    Token stream combining an import group and an event group (two groups).
    '''

    return minimal_import_tokens + minimal_event_tokens

# ** fixture: attribute_member_tokens
@pytest.fixture
def attribute_member_tokens():
    '''
    Token stream for a class with an attribute member.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            # * attribute: service
            service: ErrorService
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        # Member: attribute
        tok('ARTIFACT_MEMBER', '# * attribute: service'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'service'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'ErrorService'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
    ]

# ** fixture: annotated_section_tokens
@pytest.fixture
def annotated_section_tokens():
    '''
    Token stream for an OBSOLETE-annotated section with a class.
    Represents:
        # *** events
        # -- obsolete: replaced
        # ** event: old_event
        class OldEvent(DomainEvent):
            # * method: execute
            def execute(self):
                return None
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('OBSOLETE', '# -- obsolete: replaced'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: old_event'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'OldEvent'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('ARTIFACT_MEMBER', '# * method: execute'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('IDENTIFIER', 'execute'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('RETURN', 'return'),
        tok('PYTHON_KEYWORD', 'None'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# ** fixture: decorated_method_tokens
@pytest.fixture
def decorated_method_tokens():
    '''
    Token stream for a class with a decorated method and return annotation.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            # * method: execute
            @DomainEvent.parameters_required
            def execute(self, id: str) -> None:
                return result
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('ARTIFACT_MEMBER', '# * method: execute'),
        tok('NEWLINE', '\n'),
        # Decorator
        tok('AT', '@'),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'parameters_required'),
        tok('NEWLINE', '\n'),
        # Method def with params and return annotation
        tok('DEF', 'def'),
        tok('IDENTIFIER', 'execute'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('COMMA', ','),
        tok('IDENTIFIER', 'id'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'str'),
        tok('RPAREN', ')'),
        tok('ARROW', '->'),
        tok('PYTHON_KEYWORD', 'None'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'result'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# ** fixture: init_method_tokens
@pytest.fixture
def init_method_tokens():
    '''
    Token stream for a class with an __init__ method.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            # * init
            def __init__(self, svc: Service):
                self.svc = svc
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('ARTIFACT_MEMBER', '# * init'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('INIT', '__init__'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('COMMA', ','),
        tok('IDENTIFIER', 'svc'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'Service'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('SELF', 'self'),
        tok('DOT', '.'),
        tok('IDENTIFIER', 'svc'),
        tok('EQUALS', '='),
        tok('IDENTIFIER', 'svc'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# ** fixture: docstring_class_tokens
@pytest.fixture
def docstring_class_tokens():
    '''
    Token stream for a class with a docstring and method with docstring.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            \"\"\"Sample event.\"\"\"
            # * method: execute
            def execute(self):
                \"\"\"Run the event.\"\"\"
                return True
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('DOCSTRING', '"""Sample event."""'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_MEMBER', '# * method: execute'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('IDENTIFIER', 'execute'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('DOCSTRING', '"""Run the event."""'),
        tok('NEWLINE', '\n'),
        tok('RETURN', 'return'),
        tok('PYTHON_KEYWORD', 'True'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# ** fixture: snippet_with_comment_tokens
@pytest.fixture
def snippet_with_comment_tokens():
    '''
    Token stream for a method body with a line-comment-headed snippet.
    Represents:
        # *** events
        # ** event: sample
        class Sample(DomainEvent):
            # * method: execute
            def execute(self):
                # Do the work.
                result = compute()
                return result
    '''

    return [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        tok('ARTIFACT_MEMBER', '# * method: execute'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
        tok('IDENTIFIER', 'execute'),
        tok('LPAREN', '('),
        tok('SELF', 'self'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        # Snippet with comment header
        tok('LINE_COMMENT', '# Do the work.'),
        tok('NEWLINE', '\n'),
        tok('IDENTIFIER', 'result'),
        tok('EQUALS', '='),
        tok('IDENTIFIER', 'compute'),
        tok('LPAREN', '('),
        tok('RPAREN', ')'),
        tok('NEWLINE', '\n'),
        # Return statement (separate snippet, no comment)
        tok('RETURN', 'return'),
        tok('IDENTIFIER', 'result'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
        tok('DEDENT', ''),
    ]

# *** tests

# ** test: instantiation
def test_instantiation(parser: TiferetParser) -> None:
    '''
    Test that TiferetParser can be instantiated without errors.
    '''

    assert parser is not None
    assert parser.parser is not None


# ** test: implements_parser_service
def test_implements_parser_service(parser: TiferetParser) -> None:
    '''
    Test that TiferetParser is an instance of ParserService.
    '''

    from ...interfaces import ParserService
    assert isinstance(parser, ParserService)


# ** test: parse_minimal_imports
def test_parse_minimal_imports(parser: TiferetParser, minimal_import_tokens) -> None:
    '''
    Test parsing a minimal import group returns a Module with one group.
    '''

    ast = parser.parse(minimal_import_tokens)
    assert ast['type'] == 'Module'
    assert len(ast['groups']) == 1
    assert ast['groups'][0]['type'] == 'Group'
    assert ast['groups'][0]['header'] == '# *** imports'


# ** test: parse_import_section_body
def test_parse_import_section_body(parser: TiferetParser, minimal_import_tokens) -> None:
    '''
    Test that import sections produce an ImportBlock with ImportStmt nodes.
    '''

    ast = parser.parse(minimal_import_tokens)
    group = ast['groups'][0]
    assert len(group['sections']) == 1
    section = group['sections'][0]
    assert section['type'] == 'Section'
    assert section['header'] == '# ** core'
    assert section['body']['type'] == 'ImportBlock'
    assert len(section['body']['statements']) == 1
    assert section['body']['statements'][0]['type'] == 'ImportStmt'
    assert section['body']['statements'][0]['keyword'] == 'from'


# ** test: parse_minimal_event
def test_parse_minimal_event(parser: TiferetParser, minimal_event_tokens) -> None:
    '''
    Test parsing a minimal event class produces correct AST structure.
    '''

    ast = parser.parse(minimal_event_tokens)
    assert ast['type'] == 'Module'
    assert len(ast['groups']) == 1
    group = ast['groups'][0]
    assert group['header'] == '# *** events'
    assert len(group['sections']) == 1
    section = group['sections'][0]
    assert section['body']['type'] == 'ClassDef'
    assert section['body']['name'] == 'Sample'
    assert section['body']['bases'] == ['DomainEvent']


# ** test: parse_two_groups
def test_parse_two_groups(parser: TiferetParser, import_and_event_tokens) -> None:
    '''
    Test parsing a token stream with two groups (imports + events).
    '''

    ast = parser.parse(import_and_event_tokens)
    assert ast['type'] == 'Module'
    assert len(ast['groups']) == 2
    assert ast['groups'][0]['header'] == '# *** imports'
    assert ast['groups'][1]['header'] == '# *** events'


# ** test: parse_attribute_member
def test_parse_attribute_member(parser: TiferetParser, attribute_member_tokens) -> None:
    '''
    Test parsing a class with an attribute member produces AttrDecl.
    '''

    ast = parser.parse(attribute_member_tokens)
    class_def = ast['groups'][0]['sections'][0]['body']
    assert len(class_def['members']) == 1
    member = class_def['members'][0]
    assert member['type'] == 'Member'
    assert member['kind'] == 'attribute'
    assert member['body']['type'] == 'AttrDecl'
    assert member['body']['name'] == 'service'


# ** test: parse_annotated_section
def test_parse_annotated_section(parser: TiferetParser, annotated_section_tokens) -> None:
    '''
    Test parsing an OBSOLETE-annotated section.
    '''

    ast = parser.parse(annotated_section_tokens)
    section = ast['groups'][0]['sections'][0]
    assert len(section['annotations']) == 1
    assert section['annotations'][0]['type'] == 'Annot'
    assert section['annotations'][0]['kind'] == 'OBSOLETE'


# ** test: parse_decorated_method
def test_parse_decorated_method(parser: TiferetParser, decorated_method_tokens) -> None:
    '''
    Test parsing a decorated method with parameters and return annotation.
    '''

    ast = parser.parse(decorated_method_tokens)
    class_def = ast['groups'][0]['sections'][0]['body']
    member = class_def['members'][0]
    method = member['body']
    assert method['type'] == 'MethodDef'
    assert method['name'] == 'execute'
    assert method['decorator'] is not None
    assert method['decorator']['type'] == 'Decorator'
    assert method['return_type'] is not None
    assert len(method['params']) > 0


# ** test: parse_init_method
def test_parse_init_method(parser: TiferetParser, init_method_tokens) -> None:
    '''
    Test parsing a class with __init__ produces a Member with kind "init".
    '''

    ast = parser.parse(init_method_tokens)
    class_def = ast['groups'][0]['sections'][0]['body']
    member = class_def['members'][0]
    assert member['kind'] == 'init'
    assert member['body']['type'] == 'MethodDef'
    assert member['body']['name'] == '__init__'


# ** test: parse_class_docstring
def test_parse_class_docstring(parser: TiferetParser, docstring_class_tokens) -> None:
    '''
    Test that class and method docstrings are captured in the AST.
    '''

    ast = parser.parse(docstring_class_tokens)
    class_def = ast['groups'][0]['sections'][0]['body']
    assert class_def['docstring'] == '"""Sample event."""'
    method = class_def['members'][0]['body']
    assert method['docstring'] == '"""Run the event."""'


# ** test: parse_snippet_with_comment
def test_parse_snippet_with_comment(parser: TiferetParser, snippet_with_comment_tokens) -> None:
    '''
    Test that a comment-headed snippet collects all following statements.
    The left-recursive stmt_list consumes all statements after the LINE_COMMENT
    into a single snippet.
    '''

    ast = parser.parse(snippet_with_comment_tokens)
    class_def = ast['groups'][0]['sections'][0]['body']
    method = class_def['members'][0]['body']
    assert len(method['body']) >= 1
    commented_snippet = method['body'][0]
    assert commented_snippet['type'] == 'Snippet'
    assert commented_snippet['comment'] == '# Do the work.'
    # Both statements are consumed into this snippet's stmt_list
    assert len(commented_snippet['statements']) == 2


# ** test: parse_error_unexpected_token
def test_parse_error_unexpected_token(parser: TiferetParser) -> None:
    '''
    Test that an unexpected token raises SyntaxError with hierarchy terminology.
    '''

    # DEF directly under a group with no section header.
    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('DEF', 'def'),
    ]
    with pytest.raises(SyntaxError, match=r'Tiferet artifact hierarchy'):
        parser.parse(bad_tokens)


# ** test: parse_error_unexpected_eof
def test_parse_error_unexpected_eof(parser: TiferetParser) -> None:
    '''
    Test that unexpected end-of-input raises SyntaxError with hierarchy terminology.
    '''

    # Incomplete: group header with no newline or sections.
    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
    ]
    with pytest.raises(SyntaxError, match=r'Tiferet Domain Event structure'):
        parser.parse(bad_tokens)


# ** test: parse_error_class_no_section
def test_parse_error_class_no_section(parser: TiferetParser) -> None:
    '''
    Test that a CLASS directly under a group (missing section header) raises SyntaxError.
    '''

    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Foo'),
    ]
    with pytest.raises(SyntaxError):
        parser.parse(bad_tokens)


# ** test: parse_error_bare_attribute
def test_parse_error_bare_attribute(parser: TiferetParser) -> None:
    '''
    Test that a bare attribute inside a class (no member header) raises SyntaxError.
    '''

    bad_tokens = [
        tok('ARTIFACT_START', '# *** events'),
        tok('NEWLINE', '\n'),
        tok('ARTIFACT_SECTION', '# ** event: sample'),
        tok('NEWLINE', '\n'),
        tok('CLASS', 'class'),
        tok('IDENTIFIER', 'Sample'),
        tok('LPAREN', '('),
        tok('IDENTIFIER', 'DomainEvent'),
        tok('RPAREN', ')'),
        tok('COLON', ':'),
        tok('NEWLINE', '\n'),
        tok('INDENT', ''),
        # No ARTIFACT_MEMBER before the attribute
        tok('IDENTIFIER', 'service'),
        tok('COLON', ':'),
        tok('IDENTIFIER', 'ErrorService'),
        tok('NEWLINE', '\n'),
        tok('DEDENT', ''),
    ]
    with pytest.raises(SyntaxError):
        parser.parse(bad_tokens)
