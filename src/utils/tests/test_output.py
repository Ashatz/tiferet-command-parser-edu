"""Output Utility Tests"""

# *** imports

# ** core
import os
import json

# ** infra
import yaml

# ** app
from ..output import OutputWriter, ResultPayloadBuilder, emit

# *** tests — detect_format

# ** test: detect_format_auto_json
def test_detect_format_auto_json() -> None:
    '''
    Test auto-detection resolves .json extension to json format.
    '''

    # Detect format for a .json file path.
    result = OutputWriter.detect_format('output.json', 'auto')

    # Assert json format detected.
    assert result == 'json'


# ** test: detect_format_auto_yaml
def test_detect_format_auto_yaml() -> None:
    '''
    Test auto-detection resolves .yaml extension to yaml format.
    '''

    # Detect format for a .yaml file path.
    result = OutputWriter.detect_format('output.yaml', 'auto')

    # Assert yaml format detected.
    assert result == 'yaml'


# ** test: detect_format_auto_unknown_defaults_yaml
def test_detect_format_auto_unknown_defaults_yaml() -> None:
    '''
    Test auto-detection defaults to yaml for unknown extensions.
    '''

    # Detect format for a .txt file path.
    result = OutputWriter.detect_format('output.txt', 'auto')

    # Assert yaml format as default.
    assert result == 'yaml'


# ** test: detect_format_auto_keter
def test_detect_format_auto_keter() -> None:
    '''
    Test auto-detection resolves .keter extension to keter format.
    '''

    # Detect format for a .keter file path.
    result = OutputWriter.detect_format('output.keter', 'auto')

    # Assert keter format detected.
    assert result == 'keter'


# ** test: detect_format_explicit
def test_detect_format_explicit() -> None:
    '''
    Test that explicit format is returned regardless of file extension.
    '''

    # Detect format with explicit json, even for a .yaml path.
    result = OutputWriter.detect_format('output.yaml', 'json')

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
    OutputWriter.write(payload, output_path, 'yaml')

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
    OutputWriter.write(payload, output_path, 'json')

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
    OutputWriter.write(payload, output_path, 'auto')

    # Assert valid JSON was written.
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['event_type'] == 'TokensScanned'


# ** test: write_keter_string
def test_write_keter_string(tmp_path) -> None:
    '''
    Test that writing a keter string writes plain text.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Write a plain keter string.
    output_path = str(tmp_path / 'output.keter')
    OutputWriter.write('EventGroup(name)\n', output_path, 'keter')

    # Assert the file contains the exact string.
    with open(output_path) as f:
        assert f.read() == 'EventGroup(name)\n'


# *** tests — parse_extract_names

# ** test: parse_extract_names_none
def test_parse_extract_names_none() -> None:
    '''
    Test that None input returns None.
    '''

    # Parse None.
    result = OutputWriter.parse_extract_names(None)

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_names_empty
def test_parse_extract_names_empty() -> None:
    '''
    Test that empty string returns None.
    '''

    # Parse empty string.
    result = OutputWriter.parse_extract_names('')

    # Assert None is returned.
    assert result is None


# ** test: parse_extract_names_single
def test_parse_extract_names_single() -> None:
    '''
    Test parsing a single artifact name returns a one-element list.
    '''

    # Parse a single name.
    result = OutputWriter.parse_extract_names('add_item')

    # Assert list with one element.
    assert result == ['add_item']


# ** test: parse_extract_names_multiple
def test_parse_extract_names_multiple() -> None:
    '''
    Test parsing comma-separated names with whitespace preserves order.
    '''

    # Parse multiple names.
    result = OutputWriter.parse_extract_names('add_item, remove_item , get_item')

    # Assert all names stripped and present in order.
    assert result == ['add_item', 'remove_item', 'get_item']


# *** tests — anchored YAML output

# ** test: anchored_yaml_output
def test_anchored_yaml_output(tmp_path) -> None:
    '''
    Test that writing YAML with shared list references produces & and * markers.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Build a payload with shared list references.
    shared_params = ['a:int:true::', 'b:int:true::']
    payload = {
        'evt_grp': {
            'name': 'test',
            'evts': {
                'add': {'execute': {'params': shared_params}},
                'sub': {'execute': {'params': shared_params}},
            },
        }
    }

    # Write YAML.
    output_path = str(tmp_path / 'anchored.yaml')
    OutputWriter.write(payload, output_path, 'yaml')

    # Read the raw YAML text.
    with open(output_path) as f:
        content = f.read()

    # Assert anchor and alias markers are present.
    assert '&' in content
    assert '*' in content

    # Assert the YAML is still valid and round-trips correctly.
    loaded = yaml.safe_load(content)
    assert loaded['evt_grp']['evts']['add']['execute']['params'] == ['a:int:true::', 'b:int:true::']


# *** tests — emit helper

# ** test: emit_returns_payload_without_output
def test_emit_returns_payload_without_output() -> None:
    '''
    Test that emit returns the payload unchanged when no output path is given.
    '''

    # Invoke with no output path.
    payload = {'key': 'value'}
    result = emit(payload)

    # Assert the payload is returned unchanged.
    assert result is payload


# ** test: emit_writes_and_returns_payload
def test_emit_writes_and_returns_payload(tmp_path) -> None:
    '''
    Test that emit writes the payload to file and returns it unchanged.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Invoke with an output path.
    payload = {'event_type': 'TokensScanned'}
    output_path = str(tmp_path / 'result.json')
    result = emit(payload, output=output_path)

    # Assert the payload is returned and the file was written.
    assert result is payload
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['event_type'] == 'TokensScanned'


# *** tests — ResultPayloadBuilder

# ** test: build_envelope
def test_build_envelope() -> None:
    '''
    Test that build_envelope returns a dict with the expected shape.
    '''

    # Build the envelope.
    result = ResultPayloadBuilder.build_envelope('TokensScanned', 'test.py')

    # Assert the shape.
    assert result['event_type'] == 'TokensScanned'
    assert result['source_file'] == 'test.py'
    assert 'timestamp' in result


# ** test: build_scan_payload
def test_build_scan_payload() -> None:
    '''
    Test that build_scan_payload produces a TokensScanned envelope.
    '''

    # Build a scan payload with no tokens.
    result = ResultPayloadBuilder.build_scan_payload('test.py', None)

    # Assert the shape.
    assert result['event_type'] == 'TokensScanned'
    assert result['tokens'] == []
    assert result['token_count'] == 0


# ** test: build_codegen_payload_passthrough
def test_build_codegen_payload_passthrough() -> None:
    '''
    Test that build_codegen_payload returns the codegen dict unchanged.
    '''

    # Build with a sample dict.
    codegen = {'evt_grp': {'name': 'test'}}
    result = ResultPayloadBuilder.build_codegen_payload(codegen)

    # Assert the same dict is returned.
    assert result is codegen
