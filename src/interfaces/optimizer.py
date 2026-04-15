"""Optimizer Service Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Any, Dict, Tuple

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
    def optimize(self, codegen: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[int, str]]:
        '''
        Optimize a codegen output dict by sharing repeated structures
        and building an anchor registry for YAML serialization.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: A tuple of (optimized dict, anchor registry keyed by id()).
        :rtype: Tuple[Dict[str, Any], Dict[int, str]]
        '''

        raise NotImplementedError()
