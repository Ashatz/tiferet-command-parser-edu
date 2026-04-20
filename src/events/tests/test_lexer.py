"""Scanner Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...interfaces import LexerService
from ...mappers import TokenAggregate
from ..lexer import PerformLexicalAnalysis

# *** fixtures

# ** fixture: sample_source_file
@pytest.fixture
def sample_source_file(tmp_path) -> str:
    '''
    Create a temporary Python source file with Tiferet event artifacts.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    :return: Path to the temporary source file.
    :rtype: str
    '''

    content = '''# *** imports

# ** app
from .settings import DomainEvent

# *** events

# ** event: sample_event
class SampleEvent(DomainEvent):
    \'\'\'A sample event.\'\'\'

    def execute(self, **kwargs):
        return True

# ** event: another_event
class AnotherEvent(DomainEvent):
    \'\'\'Another event.\'\'\'

    def execute(self, **kwargs):
        return False
'''

    file_path = tmp_path / 'sample_events.py'
    file_path.write_text(content)
    return str(file_path)


# ** fixture: mock_lexer_service
@pytest.fixture
def mock_lexer_service() -> LexerService:
    '''
    Create a mock LexerService for testing.

    :return: A mock lexer service.
    :rtype: LexerService
    '''

    return mock.Mock(spec=LexerService)


# *** tests

# ** test: perform_lexical_analysis_success
def test_perform_lexical_analysis_success(
        mock_lexer_service: LexerService,
        sample_source_file: str,
    ) -> None:
    '''
    Test successful full-file tokenization via PerformLexicalAnalysis.

    :param mock_lexer_service: Mocked lexer service.
    :type mock_lexer_service: LexerService
    :param sample_source_file: Temporary source file path.
    :type sample_source_file: str
    '''

    # Arrange lexer to return sample tokens.
    mock_tokens = [
        TokenAggregate.new(type='ARTIFACT_START', value='# *** imports', lineno=1, lexpos=0),
        TokenAggregate.new(type='CLASS', value='class', lineno=2, lexpos=0),
        TokenAggregate.new(type='IDENTIFIER', value='SampleEvent', lineno=2, lexpos=6),
    ]

    mock_lexer_service.tokenize.return_value = mock_tokens

    # Execute via DomainEvent.handle (injects lexer_service).
    result = DomainEvent.handle(
        PerformLexicalAnalysis,
        dependencies={'lexer_service': mock_lexer_service},
        source_file=sample_source_file,
    )

    # Assert structure matches current module (PerformLexicalAnalysis returns list of TokenAggregate).
    assert isinstance(result, list)
    assert len(result) == len(mock_tokens)
    assert all(isinstance(t, TokenAggregate) for t in result)

    # Verify lexer was called with full file content.
    mock_lexer_service.tokenize.assert_called_once()
    called_text = mock_lexer_service.tokenize.call_args[0][0]
    assert '# *** imports' in called_text
    assert 'class SampleEvent' in called_text


# ** test: perform_lexical_analysis_missing_source_file
def test_perform_lexical_analysis_missing_source_file(
        mock_lexer_service: LexerService,
    ) -> None:
    '''
    Test that missing source_file raises TiferetError (via parameters_required).

    :param mock_lexer_service: Mocked lexer service.
    :type mock_lexer_service: LexerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformLexicalAnalysis,
            dependencies={'lexer_service': mock_lexer_service},
            # source_file intentionally omitted
        )


