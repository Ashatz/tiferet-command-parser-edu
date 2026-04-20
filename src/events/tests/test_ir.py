"""Events – IR Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...domain.ir import IREventGroup, IRImportGroups, IREvents
from ...interfaces.ir import IRService
from ...mappers import Decl
from ..ir import GenerateIR

# *** fixtures

# ** fixture: mock_ir_service
@pytest.fixture
def mock_ir_service() -> IRService:
    '''
    Returns a mock IRService for testing.

    :return: A mock IRService.
    :rtype: IRService
    '''

    return mock.Mock(spec=IRService)


# ** fixture: sample_ir
@pytest.fixture
def sample_ir() -> IREventGroup:
    '''
    Returns a minimal IREventGroup for testing.

    :return: A sample IREventGroup.
    :rtype: IREventGroup
    '''

    return IREventGroup(
        name='test_module',
        description='A test module.',
        import_groups=IRImportGroups(),
        events=IREvents(),
    )


# ** fixture: sample_decl
@pytest.fixture
def sample_decl() -> Decl:
    '''
    Returns a minimal DeclarationAggregate for testing.

    :return: A sample Decl.
    :rtype: Decl
    '''

    return Decl.new_module_decl(name='test_module')


# *** tests — GenerateIR

# ** test: generate_ir_success
def test_generate_ir_success(
        mock_ir_service: IRService,
        sample_ir: IREventGroup,
        sample_decl: Decl,
    ) -> None:
    '''
    Test that GenerateIR calls ir_service.generate and returns the IREventGroup.

    :param mock_ir_service: The mock IR service.
    :type mock_ir_service: IRService
    :param sample_ir: The expected IREventGroup result.
    :type sample_ir: IREventGroup
    :param sample_decl: The input AST declaration.
    :type sample_decl: Decl
    '''

    # Arrange the service to return the sample IR.
    mock_ir_service.generate.return_value = sample_ir

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        GenerateIR,
        dependencies={'ir_service': mock_ir_service},
        ast=sample_decl,
    )

    # Assert the result is the sample IR and the service was called.
    assert result is sample_ir
    mock_ir_service.generate.assert_called_once_with(sample_decl, {})


# ** test: generate_ir_with_semantic
def test_generate_ir_with_semantic(
        mock_ir_service: IRService,
        sample_ir: IREventGroup,
        sample_decl: Decl,
    ) -> None:
    '''
    Test that GenerateIR passes the symbol_table from semantic dict to the service.

    :param mock_ir_service: The mock IR service.
    :type mock_ir_service: IRService
    :param sample_ir: The expected IREventGroup result.
    :type sample_ir: IREventGroup
    :param sample_decl: The input AST declaration.
    :type sample_decl: Decl
    '''

    # Arrange the service and semantic data.
    mock_ir_service.generate.return_value = sample_ir
    semantic = {'symbol_table': {'module_name': 'test_module', 'scopes': {}}}

    # Execute.
    result = DomainEvent.handle(
        GenerateIR,
        dependencies={'ir_service': mock_ir_service},
        ast=sample_decl,
        semantic=semantic,
    )

    # Assert the symbol_table was passed through.
    assert result is sample_ir
    mock_ir_service.generate.assert_called_once_with(
        sample_decl,
        {'module_name': 'test_module', 'scopes': {}},
    )


# ** test: generate_ir_missing_ast
def test_generate_ir_missing_ast(mock_ir_service: IRService) -> None:
    '''
    Test that GenerateIR raises TiferetError when ast is not provided.

    :param mock_ir_service: The mock IR service.
    :type mock_ir_service: IRService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            GenerateIR,
            dependencies={'ir_service': mock_ir_service},
            # ast intentionally omitted
        )


