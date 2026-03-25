"""Artifact Block Parser Utility Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..parser import ArtifactBlockParser

# *** fixtures

# ** fixture: sample_lines
@pytest.fixture
def sample_lines() -> list:
    '''
    Return sample source file lines containing imports and event artifact blocks.

    :return: List of source lines.
    :rtype: list
    '''

    content = (
        '# *** imports\n'
        '\n'
        '# ** app\n'
        'from .settings import DomainEvent\n'
        '\n'
        '# *** events\n'
        '\n'
        '# ** event: add_item\n'
        'class AddItem(DomainEvent):\n'
        '    pass\n'
        '\n'
        '# ** event: remove_item\n'
        'class RemoveItem(DomainEvent):\n'
        '    pass\n'
    )

    return content.splitlines(keepends=True)

# *** tests — parse_extract_filter

# ** test: parse_extract_filter_none
def test_parse_extract_filter_none() -> None:
    '''
    Test that None input returns None.
    '''

    # Parse a None extract value.
    result = ArtifactBlockParser.parse_extract_filter(None)

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_filter_empty_string
def test_parse_extract_filter_empty_string() -> None:
    '''
    Test that an empty string returns None.
    '''

    # Parse an empty string.
    result = ArtifactBlockParser.parse_extract_filter('')

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_filter_single
def test_parse_extract_filter_single() -> None:
    '''
    Test parsing a single artifact name.
    '''

    # Parse a single name.
    result = ArtifactBlockParser.parse_extract_filter('add_item')

    # Assert a set with one element.
    assert result == {'add_item'}


# ** test: parse_extract_filter_multiple
def test_parse_extract_filter_multiple() -> None:
    '''
    Test parsing comma-separated artifact names with whitespace.
    '''

    # Parse multiple names with spacing.
    result = ArtifactBlockParser.parse_extract_filter('add_item, remove_item , get_item')

    # Assert all names are stripped and present.
    assert result == {'add_item', 'remove_item', 'get_item'}

# *** tests — extract_imports_block

# ** test: extract_imports_block_found
def test_extract_imports_block_found(sample_lines: list) -> None:
    '''
    Test successful extraction of the imports block.

    :param sample_lines: Sample source lines.
    :type sample_lines: list
    '''

    # Extract the imports block.
    result = ArtifactBlockParser.extract_imports_block(sample_lines)

    # Assert the block was found with expected structure.
    assert result is not None
    assert result['name'] == '__imports__'
    assert result['line_start'] == 0
    assert '# *** imports' in result['text']
    assert 'from .settings import DomainEvent' in result['text']
    assert result['length_chars'] == len(result['text'])


# ** test: extract_imports_block_not_found
def test_extract_imports_block_not_found() -> None:
    '''
    Test that lines without an imports section return None.
    '''

    # Provide lines with no imports section.
    lines = ['x = 1\n', 'y = 2\n']

    # Extract the imports block.
    result = ArtifactBlockParser.extract_imports_block(lines)

    # Assert None is returned.
    assert result is None

# *** tests — extract_artifact_blocks

# ** test: extract_artifact_blocks_events
def test_extract_artifact_blocks_events(sample_lines: list) -> None:
    '''
    Test extraction of event artifact blocks.

    :param sample_lines: Sample source lines.
    :type sample_lines: list
    '''

    # Extract event blocks.
    blocks = ArtifactBlockParser.extract_artifact_blocks(sample_lines, 'event')

    # Assert two event blocks were found.
    assert len(blocks) == 2
    assert blocks[0]['name'] == 'add_item'
    assert blocks[1]['name'] == 'remove_item'
    assert 'class AddItem' in blocks[0]['text']
    assert 'class RemoveItem' in blocks[1]['text']


# ** test: extract_artifact_blocks_none_matching
def test_extract_artifact_blocks_none_matching(sample_lines: list) -> None:
    '''
    Test extraction with a group type that has no matches.

    :param sample_lines: Sample source lines.
    :type sample_lines: list
    '''

    # Extract blocks for a non-existent group type.
    blocks = ArtifactBlockParser.extract_artifact_blocks(sample_lines, 'model')

    # Assert empty list returned.
    assert blocks == []


# ** test: extract_artifact_blocks_line_boundaries
def test_extract_artifact_blocks_line_boundaries(sample_lines: list) -> None:
    '''
    Test that block line_start and line_end boundaries are correct.

    :param sample_lines: Sample source lines.
    :type sample_lines: list
    '''

    # Extract event blocks.
    blocks = ArtifactBlockParser.extract_artifact_blocks(sample_lines, 'event')

    # Assert first block starts at the event comment line.
    assert blocks[0]['line_start'] == 7

    # Assert second block starts at its event comment and ends at EOF.
    assert blocks[1]['line_start'] == 11
    assert blocks[1]['line_end'] == len(sample_lines)


# ** test: extract_artifact_blocks_length_chars
def test_extract_artifact_blocks_length_chars(sample_lines: list) -> None:
    '''
    Test that length_chars matches the actual text length.

    :param sample_lines: Sample source lines.
    :type sample_lines: list
    '''

    # Extract event blocks.
    blocks = ArtifactBlockParser.extract_artifact_blocks(sample_lines, 'event')

    # Assert length_chars matches text length for each block.
    for block in blocks:
        assert block['length_chars'] == len(block['text'])

# *** tests — filter_blocks

# ** test: filter_blocks_no_filter
def test_filter_blocks_no_filter() -> None:
    '''
    Test that None filter returns all blocks unchanged.
    '''

    # Create sample blocks.
    blocks = [
        {'name': 'add_item'},
        {'name': 'remove_item'},
    ]

    # Filter with None.
    result = ArtifactBlockParser.filter_blocks(blocks, None)

    # Assert all blocks returned.
    assert result == blocks


# ** test: filter_blocks_with_filter
def test_filter_blocks_with_filter() -> None:
    '''
    Test filtering to a subset of blocks by name.
    '''

    # Create sample blocks.
    blocks = [
        {'name': 'add_item'},
        {'name': 'remove_item'},
        {'name': 'get_item'},
    ]

    # Filter to only add_item and get_item.
    result = ArtifactBlockParser.filter_blocks(blocks, {'add_item', 'get_item'})

    # Assert only matching blocks returned.
    assert len(result) == 2
    assert result[0]['name'] == 'add_item'
    assert result[1]['name'] == 'get_item'


# ** test: filter_blocks_no_match
def test_filter_blocks_no_match() -> None:
    '''
    Test filtering with names that match no blocks.
    '''

    # Create sample blocks.
    blocks = [{'name': 'add_item'}]

    # Filter with a name not present.
    result = ArtifactBlockParser.filter_blocks(blocks, {'nonexistent'})

    # Assert empty list returned.
    assert result == []
