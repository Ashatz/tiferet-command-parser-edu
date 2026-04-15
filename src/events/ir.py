"""IR Generation Domain Events"""

# *** imports

# ** core
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ** app
from ..domain.ir import IREventGroup
from ..interfaces.ir import IRService
from ..mappers import Decl
from ..utils import ScanOutputWriter
from .settings import DomainEvent

# *** events

# ** event: generate_ir
class GenerateIR(DomainEvent):
    '''
    Core analytical event that generates a keter IR from the parsed AST
    and optional semantic analysis result using the injected IRService.
    '''

    # * attribute: ir_service
    ir_service: IRService

    # * init
    def __init__(self, ir_service: IRService):
        '''
        Initialize with injected IR service.

        :param ir_service: The IR generation service.
        :type ir_service: IRService
        '''

        # Set the IR service dependency.
        self.ir_service = ir_service

    # * method: execute
    @DomainEvent.parameters_required(['ast'])
    def execute(self,
            ast: Decl,
            semantic: Optional[Dict[str, Any]] = None,
            **kwargs,
        ) -> IREventGroup:
        '''
        Generate an IREventGroup from the AST and optional semantic analysis result.

        :param ast: The parsed module DeclarationAggregate from PerformSyntacticAnalysis.
        :type ast: Decl
        :param semantic: The semantic analysis result dict from PerformSemanticAnalysis (optional).
        :type semantic: Dict[str, Any] | None
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The root IR node.
        :rtype: IREventGroup
        '''

        # Extract the symbol table from the semantic analysis result if provided.
        symbol_table = semantic.get('symbol_table', {}) if semantic else {}

        # Generate and return the IR event group.
        return self.ir_service.generate(ast, symbol_table)


# ** event: emit_ir_result
class EmitIRResult(DomainEvent):
    '''
    Final event in the ir.event pipeline.
    Serializes the IREventGroup to keter DSL and delegates to the output writer.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['ir'])
    def execute(self,
            ir: IREventGroup,
            source_file: str = None,
            output_format: str = 'auto',
            output: str = None,
            **kwargs,
        ) -> Any:
        '''
        Serialize the IREventGroup and emit the keter output.

        :param ir: The root IREventGroup from GenerateIR.
        :type ir: IREventGroup
        :param source_file: Original source file path (for context).
        :type source_file: str
        :param output_format: Output format — use "keter" or "auto" to detect from extension.
        :type output_format: str
        :param output: File path to write the keter output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The keter DSL string, or empty string if written to file.
        :rtype: Any
        '''

        # Serialize the IR tree to keter DSL.
        keter_str = ir.to_keter()

        # Write to file if output path is specified.
        if output:
            ScanOutputWriter.write(keter_str, output, output_format)
            return ''

        # Otherwise return the keter string directly.
        return keter_str
