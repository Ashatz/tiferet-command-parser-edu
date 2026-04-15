"""IR Generator and Docstring Parser Utilities"""

# *** imports

# ** core
import re
from typing import Any, Dict, List, Optional

# ** app
from ..domain.ast import (
    TypeKind,
    ExprKind,
    StatementKind,
    Declaration,
    Statement,
    Expression,
    ParamList,
)
from ..domain.ir import (
    IREventGroup,
    IRImportGroup,
    IRImportGroups,
    IRImport,
    IRAttribute,
    IRAttributes,
    IRAssign,
    IRInjection,
    IRInjections,
    IRParam,
    IRParams,
    IRReturn,
    IRReturns,
    IRComment,
    IRComments,
    IRStatement,
    IRStatements,
    IRSnippet,
    IRSnippets,
    IRExecute,
    IRMethod,
    IRMethods,
    IREvent,
    IREvents,
)
from ..interfaces.ir import IRService

# *** utils

# ** util: docstring_parser
class DocstringParser:
    '''
    Static utility for extracting structured information from RST-formatted docstrings.
    '''

    # * method: strip (static)
    @staticmethod
    def strip(raw: str) -> str:
        '''
        Remove triple quotes and surrounding whitespace from a raw docstring.

        :param raw: The raw docstring as it appears in the AST (e.g. \\'\\'\\'text\\'\\'\\').
        :type raw: str
        :return: The cleaned docstring text.
        :rtype: str
        '''

        # Return empty string for missing input.
        if not raw:
            return ''

        # Strip surrounding whitespace and remove triple-quote delimiters.
        s = raw.strip()
        for q in ('"""', "'''"):
            if s.startswith(q):
                s = s[3:]
            if s.endswith(q):
                s = s[:-3]
        return s.strip()

    # * method: parse_param_descriptions (static)
    @staticmethod
    def parse_param_descriptions(raw: str) -> Dict[str, str]:
        '''
        Extract RST-style :param name: description entries from a docstring.

        :param raw: The raw docstring string.
        :type raw: str
        :return: Dict mapping parameter name to description string.
        :rtype: Dict[str, str]
        '''

        # Strip the docstring and search for :param name: entries.
        text = DocstringParser.strip(raw)
        result = {}
        for match in re.finditer(
            r':param\s+(\w+):\s*(.+?)(?=\n\s*:|$)',
            text,
            re.DOTALL,
        ):
            name = match.group(1)
            desc = ' '.join(match.group(2).split())
            result[name] = desc
        return result

    # * method: parse_return_descriptions (static)
    @staticmethod
    def parse_return_descriptions(raw: str) -> List[str]:
        '''
        Extract RST-style :return: / :returns: description entries from a docstring.

        :param raw: The raw docstring string.
        :type raw: str
        :return: List of return description strings.
        :rtype: List[str]
        '''

        # Strip the docstring and search for :return: or :returns: entries.
        text = DocstringParser.strip(raw)
        descriptions = []
        for match in re.finditer(
            r':returns?:\s*(.+?)(?=\n\s*:|$)',
            text,
            re.DOTALL,
        ):
            desc = ' '.join(match.group(1).split())
            descriptions.append(desc)
        return descriptions


