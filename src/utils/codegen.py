"""Tiferet Code Generator Utility"""

# *** imports

# ** core
from typing import Any, Dict, List, Optional

# ** app
from ..domain.ir import (
    IREventGroup,
    IRImportGroups,
    IRImportGroup,
    IREvents,
    IREvent,
    IRAttributes,
    IRInjection,
    IRInjections,
    IRExecute,
    IRMethod,
    IRMethods,
    IRParam,
    IRReturn,
    IRSnippets,
    IRSnippet,
)
from ..interfaces.codegen import CodegenService

# *** utils

# ** util: tiferet_generator
class TiferetGenerator(CodegenService):
    '''
    Concrete code generator that walks an IREventGroup and produces
    a structured dict conforming to codegen/schema.yml.
    '''

    # * method: generate
    def generate(self, ir: IREventGroup) -> Dict[str, Any]:
        '''
        Entry point: build the top-level evt_grp dict from the IR.

        :param ir: The root IR node.
        :type ir: IREventGroup
        :return: The schema-conforming output dict.
        :rtype: Dict[str, Any]
        '''

        # Build the inner evt_grp dict.
        evt_grp: Dict[str, Any] = {
            'name': ir.name,
        }

        # Include description only if non-empty.
        if ir.description:
            evt_grp['desc'] = ir.description

        # Build imports section.
        impt = self.build_imports(ir.import_groups)
        if impt:
            evt_grp['impt'] = impt

        # Build events section.
        evts = self.build_events(ir.events)
        if evts:
            evt_grp['evts'] = evts

        # Return the top-level wrapper.
        return {'evt_grp': evt_grp}

    # * method: build_imports
    def build_imports(self, import_groups: IRImportGroups) -> Dict[str, Any]:
        '''
        Convert IRImportGroups to the impt dict keyed by category.

        :param import_groups: The IR import groups collection.
        :type import_groups: IRImportGroups
        :return: Dict keyed by category, each value a list of {src, tgts} dicts.
        :rtype: Dict[str, Any]
        '''

        # Return empty dict if no groups.
        if not import_groups.groups:
            return {}

        # Build each group entry.
        result: Dict[str, Any] = {}
        for group in import_groups.groups:
            entries = self.build_import_group(group)
            if entries:
                result[group.category] = entries

        return result

    # * method: build_import_group
    def build_import_group(self, group: IRImportGroup) -> List[Dict[str, Any]]:
        '''
        Convert a single IRImportGroup to a list of {src, tgts} dicts,
        collapsing imports that share the same module_path.

        :param group: The IR import group.
        :type group: IRImportGroup
        :return: List of import entry dicts.
        :rtype: List[Dict[str, Any]]
        '''

        # Collapse imports by module_path preserving order.
        seen: Dict[str, List[str]] = {}
        order: List[str] = []
        for imp in group.imports:
            if imp.module_path not in seen:
                seen[imp.module_path] = []
                order.append(imp.module_path)
            seen[imp.module_path].append(imp.symbol)

        # Build the list of entry dicts.
        entries: List[Dict[str, Any]] = []
        for module_path in order:
            entries.append({
                'src': module_path,
                'tgts': seen[module_path],
            })

        return entries

    # * method: build_events
    def build_events(self, events: IREvents) -> Dict[str, Any]:
        '''
        Convert IREvents to the evts dict keyed by artifact_name.

        :param events: The IR events collection.
        :type events: IREvents
        :return: Dict keyed by event artifact name.
        :rtype: Dict[str, Any]
        '''

        # Return empty dict if no events.
        if not events.events:
            return {}

        # Build each event entry.
        result: Dict[str, Any] = {}
        for event in events.events:
            result[event.artifact_name] = self.build_event(event)

        return result

    # * method: build_event
    def build_event(self, event: IREvent) -> Dict[str, Any]:
        '''
        Convert a single IREvent into its dict form.

        :param event: The IR event.
        :type event: IREvent
        :return: The event dict.
        :rtype: Dict[str, Any]
        '''

        # Start with required name.
        entry: Dict[str, Any] = {
            'name': event.class_name,
        }

        # Include description only if non-empty.
        if event.doc_string:
            entry['desc'] = event.doc_string

        # Build attributes section.
        attributes = self.build_attributes(event.attributes)
        if attributes:
            entry['attributes'] = attributes

        # Build injections section.
        injections = self.build_injections(event.injections)
        if injections:
            entry['injections'] = injections

        # Build execute section.
        entry['execute'] = self.build_execute(event.execute)

        # Build methods section.
        methods = self.build_methods(event.methods)
        if methods:
            entry['methods'] = methods

        return entry

    # * method: build_attributes
    def build_attributes(self, attributes: IRAttributes) -> List[Dict[str, str]]:
        '''
        Convert IRAttributes to a list of compact {name: type} dicts.

        :param attributes: The IR attributes collection.
        :type attributes: IRAttributes
        :return: List of single-key dicts.
        :rtype: List[Dict[str, str]]
        '''

        # Return empty list if no attributes.
        if not attributes.attributes:
            return []

        # Build compact attribute entries.
        return [{attr.name: attr.type} for attr in attributes.attributes]

    # * method: build_injections
    def build_injections(self, injections: IRInjections) -> List[Dict[str, Any]]:
        '''
        Convert IRInjections to a list of compact injection dicts.

        :param injections: The IR injections collection.
        :type injections: IRInjections
        :return: List of injection dicts.
        :rtype: List[Dict[str, Any]]
        '''

        # Return empty list if no injections.
        if not injections.injections:
            return []

        # Build each injection entry.
        return [self.encode_injection(inj) for inj in injections.injections]

    # * method: encode_injection
    def encode_injection(self, injection: IRInjection) -> Dict[str, Any]:
        '''
        Encode a single IRInjection as a compact dict.

        :param injection: The IR injection.
        :type injection: IRInjection
        :return: The injection dict keyed by compact spec string.
        :rtype: Dict[str, Any]
        '''

        # Build the compact spec string.
        req = 'true' if injection.required else 'false'
        spec = f'{injection.name}:{injection.type}:{req}:{injection.default}:{injection.description}'

        # Build the value dict with optional assign.
        value: Dict[str, Any] = {}
        if injection.assign:
            value['assign'] = [{
                'target': injection.assign.target,
                'value': injection.assign.source,
            }]

        # Return the keyed dict.
        return {spec: value if value else None}

    # * method: build_execute
    def build_execute(self, execute: IRExecute) -> Dict[str, Any]:
        '''
        Convert IRExecute to the execute dict.

        :param execute: The IR execute node.
        :type execute: IRExecute
        :return: The execute dict with params, returns, snpt.
        :rtype: Dict[str, Any]
        '''

        # Build the execute dict.
        result: Dict[str, Any] = {}

        # Build params list.
        params = self.build_params(execute.params.params)
        if params:
            result['params'] = params

        # Build returns list.
        returns = self.build_returns(execute.returns.returns)
        if returns:
            result['returns'] = returns

        # Build snippets list.
        snpt = self.build_snippets(execute.snippets)
        if snpt:
            result['snpt'] = snpt

        return result

    # * method: build_methods
    def build_methods(self, methods: IRMethods) -> Dict[str, Any]:
        '''
        Convert IRMethods to the methods dict keyed by method name.

        :param methods: The IR methods collection.
        :type methods: IRMethods
        :return: Dict keyed by method name.
        :rtype: Dict[str, Any]
        '''

        # Return empty dict if no methods.
        if not methods.methods:
            return {}

        # Build each method entry.
        result: Dict[str, Any] = {}
        for method in methods.methods:
            result[method.name] = self.build_method(method)

        return result

    # * method: build_method
    def build_method(self, method: IRMethod) -> Dict[str, Any]:
        '''
        Convert a single IRMethod into its dict form.

        :param method: The IR method.
        :type method: IRMethod
        :return: The method dict with params, returns, snpt.
        :rtype: Dict[str, Any]
        '''

        # Build the method dict.
        result: Dict[str, Any] = {}

        # Build params list.
        params = self.build_params(method.params.params)
        if params:
            result['params'] = params

        # Build returns list.
        returns = self.build_returns(method.returns.returns)
        if returns:
            result['returns'] = returns

        # Build snippets list.
        snpt = self.build_snippets(method.snippets)
        if snpt:
            result['snpt'] = snpt

        return result

    # * method: build_params
    def build_params(self, params: List[IRParam]) -> List[str]:
        '''
        Convert a list of IRParam to compact colon-delimited strings.

        :param params: The IR parameters.
        :type params: List[IRParam]
        :return: List of compact param strings.
        :rtype: List[str]
        '''

        # Return empty list if no params.
        if not params:
            return []

        # Encode each param.
        return [self.encode_param(p) for p in params]

    # * method: encode_param
    def encode_param(self, param: IRParam) -> str:
        '''
        Encode a single IRParam as a compact colon-delimited string.

        :param param: The IR parameter.
        :type param: IRParam
        :return: Compact string name:type:required:default:doc.
        :rtype: str
        '''

        # Build and return the colon-delimited string.
        req = 'true' if param.required else 'false'
        return f'{param.name}:{param.type}:{req}:{param.default}:{param.description}'

    # * method: build_returns
    def build_returns(self, returns: List[IRReturn]) -> List[str]:
        '''
        Convert a list of IRReturn to compact colon-delimited strings.

        :param returns: The IR return entries.
        :type returns: List[IRReturn]
        :return: List of compact return strings.
        :rtype: List[str]
        '''

        # Return empty list if no returns.
        if not returns:
            return []

        # Encode each return.
        return [self.encode_return(r) for r in returns]

    # * method: encode_return
    def encode_return(self, ret: IRReturn) -> str:
        '''
        Encode a single IRReturn as a compact colon-delimited string.

        :param ret: The IR return entry.
        :type ret: IRReturn
        :return: Compact string type:doc.
        :rtype: str
        '''

        # Build and return the colon-delimited string.
        return f'{ret.type_name}:{ret.description}'

    # * method: build_snippets
    def build_snippets(self, snippets: IRSnippets) -> List[Dict[str, Any]]:
        '''
        Convert IRSnippets to a list of paired {coms, stmt} dicts.

        :param snippets: The IR snippets collection.
        :type snippets: IRSnippets
        :return: List of snippet dicts.
        :rtype: List[Dict[str, Any]]
        '''

        # Return empty list if no snippets.
        if not snippets.snippets:
            return []

        # Build each snippet entry.
        return [self.build_snippet(s) for s in snippets.snippets]

    # * method: build_snippet
    def build_snippet(self, snippet: IRSnippet) -> Dict[str, Any]:
        '''
        Convert a single IRSnippet into its {coms, stmt} dict.

        :param snippet: The IR snippet.
        :type snippet: IRSnippet
        :return: The snippet dict.
        :rtype: Dict[str, Any]
        '''

        # Build the snippet dict, omitting empty sections.
        result: Dict[str, Any] = {}

        # Build comments list.
        coms = [c.text for c in snippet.comments.comments]
        if coms:
            result['coms'] = coms

        # Build statements list.
        stmt = [s.expr for s in snippet.statements.statements]
        if stmt:
            result['stmt'] = stmt

        return result
