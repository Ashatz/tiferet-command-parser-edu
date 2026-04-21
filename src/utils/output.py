"""Output Utilities

This module consolidates all pipeline-terminal output concerns:

- ``OutputWriter`` — low-level file writer with format detection.
- ``OutputPrinter`` — console printing for errors, AST post-order traversal,
  and symbol tables.
- ``ResultPayloadBuilder`` — per-stage envelope builders.
- ``emit()`` — convenience helper that writes a payload when ``output`` is set.
"""

# *** imports

# ** core
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ** infra
import yaml

# ** app
from ..domain.ast import Declaration, Statement, Expression, Type, ParamList

# *** utils

# ** util: output_writer
class OutputWriter:
    '''
    Utility for writing pipeline result payloads to file.
    Supports YAML, JSON, and keter formats with auto-detection from
    the target file extension.
    '''

    # * method: detect_format (static)
    @staticmethod
    def detect_format(output_path: str, output_format: str = 'auto') -> str:
        '''
        Resolve the output format. If ``output_format`` is ``'auto'``,
        detect from the file extension; otherwise return ``output_format``
        unchanged.

        :param output_path: The target file path.
        :type output_path: str
        :param output_format: Explicit format or ``'auto'`` for detection.
        :type output_format: str
        :return: Resolved format (``'yaml'``, ``'json'``, or ``'keter'``).
        :rtype: str
        '''

        # Auto-detect format from file extension.
        if output_format == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.json':
                return 'json'
            if ext == '.keter':
                return 'keter'
            return 'yaml'

        # Return the explicit format.
        return output_format

    # * method: write (static)
    @staticmethod
    def write(result: Any, output_path: str, output_format: str = 'auto') -> None:
        '''
        Write a result payload to a file in the specified format.

        :param result: The result payload to write. Dicts are encoded as
            YAML/JSON; strings are written verbatim (keter DSL).
        :type result: Any
        :param output_path: The file path to write to.
        :type output_path: str
        :param output_format: The output format (``'yaml'``, ``'json'``,
            ``'keter'``, or ``'auto'``).
        :type output_format: str
        '''

        # Resolve the format.
        fmt = OutputWriter.detect_format(output_path, output_format)

        # Write the output file.
        with open(output_path, 'w', encoding='utf-8') as f:
            if fmt == 'json':
                json.dump(result, f, indent=2, default=str)
            elif fmt == 'keter':
                f.write(result if isinstance(result, str) else str(result))
            else:
                yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    # * method: parse_extract_names (static)
    @staticmethod
    def parse_extract_names(extract: str) -> Optional[List[str]]:
        '''
        Parse a comma-separated extract filter string into a list of names
        suitable for inclusion in the output payload.

        :param extract: Comma-separated artifact names, or ``None``.
        :type extract: str
        :return: A list of stripped names, or ``None`` if ``extract`` is
            falsy.
        :rtype: Optional[List[str]]
        '''

        # Return None if no filter provided.
        if not extract:
            return None

        # Split, strip, and return as a list.
        return [name.strip() for name in extract.split(',')]


