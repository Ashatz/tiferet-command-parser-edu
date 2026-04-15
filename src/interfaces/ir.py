"""IR Service Interface"""

# *** imports

# ** core
from abc import abstractmethod
from typing import Any, Dict, Optional

# ** infra
from tiferet.interfaces.settings import Service

# ** app
from ..domain.ir import IREventGroup

# *** interfaces

# ** interface: ir_service
class IRService(Service):
    '''
    Abstract interface for IR generation from a parsed AST and symbol table.
    '''

    # * method: generate
    @abstractmethod
    def generate(self,
            ast: Any,
            symbol_table: Optional[Dict[str, Any]] = None,
        ) -> IREventGroup:
        '''
        Generate an IREventGroup from the parsed AST and optional symbol table.

        :param ast: The parsed module declaration (DeclarationAggregate) from PerformSyntacticAnalysis.
        :type ast: Any
        :param symbol_table: The symbol table dict from PerformSemanticAnalysis (optional).
        :type symbol_table: Dict[str, Any] | None
        :return: The root IR node.
        :rtype: IREventGroup
        '''

        raise NotImplementedError()
