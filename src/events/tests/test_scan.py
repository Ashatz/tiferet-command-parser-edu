"""Scanner Domain Event Tests"""

# *** imports

# ** core
import os
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError

# ** app
from ..settings import DomainEvent
from ..scan import (
    ExtractText,
    LexerInitialized,
    PerformLexicalAnalysis,
    EmitScanResult,
)
from ...interfaces import LexerService

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


# ** fixture: sample_text_blocks
@pytest.fixture
def sample_text_blocks() -> list:
    '''
    Return sample text blocks as extracted by ExtractText.

    :return: List of text block dicts.
    :rtype: list
    '''

    return [
        {
            'name': 'sample_event',
            'line_start': 7,
            'line_end': 13,
            'text': '# ** event: sample_event\nclass SampleEvent(DomainEvent):\n    pass\n',
            'length_chars': 70,
        },
    ]


# ** fixture: mock_lexer_service
@pytest.fixture
def mock_lexer_service() -> LexerService:
    '''
    Create a mock LexerService for testing.

    :return: A mock lexer service.
    :rtype: LexerService
    '''

    return mock.Mock(spec=LexerService)


# ** fixture: sample_analysis_result
@pytest.fixture
def sample_analysis_result() -> dict:
    '''
    Return a sample analysis result dict.

    :return: A sample analysis result.
    :rtype: dict
    '''

    return {
        'tokens': [
            {'type': 'ARTIFACT_SECTION', 'value': '# ** event: sample_event', 'line': 1, 'column': 0},
            {'type': 'CLASS', 'value': 'class', 'line': 2, 'column': 0},
            {'type': 'IDENTIFIER', 'value': 'SampleEvent', 'line': 2, 'column': 6},
        ],
        'token_count': 3,
        'metrics': {
            'commands_detected': 1,
            'execute_methods_found': 0,
            'verify_calls': 0,
            'service_calls': 0,
            'factory_calls': 0,
            'constants_referenced': 0,
            'docstrings_found': 0,
            'top_token_types': {'CLASS': 1, 'ARTIFACT_SECTION': 1, 'IDENTIFIER': 1},
        },
    }

# *** tests — ExtractText

# ** test: extract_text_success
def test_extract_text_success(sample_source_file: str) -> None:
    '''
    Test successful extraction of event blocks from a source file.

    :param sample_source_file: Path to the sample source file.
    :type sample_source_file: str
    '''

    # Execute the ExtractText event.
    result = DomainEvent.handle(
        ExtractText,
        source_file=sample_source_file,
    )

    # Assert imports block plus two event blocks were extracted.
    assert len(result) == 3
    assert result[0]['name'] == '__imports__'
    assert result[1]['name'] == 'sample_event'
    assert result[2]['name'] == 'another_event'
    assert result[0]['text'] is not None
    assert '# *** imports' in result[0]['text']
    assert len(result[1]['text']) > 0


# ** test: extract_text_with_filter
def test_extract_text_with_filter(sample_source_file: str) -> None:
    '''
    Test extraction with the extract filter limiting to a specific artifact.

    :param sample_source_file: Path to the sample source file.
    :type sample_source_file: str
    '''

    # Execute with extract filter for only sample_event.
    result = DomainEvent.handle(
        ExtractText,
        source_file=sample_source_file,
        extract='sample_event',
    )

    # Assert imports block plus the filtered block were returned.
    assert len(result) == 2
    assert result[0]['name'] == '__imports__'
    assert result[1]['name'] == 'sample_event'


# ** test: extract_text_missing_source_file_param
def test_extract_text_missing_source_file_param() -> None:
    '''
    Test that missing source_file parameter raises TiferetError.
    '''

    # Attempt extraction without source_file.
    with pytest.raises(TiferetError):
        DomainEvent.handle(ExtractText)


# ** test: extract_text_file_not_found
def test_extract_text_file_not_found() -> None:
    '''
    Test that a non-existent source file raises TiferetError.
    '''

    # Attempt extraction with a non-existent file.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            ExtractText,
            source_file='/nonexistent/file.py',
        )