# ** util: output_printer
class OutputPrinter:
    '''
    Utility for console printing of pipeline results. Centralizes error
    reporting, AST post-order traversal, and symbol-table diagnostics so
    every terminal emit event shares a single console surface.
    All methods are static.
    '''

    # * method: print_semantic_errors (static)
    @staticmethod
    def print_semantic_errors(errors: Optional[List[Dict[str, Any]]]) -> None:
        '''
        Print a list of semantic/type error descriptors to the console.

        :param errors: List of error descriptors from ``PerformTypeCheck``
            (each dict may carry ``error_code``, ``scope_path``, ``message``,
            ``lineno``, ``col``).
        :type errors: Optional[List[Dict[str, Any]]]
        '''

        # Nothing to print if no errors supplied.
        if not errors:
            return

        # Emit one line per error with location when available.
        for error in errors:
            loc = ''
            if error.get('lineno') is not None:
                loc = f" (line {error['lineno']}, col {error.get('col', '?')})"
            print(
                f"Type Error [{error.get('error_code', 'UNKNOWN')}] "
                f"in {error.get('scope_path', '?')}{loc}: "
                f"{error.get('message', '')}"
            )

    # * method: print_dead_code_warnings (static)
    @staticmethod
    def print_dead_code_warnings(warnings: Optional[List[Dict[str, Any]]]) -> None:
        '''
        Print a list of dead-code warnings (statements that follow a
        ``return`` within the same scope) to the console.

        :param warnings: List of warning descriptors from ``AnalyzeReturns``
            (each dict may carry ``warning_code``, ``scope_path``,
            ``message``, ``lineno``, ``col``, ``return_lineno``,
            ``return_col``).
        :type warnings: Optional[List[Dict[str, Any]]]
        '''

        # Nothing to print if no warnings supplied.
        if not warnings:
            return

        # Emit one line per warning with location when available.
        for warning in warnings:
            loc = ''
            if warning.get('lineno') is not None:
                loc = f" (line {warning['lineno']}, col {warning.get('col', '?')})"
            return_loc = ''
            if warning.get('return_lineno') is not None:
                return_loc = (
                    f" [after return at line {warning['return_lineno']},"
                    f" col {warning.get('return_col', '?')}]"
                )
            print(
                f"Warning [{warning.get('warning_code', 'UNKNOWN')}] "
                f"in {warning.get('scope_path', '?')}{loc}: "
                f"{warning.get('message', '')}{return_loc}"
            )

    # * method: print_ast (static)
    @staticmethod
    def print_ast(ast: Declaration) -> None:
        '''
        Print the AST post-order traversal with a section header.

        :param ast: The module ``Declaration`` root.
        :type ast: Declaration
        '''

        # Emit section banner then walk the declaration tree.
        print()
        print('--- AST (Post-Order Traversal) ---')
        print()
        OutputPrinter.print_declaration(ast)

    # * method: print_symbol_table (static)
    @staticmethod
    def print_symbol_table(symbol_table: Dict[str, Any]) -> None:
        '''
        Print the symbol table in a readable hierarchical format.

        :param symbol_table: The symbol table dict from
            ``SymbolTableBuilder.build()``.
        :type symbol_table: Dict[str, Any]
        '''

        module_name = symbol_table.get('module_name', 'unknown')
        scopes = symbol_table.get('scopes', {})

        # Leading newline for spacing and section header.
        print()
        print(f'=== Symbol Table: {module_name} ===')
        print()

        # Iterate scopes and print each with its symbols and children.
        for scope_path, scope_data in scopes.items():
            kind = scope_data.get('kind', '?')
            parent = scope_data.get('parent_path', None)
            parent_str = f' (parent: {parent})' if parent else ''

            print(f'Scope: {scope_path} [{kind}]{parent_str}')

            # Print symbols in the scope.
            symbols = scope_data.get('symbols', {})
            if symbols:
                print(f'  Symbols:')
                for sym_name, sym_data in symbols.items():
                    sym_kind = sym_data.get('kind', '?')
                    sym_type = sym_data.get('type_annotation', None)
                    sym_source = sym_data.get('source_module', None)

                    parts = [f'    {sym_name} [{sym_kind}]']
                    if sym_type:
                        parts.append(f'type={sym_type}')
                    if sym_source:
                        parts.append(f'from={sym_source}')
                    print(' '.join(parts))

            # Print children scopes.
            children = scope_data.get('children', {})
            if children:
                print(f'  Children:')
                for child_name, child_path in children.items():
                    print(f'    {child_name} -> {child_path}')

            print()

    # * method: print_declaration (static)
    @staticmethod
    def print_declaration(decl: Declaration, indent: int = 0) -> None:
        '''
        Print a declaration node using post-order traversal (children first).

        :param decl: The declaration to print.
        :type decl: Declaration
        :param indent: Current indentation level.
        :type indent: int
        '''

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit the code body (statement chain).
        if decl.code:
            OutputPrinter.print_statement(decl.code, indent + 1)

        # Visit the value expression.
        if decl.value:
            OutputPrinter.print_expression(decl.value, indent + 1)

        # Visit the type.
        if decl.type:
            OutputPrinter.print_type(decl.type, indent + 1)

        # Print this declaration node (post-order: after children).
        type_str = f' : {decl.type.kind}' if decl.type else ''
        doc_str = ''
        if decl.doc_string:
            doc_text = decl.doc_string[:40] + '...' if len(decl.doc_string) > 40 else decl.doc_string
            doc_str = f' doc="{doc_text}"'
        print(f'{prefix}[Declaration] name={decl.name}{type_str}{doc_str}')

        # Follow the .next chain (sibling declarations).
        if decl.next:
            OutputPrinter.print_declaration(decl.next, indent)

    # * method: print_statement (static)
    @staticmethod
    def print_statement(stmt: Statement, indent: int = 0) -> None:
        '''
        Print a statement node using post-order traversal.

        :param stmt: The statement to print.
        :type stmt: Statement
        :param indent: Current indentation level.
        :type indent: int
        '''

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit body (for artifact, snippet, if_else, for, while).
        if stmt.body:
            OutputPrinter.print_statement(stmt.body, indent + 1)

        # Visit else_body.
        if stmt.else_body:
            OutputPrinter.print_statement(stmt.else_body, indent + 1)

        # Visit declaration.
        if stmt.decl:
            OutputPrinter.print_declaration(stmt.decl, indent + 1)

        # Visit init_expr (for import_from).
        if stmt.init_expr:
            OutputPrinter.print_expression(stmt.init_expr, indent + 1)

        # Visit expr.
        if stmt.expr:
            OutputPrinter.print_expression(stmt.expr, indent + 1)

        # Print this statement node (post-order: after children).
        print(f'{prefix}[Statement] kind={stmt.kind}')

        # Follow the .next chain (sibling statements).
        if stmt.next:
            OutputPrinter.print_statement(stmt.next, indent)

    # * method: print_expression (static)
    @staticmethod
    def print_expression(expr: Expression, indent: int = 0) -> None:
        '''
        Print an expression node using post-order traversal.

        :param expr: The expression to print.
        :type expr: Expression
        :param indent: Current indentation level.
        :type indent: int
        '''

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit left sub-expression.
        if expr.left:
            OutputPrinter.print_expression(expr.left, indent + 1)

        # Visit right sub-expression.
        if expr.right:
            OutputPrinter.print_expression(expr.right, indent + 1)

        # Print this expression node (post-order: after children).
        val = f' value={expr.value}' if expr.value else ''
        name = f' name={expr.name}' if expr.name else ''
        print(f'{prefix}[Expression] kind={expr.kind}{name}{val}')

    # * method: print_type (static)
    @staticmethod
    def print_type(type_node: Type, indent: int = 0) -> None:
        '''
        Print a type node using post-order traversal.

        :param type_node: The type to print.
        :type type_node: Type
        :param indent: Current indentation level.
        :type indent: int
        '''

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit subtype.
        if type_node.subtype:
            OutputPrinter.print_type(type_node.subtype, indent + 1)

        # Visit return_type.
        if type_node.return_type:
            OutputPrinter.print_type(type_node.return_type, indent + 1)

        # Visit params.
        if type_node.params:
            OutputPrinter.print_param_list(type_node.params, indent + 1)

        # Print this type node (post-order: after children).
        name = f' name={type_node.name}' if type_node.name else ''
        print(f'{prefix}[Type] kind={type_node.kind}{name}')

    # * method: print_param_list (static)
    @staticmethod
    def print_param_list(param: ParamList, indent: int = 0) -> None:
        '''
        Print a parameter list node using post-order traversal.

        :param param: The first parameter in the linked list.
        :type param: ParamList
        :param indent: Current indentation level.
        :type indent: int
        '''

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit default value expression.
        if param.default:
            OutputPrinter.print_expression(param.default, indent + 1)

        # Visit type.
        if param.type:
            OutputPrinter.print_type(param.type, indent + 1)

        # Print this param node (post-order: after children).
        req = ' required' if param.required else ' optional'
        print(f'{prefix}[Param] name={param.name}{req}')

        # Follow the .next chain.
        if param.next:
            OutputPrinter.print_param_list(param.next, indent)


