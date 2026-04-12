"""Parser Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...interfaces import ParserService
from ...mappers import TokenAggregate
from ..parser import PerformSyntacticAnalysis, EmitParseResult

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
    Return sample token list as List[TokenAggregate] (what PerformSyntacticAnalysis actually receives).

    :return: List of TokenAggregate objects.
    :rtype: list
    '''

    return [
        TokenAggregate.new(type='ARTIFACT_START', value='# *** events', lineno=1, lexpos=0),
        TokenAggregate.new(type='NEWLINE', value='\n', lineno=1, lexpos=13),
        TokenAggregate.new(type='ARTIFACT_SECTION', value='# ** event: sample_event', lineno=3, lexpos=0),
        TokenAggregate.new(type='CLASS', value='class', lineno=4, lexpos=0),
        TokenAggregate.new(type='IDENTIFIER', value='SampleEvent', lineno=4, lexpos=6),
    ]


# ** fixture: sample_ast
@pytest.fixture
def sample_ast() -> dict:
    '''
    Return a sample Module AST as produced by the parser service.

    :return: A Module AST dict.
    :rtype: dict
    '''

    return {
        'type': 'Module',
        'groups': [
            {
                'type': 'Group',
                'header': '# *** events',
                'sections': [
                    {
                        'type': 'Section',
                        'header': '# ** event: sample_event',
                        'annotations': [],
                        'body': {
                            'type': 'ClassDef',
                            'name': 'SampleEvent',
                            'bases': ['DomainEvent'],
                            'docstring': None,
                            'members': [],
                        },
                    },
                ],
            },
        ],
    }


# *** tests — PerformSyntacticAnalysis

# ** test: perform_syntactic_analysis_success
def test_perform_syntactic_analysis_success(
        mock_parser_service: ParserService,
        sample_tokens: list,
        sample_ast: dict,
    ) -> None:
    '''
    Test successful syntactic parsing of tokens into a valid Module AST.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens (List[TokenAggregate]).
    :type sample_tokens: list
    :param sample_ast: Expected AST result.
    :type sample_ast: dict
    '''

    # Arrange the parser service to return the sample AST.
    mock_parser_service.parse.return_value = sample_ast

    # Execute via DomainEvent.handle (passes tokens directly).
    result = DomainEvent.handle(
        PerformSyntacticAnalysis,
        dependencies={'parser_service': mock_parser_service},
        tokens=sample_tokens,
    )

    # Assert the returned value is the AST dict with Module root.
    assert isinstance(result, dict)
    assert result['type'] == 'Module'
    assert len(result.get('groups', [])) == 1

    # Verify the parser service was called with the exact tokens list.
    mock_parser_service.parse.assert_called_once_with(sample_tokens)


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
            # tokens intentionally omitted
        )


# ** test: perform_syntactic_analysis_invalid_ast
def test_perform_syntactic_analysis_invalid_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that an invalid AST root (not a Module) raises TiferetError via self.verify.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens.
    :type sample_tokens: list
    '''

    # Arrange parser to return something that fails the Module check.
    mock_parser_service.parse.return_value = {'type': 'InvalidRoot'}

    with pytest.raises(TiferetError) as exc_info:
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            tokens=sample_tokens,
        )

    assert exc_info.value.error_code == 'INVALID_AST_STRUCTURE'


# ** test: perform_syntactic_analysis_none_ast
def test_perform_syntactic_analysis_none_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that returning None from the parser raises TiferetError.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample tokens.
    :type sample_tokens: list
    '''

    mock_parser_service.parse.return_value = None

    with pytest.raises(TiferetError) as exc_info:
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            tokens=sample_tokens,
        )

    assert exc_info.value.error_code == 'INVALID_AST_STRUCTURE'


# *** tests — EmitParseResult

# ** test: emit_parse_result_default
def test_emit_parse_result_default(
        sample_ast: dict,
        sample_tokens: list,
    ) -> None:
    '''
    Test default EmitParseResult behavior (includes tokens, no summary-only).
    '''

    result = DomainEvent.handle(
        EmitParseResult,
        ast=sample_ast,
        tokens=sample_tokens,
        source_file='test.py',
    )

    assert result['event_type'] == 'ParseCompleted'
    assert result['source_file'] == 'test.py'
    assert result['token_count'] == len(sample_tokens)
    assert result['ast'] == sample_ast
    assert 'tokens' in result
    assert len(result['tokens']) == len(sample_tokens)
    assert 'timestamp' in result


# ** test: emit_parse_result_summary_only
def test_emit_parse_result_summary_only(
        sample_ast: dict,
        sample_tokens: list,
    ) -> None:
    '''
    Test that summary_only=True omits the full tokens list.
    '''

    result = DomainEvent.handle(
        EmitParseResult,
        ast=sample_ast,
        tokens=sample_tokens,
        source_file='test.py',
        summary_only=True,
    )

    assert 'tokens' not in result
    assert 'metrics' in result


# ** test: emit_parse_result_with_extract