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
from ..scan import ExtractText

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
