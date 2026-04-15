"""Optimizer Service Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Any, Dict

# ** infra
from tiferet.interfaces.settings import Service

# *** interfaces

# ** interface: optimizer_service
class OptimizerService(Service):
    '''
    Abstract interface for optimizing codegen output with YAML anchors/aliases.
    '''

    # * method: optimize
    @abstractmethod
    def optimize(self, codegen: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Optimize a codegen output dict by sharing repeated structures
        so that PyYAML emits anchors and aliases automatically.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: The optimized dict with shared object references.
        :rtype: Dict[str, Any]
        '''

        raise NotImplementedError()
