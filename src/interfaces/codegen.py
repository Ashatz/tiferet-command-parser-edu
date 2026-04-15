"""Codegen Service Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Any, Dict

# ** infra
from tiferet.interfaces.settings import Service

# ** app
from ..domain.ir import IREventGroup

# *** interfaces

# ** interface: codegen_service
class CodegenService(Service):
    '''
    Abstract interface for code generation from an IR event group.
    '''

    # * method: generate
    @abstractmethod
    def generate(self, ir: IREventGroup) -> Dict[str, Any]:
        '''
        Transform an IREventGroup into a schema-conforming output dict.

        :param ir: The root IR node.
        :type ir: IREventGroup
        :return: The structured output dict conforming to codegen/schema.yml.
        :rtype: Dict[str, Any]
        '''

        raise NotImplementedError()
