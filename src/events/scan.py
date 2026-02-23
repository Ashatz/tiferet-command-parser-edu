"""Scanner Domain Events"""

# *** imports

# ** core
import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from collections import Counter

# ** infra
import yaml

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

        # Build the section pattern for the given group type.
        section_pattern = re.compile(
            rf'^\s*#\s*\*\*\s+{re.escape(group_type)}:\s+(\S+)'
        )

        # Parse optional extract filter into a set.
        extract_ids = None
        if extract:
            extract_ids = set(name.strip() for name in extract.split(','))

        # Walk lines to find matching blocks.
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

        # Apply extract filter if specified.
        if extract_ids:
            blocks = [b for b in blocks if b['name'] in extract_ids]

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
    Event to validate extracted text blocks are ready for tokenization.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['text_blocks'])
    def execute(self,
            text_blocks: List[Dict[str, Any]],
            **kwargs,
        ) -> List[Dict[str, Any]]:
        '''
        Validate that text blocks are non-empty and ready for lexical analysis.

        :param text_blocks: The extracted text blocks to validate.
        :type text_blocks: List[Dict[str, Any]]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The validated text blocks.
        :rtype: List[Dict[str, Any]]
        '''

        # Verify the blocks list is not empty.
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
    Event to tokenize text blocks and compute domain metrics.
    Injects lexer_service for PLY-based tokenization.
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
        Tokenize validated text blocks and compute lexical metrics.

        :param validated_blocks: The validated text blocks to analyze.
        :type validated_blocks: List[Dict[str, Any]]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Dict with tokens, token_count, and metrics.
        :rtype: Dict[str, Any]
        '''

        # Tokenize all blocks.
        all_tokens = []
        for block in validated_blocks:
            block_tokens = self.lexer_service.tokenize(block['text'])
            all_tokens.extend(block_tokens)

        # Compute domain metrics from the token stream.
        type_counts = Counter(tok['type'] for tok in all_tokens)

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


# ** event: emit_scan_result
class EmitScanResult(DomainEvent):
    '''
    Event to assemble and format the final scan result payload.
    '''

    # * method: execute
    def execute(self,
            source_file: str = None,
            analysis_result: Dict[str, Any] = None,
            summary_only: bool = False,
            with_metrics: bool = False,
            output_format: str = 'yaml',
            metrics_format: str = 'yaml',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble the final scan result and optionally write to file.

        :param source_file: The original source file path.
        :type source_file: str
        :param analysis_result: The analysis result from PerformLexicalAnalysis.
        :type analysis_result: Dict[str, Any]
        :param summary_only: If True, omit the token list.
        :type summary_only: bool
        :param with_metrics: If True, include metrics in output.
        :type with_metrics: bool
        :param output_format: Output format (yaml, json, console).
        :type output_format: str
        :param metrics_format: Metrics rendering format (yaml, json, text).
        :type metrics_format: str
        :param output: Optional output file path.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The formatted scan result dict.
        :rtype: Dict[str, Any]
        '''

        # Use empty defaults if analysis_result is missing.
        analysis = analysis_result or {
            'tokens': [],
            'token_count': 0,
            'metrics': {},
        }

        # Build the result payload.
        result = {
            'event_type': 'TokensScanned',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'token_count': analysis['token_count'],
        }

        # Include metrics if requested or summary-only mode.
        if with_metrics or summary_only:
            result['metrics'] = analysis['metrics']

        # Include tokens unless summary-only mode.
        if not summary_only:
            result['tokens'] = analysis['tokens']

        # Write to file if output path is specified.
        if output:
            self._write_output(result, output, output_format)

        # Return the result payload.
        return result

    # * method: _write_output
    def _write_output(self,
            result: Dict[str, Any],
            output_path: str,
            output_format: str,
        ) -> None:
        '''
        Write the scan result to a file in the specified format.

        :param result: The scan result dict.
        :type result: Dict[str, Any]
        :param output_path: The file path to write to.
        :type output_path: str
        :param output_format: The output format (yaml, json).
        :type output_format: str
        '''

        # Determine format from file extension if auto.
        if output_format == 'auto':
            if output_path.endswith(('.yaml', '.yml')):
                output_format = 'yaml'
            elif output_path.endswith('.json'):
                output_format = 'json'
            else:
                output_format = 'yaml'

        # Write the result to the output file.
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format == 'json':
                json.dump(result, f, indent=2, default=str)
            else:
                yaml.dump(result, f, default_flow_style=False, sort_keys=False)
