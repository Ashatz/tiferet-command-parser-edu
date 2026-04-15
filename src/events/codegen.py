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
            **kwargs,
        ) -> Dict[str, Any]:
        '''
        Optimize the codegen dict by sharing repeated structures.

        :param codegen: The codegen output dict from GenerateCode.
        :type codegen: Dict[str, Any]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The optimized codegen dict.
        :rtype: Dict[str, Any]
        '''

        # Run the optimizer and capture the anchor registry.
        optimized, anchor_registry = self.optimizer_service.optimize(codegen)

        # Embed the anchor registry in the codegen dict for downstream events.
        if anchor_registry:
            optimized['__anchor_registry__'] = anchor_registry

        # Return the optimized dict.
        return optimized


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
            anchor_registry: Dict[int, str] = None,
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
        :param anchor_registry: Optional anchor registry from OptimizeCode.
        :type anchor_registry: Dict[int, str]
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The codegen dict, or empty string if written to file.
        :rtype: Any
        '''

        # Extract and remove the embedded anchor registry if present.
        anchor_registry = codegen.pop('__anchor_registry__', None)

        # Write to file if output path is specified.
        if output:
            ScanOutputWriter.write(
                codegen, output, output_format,
                anchor_registry=anchor_registry,
            )
            return ''

        # Otherwise return the codegen dict directly.
        return codegen
