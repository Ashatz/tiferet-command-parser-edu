"""Events – Codegen Domain Event Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.events import TiferetError, DomainEvent

# ** app
from ...domain.ir import IREventGroup, IRImportGroups, IREvents
from ...interfaces.codegen import CodegenService
from ...interfaces.optimizer import OptimizerService
from ..codegen import GenerateCode
from ..optimizer import OptimizeCode

# *** fixtures

# ** fixture: mock_codegen_service
@pytest.fixture
def mock_codegen_service() -> CodegenService:
    '''
    Returns a mock CodegenService for testing.

    :return: A mock CodegenService.
    :rtype: CodegenService
    '''

    return mock.Mock(spec=CodegenService)


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


# ** fixture: sample_codegen_output
@pytest.fixture
def sample_codegen_output() -> dict:
    '''
    Returns a sample codegen output dict for testing.

    :return: A sample codegen dict.
    :rtype: dict
    '''

    return {
        'evt_grp': {
            'name': 'test_module',
            'desc': 'A test module.',
        }
    }


# *** tests — GenerateCode

# ** test: generate_code_success
def test_generate_code_success(
        mock_codegen_service: CodegenService,
        sample_ir: IREventGroup,
        sample_codegen_output: dict,
    ) -> None:
    '''
    Test that GenerateCode calls codegen_service.generate and returns the dict.

    :param mock_codegen_service: The mock codegen service.
    :type mock_codegen_service: CodegenService
    :param sample_ir: The input IREventGroup.
    :type sample_ir: IREventGroup
    :param sample_codegen_output: The expected output dict.
    :type sample_codegen_output: dict
    '''

    # Arrange the service to return the sample output.
    mock_codegen_service.generate.return_value = sample_codegen_output

    # Execute via DomainEvent.handle.
    result = DomainEvent.handle(
        GenerateCode,
        dependencies={'codegen_service': mock_codegen_service},
        ir=sample_ir,
    )

    # Assert the result is the expected output and the service was called.
    assert result is sample_codegen_output
    mock_codegen_service.generate.assert_called_once_with(sample_ir)


# ** test: generate_code_missing_ir
def test_generate_code_missing_ir(mock_codegen_service: CodegenService) -> None:
    '''
    Test that GenerateCode raises TiferetError when ir is not provided.

    :param mock_codegen_service: The mock codegen service.
    :type mock_codegen_service: CodegenService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            GenerateCode,
            dependencies={'codegen_service': mock_codegen_service},
            # ir intentionally omitted
        )


# *** tests — OptimizeCode

# ** fixture: mock_optimizer_service
@pytest.fixture
def mock_optimizer_service() -> OptimizerService:
    '''
    Returns a mock OptimizerService for testing.

    :return: A mock OptimizerService.
    :rtype: OptimizerService
    '''

    return mock.Mock(spec=OptimizerService)


# ** test: optimize_code_success
def test_optimize_code_success(
        mock_optimizer_service: OptimizerService,
        sample_codegen_output: dict,
    ) -> None:
    '''
    Test that OptimizeCode calls optimizer_service.optimize and returns the dict.

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    :param sample_codegen_output: The sample codegen output dict.
    :type sample_codegen_output: dict
    '''

    # Arrange the service to return the same dict.
    mock_optimizer_service.optimize.return_value = sample_codegen_output

    # Execute via DomainEvent.handle with O2 optimization level.
    result = DomainEvent.handle(
        OptimizeCode,
        dependencies={'optimizer_service': mock_optimizer_service},
        codegen=sample_codegen_output,
        O='O2',
    )

    # Assert the result is the optimized dict and the service was called.
    assert result is sample_codegen_output
    mock_optimizer_service.optimize.assert_called_once_with(sample_codegen_output)


# ** test: optimize_code_missing_codegen
def test_optimize_code_missing_codegen(mock_optimizer_service: OptimizerService) -> None:
    '''
    Test that OptimizeCode raises TiferetError when codegen is not provided.

    :param mock_optimizer_service: The mock optimizer service.
    :type mock_optimizer_service: OptimizerService
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            OptimizeCode,
            dependencies={'optimizer_service': mock_optimizer_service},
            # codegen intentionally omitted
        )
