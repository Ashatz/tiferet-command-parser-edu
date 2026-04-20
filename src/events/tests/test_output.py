"""Output Domain Event Tests"""

# *** imports

# ** core
import os

# ** infra
import pytest
from tiferet.events import DomainEvent, TiferetError

# ** app
from ...domain.ir import IREventGroup, IRImportGroups, IREvents
from ...mappers import Decl, Tok, TokenAggregate
from ..output import EmitResult

# *** fixtures

# ** fixture: sample_tokens
@pytest.fixture
def sample_tokens() -> list:
    '''
    Return a small list of token aggregates for stage tests.
    '''

    # Construct a simple two-token list.
    return [
        Tok.new(type='CLASS', value='class', lineno=1, lexpos=0),
        Tok.new(type='IDENTIFIER', value='Sample', lineno=1, lexpos=6),
    ]


# ** fixture: sample_decl
@pytest.fixture
def sample_decl() -> Decl:
    '''
    Return a minimal module declaration aggregate.
    '''

    # Build a module declaration.
    return Decl.new_module_decl(name='test_module')


# ** fixture: sample_ir
@pytest.fixture
def sample_ir() -> IREventGroup:
    '''
    Return a minimal IREventGroup.
    '''

    # Build an IR event group.
    return IREventGroup(
        name='test_module',
        description='A test module.',
        import_groups=IRImportGroups(),
        events=IREvents(),
    )


# ** fixture: sample_semantic
@pytest.fixture
def sample_semantic() -> dict:
    '''
    Return a minimal semantic analysis result.
    '''

    # Build the minimal expected shape.
    return {
        'symbol_table': {'module_name': 'test_module', 'scopes': {}},
        'resolution': {'resolved': [], 'unresolved': []},
    }


# *** tests — detect_stage

# ** test: detect_stage_prefers_codegen
def test_detect_stage_prefers_codegen(
        sample_tokens: list,
        sample_decl: Decl,
        sample_ir: IREventGroup,
        sample_semantic: dict,
    ) -> None:
    '''
    Test that detect_stage picks codegen when the codegen dict is present.
    '''

    # All inputs present; codegen should win.
    stage = EmitResult.detect_stage(
        tokens=sample_tokens,
        ast=sample_decl,
        semantic=sample_semantic,
        ir=sample_ir,
        codegen={'evt_grp': {'name': 'test'}},
    )

    # Assert codegen stage selected.
    assert stage == 'codegen'


# ** test: detect_stage_prefers_ir_over_semantic
def test_detect_stage_prefers_ir_over_semantic(
        sample_decl: Decl,
        sample_ir: IREventGroup,
        sample_semantic: dict,
    ) -> None:
    '''
    Test that detect_stage picks ir when ir and semantic are both present.
    '''

    # ir stage should be selected over semantic.
    stage = EmitResult.detect_stage(
        ast=sample_decl,
        semantic=sample_semantic,
        ir=sample_ir,
    )
    assert stage == 'ir'


# ** test: detect_stage_semantic
def test_detect_stage_semantic(sample_decl: Decl, sample_semantic: dict) -> None:
    '''
    Test that detect_stage picks semantic when semantic is present without ir/codegen.
    '''

    # semantic should be selected.
    stage = EmitResult.detect_stage(ast=sample_decl, semantic=sample_semantic)
    assert stage == 'semantic'


# ** test: detect_stage_parse
def test_detect_stage_parse(sample_decl: Decl) -> None:
    '''
    Test that detect_stage picks parse when only the AST is present.
    '''

    # parse should be selected.
    assert EmitResult.detect_stage(ast=sample_decl) == 'parse'


# ** test: detect_stage_scan
def test_detect_stage_scan(sample_tokens: list) -> None:
    '''
    Test that detect_stage picks scan when only tokens are present.
    '''

    # scan should be selected.
    assert EmitResult.detect_stage(tokens=sample_tokens) == 'scan'


