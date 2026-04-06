"""Parser Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError

# ** app
from ..settings import DomainEvent
from ..parser import ParserInitialized, PerformSyntacticAnalysis, SyntacticAnalysisCompleted
from ...interfaces import ParserService

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
    Return sample token list as produced by PerformLexicalAnalysis.

    :return: List of token dicts.
    :rtype: list
    '''

    return [
        {'type': 'ARTIFACT_START', 'value': '# *** events', 'line': 1, 'column': 0},
        {'type': 'NEWLINE', 'value': '\n', 'line': 1, 'column': 13},
        {'type': 'ARTIFACT_SECTION', 'value': '# ** event: sample_event', 'line': 3, 'column': 0},
        {'type': 'NEWLINE', 'value': '\n', 'line': 3, 'column': 24},
        {'type': 'CLASS', 'value': 'class', 'line': 4, 'column': 0},
        {'type': 'IDENTIFIER', 'value': 'SampleEvent', 'line': 4, 'column': 6},
    ]

# ** fixture: sample_ast
@pytest.fixture
def sample_ast() -> dict:
    '''
    Return a sample Module AST as produced by TiferetParser.

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

# *** tests — ParserInitialized

# ** test: parser_initialized_success
def test_parser_initialized_success(mock_parser_service: ParserService) -> None:
    '''
    Test successful validation of the parser service.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    '''

    # Execute the ParserInitialized event.
    result = DomainEvent.handle(
        ParserInitialized,
        dependencies={'parser_service': mock_parser_service},
    )

    # Assert the parser service is returned.
    assert result is mock_parser_service


# ** test: parser_initialized_none_service
def test_parser_initialized_none_service() -> None:
    '''
    Test that a None parser service raises TiferetError.
    '''

    # Attempt with None parser service.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            ParserInitialized,
            dependencies={'parser_service': None},
        )

# *** tests — PerformSyntacticAnalysis

# ** test: perform_syntactic_analysis_success
def test_perform_syntactic_analysis_success(
        mock_parser_service: ParserService,
        sample_tokens: list,
        sample_ast: dict,
    ) -> None:
    '''
    Test successful syntactic parsing of tokens into AST.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample token list.
    :type sample_tokens: list
    :param sample_ast: Expected AST result.
    :type sample_ast: dict
    '''

    # Arrange the parser service to return the sample AST.
    mock_parser_service.parse.return_value = sample_ast

    # Build analysis_result as produced by PerformLexicalAnalysis.
    analysis_result = {
        'tokens': sample_tokens,
        'token_count': len(sample_tokens),
        'metrics': {},
    }

    # Execute via DomainEvent.handle with injected dependency.
    result = DomainEvent.handle(
        PerformSyntacticAnalysis,
        dependencies={'parser_service': mock_parser_service},
        analysis_result=analysis_result,
    )

    # Assert the AST structure is correct.
    assert isinstance(result, dict)
    assert result['type'] == 'Module'
    assert len(result['groups']) == 1

    # Verify the parser service was called with the tokens.
    mock_parser_service.parse.assert_called_once_with(sample_tokens)


# ** test: perform_syntactic_analysis_missing_analysis_result
def test_perform_syntactic_analysis_missing_analysis_result(
        mock_parser_service: ParserService,
    ) -> None:
    '''
    Test that missing analysis_result parameter raises TiferetError.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    '''

    # Attempt without analysis_result.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
        )


# ** test: perform_syntactic_analysis_invalid_ast
def test_perform_syntactic_analysis_invalid_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that an invalid AST root raises TiferetError.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample token list.
    :type sample_tokens: list
    '''

    # Arrange the parser to return a non-Module dict.
    mock_parser_service.parse.return_value = {'type': 'InvalidRoot'}

    # Build analysis_result with sample tokens.
    analysis_result = {
        'tokens': sample_tokens,
        'token_count': len(sample_tokens),
        'metrics': {},
    }

    # Attempt parsing with an invalid AST result.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            analysis_result=analysis_result,
        )


# ** test: perform_syntactic_analysis_none_ast
def test_perform_syntactic_analysis_none_ast(
        mock_parser_service: ParserService,
        sample_tokens: list,
    ) -> None:
    '''
    Test that a None AST result raises TiferetError.

    :param mock_parser_service: Mocked parser service.
    :type mock_parser_service: ParserService
    :param sample_tokens: Sample token list.
    :type sample_tokens: list
    '''

    # Arrange the parser to return None.
    mock_parser_service.parse.return_value = None

    # Build analysis_result with sample tokens.
    analysis_result = {
        'tokens': sample_tokens,
        'token_count': len(sample_tokens),
        'metrics': {},
    }

    # Attempt parsing with a None result.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformSyntacticAnalysis,
            dependencies={'parser_service': mock_parser_service},
            analysis_result=analysis_result,
        )

# *** tests — SyntacticAnalysisCompleted

# ** test: syntactic_analysis_completed_success
def test_syntactic_analysis_completed_success(sample_ast: dict) -> None:
    '''
    Test successful finalization of syntactic analysis.

    :param sample_ast: Sample Module AST.
    :type sample_ast: dict
    '''

    # Execute the SyntacticAnalysisCompleted event.
    result = DomainEvent.handle(
        SyntacticAnalysisCompleted,
        ast=sample_ast,
    )

    # Assert the enriched payload structure.
    assert result['event_type'] == 'SyntacticAnalysisCompleted'
    assert result['ast'] is sample_ast
    assert result['group_count'] == 1


# ** test: syntactic_analysis_completed_empty_groups
def test_syntactic_analysis_completed_empty_groups() -> None:
    '''
    Test finalization with an AST that has no groups.
    '''

    # Create an AST with empty groups.
    ast = {'type': 'Module', 'groups': []}

    # Execute the event.
    result = DomainEvent.handle(
        SyntacticAnalysisCompleted,
        ast=ast,
    )

    # Assert group_count is zero.
    assert result['group_count'] == 0
    assert result['ast'] is ast


# ** test: syntactic_analysis_completed_missing_ast
def test_syntactic_analysis_completed_missing_ast() -> None:
    '''
    Test that a missing AST raises TiferetError.
    '''

    # Attempt without ast parameter.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            SyntacticAnalysisCompleted,
            ast=None,
        )
