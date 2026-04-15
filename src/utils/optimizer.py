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
    def optimize(self, codegen: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[int, str]]:
        '''
        Optimize the codegen dict by replacing repeated params/returns lists
        with shared object references and building an anchor registry.

        :param codegen: The codegen output dict from TiferetGenerator.
        :type codegen: Dict[str, Any]
        :return: A tuple of (optimized dict, anchor registry).
        :rtype: Tuple[Dict[str, Any], Dict[int, str]]
        '''

        # Collect all params and returns lists with their locations.
        locations = self.collect_lists(codegen)

        # Build shared references and anchor registry.
        registry: Dict[int, str] = {}
        for fingerprint, entries in locations.items():
            kind, values = fingerprint

            # Only anchor lists that appear more than once.
            if len(entries) < 2:
                continue

            # Create one canonical list object shared by all locations.
            canonical = list(values)
            anchor_name = self.build_anchor_name(values, kind)
            registry[id(canonical)] = anchor_name

            # Patch all locations to reference the canonical object.
            for parent, key in entries:
                parent[key] = canonical

        # Return the mutated dict and registry.
        return codegen, registry

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
            self._collect_from_callable(execute, collected)

            # Collect from methods section.
            methods = event.get('methods', {})
            for method_name, method in methods.items():
                self._collect_from_callable(method, collected)

        return collected

    # * method: _collect_from_callable
    def _collect_from_callable(self,
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

    # * method: build_anchor_name
    def build_anchor_name(self, values: tuple, kind: str) -> str:
        '''
        Generate a meaningful YAML anchor name from the list content and kind.

        For params, extracts the type of each param and joins with the param names.
        For returns, uses the return type(s).

        :param values: The tuple of compact string values.
        :type values: tuple
        :param kind: Either 'params' or 'returns'.
        :type kind: str
        :return: A descriptive anchor name.
        :rtype: str
        '''

        if kind == 'params':
            # Extract name and type from each param string (name:type:req:default:doc).
            parts = []
            types = set()
            for val in values:
                segments = val.split(':')
                parts.append(segments[0])
                if len(segments) > 1:
                    types.add(segments[1])

            # Build name: type_name1_name2_params (e.g., int_a_b_params).
            type_prefix = '_'.join(sorted(types)) if types else 'mixed'
            names_suffix = '_'.join(parts)
            return f'{type_prefix}_{names_suffix}_params'

        if kind == 'returns':
            # Extract return types from type:doc strings.
            types = []
            for val in values:
                segments = val.split(':')
                types.append(segments[0])

            # Build name: type_returns (e.g., int_returns).
            type_prefix = '_'.join(types)
            return f'{type_prefix}_returns'

        # Fallback for unknown kinds.
        return f'{kind}_anchor'
