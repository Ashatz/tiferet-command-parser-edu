"""Scan Output Writer Utility Tests"""

# *** imports

# ** core
import os
import json

# ** infra
import pytest
import yaml

# ** app
from ..output import ScanOutputWriter

# *** tests — detect_format

# ** test: detect_format_auto_json
def test_detect_format_auto_json() -> None:
    '''
    Test auto-detection resolves .json extension to json format.
    '''

    # Detect format for a .json file path.
    result = ScanOutputWriter.detect_format('output.json', 'auto')

    # Assert json format detected.
    assert result == 'json'


# ** test: detect_format_auto_yaml
def test_detect_format_auto_yaml() -> None:
    '''
    Test auto-detection resolves .yaml extension to yaml format.
    '''

    # Detect format for a .yaml file path.
    result = ScanOutputWriter.detect_format('output.yaml', 'auto')

    # Assert yaml format detected.
    assert result == 'yaml'


# ** test: detect_format_auto_unknown_defaults_yaml
def test_detect_format_auto_unknown_defaults_yaml() -> None:
    '''
    Test auto-detection defaults to yaml for unknown extensions.
    '''

    # Detect format for a .txt file path.
    result = ScanOutputWriter.detect_format('output.txt', 'auto')

    # Assert yaml format as default.
    assert result == 'yaml'


# ** test: detect_format_explicit
def test_detect_format_explicit() -> None:
    '''
    Test that explicit format is returned regardless of file extension.
    '''

    # Detect format with explicit json, even for a .yaml path.
    result = ScanOutputWriter.detect_format('output.yaml', 'json')

    # Assert the explicit format is honored.
    assert result == 'json'

# *** tests — write

# ** test: write_yaml
def test_write_yaml(tmp_path) -> None:
    '''
    Test writing a result payload as YAML.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Build a sample payload.
    payload = {'event_type': 'TokensScanned', 'token_count': 5}

    # Write as YAML.
    output_path = str(tmp_path / 'result.yaml')
    ScanOutputWriter.write(payload, output_path, 'yaml')

    # Assert file was created and contains valid YAML.
    assert os.path.isfile(output_path)
    with open(output_path) as f:
        loaded = yaml.safe_load(f)
    assert loaded['event_type'] == 'TokensScanned'
    assert loaded['token_count'] == 5


# ** test: write_json
def test_write_json(tmp_path) -> None:
    '''
    Test writing a result payload as JSON.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Build a sample payload.
    payload = {'event_type': 'TokensScanned', 'token_count': 5}

    # Write as JSON.
    output_path = str(tmp_path / 'result.json')
    ScanOutputWriter.write(payload, output_path, 'json')

    # Assert file was created and contains valid JSON.
    assert os.path.isfile(output_path)
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['event_type'] == 'TokensScanned'
    assert loaded['token_count'] == 5


# ** test: write_auto_json
def test_write_auto_json(tmp_path) -> None:
    '''
    Test that auto format writes JSON when the path ends in .json.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Build a sample payload.
    payload = {'event_type': 'TokensScanned'}

    # Write with auto format to a .json path.
    output_path = str(tmp_path / 'result.json')
    ScanOutputWriter.write(payload, output_path, 'auto')

    # Assert valid JSON was written.
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['event_type'] == 'TokensScanned'

# *** tests — parse_extract_names

# ** test: parse_extract_names_none
def test_parse_extract_names_none() -> None:
    '''
    Test that None input returns None.
    '''

    # Parse None.
    result = ScanOutputWriter.parse_extract_names(None)

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_names_empty
def test_parse_extract_names_empty() -> None:
    '''
    Test that empty string returns None.
    '''

    # Parse empty string.
    result = ScanOutputWriter.parse_extract_names('')

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_names_single
def test_parse_extract_names_single() -> None:
    '''
    Test parsing a single artifact name returns a one-element list.
    '''

    # Parse a single name.
    result = ScanOutputWriter.parse_extract_names('add_item')

    # Assert list with one element.
    assert result == ['add_item']


# ** test: parse_extract_names_multiple
def test_parse_extract_names_multiple() -> None:
    '''
    Test parsing comma-separated names with whitespace preserves order.
    '''

    # Parse multiple names.
    result = ScanOutputWriter.parse_extract_names('add_item, remove_item , get_item')

    # Assert all names stripped and present in order.
    assert result == ['add_item', 'remove_item', 'get_item']
