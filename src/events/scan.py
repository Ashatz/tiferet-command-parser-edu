"""Scanner Domain Events"""

# *** imports

# ** core
import os
from datetime import datetime, timezone
from typing import Dict, Any

# ** infra
from tiferet import File

# ** app
from .settings import DomainEvent
from ..interfaces import LexerService
from ..utils import ScanOutputWriter

# *** events

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
    @DomainEvent.parameters_required(['source_file'])
    def execute(self,
            source_file: str,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Tokenize all validated blocks and compute domain metrics.

        :param source_file: The path to the source file to be tokenized.
        :type source_file: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: Analysis result with tokens, token_count, and metrics.
        :rtype: Dict[str, Any]
        '''

        with File(source_file) as f:
            text = f.file.read()

        # Tokenize all blocks.
        all_tokens = self.lexer_service.tokenize(text)

        # Return the analysis result.
        return {
            'tokens': [t.model_dump() for t in all_tokens],
            'token_count': len(all_tokens)
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
            output_format: str = 'yaml',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble and emit the scan result payload.

        :param source_file: Original source file path.
        :type source_file: str
        :param analysis_result: Output from PerformLexicalAnalysis.
        :type analysis_result: Dict[str, Any]
        :param summary_only: If truthy, omit tokens and include metrics.
        :type summary_only: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param output: File path to write output to.
        :type output: str
        :return: The assembled result payload.
        :rtype: Dict[str, Any]
        '''

        # Default analysis if missing.
        analysis = analysis_result or {
            'tokens': [],
            'token_count': 0
        }

        # Build base payload.
        result = {
            'event_type': 'TokensScanned',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'token_count': analysis['token_count'],
        }

        # Include tokens unless summary-only.
        result['tokens'] = analysis['tokens']

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)

        # Return the result payload.
        return result
