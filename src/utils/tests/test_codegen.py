"""Utils – TiferetGenerator Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..codegen import TiferetGenerator
from ...domain.ir import (
    IREventGroup,
    IRImportGroups,
    IRImportGroup,
    IRImport,
    IREvents,
    IREvent,
    IRAttributes,
    IRAttribute,
    IRInjections,
    IRInjection,
    IRAssign,
    IRExecute,
    IRParams,
    IRParam,
    IRReturns,
    IRReturn,
    IRSnippets,
    IRSnippet,
    IRComments,
    IRComment,
    IRStatements,
    IRStatement,
    IRMethods,
    IRMethod,
)

# *** fixtures

# ** fixture: generator
@pytest.fixture
def generator() -> TiferetGenerator:
    '''
    Returns a fresh TiferetGenerator instance.

    :return: A TiferetGenerator.
    :rtype: TiferetGenerator
    '''

    return TiferetGenerator()


# ** fixture: imports_only_ir
@pytest.fixture
def imports_only_ir() -> IREventGroup:
    '''
    Returns an IR with imports but no events (pass_imports_only shape).

    :return: An IREventGroup with imports only.
    :rtype: IREventGroup
    '''

    return IREventGroup(
        name='pass_imports_only',
        description='Tiferet Empty Events Sample',
        import_groups=IRImportGroups(groups=[
            IRImportGroup(category='core', imports=[
                IRImport(module_path='typing', symbol='Any'),
            ]),
            IRImportGroup(category='app', imports=[
                IRImport(module_path='.settings', symbol='DomainEvent'),
                IRImport(module_path='.settings', symbol='a'),
                IRImport(module_path='..interfaces', symbol='ErrorService'),
            ]),
        ]),
        events=IREvents(),
    )


# ** fixture: minimal_event_ir
@pytest.fixture
def minimal_event_ir() -> IREventGroup:
    '''
    Returns an IR with a single minimal event (pass_minimal_event shape).

    :return: An IREventGroup with one event.
    :rtype: IREventGroup
    '''

    return IREventGroup(
        name='pass_minimal_event',
        description='',
        import_groups=IRImportGroups(groups=[
            IRImportGroup(category='app', imports=[
                IRImport(module_path='.settings', symbol='DomainEvent'),
            ]),
        ]),
        events=IREvents(events=[
            IREvent(
                artifact_name='ping',
                class_name='Ping',
                doc_string='A minimal event with no attributes and a single method.',
                attributes=IRAttributes(),
                injections=IRInjections(),
                execute=IRExecute(
                    params=IRParams(params=[
                        IRParam(name='kwargs', type='dict', required=False),
                    ]),
                    returns=IRReturns(returns=[
                        IRReturn(type_name='str', description=''),
                    ]),
                    snippets=IRSnippets(snippets=[
                        IRSnippet(
                            comments=IRComments(comments=[
                                IRComment(text='Return pong.'),
                            ]),
                            statements=IRStatements(statements=[
                                IRStatement(expr="Return('pong')"),
                            ]),
                        ),
                    ]),
                ),
                methods=IRMethods(),
            ),
        ]),
    )


# ** fixture: injection_event_ir
@pytest.fixture
def injection_event_ir() -> IREventGroup:
    '''
    Returns an IR with attributes and injections (pass_minimal_injection_event shape).

    :return: An IREventGroup with injection.
    :rtype: IREventGroup
    '''

    return IREventGroup(
        name='pass_minimal_injection_event',
        description='Sample event for testing minimal injection.',
        import_groups=IRImportGroups(groups=[
            IRImportGroup(category='app', imports=[
                IRImport(module_path='.settings', symbol='DomainEvent'),
            ]),
        ]),
        events=IREvents(events=[
            IREvent(
                artifact_name='ping',
                class_name='Ping',
                doc_string='',
                attributes=IRAttributes(attributes=[
                    IRAttribute(name='pong', type='str'),
                ]),
                injections=IRInjections(injections=[
                    IRInjection(
                        name='pong',
                        type='str',
                        required=True,
                        default='',
                        description='',
                        assign=IRAssign(target='pong', source='pong'),
                    ),
                ]),
                execute=IRExecute(
                    params=IRParams(params=[
                        IRParam(name='kwargs', type='dict', required=False),
                    ]),
                    returns=IRReturns(returns=[
                        IRReturn(type_name='str', description=''),
                    ]),
                    snippets=IRSnippets(snippets=[
                        IRSnippet(
                            comments=IRComments(comments=[
                                IRComment(text='Return the pong string.'),
                            ]),
                            statements=IRStatements(statements=[
                                IRStatement(expr='Return(self.pong)'),
                            ]),
                        ),
                    ]),
                ),
                methods=IRMethods(),
            ),
        ]),
    )


# ** fixture: multiple_events_ir
@pytest.fixture
def multiple_events_ir() -> IREventGroup:
    '''
    Returns an IR with multiple events (pass_multiple_operator_events shape).

    :return: An IREventGroup with multiple events.
    :rtype: IREventGroup
    '''

    def make_operator_event(name: str, class_name: str, op: str, ret_type: str) -> IREvent:
        return IREvent(
            artifact_name=name,
            class_name=class_name,
            doc_string=f'An event that performs {name}.',
            attributes=IRAttributes(),
            injections=IRInjections(),
            execute=IRExecute(
                params=IRParams(params=[
                    IRParam(name='a', type='int', required=True),
                    IRParam(name='b', type='int', required=True),
                ]),
                returns=IRReturns(returns=[
                    IRReturn(type_name=ret_type, description=''),
                ]),
                snippets=IRSnippets(snippets=[
                    IRSnippet(
                        comments=IRComments(),
                        statements=IRStatements(statements=[
                            IRStatement(expr=f'Return({op}(a, b))'),
                        ]),
                    ),
                ]),
            ),
            methods=IRMethods(),
        )

    return IREventGroup(
        name='pass_multiple_operator_events',
        description='Multiple operator events.',
        import_groups=IRImportGroups(groups=[
            IRImportGroup(category='infra', imports=[
                IRImport(module_path='tiferet.events', symbol='DomainEvent'),
            ]),
        ]),
        events=IREvents(events=[
            make_operator_event('add', 'Add', 'Add', 'int'),
            make_operator_event('subtract', 'Subtract', 'Sub', 'int'),
            make_operator_event('divide', 'Divide', 'Div', 'float'),
        ]),
    )


# ** fixture: helper_method_ir
@pytest.fixture
def helper_method_ir() -> IREventGroup:
    '''
    Returns an IR with a helper method (pass_helper_method_event shape).

    :return: An IREventGroup with a helper method.
    :rtype: IREventGroup
    '''

    return IREventGroup(
        name='pass_helper_method_event',
        description='A calculator event with a helper method.',
        import_groups=IRImportGroups(groups=[
            IRImportGroup(category='infra', imports=[
                IRImport(module_path='tiferet.events', symbol='DomainEvent'),
            ]),
        ]),
        events=IREvents(events=[
            IREvent(
                artifact_name='add_integer',
                class_name='AddInteger',
                doc_string='An event that adds two numbers.',
                attributes=IRAttributes(),
                injections=IRInjections(),
                execute=IRExecute(
                    params=IRParams(params=[
                        IRParam(name='a', type='str', required=True, description='The first operand.'),
                        IRParam(name='b', type='str', required=True, description='The second operand.'),
                        IRParam(name='kwargs', type='dict', required=False),
                    ]),
                    returns=IRReturns(returns=[
                        IRReturn(type_name='int', description='The integer sum.'),
                    ]),
                    snippets=IRSnippets(snippets=[
                        IRSnippet(
                            comments=IRComments(comments=[
                                IRComment(text='Convert inputs to integers.'),
                            ]),
                            statements=IRStatements(statements=[
                                IRStatement(expr='Assign(x, Call(self.to_int, a))'),
                                IRStatement(expr='Assign(y, Call(self.to_int, b))'),
                            ]),
                        ),
                        IRSnippet(
                            comments=IRComments(comments=[
                                IRComment(text='Return the sum.'),
                            ]),
                            statements=IRStatements(statements=[
                                IRStatement(expr='Return(Add(x, y))'),
                            ]),
                        ),
                    ]),
                ),
                methods=IRMethods(methods=[
                    IRMethod(
                        name='to_int',
                        params=IRParams(params=[
                            IRParam(name='value', type='str', required=True, description='The value to convert.'),
                        ]),
                        returns=IRReturns(returns=[
                            IRReturn(type_name='int', description='The integer representation.'),
                        ]),
                        snippets=IRSnippets(snippets=[
                            IRSnippet(
                                comments=IRComments(comments=[
                                    IRComment(text='Return the integer conversion.'),
                                ]),
                                statements=IRStatements(statements=[
                                    IRStatement(expr='Return(Call(int, value))'),
                                ]),
                            ),
                        ]),
                    ),
                ]),
            ),
        ]),
    )


# *** tests

# ** test: imports_only_module
def test_imports_only_module(generator: TiferetGenerator, imports_only_ir: IREventGroup) -> None:
    '''
    Test codegen of an imports-only module produces impt but no evts.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    :param imports_only_ir: The imports-only IR fixture.
    :type imports_only_ir: IREventGroup
    '''

    result = generator.generate(imports_only_ir)

    # Top-level wrapper present.
    assert 'evt_grp' in result
    grp = result['evt_grp']

    # Name and description set.
    assert grp['name'] == 'pass_imports_only'
    assert grp['desc'] == 'Tiferet Empty Events Sample'

    # Imports present with correct categories.
    assert 'impt' in grp
    assert 'core' in grp['impt']
    assert 'app' in grp['impt']

    # Core has one import entry.
    assert len(grp['impt']['core']) == 1
    assert grp['impt']['core'][0]['src'] == 'typing'
    assert grp['impt']['core'][0]['tgts'] == ['Any']

    # App has two import entries (settings collapsed, interfaces separate).
    assert len(grp['impt']['app']) == 2
    assert grp['impt']['app'][0]['tgts'] == ['DomainEvent', 'a']

    # No events section.
    assert 'evts' not in grp


# ** test: minimal_event
def test_minimal_event(generator: TiferetGenerator, minimal_event_ir: IREventGroup) -> None:
    '''
    Test codegen of a minimal single-event module.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    :param minimal_event_ir: The minimal event IR fixture.
    :type minimal_event_ir: IREventGroup
    '''

    result = generator.generate(minimal_event_ir)
    grp = result['evt_grp']

    # No description for empty string.
    assert 'desc' not in grp

    # Events present with one entry.
    assert 'evts' in grp
    assert 'ping' in grp['evts']
    event = grp['evts']['ping']

    # Name and description.
    assert event['name'] == 'Ping'
    assert 'desc' in event

    # No attributes, injections, or methods.
    assert 'attributes' not in event
    assert 'injections' not in event
    assert 'methods' not in event

    # Execute section present.
    assert 'execute' in event
    assert 'params' in event['execute']
    assert 'returns' in event['execute']
    assert 'snpt' in event['execute']


# ** test: injection_event
def test_injection_event(generator: TiferetGenerator, injection_event_ir: IREventGroup) -> None:
    '''
    Test codegen of an event with attributes and injections.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    :param injection_event_ir: The injection event IR fixture.
    :type injection_event_ir: IREventGroup
    '''

    result = generator.generate(injection_event_ir)
    event = result['evt_grp']['evts']['ping']

    # Attributes present.
    assert 'attributes' in event
    assert len(event['attributes']) == 1
    assert event['attributes'][0] == {'pong': 'str'}

    # Injections present.
    assert 'injections' in event
    assert len(event['injections']) == 1
    inj = event['injections'][0]
    spec = list(inj.keys())[0]
    assert 'pong:str:true' in spec
    assert 'assign' in inj[spec]
    assert inj[spec]['assign'][0]['target'] == 'pong'
    assert inj[spec]['assign'][0]['value'] == 'pong'

    # No description key for empty docstring.
    assert 'desc' not in event


# ** test: multiple_events
def test_multiple_events(generator: TiferetGenerator, multiple_events_ir: IREventGroup) -> None:
    '''
    Test codegen of a module with multiple events.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    :param multiple_events_ir: The multiple events IR fixture.
    :type multiple_events_ir: IREventGroup
    '''

    result = generator.generate(multiple_events_ir)
    evts = result['evt_grp']['evts']

    # All three events keyed correctly.
    assert 'add' in evts
    assert 'subtract' in evts
    assert 'divide' in evts
    assert evts['add']['name'] == 'Add'
    assert evts['subtract']['name'] == 'Subtract'
    assert evts['divide']['name'] == 'Divide'

    # Each event has params with a and b.
    for key in ('add', 'subtract', 'divide'):
        params = evts[key]['execute']['params']
        assert len(params) == 2
        assert params[0].startswith('a:int:true')


# ** test: helper_method_event
def test_helper_method_event(generator: TiferetGenerator, helper_method_ir: IREventGroup) -> None:
    '''
    Test codegen of an event with a helper method.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    :param helper_method_ir: The helper method IR fixture.
    :type helper_method_ir: IREventGroup
    '''

    result = generator.generate(helper_method_ir)
    event = result['evt_grp']['evts']['add_integer']

    # Methods section present.
    assert 'methods' in event
    assert 'to_int' in event['methods']
    method = event['methods']['to_int']

    # Method has params, returns, and snippets.
    assert 'params' in method
    assert 'returns' in method
    assert 'snpt' in method
    assert len(method['params']) == 1
    assert method['params'][0].startswith('value:str:true')

    # Execute has two snippets.
    assert len(event['execute']['snpt']) == 2


# ** test: empty_node_omission
def test_empty_node_omission(generator: TiferetGenerator) -> None:
    '''
    Test that empty attributes, injections, methods, and description are omitted.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    '''

    ir = IREventGroup(
        name='empty_test',
        description='',
        import_groups=IRImportGroups(),
        events=IREvents(events=[
            IREvent(
                artifact_name='noop',
                class_name='Noop',
                doc_string='',
                attributes=IRAttributes(),
                injections=IRInjections(),
                execute=IRExecute(),
                methods=IRMethods(),
            ),
        ]),
    )

    result = generator.generate(ir)
    grp = result['evt_grp']

    # No description, no imports.
    assert 'desc' not in grp
    assert 'impt' not in grp

    # Event has no optional sections.
    event = grp['evts']['noop']
    assert 'desc' not in event
    assert 'attributes' not in event
    assert 'injections' not in event
    assert 'methods' not in event


# ** test: snippet_omits_empty_comments
def test_snippet_omits_empty_comments(generator: TiferetGenerator) -> None:
    '''
    Test that a snippet with no comments omits the coms key.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    '''

    snippet = IRSnippet(
        comments=IRComments(),
        statements=IRStatements(statements=[
            IRStatement(expr='Return(Add(a, b))'),
        ]),
    )

    result = generator.build_snippet(snippet)

    assert 'coms' not in result
    assert 'stmt' in result
    assert result['stmt'] == ['Return(Add(a, b))']


# ** test: import_group_collapses_same_module
def test_import_group_collapses_same_module(generator: TiferetGenerator) -> None:
    '''
    Test that imports from the same module are collapsed into one entry.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    '''

    group = IRImportGroup(category='app', imports=[
        IRImport(module_path='.settings', symbol='DomainEvent'),
        IRImport(module_path='.settings', symbol='a'),
        IRImport(module_path='..interfaces', symbol='ErrorService'),
    ])

    result = generator.build_import_group(group)

    assert len(result) == 2
    assert result[0]['src'] == '.settings'
    assert result[0]['tgts'] == ['DomainEvent', 'a']
    assert result[1]['src'] == '..interfaces'
    assert result[1]['tgts'] == ['ErrorService']


# ** test: encode_param_compact_format
def test_encode_param_compact_format(generator: TiferetGenerator) -> None:
    '''
    Test that encode_param produces the correct compact format.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    '''

    param = IRParam(
        name='a',
        type='str',
        required=True,
        default='',
        description='The first operand.',
    )

    result = generator.encode_param(param)

    assert result == 'a:str:true::The first operand.'


# ** test: encode_return_compact_format
def test_encode_return_compact_format(generator: TiferetGenerator) -> None:
    '''
    Test that encode_return produces the correct compact format.

    :param generator: The TiferetGenerator instance.
    :type generator: TiferetGenerator
    '''

    ret = IRReturn(type_name='int', description='The integer sum.')

    result = generator.encode_return(ret)

    assert result == 'int:The integer sum.'
