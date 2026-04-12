"""Scanner Domain Events"""

# *** imports

# ** core
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# ** infra
from tiferet import File

# ** app
from .settings import DomainEvent
from ..interfaces import LexerService
from ..mappers import TokenAggregate
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
        ) -> List[TokenAggregate]:
        '''
        Tokenize all validated blocks and compute domain metrics.

        :param source_file: The path to the source file to be tokenized.
        :type source_file: str
        :return: List of token aggregates.
        :rtype: List[TokenAggregate]
        '''

        with File(source_file) as f:
            text = f.file.read()

        # Tokenize the text using the injected lexer service and return the list of token aggregates.
        return self.lexer_service.tokenize(text)

# ** event: emit_scan_result
class EmitScanResult(DomainEvent):
    '''
    Terminal pipeline event that assembles the scan result payload,
    applies output mode flags, and optionally writes to file.
    '''

    # * method: execute
    def execute(self,
            source_file: str = None,
            tokens: List[TokenAggregate] = None,
            output_format: str = 'yaml',
            output: str = None,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Assemble and emit the scan result payload.

        :param source_file: Original source file path.
        :type source_file: str
        :param tokens: List of token aggregates from PerformLexicalAnalysis.
        :type tokens: List[TokenAggregate]
        :param summary_only: If truthy, omit tokens and include metrics.
        :type summary_only: bool
        :param output_format: Output format: yaml, json, or auto.
        :type output_format: str
        :param output: File path to write output to.
        :type output: str
        :return: The assembled result payload.
        :rtype: Dict[str, Any]
        '''

        # Build base payload.
        result = {
            'event_type': 'TokensScanned',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
            'tokens': [t.model_dump() for t in tokens] if tokens else [],
            'token_count': len(tokens) if tokens else 0,
        }

        # Write to file if output path specified.
        if output:
            ScanOutputWriter.write(result, output, output_format)

        # Return the result payload.
        return result
