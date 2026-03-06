"""Scanner Domain Events"""

# *** imports

# ** core
import os
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any

# ** app
from .settings import DomainEvent, a
from ..interfaces import LexerService
from ..utils import ArtifactBlockParser, ScanOutputWriter

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

        # Parse optional extract filter into a set.
        extract_ids = ArtifactBlockParser.parse_extract_filter(extract)

        # Extract the imports block.
        imports_block = ArtifactBlockParser.extract_imports_block(lines)

        # Extract artifact blocks for the given group type.
        blocks = ArtifactBlockParser.extract_artifact_blocks(lines, group_type)

        # Apply extract filter if specified (imports are always included).
        blocks = ArtifactBlockParser.filter_blocks(blocks, extract_ids)

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


# ** event: emit_scan_result
class EmitScanResult(DomainEvent):
    '''
    Terminal pipeline event that assembles the scan result payload,
    applies output mode flags, and optionally writes to file.
    '''

    # * method: execute
    def execute(self,
            source_file: str = None,
            analysis_result: Dict[str, Any] = None,
            extract: str = None,
            summary_only: bool = False,
            with_metrics: bool = False,
            output_format: str = 'yaml',
            metrics_format: str = 'yaml',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble and emit the scan result payload.

        :param source_file: Original source file path.
        :type source_file: str
        :param analysis_result: Output from PerformLexicalAnalysis.
        :type analysis_result: Dict[str, Any]
        :param extract: Original -x filter string.
        :type extract: str
        :param summary_only: If truthy, omit tokens and include metrics.
        :type summary_only: bool
        :param with_metrics: If truthy, include metrics alongside tokens.
        :type with_metrics: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param metrics_format: Reserved for future use.
        :type metrics_format: str
        :param output: File path to write output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The assembled result payload.
        :rtype: Dict[str, Any]
        '''

        # Default analysis if missing.
        analysis = analysis_result or {
            'tokens': [],
            'token_count': 0,
            'metrics': {},
        }

        # Build base payload.
        result = {
            'event_type': 'TokensScanned',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'token_count': analysis['token_count'],
        }

        # Include extracted artifact names if -x was used.
        extracted_names = ScanOutputWriter.parse_extract_names(extract)
        if extracted_names:
            result['extracted_artifacts'] = extracted_names

        # Include metrics if requested.
        if with_metrics or summary_only:
            result['metrics'] = analysis['metrics']

        # Include tokens unless summary-only.
        if not summary_only:
            result['tokens'] = analysis['tokens']

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)

        # Return the result payload.
        return result