# ** test: detect_stage_none
def test_detect_stage_none() -> None:
    '''
    Test that detect_stage returns None when no inputs are provided.
    '''

    # With no inputs, stage is None.
    assert EmitResult.detect_stage() is None


# *** tests — stage dispatch

# ** test: emit_result_scan
def test_emit_result_scan(sample_tokens: list) -> None:
    '''
    Test scan-stage dispatch returns a TokensScanned envelope.
    '''

    # Emit with tokens only.
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        source_file='test.py',
        tokens=sample_tokens,
    )

    # Assert envelope shape.
    assert result['event_type'] == 'TokensScanned'
    assert result['token_count'] == 2


# ** test: emit_result_parse
def test_emit_result_parse(sample_decl: Decl) -> None:
    '''
    Test parse-stage dispatch returns a ParseCompleted envelope.
    '''

    # Emit with AST only (no tokens => parse stage).
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        source_file='test.py',
        ast=sample_decl,
    )

    # Assert envelope shape.
    assert result['event_type'] == 'ParseCompleted'
    assert 'ast' in result


# ** test: emit_result_semantic_with_errors
def test_emit_result_semantic_with_errors(
        sample_decl: Decl,
        sample_semantic: dict,
    ) -> None:
    '''
    Test that semantic-stage dispatch omits the symbol table when errors exist.
    '''

    # Emit with semantic errors present.
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        source_file='test.py',
        ast=sample_decl,
        semantic=sample_semantic,
        semantic_errors=[{
            'error_code': 'TYPE_MISMATCH_ASSIGNMENT',
            'scope_path': 'module.Sample',
            'message': 'bad',
        }],
    )

    # Assert errors cause the symbol table to be omitted.
    assert result['event_type'] == 'SemanticAnalysisCompleted'
    assert 'symbol_table' not in result
    assert 'resolution' not in result


# ** test: emit_result_ir
def test_emit_result_ir(sample_ir: IREventGroup) -> None:
    '''
    Test ir-stage dispatch returns a keter DSL string.
    '''

    # Emit with IR only.
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        ir=sample_ir,
    )

    # Assert result is a keter string.
    assert isinstance(result, str)
    assert 'EventGroup(test_module' in result


# ** test: emit_result_codegen
def test_emit_result_codegen() -> None:
    '''
    Test codegen-stage dispatch returns the codegen dict unchanged.
    '''

    # Emit with codegen dict only.
    codegen = {'evt_grp': {'name': 'test_module'}}
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        codegen=codegen,
    )

    # Assert the same dict is returned.
    assert result is codegen


# ** test: emit_result_explicit_stage_override
def test_emit_result_explicit_stage_override(
        sample_tokens: list,
        sample_ir: IREventGroup,
    ) -> None:
    '''
    Test that an explicit stage hint overrides auto-detection.
    '''

    # Even with ir present, forcing scan should pick the scan payload.
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        stage='scan',
        source_file='test.py',
        tokens=sample_tokens,
        ir=sample_ir,
    )

    # Assert the scan envelope is returned.
    assert result['event_type'] == 'TokensScanned'


# ** test: emit_result_no_inputs_raises
def test_emit_result_no_inputs_raises() -> None:
    '''
    Test that EmitResult raises when no inputs are supplied.
    '''

    # With no inputs, a TiferetError should be raised.
    with pytest.raises(TiferetError):
        DomainEvent.handle(
            EmitResult,
            dependencies={},
        )


# ** test: emit_result_writes_file
def test_emit_result_writes_file(sample_decl: Decl, tmp_path) -> None:
    '''
    Test that EmitResult writes the payload to file when output is set.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: pathlib.Path
    '''

    # Emit with an output path and verify the file is written.
    output_path = str(tmp_path / 'parse.yaml')
    result = DomainEvent.handle(
        EmitResult,
        dependencies={},
        ast=sample_decl,
        source_file='test.py',
        output=output_path,
    )

    # Payload is always returned and the file is written.
    assert result['event_type'] == 'ParseCompleted'
    assert os.path.isfile(output_path)
