"""Code Generation Domain Events"""

# *** imports

# ** core
from typing import Any, Dict

# ** infra
from tiferet import File, Json

# ** app
from ..domain.ir import IREventGroup
from ..interfaces.codegen import CodegenService
from ..mappers import Decl
from ..mappers.ir import KeterIREventGroup
from .settings import DomainEvent, a

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


# ** event: load_from_keter
class LoadFromKeter(DomainEvent):
    '''
    Loads a .keter IR file and parses it into an IREventGroup
    via the KeterIREventGroup transfer object.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['source_file'])
    def execute(self,
            source_file: str,
            **kwargs,
        ) -> IREventGroup:
        '''
        Read a .keter file and parse it into an IREventGroup.

        :param source_file: Path to the .keter file.
        :type source_file: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The parsed IREventGroup.
        :rtype: IREventGroup
        '''

        # Load the keter text from the file.
        with File(source_file) as f:
            text = f.file.read()

        # Parse the keter DSL into an IREventGroup via the transfer object.
        try:
            return KeterIREventGroup.from_data(text)
        except ValueError as e:
            self.raise_error(
                'INVALID_KETER_SYNTAX',
                str(e),
                source_file=source_file,
            )


# ** event: load_from_ast
class LoadFromAST(DomainEvent):
    '''
    Loads a JSON AST file (output of parse event) and reconstructs
    the DeclarationAggregate directly via Pydantic model_validate.
    '''

    # * method: execute
    @DomainEvent.parameters_required(['source_file'])
    def execute(self,
            source_file: str,
            **kwargs,
        ) -> Decl:
        '''
        Read a JSON AST file and reconstruct the DeclarationAggregate.

        :param source_file: Path to the JSON AST file.
        :type source_file: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The reconstructed DeclarationAggregate.
        :rtype: Decl
        '''

        # Load the JSON data from the file.
        with Json(source_file) as j:
            data = j.load()

        # Extract the ast dict from a parse-event result payload, or use directly.
        ast_dict = data.get('ast', data)

        # Reconstruct the DeclarationAggregate via Pydantic model_validate.
        return Decl.model_validate(ast_dict)