# ** test: extract_text_no_matching_blocks
def test_extract_text_no_matching_blocks(tmp_path) -> None:
    '''
    Test that no matching blocks raises TiferetError.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Create a file with no event blocks.
    file_path = tmp_path / 'empty.py'
    file_path.write_text('# Just a regular comment\nx = 1\n')

    # Attempt extraction from a file with no matching blocks.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            ExtractText,
            source_file=str(file_path),
        )

# *** tests — LexerInitialized

# ** test: lexer_initialized_success
def test_lexer_initialized_success(sample_text_blocks: list) -> None:
    '''
    Test successful validation of text blocks.

    :param sample_text_blocks: Sample text blocks.
    :type sample_text_blocks: list
    '''

    # Execute the LexerInitialized event.
    result = DomainEvent.handle(
        LexerInitialized,
        text_blocks=sample_text_blocks,
    )

    # Assert the blocks are returned unchanged.
    assert result == sample_text_blocks


# ** test: lexer_initialized_missing_param
def test_lexer_initialized_missing_param() -> None:
    '''
    Test that missing text_blocks parameter raises TiferetError.
    '''

    # Attempt without text_blocks.
    with pytest.raises(TiferetError):
        DomainEvent.handle(LexerInitialized)


# ** test: lexer_initialized_empty_blocks
def test_lexer_initialized_empty_blocks() -> None:
    '''
    Test that empty text blocks list raises TiferetError.
    '''

    # Attempt with empty list.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            LexerInitialized,
            text_blocks=[],
        )


# ** test: lexer_initialized_empty_text
def test_lexer_initialized_empty_text() -> None:
    '''
    Test that a block with empty text raises TiferetError.
    '''

    # Attempt with a block that has blank text.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            LexerInitialized,
            text_blocks=[{'name': 'bad_block', 'text': '   '}],
        )

# *** tests — PerformLexicalAnalysis

# ** test: perform_lexical_analysis_success
def test_perform_lexical_analysis_success(
        mock_lexer_service: LexerService,
        sample_text_blocks: list,
    ) -> None:
    '''
    Test successful tokenization and metrics computation.

    :param mock_lexer_service: Mocked lexer service.
    :type mock_lexer_service: LexerService
    :param sample_text_blocks: Sample text blocks.
    :type sample_text_blocks: list
    '''

    # Arrange the lexer service to return sample tokens.
    mock_lexer_service.tokenize.return_value = [
        {'type': 'CLASS', 'value': 'class', 'line': 1, 'column': 0},
        {'type': 'IDENTIFIER', 'value': 'SampleEvent', 'line': 1, 'column': 6},
        {'type': 'EXECUTE', 'value': 'execute', 'line': 3, 'column': 8},
    ]

    # Execute via DomainEvent.handle with injected dependency.
    result = DomainEvent.handle(
        PerformLexicalAnalysis,
        dependencies={'lexer_service': mock_lexer_service},
        validated_blocks=sample_text_blocks,
    )

    # Assert the result structure.
    assert 'tokens' in result
    assert 'token_count' in result
    assert 'metrics' in result
    assert result['token_count'] == 3
    assert result['metrics']['commands_detected'] == 1
    assert result['metrics']['execute_methods_found'] == 1

    # Verify the lexer service was called.
    mock_lexer_service.tokenize.assert_called_once_with(sample_text_blocks[0]['text'])


# ** test: perform_lexical_analysis_missing_param
def test_perform_lexical_analysis_missing_param(
        mock_lexer_service: LexerService,
    ) -> None:
    '''
    Test that missing validated_blocks raises TiferetError.

    :param mock_lexer_service: Mocked lexer service.
    :type mock_lexer_service: LexerService
    '''

    # Attempt without validated_blocks.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            PerformLexicalAnalysis,
            dependencies={'lexer_service': mock_lexer_service},
        )

# *** tests — EmitScanResult

# ** test: emit_scan_result_default
def test_emit_scan_result_default(sample_analysis_result: dict) -> None:
    '''
    Test default emit returns tokens and token_count.

    :param sample_analysis_result: Sample analysis result.
    :type sample_analysis_result: dict
    '''

    # Execute the EmitScanResult event.
    result = DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
        analysis_result=sample_analysis_result,
    )

    # Assert default includes tokens and no metrics.
    assert result['event_type'] == 'TokensScanned'
    assert result['source_file'] == 'test.py'
    assert result['token_count'] == 3
    assert 'tokens' in result
    assert 'metrics' not in result


# ** test: emit_scan_result_summary_only
def test_emit_scan_result_summary_only(sample_analysis_result: dict) -> None:
    '''
    Test summary-only mode omits tokens and includes metrics.

    :param sample_analysis_result: Sample analysis result.
    :type sample_analysis_result: dict
    '''

    # Execute with summary_only flag.
    result = DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
        analysis_result=sample_analysis_result,
        summary_only=True,
    )

    # Assert tokens are omitted, metrics are present.
    assert 'tokens' not in result
    assert 'metrics' in result
    assert result['token_count'] == 3


# ** test: emit_scan_result_with_metrics
def test_emit_scan_result_with_metrics(sample_analysis_result: dict) -> None:
    '''
    Test with_metrics flag includes both tokens and metrics.

    :param sample_analysis_result: Sample analysis result.
    :type sample_analysis_result: dict
    '''

    # Execute with with_metrics flag.
    result = DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
        analysis_result=sample_analysis_result,
        with_metrics=True,
    )

    # Assert both tokens and metrics are present.
    assert 'tokens' in result
    assert 'metrics' in result


# ** test: emit_scan_result_no_analysis
def test_emit_scan_result_no_analysis() -> None:
    '''
    Test emit with no analysis_result uses empty defaults.
    '''

    # Execute without analysis_result.
    result = DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
    )

    # Assert default empty result.
    assert result['token_count'] == 0
    assert result['tokens'] == []


# ** test: emit_scan_result_write_yaml
def test_emit_scan_result_write_yaml(
        sample_analysis_result: dict,
        tmp_path,
    ) -> None:
    '''
    Test writing result to a YAML file.

    :param sample_analysis_result: Sample analysis result.
    :type sample_analysis_result: dict
    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Set the output path.
    output_path = str(tmp_path / 'result.yaml')

    # Execute with output path.
    DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
        analysis_result=sample_analysis_result,
        output=output_path,
    )

    # Assert the file was created with content.
    assert os.path.isfile(output_path)
    with open(output_path) as f:
        content = f.read()
    assert 'TokensScanned' in content


# ** test: emit_scan_result_write_json
def test_emit_scan_result_write_json(
        sample_analysis_result: dict,
        tmp_path,
    ) -> None:
    '''
    Test writing result to a JSON file.

    :param sample_analysis_result: Sample analysis result.
    :type sample_analysis_result: dict
    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Set the output path.
    output_path = str(tmp_path / 'result.json')

    # Execute with output path and json format.
    DomainEvent.handle(
        EmitScanResult,
        source_file='test.py',
        analysis_result=sample_analysis_result,
        output=output_path,
        output_format='json',
    )

    # Assert the file was created with JSON content.
    assert os.path.isfile(output_path)
    with open(output_path) as f:
        content = f.read()
    assert '"event_type"' in content
