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
from ..codegen import GenerateCode, OptimizeCode, EmitCodegenResult

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


# *** tests — EmitCodegenResult

# ** test: emit_codegen_result_returns_dict
def test_emit_codegen_result_returns_dict(sample_codegen_output: dict) -> None:
    '''
    Test that EmitCodegenResult returns the codegen dict when no output path is given.

    :param sample_codegen_output: The sample codegen output dict.
    :type sample_codegen_output: dict
    '''

    # Execute without an output path.
    result = DomainEvent.handle(
        EmitCodegenResult,
        dependencies={},
        codegen=sample_codegen_output,
    )

    # Verify the result is the codegen dict.
    assert result is sample_codegen_output


# ** test: emit_codegen_result_writes_yaml
def test_emit_codegen_result_writes_yaml(
        sample_codegen_output: dict,
        tmp_path,
    ) -> None:
    '''
    Test that EmitCodegenResult writes YAML output to file when output path is given.

    :param sample_codegen_output: The sample codegen output dict.
    :type sample_codegen_output: dict
    :param tmp_path: Pytest temporary path fixture.
    :type tmp_path: pathlib.Path
    '''

    # Define a temporary output path.
    output_path = str(tmp_path / 'output.yaml')

    # Execute with output path.
    result = DomainEvent.handle(
        EmitCodegenResult,
        dependencies={},
        codegen=sample_codegen_output,
        output=output_path,
    )

    # Verify the event returned empty string and the file was written.
    assert result == ''
    with open(output_path, 'r') as f:
        content = f.read()
    assert 'test_module' in content


# ** test: emit_codegen_result_writes_json
def test_emit_codegen_result_writes_json(
        sample_codegen_output: dict,
        tmp_path,
    ) -> None:
    '''
    Test that EmitCodegenResult writes JSON output to file.

    :param sample_codegen_output: The sample codegen output dict.
    :type sample_codegen_output: dict
    :param tmp_path: Pytest temporary path fixture.
    :type tmp_path: pathlib.Path
    '''

    # Define a temporary JSON output path.
    output_path = str(tmp_path / 'output.json')

    # Execute with output path.
    result = DomainEvent.handle(
        EmitCodegenResult,
        dependencies={},
        codegen=sample_codegen_output,
        output=output_path,
    )

    # Verify the file was written as JSON.
    assert result == ''
    with open(output_path, 'r') as f:
        content = f.read()
    assert '"test_module"' in content


# ** test: emit_codegen_result_missing_codegen
def test_emit_codegen_result_missing_codegen() -> None:
    '''
    Test that EmitCodegenResult raises TiferetError when codegen is not provided.
    '''

    with pytest.raises(TiferetError):
        DomainEvent.handle(
            EmitCodegenResult,
            dependencies={},
            # codegen intentionally omitted
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

    # Execute via DomainEvent.handle with optimize flag.
    result = DomainEvent.handle(
        OptimizeCode,
        dependencies={'optimizer_service': mock_optimizer_service},
        codegen=sample_codegen_output,
        optimize='true',
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
