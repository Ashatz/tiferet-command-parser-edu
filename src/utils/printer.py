"""AST Post-Order Traversal Printer and Symbol Table Printer Utilities"""

# *** imports

# ** core
from typing import Dict, Any

# ** app
from ..domain.ast import Declaration, Statement, Expression, Type, ParamList

# *** utils

# ** util: ast_printer
class ASTPrinter:
    """
    Utility for printing the AST using post-order traversal
    and printing symbol tables in a readable format.
    All methods are static.
    """

    # * method: print_ast (static)
    @staticmethod
    def print_ast(decl: Declaration, indent: int = 0) -> None:
        """
        Print the AST using post-order traversal (children before parent).
        Walks the full Declaration -> Statement -> Expression tree.

        :param decl: The root declaration (module).
        :type decl: Declaration
        :param indent: Current indentation level.
        :type indent: int
        """

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit the code body (statement chain).
        if decl.code:
            ASTPrinter.print_statement(decl.code, indent + 1)

        # Visit the value expression.
        if decl.value:
            ASTPrinter.print_expression(decl.value, indent + 1)

        # Visit the type.
        if decl.type:
            ASTPrinter.print_type(decl.type, indent + 1)

        # Print this declaration node (post-order: after children).
        type_str = f' : {decl.type.kind}' if decl.type else ''
        doc_str = ''
        if decl.doc_string:
            doc_text = decl.doc_string[:40] + '...' if len(decl.doc_string) > 40 else decl.doc_string
            doc_str = f' doc="{doc_text}"'
        print(f'{prefix}[Declaration] name={decl.name}{type_str}{doc_str}')

        # Follow the .next chain (sibling declarations).
        if decl.next:
            ASTPrinter.print_ast(decl.next, indent)

    # * method: print_statement (static)
    @staticmethod
    def print_statement(stmt: Statement, indent: int = 0) -> None:
        """
        Print a statement node using post-order traversal.

        :param stmt: The statement to print.
        :type stmt: Statement
        :param indent: Current indentation level.
        :type indent: int
        """

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit body (for artifact, snippet, if_else, for, while).
        if stmt.body:
            ASTPrinter.print_statement(stmt.body, indent + 1)

        # Visit else_body.
        if stmt.else_body:
            ASTPrinter.print_statement(stmt.else_body, indent + 1)

        # Visit declaration.
        if stmt.decl:
            ASTPrinter.print_ast(stmt.decl, indent + 1)

        # Visit init_expr (for import_from).
        if stmt.init_expr:
            ASTPrinter.print_expression(stmt.init_expr, indent + 1)

        # Visit expr.
        if stmt.expr:
            ASTPrinter.print_expression(stmt.expr, indent + 1)

        # Print this statement node (post-order: after children).
        print(f'{prefix}[Statement] kind={stmt.kind}')

        # Follow the .next chain (sibling statements).
        if stmt.next:
            ASTPrinter.print_statement(stmt.next, indent)

    # * method: print_expression (static)
    @staticmethod
    def print_expression(expr: Expression, indent: int = 0) -> None:
        """
        Print an expression node using post-order traversal.

        :param expr: The expression to print.
        :type expr: Expression
        :param indent: Current indentation level.
        :type indent: int
        """

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit left sub-expression.
        if expr.left:
            ASTPrinter.print_expression(expr.left, indent + 1)

        # Visit right sub-expression.
        if expr.right:
            ASTPrinter.print_expression(expr.right, indent + 1)

        # Print this expression node (post-order: after children).
        val = f' value={expr.value}' if expr.value else ''
        name = f' name={expr.name}' if expr.name else ''
        print(f'{prefix}[Expression] kind={expr.kind}{name}{val}')

    # * method: print_type (static)
    @staticmethod
    def print_type(type_node: Type, indent: int = 0) -> None:
        """
        Print a type node using post-order traversal.

        :param type_node: The type to print.
        :type type_node: Type
        :param indent: Current indentation level.
        :type indent: int
        """

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit subtype.
        if type_node.subtype:
            ASTPrinter.print_type(type_node.subtype, indent + 1)

        # Visit return_type.
        if type_node.return_type:
            ASTPrinter.print_type(type_node.return_type, indent + 1)

        # Visit params.
        if type_node.params:
            ASTPrinter.print_param_list(type_node.params, indent + 1)

        # Print this type node (post-order: after children).
        name = f' name={type_node.name}' if type_node.name else ''
        print(f'{prefix}[Type] kind={type_node.kind}{name}')

    # * method: print_param_list (static)
    @staticmethod
    def print_param_list(param: ParamList, indent: int = 0) -> None:
        """
        Print a parameter list node using post-order traversal.

        :param param: The first parameter in the linked list.
        :type param: ParamList
        :param indent: Current indentation level.
        :type indent: int
        """

        prefix = '  ' * indent

        # Post-order: visit children first.

        # Visit default value expression.
        if param.default:
            ASTPrinter.print_expression(param.default, indent + 1)

        # Visit type.
        if param.type:
            ASTPrinter.print_type(param.type, indent + 1)

        # Print this param node (post-order: after children).
        req = ' required' if param.required else ' optional'
        print(f'{prefix}[Param] name={param.name}{req}')

        # Follow the .next chain.
        if param.next:
            ASTPrinter.print_param_list(param.next, indent)

    # * method: print_symbol_table (static)
    @staticmethod
    def print_symbol_table(symbol_table: Dict[str, Any]) -> None:
        """
        Print the symbol table in a readable hierarchical format.

        :param symbol_table: The symbol table dict from SymbolTableBuilder.build().
        :type symbol_table: Dict[str, Any]
        """

        module_name = symbol_table.get('module_name', 'unknown')
        scopes = symbol_table.get('scopes', {})

        print(f'=== Symbol Table: {module_name} ===')
        print()

        for scope_path, scope_data in scopes.items():
            kind = scope_data.get('kind', '?')
            parent = scope_data.get('parent_path', None)
            parent_str = f' (parent: {parent})' if parent else ''

            print(f'Scope: {scope_path} [{kind}]{parent_str}')

            # Print symbols.
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

            # Print children.
            children = scope_data.get('children', {})
            if children:
                print(f'  Children:')
                for child_name, child_path in children.items():
                    print(f'    {child_name} -> {child_path}')

            print()