# ** util: result_payload_builder
class ResultPayloadBuilder:
    '''
    Per-stage result payload builders. Each stage's builder assembles the
    envelope shape expected by its corresponding pipeline feature.
    All methods are static.
    '''

    # * method: build_envelope (static)
    @staticmethod
    def build_envelope(event_type: str, source_file: Optional[str]) -> Dict[str, Any]:
        '''
        Build the shared envelope (event_type, timestamp, source_file) used
        by the scan, parse, and semantic stages.

        :param event_type: The event type identifier for the payload.
        :type event_type: str
        :param source_file: Optional source file path.
        :type source_file: Optional[str]
        :return: The envelope dict.
        :rtype: Dict[str, Any]
        '''

        # Assemble the standard envelope fields.
        return {
            'event_type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_file': source_file,
        }

    # * method: build_scan_payload (static)
    @staticmethod
    def build_scan_payload(
            source_file: Optional[str],
            tokens: Optional[List[Any]],
        ) -> Dict[str, Any]:
        '''
        Assemble the scan result payload.

        :param source_file: Original source file path.
        :type source_file: Optional[str]
        :param tokens: List of token aggregates.
        :type tokens: Optional[List[Any]]
        :return: The assembled scan payload.
        :rtype: Dict[str, Any]
        '''

        # Build the envelope and append the token list + count.
        result = ResultPayloadBuilder.build_envelope('TokensScanned', source_file)
        result['tokens'] = [t.model_dump() for t in tokens] if tokens else []
        result['token_count'] = len(tokens) if tokens else 0

        # Return the assembled payload.
        return result

    # * method: build_parse_payload (static)
    @staticmethod
    def build_parse_payload(
            source_file: Optional[str],
            ast: Any,
            tokens: Optional[List[Any]] = None,
            extract: Optional[str] = None,
            include_tokens: bool = False,
        ) -> Dict[str, Any]:
        '''
        Assemble the parse result payload.

        :param source_file: Original source file path.
        :type source_file: Optional[str]
        :param ast: The parsed module declaration aggregate.
        :type ast: Any
        :param tokens: Optional list of token aggregates.
        :type tokens: Optional[List[Any]]
        :param extract: Optional comma-separated extract filter string.
        :type extract: Optional[str]
        :param include_tokens: If truthy, include tokens in the output.
        :type include_tokens: bool
        :return: The assembled parse payload.
        :rtype: Dict[str, Any]
        '''

        # Build the envelope and append the serialized AST.
        result = ResultPayloadBuilder.build_envelope('ParseCompleted', source_file)
        result['ast'] = ast.model_dump(exclude_none=True, exclude_unset=True)

        # Include extracted artifact names if an extract filter was supplied.
        extracted_names = OutputWriter.parse_extract_names(extract)
        if extracted_names:
            result['extracted_artifacts'] = extracted_names

        # Include the tokens list and count if requested.
        if include_tokens:
            result['tokens'] = [t.model_dump() for t in tokens] if tokens else []
            result['token_count'] = len(tokens) if tokens else 0

        # Return the assembled payload.
        return result

    # * method: build_semantic_payload (static)
    @staticmethod
    def build_semantic_payload(
            source_file: Optional[str],
            semantic: Dict[str, Any],
            semantic_errors: Optional[List[Dict[str, Any]]] = None,
            dead_code_warnings: Optional[List[Dict[str, Any]]] = None,
            ast: Any = None,
            tokens: Optional[List[Any]] = None,
            include_tokens: bool = False,
            include_ast: bool = False,
        ) -> Dict[str, Any]:
        '''
        Assemble the semantic analysis result payload.

        :param source_file: Original source file path.
        :type source_file: Optional[str]
        :param semantic: Semantic analysis result.
        :type semantic: Dict[str, Any]
        :param semantic_errors: Optional list of type check error descriptors.
        :type semantic_errors: Optional[List[Dict[str, Any]]]
        :param dead_code_warnings: Optional list of dead-code warning
            descriptors from ``AnalyzeReturns``.
        :type dead_code_warnings: Optional[List[Dict[str, Any]]]
        :param ast: Optional parsed AST root.
        :type ast: Any
        :param tokens: Optional list of token aggregates.
        :type tokens: Optional[List[Any]]
        :param include_tokens: If truthy, include tokens in the output.
        :type include_tokens: bool
        :param include_ast: If truthy, include the AST in the output.
        :type include_ast: bool
        :return: The assembled semantic payload.
        :rtype: Dict[str, Any]
        '''

        # Build the envelope. Omit the symbol table and resolution when type errors exist.
        result = ResultPayloadBuilder.build_envelope('SemanticAnalysisCompleted', source_file)
        if not semantic_errors:
            result['symbol_table'] = semantic.get('symbol_table', {}) if semantic else {}
            result['resolution'] = semantic.get('resolution', {}) if semantic else {}

        # Include dead-code warnings when any were reported.
        if dead_code_warnings:
            result['dead_code_warnings'] = dead_code_warnings

        # Include the AST if requested and available.
        if include_ast and ast is not None and hasattr(ast, 'model_dump'):
            result['ast'] = ast.model_dump(exclude_none=True, exclude_unset=True)

        # Include the tokens list and count if requested.
        if include_tokens:
            result['tokens'] = [t.model_dump() for t in tokens] if tokens else []
            result['token_count'] = len(tokens) if tokens else 0

        # Return the assembled payload.
        return result

    # * method: build_ir_payload (static)
    @staticmethod
    def build_ir_payload(ir: Any) -> str:
        '''
        Serialize the IREventGroup to a keter DSL string.

        :param ir: The root IREventGroup.
        :type ir: Any
        :return: The keter DSL string.
        :rtype: str
        '''

        # Delegate to the aggregate's serialization method.
        return ir.to_keter()

    # * method: build_codegen_payload (static)
    @staticmethod
    def build_codegen_payload(
            codegen: Dict[str, Any],
            semantic_errors: Optional[List[Dict[str, Any]]] = None,
            dead_code_warnings: Optional[List[Dict[str, Any]]] = None,
        ) -> Dict[str, Any]:
        '''
        Return the codegen dict as the payload. ``semantic_errors`` and
        ``dead_code_warnings`` are printed by the caller and do not alter
        the payload shape.

        :param codegen: The codegen output dict.
        :type codegen: Dict[str, Any]
        :param semantic_errors: Optional list of type check error descriptors.
        :type semantic_errors: Optional[List[Dict[str, Any]]]
        :param dead_code_warnings: Optional list of dead-code warning
            descriptors from ``AnalyzeReturns``.
        :type dead_code_warnings: Optional[List[Dict[str, Any]]]
        :return: The codegen dict.
        :rtype: Dict[str, Any]
        '''

        # Pass the codegen dict through unchanged.
        return codegen


# ** util: emit (function)
def emit(payload: Any, output: Optional[str] = None, output_format: str = 'auto') -> Any:
    '''
    Emit a payload: write to a file when ``output`` is set, and return
    the payload. The payload is always returned so downstream callers
    and tests can inspect the result uniformly.

    :param payload: The assembled payload (dict or string).
    :type payload: Any
    :param output: Optional output file path.
    :type output: Optional[str]
    :param output_format: Output format (``'yaml'``, ``'json'``, ``'keter'``,
        or ``'auto'``).
    :type output_format: str
    :return: The payload (unchanged).
    :rtype: Any
    '''

    # Write to file if an output path is specified.
    if output:
        OutputWriter.write(payload, output, output_format)

    # Always return the payload.
    return payload
