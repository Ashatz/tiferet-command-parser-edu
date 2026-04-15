"""YAML Anchor/Alias Optimizer Utility"""

# *** imports

# ** core
from typing import Any, Dict, List, Tuple

# ** app
from ..interfaces.optimizer import OptimizerService

# *** utils

# ** util: yaml_anchor_optimizer
class YamlAnchorOptimizer(OptimizerService):
    '''
    Concrete optimizer that deduplicates repeated params and returns lists
    across events by sharing Python object references, enabling PyYAML to
    emit YAML anchors and aliases automatically.
    '''

    # * method: optimize
    def optimize(self, codegen: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Optimize the codegen dict by replacing repeated params/returns lists
        with shared object references and collecting anchor declarations
        into a top-level vars section.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: The optimized dict with vars and shared references.
        :rtype: Dict[str, Any]
        '''

        # Collect all params and returns lists with their locations.
        locations = self.collect_lists(codegen)

        # Build the vars list and share references for repeated structures.
        vars_list: List[Any] = []
        for fingerprint, entries in locations.items():
            kind, values = fingerprint

            # Only share lists that appear more than once.
            if len(entries) < 2:
                continue

            # Create one canonical list object shared by all locations.
            canonical = list(values)

            # Add the canonical object to vars for anchor declaration.
            vars_list.append(canonical)

            # Patch all locations to reference the canonical object.
            for parent, key in entries:
                parent[key] = canonical

        # Build the result with vars before evt_grp so anchors are declared first.
        if vars_list:
            result: Dict[str, Any] = {'vars': vars_list}
            result['evt_grp'] = codegen['evt_grp']
            return result

        # Return the original dict unchanged when no vars are needed.
        return codegen

    # * method: collect_lists
    def collect_lists(self, codegen: Dict[str, Any]) -> Dict[Tuple, List[Tuple[Dict, str]]]:
        '''
        Walk the codegen dict and collect all params and returns lists
        with their parent dict and key for later patching.

        :param codegen: The codegen output dict.
        :type codegen: Dict[str, Any]
        :return: Dict keyed by (kind, tuple(values)) to list of (parent_dict, key) locations.
        :rtype: Dict[Tuple, List[Tuple[Dict, str]]]
        '''

        # Initialize the collector.
        collected: Dict[Tuple, List[Tuple[Dict, str]]] = {}

        # Get events dict; return empty if no events.
        evt_grp = codegen.get('evt_grp', {})
        evts = evt_grp.get('evts', {})
        if not evts:
            return collected

        # Walk each event.
        for event_key, event in evts.items():

            # Collect from execute section.
            execute = event.get('execute', {})
            self.collect_from_callable(execute, collected)

            # Collect from methods section.
            methods = event.get('methods', {})
            for method_name, method in methods.items():
                self.collect_from_callable(method, collected)

        return collected

    # * method: collect_from_callable
    def collect_from_callable(self,
            callable_dict: Dict[str, Any],
            collected: Dict[Tuple, List[Tuple[Dict, str]]],
        ) -> None:
        '''
        Collect params and returns lists from an execute or method dict.

        :param callable_dict: The execute or method dict.
        :type callable_dict: Dict[str, Any]
        :param collected: The collector to append to.
        :type collected: Dict[Tuple, List[Tuple[Dict, str]]]
        '''

        # Collect params list.
        if 'params' in callable_dict:
            values = callable_dict['params']
            fingerprint = ('params', tuple(values))
            collected.setdefault(fingerprint, []).append((callable_dict, 'params'))

        # Collect returns list.
        if 'returns' in callable_dict:
            values = callable_dict['returns']
            fingerprint = ('returns', tuple(values))
            collected.setdefault(fingerprint, []).append((callable_dict, 'returns'))
