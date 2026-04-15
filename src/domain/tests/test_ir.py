"""Domain – IR Domain Objects Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..ir import (
    IRImport,
    IRImportGroup,
    IRImportGroups,
    IRAttribute,
    IRAttributes,
    IRAssign,
    IRInjection,
    IRParam,
    IRReturn,
    IRReturns,
    IRComment,
    IRStatement,
    IRSnippet,
    IRSnippets,
    IRExecute,
    IRMethods,
    IREvent,
    IREventGroup,
)

# *** fixtures

# ** fixture: sample_import
@pytest.fixture
def sample_import() -> IRImport:
    '''
    Returns a sample IRImport node.

    :return: An IRImport for DomainEvent from .settings.
    :rtype: IRImport
    '''

    return IRImport(module_path='.settings', symbol='DomainEvent')


# ** fixture: sample_import_group
@pytest.fixture
def sample_import_group(sample_import: IRImport) -> IRImportGroup:
    '''
    Returns a sample IRImportGroup with one import.

    :param sample_import: The import to include.
    :type sample_import: IRImport
    :return: An IRImportGroup for the "app" category.
    :rtype: IRImportGroup
    '''

    return IRImportGroup(category='app', imports=[sample_import])


# ** fixture: sample_execute
@pytest.fixture
def sample_execute() -> IRExecute:
    '''
    Returns a minimal IRExecute node with one param and one return.

    :return: A sample IRExecute node.
    :rtype: IRExecute
    '''

    from ..ir import IRParams, IRParam, IRReturns, IRReturn, IRSnippets
    return IRExecute(
        name='execute',
        params=IRParams(params=[IRParam(name='a', type='int', required=True)]),
        returns=IRReturns(returns=[IRReturn(type_name='int', description='The result.')]),
        snippets=IRSnippets(),
    )


# *** tests

# ** test: ir_import_to_keter
def test_ir_import_to_keter(sample_import: IRImport) -> None:
    '''
    Test that IRImport serializes correctly with quotes and trailing comma.

    :param sample_import: Sample import node.
    :type sample_import: IRImport
    '''

    result = sample_import.to_keter(indent=0)
    assert result == 'Import(.settings, DomainEvent),'


# ** test: ir_import_to_keter_indented
def test_ir_import_to_keter_indented(sample_import: IRImport) -> None:
    '''
    Test that IRImport respects the indent level.

    :param sample_import: Sample import node.
    :type sample_import: IRImport
    '''

    result = sample_import.to_keter(indent=2)
    assert result.startswith('        Import(.settings,')


# ** test: ir_import_group_to_keter
def test_ir_import_group_to_keter(sample_import_group: IRImportGroup) -> None:
    '''
    Test that IRImportGroup wraps imports in the ImportGroup constructor.

    :param sample_import_group: Sample import group.
    :type sample_import_group: IRImportGroup
    '''

    result = sample_import_group.to_keter(indent=0)
    assert 'ImportGroup(app, Imports(' in result
    assert 'Import(.settings, DomainEvent),' in result


# ** test: ir_attribute_to_keter
def test_ir_attribute_to_keter() -> None:
    '''
    Test that IRAttribute serializes name and type correctly.
    '''

    attr = IRAttribute(name='pong', type='str')
    result = attr.to_keter(indent=0)
    assert result == 'Attribute(pong, str),'


# ** test: ir_assign_to_keter
def test_ir_assign_to_keter() -> None:
    '''
    Test that IRAssign serializes to the Assign(Attribute(...), "...") form.
    '''

    assign = IRAssign(target='error_service', source='error_service')
    result = assign.to_keter(indent=0)
    assert result == 'Assign(Attribute(error_service), error_service)'


# ** test: ir_injection_to_keter
def test_ir_injection_to_keter() -> None:
    '''
    Test that IRInjection serializes to a param string + Assign expression.
    '''

    from ..ir import IRInjection
    inj = IRInjection(
        name='error_service',
        type='ErrorService',
        description='The error service.',
        assign=IRAssign(target='error_service', source='error_service'),
    )
    result = inj.to_keter(indent=0)
    assert 'Injection("error_service:ErrorService:true::The error service.",' in result
    assert 'Assign(Attribute(error_service), error_service)' in result


# ** test: ir_param_required_to_keter
def test_ir_param_required_to_keter() -> None:
    '''
    Test IRParam encoding for a required param with no default or description.
    '''

    param = IRParam(name='id', type='str', required=True, default='', description='')
    result = param.to_keter(indent=0)
    assert result == 'Param("id:str:true::"),'


# ** test: ir_param_optional_to_keter
def test_ir_param_optional_to_keter() -> None:
    '''
    Test IRParam encoding for an optional param with a default and description.
    '''

    param = IRParam(
        name='include_defaults',
        type='bool',
        required=False,
        default='False',
        description='Search defaults if not found.',
    )
    result = param.to_keter(indent=0)
    assert 'Param("include_defaults:bool:false:False:Search defaults if not found."),' == result


# ** test: ir_return_to_keter
def test_ir_return_to_keter() -> None:
    '''
    Test IRReturn serializes to type:description format.
    '''

    ret = IRReturn(type_name='str', description='The result string.')
    result = ret.to_keter(indent=0)
    assert result == 'Return("str:The result string."),'


# ** test: ir_methods_empty_to_keter
def test_ir_methods_empty_to_keter() -> None:
    '''
    Test that an empty IRMethods serializes to Methods() on a single line.
    '''

    methods = IRMethods()
    result = methods.to_keter(indent=0)
    assert result == 'Methods()'


# ** test: ir_execute_to_keter_contains_sections
def test_ir_execute_to_keter_contains_sections(sample_execute: IRExecute) -> None:
    '''
    Test that IRExecute output contains Execute, Params, Returns, and Snippets sections.

    :param sample_execute: Sample execute node.
    :type sample_execute: IRExecute
    '''

    result = sample_execute.to_keter(indent=0)
    assert 'Execute(' in result
    assert 'Params(' in result
    assert 'Returns(' in result
    assert 'Snippets(' in result


# ** test: ir_event_group_to_keter_structure
def test_ir_event_group_to_keter_structure() -> None:
    '''
    Test that IREventGroup output contains the root EventGroup constructor with
    ImportGroups and Events sections.
    '''

    from ..ir import IRImportGroups, IREvents
    group = IREventGroup(
        name='test_module',
        description='A test module.',
        import_groups=IRImportGroups(),
        events=IREvents(),
    )
    result = group.to_keter()
    assert 'EventGroup(test_module, "A test module.",' in result
    assert 'ImportGroups(' in result
    assert 'Events(' in result
