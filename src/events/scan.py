"""Scanner Domain Events"""

# *** imports

# ** core
import os
import re
from collections import Counter
from typing import List, Dict, Any

# ** app
from .settings import DomainEvent, a
from ..interfaces import LexerService

# *** events

# ** event: extract_text
class ExtractText(DomainEvent):
    '''
    Event to locate and extract matching artifact blocks from a source file.
    Filters by group_type (e.g. "event") and optional extracted_ids.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['source_file'])
    def execute(self,
            source_file: str,
            group_type: str = 'event',
            extract: str = None,
            **kwargs,
        ) -> List[Dict[str, Any]]:
        '''
        Extract text blocks matching the artifact pattern from the source file.

        :param source_file: Path to the Python source file.
        :type source_file: str
        :param group_type: The artifact group type to extract (default: "event").
        :type group_type: str
        :param extract: Comma-separated artifact names to extract (optional).
        :type extract: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A list of extracted text block dicts.
        :rtype: List[Dict[str, Any]]
        '''

        # Verify the source file exists.
        self.verify(
            expression=os.path.isfile(source_file),
            error_code='SOURCE_FILE_NOT_FOUND',
            message=f'Source file not found: {source_file}',
            source_file=source_file,
        )

        # Read the source file contents.
        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Build patterns for the given group type and imports section.
        section_pattern = re.compile(
            rf'^\s*#\s*\*\*\s+{re.escape(group_type)}:\s+(\S+)'
        )
        imports_start_pattern = re.compile(r'^\s*#\s*\*{3}\s+imports\s*$')
        top_level_pattern = re.compile(r'^\s*#\s*\*{3}\s+\S+')

        # Parse optional extract filter into a set.
        extract_ids = None
        if extract:
            extract_ids = set(name.strip() for name in extract.split(','))

        # Locate the imports section (from # *** imports to next # *** section).
        imports_block = None
        imports_start = None

        for i, line in enumerate(lines):
            if imports_start is None:
                if imports_start_pattern.match(line):
                    imports_start = i
            elif top_level_pattern.match(line):
                imports_block = {
                    'name': '__imports__',
                    'line_start': imports_start,
                    'line_end': i,
                    'text': ''.join(lines[imports_start:i]),
                    'length_chars': 0,
                }
                imports_block['length_chars'] = len(imports_block['text'])
                break

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

        # Apply extract filter if specified (imports are always included).
        if extract_ids:
            blocks = [b for b in blocks if b['name'] in extract_ids]

        # Prepend the imports block if found.
        if imports_block:
            blocks.insert(0, imports_block)

        # Verify at least one block was found.
        self.verify(
            expression=len(blocks) > 0,
            error_code='TEXT_EXTRACTION_FAILED',
            message=f'No {group_type} blocks found in {source_file}.',
            source_file=source_file,
            group_type=group_type,
        )

        # Return the extracted blocks.
        return blocks


# ** event: lexer_initialized
class LexerInitialized(DomainEvent):
    '''
    Validation gate event that verifies extracted text blocks are
    non-empty and suitable for lexical analysis.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['text_blocks'])
    def execute(self,
            text_blocks: List[Dict[str, Any]],
            **kwargs,
        ) -> List[Dict[str, Any]]:
        '''
        Validate that text blocks are non-empty and contain text.

        :param text_blocks: The list of text block dicts from ExtractText.
        :type text_blocks: List[Dict[str, Any]]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The validated text blocks, unchanged.
        :rtype: List[Dict[str, Any]]
        '''

        # Verify the blocks list is non-empty.
        self.verify(
            expression=len(text_blocks) > 0,
            error_code='TEXT_EXTRACTION_FAILED',
            message='No text blocks provided for lexer initialization.',
        )

        # Verify each block has non-empty text.
        for block in text_blocks:
            self.verify(
                expression=bool(block.get('text', '').strip()),
                error_code='TEXT_EXTRACTION_FAILED',
                message=f'Empty text block: {block.get("name", "unknown")}.',
                block_name=block.get('name', 'unknown'),
            )

        # Return the validated blocks.
        return text_blocks


# ** event: perform_lexical_analysis
class PerformLexicalAnalysis(DomainEvent):
    '''
    Core analytical event that tokenizes validated text blocks via
    an injected LexerService and computes aggregate domain metrics.
    '''

    # * attribute: lexer_service
    lexer_service: LexerService

    # * init
    def __init__(self, lexer_service: LexerService):
        '''
        Initialize the PerformLexicalAnalysis event.

        :param lexer_service: The lexer service for tokenization.
        :type lexer_service: LexerService
        '''

        # Set the lexer service dependency.
        self.lexer_service = lexer_service

    # * method: execute
    @DomainEvent.parameters_required(['validated_blocks'])
    def execute(self,
            validated_blocks: List[Dict[str, Any]],
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Tokenize all validated blocks and compute domain metrics.

        :param validated_blocks: The list of validated text block dicts.
        :type validated_blocks: List[Dict[str, Any]]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Analysis result with tokens, token_count, and metrics.
        :rtype: Dict[str, Any]
        '''

        # Tokenize all blocks.
        all_tokens = []
        for block in validated_blocks:
            block_tokens = self.lexer_service.tokenize(block['text'])
            all_tokens.extend(block_tokens)

        # Count token types for metrics computation.
        type_counts = Counter(t['type'] for t in all_tokens)

        # Compute domain metrics from token type counts.
        metrics = {
            'commands_detected': type_counts.get('CLASS', 0),
            'execute_methods_found': type_counts.get('EXECUTE', 0),
            'verify_calls': type_counts.get('VERIFY', 0),
            'parameters_required_decorators': type_counts.get('PARAMETERS_REQUIRED', 0),
            'service_calls': type_counts.get('SERVICE_CALL', 0),
            'factory_calls': type_counts.get('FACTORY_CALL', 0),
            'constants_referenced': type_counts.get('CONST_REF', 0),
            'docstrings_found': type_counts.get('DOCSTRING', 0),
            'top_token_types': dict(type_counts.most_common(10)),
        }

        # Return the analysis result.
        return {
            'tokens': all_tokens,
            'token_count': len(all_tokens),
            'metrics': metrics,
        }