# ** util: ir_generator
class IRGenerator(IRService):
    '''
    Concrete IR generation utility that walks a DeclarationAggregate AST
    and produces an IREventGroup conforming to the keter IR schema.
    '''

    # * method: generate
    def generate(self,
            ast: Any,
            symbol_table: Optional[Dict[str, Any]] = None,
        ) -> IREventGroup:
        '''
        Entry point: walk the module declaration and produce an IREventGroup.

        :param ast: The module-level DeclarationAggregate from PerformSyntacticAnalysis.
        :type ast: Any
        :param symbol_table: Optional symbol table dict from PerformSemanticAnalysis.
        :type symbol_table: Dict[str, Any] | None
        :return: The root IR node.
        :rtype: IREventGroup
        '''

        # Extract module name and description from the AST root.
        module_name = ast.name or 'unknown'
        description = DocstringParser.strip(ast.doc_string) if ast.doc_string else ''

        # Initialize empty import groups and events collections.
        import_groups = IRImportGroups()
        events = IREvents()

        # Walk the top-level statement chain, dispatching by artifact group name.
        if ast.code:
            current = ast.code
            while current:
                if current.kind == StatementKind.ARTIFACT and current.decl:
                    if current.decl.name == 'imports' and current.body:
                        self.build_import_groups(current.body, import_groups)
                    elif current.body:
                        self.build_events(current.body, events)
                current = current.next

        # Return the assembled IR event group.
        return IREventGroup(
            name=module_name,
            description=description,
            import_groups=import_groups,
            events=events,
        )

    # * method: build_import_groups
    def build_import_groups(self,
            body_stmt: Statement,
            import_groups: IRImportGroups,
        ) -> None:
        '''
        Walk the import category chain and populate the IRImportGroups collection.

        :param body_stmt: The first statement in the imports artifact body.
        :type body_stmt: Statement
        :param import_groups: The collection to populate.
        :type import_groups: IRImportGroups
        '''

        # Walk the chain of ** import-category artifact siblings.
        current = body_stmt
        while current:
            if current.kind == StatementKind.ARTIFACT and current.decl:
                category = current.decl.name
                imports = self.collect_imports(current.body) if current.body else []
                if imports:
                    import_groups.groups.append(
                        IRImportGroup(category=category, imports=imports)
                    )
            current = current.next

    # * method: collect_imports
    def collect_imports(self, body_stmt: Statement) -> List[IRImport]:
        '''
        Collect IRImport entries from a chain of import_from statements.

        :param body_stmt: The first statement in an import category body.
        :type body_stmt: Statement
        :return: List of IRImport objects.
        :rtype: List[IRImport]
        '''

        # Walk import_from statements and collect symbol entries.
        imports = []
        current = body_stmt
        while current:
            if current.kind == StatementKind.IMPORT_FROM:
                module_path = ''
                if current.init_expr and current.init_expr.name:
                    module_path = current.init_expr.name
                for symbol in self.collect_import_names(current.expr):
                    imports.append(IRImport(module_path=module_path, symbol=symbol))
            current = current.next
        return imports

    # * method: collect_import_names
    def collect_import_names(self, expr: Optional[Expression]) -> List[str]:
        '''
        Recursively collect imported symbol names from an import expression tree.

        :param expr: The import expression node.
        :type expr: Expression | None
        :return: List of symbol name strings.
        :rtype: List[str]
        '''

        # Return empty list for missing expression.
        if not expr:
            return []

        # Simple name import.
        if expr.kind == ExprKind.NAME:
            return [expr.name] if expr.name else []

        # Multi-symbol import — recurse both sides.
        if expr.kind == ExprKind.IMPORT_MULTI:
            return (
                self.collect_import_names(expr.left)
                + self.collect_import_names(expr.right)
            )

        # Aliased import — use the alias (right side).
        if expr.kind == ExprKind.IMPORT_AS:
            if expr.right and expr.right.name:
                return [expr.right.name]
            return []

        return []

    # * method: build_events
    def build_events(self,
            body_stmt: Statement,
            events: IREvents,
        ) -> None:
        '''
        Walk the event artifact chain and populate the IREvents collection.

        :param body_stmt: The first statement in the events artifact body.
        :type body_stmt: Statement
        :param events: The collection to populate.
        :type events: IREvents
        '''

        # Walk the chain of ** event artifact siblings.
        current = body_stmt
        while current:
            if current.kind == StatementKind.ARTIFACT and current.body:
                event = self.extract_event_from_body(current.body)
                if event:
                    events.events.append(event)
            current = current.next

    # * method: extract_event_from_body
    def extract_event_from_body(self, body_stmt: Statement) -> Optional[IREvent]:
        '''
        Extract an IREvent from a decl statement containing a class declaration.

        :param body_stmt: The statement wrapping the class declaration.
        :type body_stmt: Statement
        :return: The constructed IREvent, or None if the statement is not a class decl.
        :rtype: IREvent | None
        '''

        # The body must be a decl statement with a class declaration.
        if body_stmt.kind != StatementKind.DECL or not body_stmt.decl:
            return None

        # Extract class name and docstring, then delegate to build_event.
        class_decl = body_stmt.decl
        doc_string = DocstringParser.strip(class_decl.doc_string) if class_decl.doc_string else ''
        return self.build_event(class_decl, doc_string)

    # * method: build_event
    def build_event(self, class_decl: Declaration, doc_string: str) -> IREvent:
        '''
        Dispatch ARTIFACT_MEMBER nodes by role and assemble an IREvent.

        :param class_decl: The class Declaration node.
        :type class_decl: Declaration
        :param doc_string: The stripped class docstring.
        :type doc_string: str
        :return: The assembled IREvent.
        :rtype: IREvent
        '''

        # Initialize empty member collections.
        attributes = IRAttributes()
        injections = IRInjections()
        execute = IRExecute()
        methods = IRMethods()

        # Walk the ARTIFACT_MEMBER chain if the class has a body.
        if class_decl.code and class_decl.code.kind == StatementKind.DECL:
            first_member = class_decl.code.decl
            if first_member:
                self.process_member_chain(
                    first_member, attributes, injections, execute, methods
                )

        # Return the assembled event.
        return IREvent(
            class_name=class_decl.name,
            doc_string=doc_string,
            attributes=attributes,
            injections=injections,
            execute=execute,
            methods=methods,
        )

    # * method: process_member_chain
    def process_member_chain(self,
            member_decl: Declaration,
            attributes: IRAttributes,
            injections: IRInjections,
            execute: IRExecute,
            methods: IRMethods,
        ) -> None:
        '''
        Walk the ARTIFACT_MEMBER declaration chain, dispatching each member by role.

        :param member_decl: The first ARTIFACT_MEMBER declaration.
        :type member_decl: Declaration
        :param attributes: The attributes collection to populate.
        :type attributes: IRAttributes
        :param injections: The injections collection to populate.
        :type injections: IRInjections
        :param execute: The execute node to populate.
        :type execute: IRExecute
        :param methods: The methods collection to populate.
        :type methods: IRMethods
        '''

        # Iterate ARTIFACT_MEMBER declarations via the .next chain.
        current = member_decl
        while current:

            # Only process ARTIFACT_MEMBER declarations.
            is_artifact_member = (
                current.type
                and current.type.kind == TypeKind.ARTIFACT
                and (current.metadata or {}).get('type') == 'ARTIFACT_MEMBER'
            )
            if not is_artifact_member:
                break

            # Dispatch by member role name.
            role = current.name
            if role == 'attribute':
                self.build_attributes(current, attributes)
            elif role == 'init':
                self.build_injections(current, injections)
            elif role == 'method' and current.code:
                inner = current.code
                if inner.kind == StatementKind.DECL and inner.decl:
                    if inner.decl.name == 'execute':
                        self.build_execute(current, execute)
                    else:
                        method = self.build_method(current)
                        if method:
                            methods.methods.append(method)

            current = current.next

    # * method: build_attributes
    def build_attributes(self,
            member_decl: Declaration,
            attributes: IRAttributes,
        ) -> None:
        '''
        Extract an IRAttribute from an attribute ARTIFACT_MEMBER declaration.

        :param member_decl: The attribute member declaration.
        :type member_decl: Declaration
        :param attributes: The collection to append to.
        :type attributes: IRAttributes
        '''

        # The member code must contain the actual attribute declaration.
        if not member_decl.code or member_decl.code.kind != StatementKind.DECL:
            return
        attr_decl = member_decl.code.decl
        if not attr_decl:
            return

        # Derive the type name and append the attribute.
        type_name = self.get_type_name(attr_decl.type)
        attributes.attributes.append(IRAttribute(name=attr_decl.name, type=type_name))

    # * method: build_injections
    def build_injections(self,
            member_decl: Declaration,
            injections: IRInjections,
        ) -> None:
        '''
        Extract IRInjection entries from an init ARTIFACT_MEMBER declaration.

        :param member_decl: The init member declaration.
        :type member_decl: Declaration
        :param injections: The collection to append to.
        :type injections: IRInjections
        '''

        # The inner code must contain the __init__ function declaration.
        if not member_decl.code or member_decl.code.kind != StatementKind.DECL:
            return
        init_decl = member_decl.code.decl
        if not init_decl or not init_decl.type or not init_decl.type.params:
            return

        # Extract param descriptions from the init docstring.
        doc_string = init_decl.doc_string or ''
        param_descs = DocstringParser.parse_param_descriptions(doc_string)

        # Walk the parameter chain (skip self) and build an Injection per param.
        param = init_decl.type.params
        while param:
            if param.name != 'self':
                type_name = self.get_type_name(param.type)
                assign = IRAssign(target=param.name, source=param.name)
                injections.injections.append(
                    IRInjection(
                        name=param.name,
                        type=type_name,
                        description=param_descs.get(param.name, ''),
                        assign=assign,
                    )
                )
            param = param.next

    # * method: build_execute
    def build_execute(self,
            member_decl: Declaration,
            execute: IRExecute,
        ) -> None:
        '''
        Populate an IRExecute node from a method ARTIFACT_MEMBER named execute.

        :param member_decl: The method member declaration.
        :type member_decl: Declaration
        :param execute: The IRExecute node to populate in place.
        :type execute: IRExecute
        '''

        # Extract the inner execute function declaration.
        if not member_decl.code or member_decl.code.kind != StatementKind.DECL:
            return
        method_decl = member_decl.code.decl
        if not method_decl:
            return

        # Get docstring, params, returns, and snippets.
        doc_string = method_decl.doc_string or ''
        return_type = self.get_return_type_name(method_decl.type)

        execute.name = 'execute'
        execute.params = self.build_params(
            method_decl.type.params if method_decl.type else None,
            doc_string,
        )
        execute.returns = self.build_returns(return_type, doc_string)
        execute.snippets = self.build_snippets(method_decl.code) if method_decl.code else IRSnippets()

    # * method: build_method
    def build_method(self, member_decl: Declaration) -> Optional[IRMethod]:
        '''
        Build an IRMethod from a non-execute method ARTIFACT_MEMBER declaration.

        :param member_decl: The method member declaration.
        :type member_decl: Declaration
        :return: The constructed IRMethod, or None if extraction fails.
        :rtype: IRMethod | None
        '''

        # Extract the inner function declaration.
        if not member_decl.code or member_decl.code.kind != StatementKind.DECL:
            return None
        method_decl = member_decl.code.decl
        if not method_decl:
            return None

        # Get docstring, params, returns, and snippets.
        doc_string = method_decl.doc_string or ''
        return_type = self.get_return_type_name(method_decl.type)

        return IRMethod(
            name=method_decl.name,
            params=self.build_params(
                method_decl.type.params if method_decl.type else None,
                doc_string,
            ),
            returns=self.build_returns(return_type, doc_string),
            snippets=self.build_snippets(method_decl.code) if method_decl.code else IRSnippets(),
        )

    # * method: build_params
    def build_params(self,
            params_node: Optional[ParamList],
            doc_string: str = '',
        ) -> IRParams:
        '''
        Walk a ParamList linked list (skipping self) and build an IRParams collection.

        :param params_node: The first node in the parameter linked list.
        :type params_node: ParamList | None
        :param doc_string: The raw method docstring for description extraction.
        :type doc_string: str
        :return: The assembled IRParams.
        :rtype: IRParams
        '''

        # Parse parameter descriptions from the docstring up front.
        params = IRParams()
        if not params_node:
            return params

        param_descs = DocstringParser.parse_param_descriptions(doc_string)

        # Walk the linked list, skipping self.
        current = params_node
        while current:
            if current.name != 'self':
                type_name = self.get_type_name(current.type)

                # Encode default value if present.
                default = ''
                if current.default:
                    default = self.encode_expr(current.default)

                params.params.append(IRParam(
                    name=current.name,
                    type=type_name,
                    required=current.required,
                    default=default,
                    description=param_descs.get(current.name, ''),
                ))
            current = current.next

        return params

    # * method: build_returns
    def build_returns(self,
            return_type_name: str,
            doc_string: str = '',
        ) -> IRReturns:
        '''
        Build an IRReturns collection from the return type kind and docstring.

        :param return_type_name: The return type name string (e.g. "str", "Error").
        :type return_type_name: str
        :param doc_string: The raw method docstring for description extraction.
        :type doc_string: str
        :return: The assembled IRReturns.
        :rtype: IRReturns
        '''

        # Parse return descriptions from the docstring.
        returns = IRReturns()
        descriptions = DocstringParser.parse_return_descriptions(doc_string)

        # Produce one Return per description entry, or a bare entry if none found.
        if descriptions:
            for desc in descriptions:
                returns.returns.append(
                    IRReturn(type_name=return_type_name, description=desc)
                )
        else:
            returns.returns.append(
                IRReturn(type_name=return_type_name, description='')
            )
        return returns

    # * method: build_snippets
    def build_snippets(self, code_stmt: Statement) -> IRSnippets:
        '''
        Walk a method body statement chain and build an IRSnippets collection.

        :param code_stmt: The first statement in the method body.
        :type code_stmt: Statement
        :return: The assembled IRSnippets.
        :rtype: IRSnippets
        '''

        # Walk the top-level statement chain for snippet nodes.
        snippets = IRSnippets()
        current = code_stmt
        while current:
            if current.kind == StatementKind.SNIPPET:
                snippet = self.build_snippet(current)
                if snippet:
                    snippets.snippets.append(snippet)
            current = current.next
        return snippets

    # * method: build_snippet
    def build_snippet(self, snippet_stmt: Statement) -> Optional[IRSnippet]:
        '''
        Build an IRSnippet from a snippet statement by walking its body chain.

        :param snippet_stmt: The snippet statement.
        :type snippet_stmt: Statement
        :return: The assembled IRSnippet, or None if the body is empty.
        :rtype: IRSnippet | None
        '''

        # Walk the snippet body, separating comments from executable statements.
        comments = IRComments()
        statements = IRStatements()

        current = snippet_stmt.body
        while current:
            if current.kind == StatementKind.COMMENT:
                text = ''
                if current.expr and current.expr.value:
                    text = current.expr.value.lstrip('#').strip()
                comments.comments.append(IRComment(text=text))
            elif current.kind in (
                StatementKind.EXPR,
                StatementKind.RETURN,
                StatementKind.IF_ELSE,
            ):
                expr_str = self.encode_stmt(current)
                if expr_str:
                    statements.statements.append(IRStatement(expr=expr_str))
            current = current.next

        return IRSnippet(comments=comments, statements=statements)

    # * method: encode_stmt
    def encode_stmt(self, stmt: Statement) -> str:
        '''
        Encode a statement node as a string expression.

        :param stmt: The statement to encode.
        :type stmt: Statement
        :return: String-encoded expression.
        :rtype: str
        '''

        # Encode return statement.
        if stmt.kind == StatementKind.RETURN:
            inner = self.encode_expr(stmt.expr) if stmt.expr else ''
            return f'Return({inner})'

        # Encode expression statement.
        if stmt.kind == StatementKind.EXPR:
            return self.encode_expr(stmt.expr) if stmt.expr else ''

        # Encode if/else statement.
        if stmt.kind == StatementKind.IF_ELSE:
            cond = self.encode_expr(stmt.expr) if stmt.expr else ''
            body = self.encode_stmt(stmt.body) if stmt.body else ''
            return f'If({cond}, {body})'

        return ''

    # * method: encode_expr
    def encode_expr(self, expr: Optional[Expression]) -> str:
        '''
        Recursively encode an expression node as a string.

        :param expr: The expression node to encode.
        :type expr: Expression | None
        :return: String-encoded expression.
        :rtype: str
        '''

        # Return empty string for missing expression.
        if not expr:
            return ''

        kind = expr.kind

        # Name reference — check for exponentiation hack (kind=name, value="**").
        if kind == ExprKind.NAME:
            if expr.value == '**' and expr.left is not None:
                left = self.encode_expr(expr.left)
                right = self.encode_expr(expr.right)
                return f'Exp({left}, {right})'
            return expr.name or expr.value or ''

        # Literal values.
        if kind in (ExprKind.STR_VAL, ExprKind.INT_VAL, ExprKind.NUM_VAL, ExprKind.BOOL_VAL):
            return expr.value or ''

        # Assignment expression.
        if kind == ExprKind.ASSIGN:
            left = self.encode_expr(expr.left)
            right = self.encode_expr(expr.right)
            return f'Assign({left}, {right})'

        # Arithmetic operators.
        if kind == ExprKind.ADD:
            return f'Add({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'
        if kind == ExprKind.SUB:
            return f'Sub({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'
        if kind == ExprKind.MUL:
            return f'Mul({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'
        if kind == ExprKind.DIV:
            return f'Div({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'
        if kind == ExprKind.MOD:
            return f'Mod({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'
        if kind == ExprKind.EXP:
            return f'Exp({self.encode_expr(expr.left)}, {self.encode_expr(expr.right)})'

        # Comment expression — return the text value.
        if kind == ExprKind.COMMENT:
            return expr.value or ''

        return ''

    # * method: get_type_name
    def get_type_name(self, type_obj: Any) -> str:
        '''
        Extract a type name string from an AST Type node.

        :param type_obj: The AST Type node.
        :type type_obj: Any
        :return: The type name string (e.g. "str", "ErrorService").
        :rtype: str
        '''

        # Return unknown for missing type.
        if not type_obj:
            return 'unknown'

        kind = type_obj.kind

        # Class-typed nodes carry their name explicitly.
        if kind == TypeKind.CLASS:
            return type_obj.name or 'unknown'

        # All other kinds use the enum value string directly.
        return kind.value

    # * method: get_return_type_name
    def get_return_type_name(self, type_obj: Any) -> str:
        '''
        Extract the return type name string from a function AST Type node.

        :param type_obj: The function AST Type node.
        :type type_obj: Any
        :return: The return type name string.
        :rtype: str
        '''

        # Default to unknown for missing or non-func types.
        if not type_obj or not type_obj.return_type:
            return 'unknown'
        return self.get_type_name(type_obj.return_type)
