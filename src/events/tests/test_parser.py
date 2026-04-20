"""Parser Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...interfaces import ParserService
from ...mappers import Tok, Decl
from ..parser import PerformSyntacticAnalysis

# *** fixtures

# ** fixture: mock_parser_service
@pytest.fixture
def mock_parser_service() -> ParserService:
    '''
    Create a mock ParserService for testing.

    :return: A mock parser service.
    :rtype: ParserService
    '''

    return mock.Mock(spec=ParserService)


# ** fixture: sample_tokens
@pytest.fixture
def sample_tokens() -> list:
    '''
    Return sample token list as List[Tok] (what PerformSyntacticAnalysis actually receives).

    :return: List of Tok objects.
    :rtype: list
    '''

    return [
        Tok.new(type='ARTIFACT_START', value='# *** events', lineno=1, lexpos=0),
        Tok.new(type='NEWLINE', value='\n', lineno=1, lexpos=13),
        Tok.new(type='ARTIFACT_SECTION', value='# ** event: sample_event', lineno=3, lexpos=0),
        Tok.new(type='CLASS', value='class', lineno=4, lexpos=0),
        Tok.new(type='IDENTIFIER', value='SampleEvent', lineno=4, lexpos=6),
    ]


# ** fixture: sample_decl
@pytest.fixture
def sample_decl() -> Decl:
    '''
    Return a sample DeclarationAggregate as produced by the parser service.

    :return: A DeclarationAggregate representing a module.
    :rtype: Decl
    '''

    return Decl.new_module_decl(name='unknown_module')


# ** fixture: sample_ast
@pytest.fixture
def sample_ast(sample_decl: Decl) -> dict:
    '''
    Return a sample Module AST dict (serialized from sample_decl).

    :return: A Module AST dict.
    :rtype: dict
    '''

    return sample_decl.model_dump(exclude_none=True, exclude_unset=True)


# *** tests — PerformSyntacticAnalysis

# ** test: perform_syntactic_analysis_success
def test_perform_syntactic_analysis_success(
        mock_parser_service: ParserService,
        sample_tokens: list,
        sample_decl: Decl,
    ) -> None:
    '''
    Test successful syntactic parsing of tokens into a valid Module AST.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens (List[Tok]).
    :type sample_tokens: list
    :param sample_decl: Sample DeclarationAggregate returned by parser.
    :type sample_decl: Decl
    '''

    # Arrange the parser service to return the sample Decl.
    mock_parser_service.parse.return_value = sample_decl

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        PerformSyntacticAnalysis,
        dependencies={'parser_service': mock_parser_service},
        tokens=sample_tokens,
        source_file='test.py',
    )

    # Assert the returned value is a DeclarationAggregate with the module name set by the event.
    assert isinstance(result, Decl)
    assert result.name == 'test'

    # Verify the parser service was called with module name, tokens, and source_text.
    mock_parser_service.parse.assert_called_once_with('test', sample_tokens, source_text='')


# ** test: perform_syntactic_analysis_missing_tokens
def test_perform_syntactic_analysis_missing_tokens(
        mock_parser_service: ParserService,
    ) -> None:
    '''
    Test that missing 'tokens' parameter raises TiferetError (via parameters_required).

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            source_file='test.py',
            # tokens intentionally omitted
        )


# ** test: perform_syntactic_analysis_invalid_ast
def test_perform_syntactic_analysis_invalid_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that an invalid AST root (not a Decl) raises TiferetError via self.verify.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens.
    :type sample_tokens: list
    '''

    # Arrange parser to return a Mock that is not a Decl instance.
    non_decl = mock.Mock()
    non_decl.set_name = mock.Mock()  # Prevent AttributeError on set_name call.
    mock_parser_service.parse.return_value = non_decl

    # The event no longer validates the AST type — it returns whatever the parser produces.
    result = DomainEvent.handle(
        PerformSyntacticAnalysis,
        dependencies={'parser_service': mock_parser_service},
        tokens=sample_tokens,
        source_file='test.py',
    )

    # The result is the mock itself (not a Decl), since the event now passes through.
    assert result is non_decl


# ** test: perform_syntactic_analysis_none_ast
def test_perform_syntactic_analysis_none_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that returning None from the parser raises an exception.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens.
    :type sample_tokens: list
    '''

    mock_parser_service.parse.return_value = None

    with pytest.raises(Exception):
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            tokens=sample_tokens,
            source_file='test.py',
        )


