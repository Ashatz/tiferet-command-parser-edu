"""Scan Output Writer Utility"""

# *** imports

# ** core
import os
import json
from typing import Dict, Any, List, Optional, Set

# ** infra
import yaml

# *** classes

# ** class: scan_output_writer
class ScanOutputWriter:
    '''
    Utility for writing scan result payloads to file.
    Supports YAML and JSON formats with auto-detection from file extension.
    '''

    # * method: detect_format (static)
    @staticmethod
    def detect_format(output_path: str, output_format: str = 'yaml') -> str:
        '''
        Resolve the output format. If ``output_format`` is ``'auto'``,
        detect from the file extension; otherwise return ``output_format``
        unchanged.

        :param output_path: The target file path.
        :type output_path: str
        :param output_format: Explicit format or ``'auto'`` for detection.
        :type output_format: str
        :return: Resolved format string (``'yaml'`` or ``'json'``).
        :rtype: str
        '''

        # Auto-detect format from file extension.
        if output_format == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.json':
                return 'json'
            return 'yaml'

        # Return the explicit format.
        return output_format

    # * method: write (static)
    @staticmethod
    def write(result: Dict[str, Any], output_path: str, output_format: str = 'yaml') -> None:
        '''
        Write a result payload to a file in the specified format.

        :param result: The result payload to write.
        :type result: Dict[str, Any]
        :param output_path: The file path to write to.
        :type output_path: str
        :param output_format: The output format (``'yaml'``, ``'json'``, or ``'auto'``).
        :type output_format: str
        '''

        # Resolve the format.
        fmt = ScanOutputWriter.detect_format(output_path, output_format)

        # Write the output file.
        with open(output_path, 'w', encoding='utf-8') as f:
            if fmt == 'json':
                json.dump(result, f, indent=2, default=str)
            else:
                yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    # * method: parse_extract_names (static)
    @staticmethod
    def parse_extract_names(extract: str) -> Optional[List[str]]:
        '''
        Parse a comma-separated extract filter string into a list of names
        suitable for inclusion in the output payload.

        :param extract: Comma-separated artifact names, or None.
        :type extract: str
        :return: A list of stripped names, or None if extract is falsy.
        :rtype: Optional[List[str]]
        '''

        # Return None if no filter provided.
        if not extract:
            return None

        # Split, strip, and return as a list.
        return [name.strip() for name in extract.split(',')]
