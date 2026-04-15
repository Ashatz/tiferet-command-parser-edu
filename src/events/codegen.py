"""Code Generation Domain Events"""

# *** imports

# ** core
from typing import Any, Dict, Optional

# ** app
from ..domain.ir import IREventGroup
from ..interfaces.codegen import CodegenService
from ..interfaces.optimizer import OptimizerService
from ..utils import ScanOutputWriter
from .settings import DomainEvent

# *** events

# ** event: generate_code
class GenerateCode(DomainEvent):
    '''
    Core analytical event that generates a schema-conforming output dict
    from the IR using the injected CodegenService.
    '''

    # * attribute: codegen_service
    codegen_service: CodegenService

    # * init
    def __init__(self, codegen_service: CodegenService):
        '''
        Initialize with injected codegen service.

        :param codegen_service: The code generation service.
        :type codegen_service: CodegenService
        '''

        # Set the codegen service dependency.
        self.codegen_service = codegen_service

    # * method: execute
    @DomainEvent.parameters_required(['ir'])
    def execute(self,
            ir: IREventGroup,
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Generate the schema-conforming output dict from the IR.

        :param ir: The root IREventGroup from GenerateIR.
        :type ir: IREventGroup
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The structured output dict.
        :rtype: Dict[str, Any]
        '''

        # Generate and return the codegen output.
        return self.codegen_service.generate(ir)


# ** event: optimize_code
class OptimizeCode(DomainEvent):
    '''
    Optimization event that deduplicates repeated structures in the codegen
    output dict, enabling YAML anchor/alias emission.
    '''

    # * attribute: optimizer_service
    optimizer_service: OptimizerService

    # * init
    def __init__(self, optimizer_service: OptimizerService):
        '''
        Initialize with injected optimizer service.

        :param optimizer_service: The optimizer service.
        :type optimizer_service: OptimizerService
        '''

        # Set the optimizer service dependency.
        self.optimizer_service = optimizer_service

    # * method: execute
    @DomainEvent.parameters_required(['codegen'])
    def execute(self,
            codegen: Dict[str, Any],
            O: str = 'O0',
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Optimize the codegen dict based on the requested optimization level.
        O0 passes through unchanged; O1 applies YAML anchor/alias deduplication.

        :param codegen: The codegen output dict from GenerateCode.
        :type codegen: Dict[str, Any]
        :param O: Optimization level (O0, O1, etc.).
        :type O: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The optimized or original codegen dict.
        :rtype: Dict[str, Any]
        '''

        # Normalize the optimization level.
        level = O.strip().upper() if O else 'O0'

        # Pass through unchanged at O0.
        if level == 'O0':
            return codegen

        # O1: YAML anchor/alias deduplication.
        if level >= 'O1':
            codegen = self.optimizer_service.optimize(codegen)

        # Return the optimized dict.
        return codegen


# ** event: emit_codegen_result
class EmitCodegenResult(DomainEvent):
    '''
    Final event in the codegen.event pipeline.
    Writes the codegen output dict to a YAML or JSON file.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['codegen'])
    def execute(self,
            codegen: Dict[str, Any],
            source_file: str = None,
            output_format: str = 'auto',
            output: str = None,
            **kwargs,
        ) -> Any:
        '''
        Emit the codegen result, writing to file or returning the dict.

        :param codegen: The codegen output dict from GenerateCode.
        :type codegen: Dict[str, Any]
        :param source_file: Original source file path (for context).
        :type source_file: str
        :param output_format: Output format — yaml, json, or auto.
        :type output_format: str
        :param output: File path to write the output to.
        :type output: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The codegen dict, or empty string if written to file.
        :rtype: Any
        '''

        # Write to file if output path is specified.
        if output:
            ScanOutputWriter.write(codegen, output, output_format)
            return ''

        # Otherwise return the codegen dict directly.
        return codegen
