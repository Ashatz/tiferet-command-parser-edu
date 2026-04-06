"""Artifact Block Parser Utility"""

# *** imports

# ** core
import re
from typing import List, Dict, Any, Set, Optional

# *** utils

# ** util: artifact_block_parser
class ArtifactBlockParser:
    '''
    Utility for parsing Tiferet artifact blocks from source file lines.
    Extracts imports sections and group-typed artifact blocks
    (e.g. event, model, context) using the structured comment convention.
    '''

    # * method: parse_extract_filter (static)
    @staticmethod
    def parse_extract_filter(extract: str) -> Optional[Set[str]]:
        '''
        Parse a comma-separated extract filter string into a set of names.

        :param extract: Comma-separated artifact names, or None.
        :type extract: str
        :return: A set of stripped names, or None if extract is falsy.
        :rtype: Optional[Set[str]]
        '''

        # Return None if no filter provided.
        if not extract:
            return None

        # Split, strip, and return as a set.
        return set(name.strip() for name in extract.split(','))

    # * method: extract_imports_block (static)
    @staticmethod
    def extract_imports_block(lines: List[str]) -> Optional[Dict[str, Any]]:
        '''
        Locate and extract the imports section from source lines.
        The imports block spans from ``# *** imports`` to the next
        top-level ``# ***`` section.

        :param lines: The source file lines.
        :type lines: List[str]
        :return: A block dict with name, line_start, line_end, text,
                 and length_chars, or None if not found.
        :rtype: Optional[Dict[str, Any]]
        '''

        # Build patterns for imports start and next top-level section.
        imports_start_pattern = re.compile(r'^\s*#\s*\*{3}\s+imports\s*$')
        top_level_pattern = re.compile(r'^\s*#\s*\*{3}\s+\S+')

        # Walk lines to find the imports section boundaries.
        imports_start = None

        for i, line in enumerate(lines):
            if imports_start is None:
                if imports_start_pattern.match(line):
                    imports_start = i
            elif top_level_pattern.match(line):
                text = ''.join(lines[imports_start:i])
                return {
                    'name': '__imports__',
                    'line_start': imports_start,
                    'line_end': i,
                    'text': text,
                    'length_chars': len(text),
                }

        # Return None if no imports section found.
        return None

    # * method: extract_artifact_blocks (static)
    @staticmethod
    def extract_artifact_blocks(
            lines: List[str],
            group_type: str = 'event',
        ) -> List[Dict[str, Any]]:
        '''
        Walk source lines and extract all artifact blocks matching
        the given group type (e.g. ``# ** event: <name>``).

        :param lines: The source file lines.
        :type lines: List[str]
        :param group_type: The artifact group type to match.
        :type group_type: str
        :return: A list of block dicts with name, line_start, line_end,
                 text, and length_chars.
        :rtype: List[Dict[str, Any]]
        '''

        # Build the section pattern for the given group type.
        section_pattern = re.compile(
            rf'^\s*#\s*\*\*\s+{re.escape(group_type)}:\s+(\S+)'
        )

        # Walk lines to find matching artifact blocks.
        blocks = []
        current_block = None

        for i, line in enumerate(lines):
            match = section_pattern.match(line)

            if match:

                # Close the previous block if open.
                if current_block is not None:
                    current_block['line_end'] = i
                    current_block['text'] = ''.join(
                        lines[current_block['line_start']:i]
                    )
                    current_block['length_chars'] = len(current_block['text'])
                    blocks.append(current_block)

                # Start a new block.
                name = match.group(1)
                current_block = {
                    'name': name,
                    'line_start': i,
                    'line_end': None,
                    'text': None,
                    'length_chars': 0,
                }

        # Close the last block.
        if current_block is not None:
            current_block['line_end'] = len(lines)
            current_block['text'] = ''.join(
                lines[current_block['line_start']:]
            )
            current_block['length_chars'] = len(current_block['text'])
            blocks.append(current_block)

        # Return the extracted blocks.
        return blocks

    # * method: filter_blocks (static)
    @staticmethod
    def filter_blocks(
            blocks: List[Dict[str, Any]],
            extract_ids: Optional[Set[str]],
        ) -> List[Dict[str, Any]]:
        '''
        Apply an extract filter to a list of blocks.

        :param blocks: The artifact blocks to filter.
        :type blocks: List[Dict[str, Any]]
        :param extract_ids: Set of artifact names to keep, or None for all.
        :type extract_ids: Optional[Set[str]]
        :return: The filtered list of blocks.
        :rtype: List[Dict[str, Any]]
        '''

        # Return all blocks if no filter specified.
        if not extract_ids:
            return blocks

        # Filter to only blocks whose name is in the extract set.
        return [b for b in blocks if b['name'] in extract_ids]
