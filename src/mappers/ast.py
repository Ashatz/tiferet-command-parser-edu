"""Tiferet Compiler AST Mapper Objects"""

# *** imports

# ** core
from typing import Optional

# ** infra
from pydantic import Field

# ** app
from os import name

from dependencies import value

from src.domain.ast import ParamList

from ..domain import TypeKind, ExprKind, StatementKind, Type, ParamList, Declaration, Expression, Statement

# *** mappers

# ** mapper: type_aggregate
class TypeAggregate(Type):
    """Aggregate representing a type in the Tiferet AST, such as a class or method type."""

    # * method: set_return_type
    def set_return_type(self, return_type: 'TypeAggregate'):
        """
        Set the return type of this type aggregate (e.g., for function types).

        :param return_type: The TypeAggregate to set as the return type of this type.
        :type return_type: TypeAggregate
        """

        # If the current return type is set, set the return type of the existing return type to the new return type (creating a chain). Otherwise, set the return type directly.
        if self.return_type:
            self.return_type.set_return_type(return_type)
        else:
            self.return_type = return_type


    # * method: set_subtype
    def set_subtype(self, subtype: 'TypeAggregate'):
        """
        Set the subtype of this type aggregate (e.g., for class types, the subtype can represent subclasses).

        :param subtype: The TypeAggregate to set as the subtype of this type.
        :type subtype: TypeAggregate
        """

        # If the current subtype is set, set the subtype of the existing subtype to the new subtype (creating a chain). Otherwise, set the subtype directly.
        if self.subtype:
            self.subtype.set_subtype(subtype)
        else:
            self.subtype = subtype

    # * method: new
    @staticmethod
    def new(kind: TypeKind, subtype: Optional['TypeAggregate'] = None, params: Optional['ParamList'] = None) -> 'TypeAggregate':
        """Create a new TypeAggregate instance with the given kind, subtype, and parameters.

        :param kind: The kind of the type (e.g., "class", "function", "int", "str").
        :type kind: TypeKind
        :param subtype: Optional subtype of the type (e.g., element type for list types).
        :type subtype: TypeAggregate | None
        :param params: Optional list of parameters for function types.
        :type params: ParamList | None
        :return: A new TypeAggregate instance with the specified kind, subtype, and parameters.
        :rtype: TypeAggregate
        """
        
        return TypeAggregate(
            kind=kind,
            subtype=subtype,
            params=params
        )

    # * method: new_null_type
    @staticmethod
    def new_null_type() -> 'TypeAggregate':
        """
        Create a new TypeAggregate representing a null type (e.g., for untyped declarations).

        :return: A new TypeAggregate instance representing the null type.
        :rtype: TypeAggregate
        """

        return TypeAggregate(
            kind=TypeKind.NONE
        )

    # * method: new_unknown_type
    @staticmethod
    def new_unknown_type() -> 'TypeAggregate':
        """
        Create a new TypeAggregate representing an unknown type (e.g., for cases where the type cannot be determined).

        :return: A new TypeAggregate instance representing the unknown type.
        :rtype: TypeAggregate
        """

        return TypeAggregate(
            kind=TypeKind.UNKNOWN
        )
    
    # * method: new_func_type
    @staticmethod
    def new_func_type(params: Optional['ParamList'] = None, return_type: Optional['TypeAggregate'] = None) -> 'TypeAggregate':
        """
        Create a new TypeAggregate representing a function type.

        :param params: Optional list of parameters for the function type.
        :type params: ParamList | None
        :param return_type: Optional return type of the function type.
        :type return_type: TypeAggregate | None
        :return: A new TypeAggregate instance representing the function type.
        :rtype: TypeAggregate
        """
        return TypeAggregate(
            kind=TypeKind.FUNC,
            params=params,
            return_type=return_type
        )

    # * method: new_artifact_type
    @staticmethod
    def new_artifact_type() -> 'TypeAggregate':
        """
        Create a new TypeAggregate representing an artifact type (e.g., class or method type).

        :return: A new TypeAggregate instance representing the artifact type.
        :rtype: TypeAggregate
        """
        
        return TypeAggregate(
            kind=TypeKind.ARTIFACT
        )
    
    # * method: new_class_type
    @staticmethod
    def new_class_type(name: Optional[str] = None, subclasses: Optional['TypeAggregate'] = None) -> 'TypeAggregate':
        """
        Create a new TypeAggregate representing a class type.

        :param name: Optional name of the class type.
        :type name: str | None
        :param subclasses: Optional TypeAggregate representing subclasses of this class type (for inheritance).
        :type subclasses: TypeAggregate | None
        :return: A new TypeAggregate instance representing the class type.
        :rtype: TypeAggregate
        """

        return TypeAggregate(
            kind=TypeKind.CLASS,
            name=name,
            subtype=subclasses
        )
    
# ** mapper: param_list_aggregate
class ParamListAggregate(ParamList):
    """Aggregate representing a parameter in the Tiferet AST, used for method or function declarations."""

    # * method: set_next
    def set_next(self, next_param: 'ParamListAggregate'):
        """
        Set the next parameter in the list for this parameter aggregate.

        :param next_param: The next ParamListAggregate to link to this parameter.
        :type next_param: ParamListAggregate
        """

        # If there is no next parameter yet, set it directly. Otherwise, delegate to the existing next parameter to set the new next parameter (creating a chain).
        if not self.next:
            self.next = next_param
        else:
            self.next.set_next(next_param)

    # * method: set_type
    def set_type(self, type: 'TypeAggregate'):
        """
        Set the type of this parameter aggregate.

        :param type: The TypeAggregate to set as the type of this parameter.
        :type type: TypeAggregate
        """

        self.type = type

    # * method: set_default
    def set_default(self, default: 'ExpressionAggregate'):
        """
        Set the default value of this parameter aggregate. Setting a default value also implies that the parameter is optional (i.e., not required).

        :param default: The ExpressionAggregate to set as the default value of this parameter.
        :type default: ExpressionAggregate
        """

        self.default = default
        self.required = False

    # * method: new
    @staticmethod
    def new(name: str, type: Optional[TypeAggregate] = None, required: bool = True, default: Optional['ExpressionAggregate'] = None) -> 'ParamListAggregate':
        """
        Create a new ParamListAggregate instance with the given name, type, required flag, and default value.

        :param name: The name of the parameter.
        :type name: str
        :param type: Optional TypeAggregate representing the type of the parameter.
        :type type: TypeAggregate | None
        :param required: Boolean flag indicating whether the parameter is required (default is True).
        :type required: bool
        :param default: Optional ExpressionAggregate representing the default value of the parameter (if it is optional).
        :type default: ExpressionAggregate | None
        :return: A new ParamListAggregate instance with the specified attributes.
        :rtype: ParamListAggregate
        """

        return ParamListAggregate(
            name=name,
            type=type,
            required=required,
            default=default
        )
    
    # * method: new_args_param
    @staticmethod
    def new_args_param(name: str = 'args') -> 'ParamListAggregate':
        """
        Create a new ParamListAggregate representing a variable-length argument parameter (e.g., *args).

        :param name: The name of the variable-length argument parameter (default is 'args').
        :type name: str
        :return: A new ParamListAggregate instance representing the variable-length argument parameter.
        :rtype: ParamListAggregate
        """

        return ParamListAggregate(
            name=name,
            type=TypeAggregate.new(
                kind=TypeKind.LIST,
                subtype=TypeAggregate.new_unknown_type()
            )
        )
    
    # * method: new_kwargs_param
    @staticmethod
    def new_kwargs_param(name: str = 'kwargs') -> 'ParamListAggregate':
        """
        Create a new ParamListAggregate representing a variable-length keyword argument parameter (e.g., **kwargs).

        :param name: The name of the variable-length keyword argument parameter (default is 'kwargs').
        :type name: str
        :return: A new ParamListAggregate instance representing the variable-length keyword argument parameter.
        :rtype: ParamListAggregate
        """

        return ParamListAggregate(
            name=name,
            type=TypeAggregate.new(
                kind=TypeKind.DICT,
                subtype=TypeAggregate.new_unknown_type()
            )
        )

# ** mapper: expression_aggregate
class ExpressionAggregate(Expression):

    # * method: set_left
    def set_left(self, left: 'ExpressionAggregate'):
        """
        Set the left sub-expression of this expression aggregate.

        :param left: The ExpressionAggregate to set as the left sub-expression.
        :type left: ExpressionAggregate
        """

        # If there is already a left sub-expression, delegate to it to set the new left sub-expression (creating a chain). Otherwise, set the left sub-expression directly.
        if self.left:
            self.left.set_left(left)
        else:
            self.left = left

    # * method: set_right
    def set_right(self, right: 'ExpressionAggregate'):
        """
        Set the right sub-expression of this expression aggregate.

        :param right: The ExpressionAggregate to set as the right sub-expression.
        :type right: ExpressionAggregate
        """

        # If there is already a right sub-expression, delegate to it to set the new right sub-expression (creating a chain). Otherwise, set the right sub-expression directly.
        if self.right:
            self.right.set_right(right)
        else:
            self.right = right

    # * method: new_name_expr
    @staticmethod
    def new_name_expr(name: Optional[str], left: Optional['ExpressionAggregate'] = None, right: Optional['ExpressionAggregate'] = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a named expression (e.g., variable reference).
        :param name: The name of the expression (e.g., variable name).
        :type name: str
        :return: A new ExpressionAggregate instance representing the named expression.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.NAME,
            name=name,
            left=left,
            right=right,
            lineno=lineno,
            col=col,
        )

    # * method: new_literal_expr
    @staticmethod
    def new_name_or_literal_expr(value: str, lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a literal expression (e.g., string or numeric literal).
        :param value: The value of the literal expression.
        :type value: str
        :return: A new ExpressionAggregate instance representing the literal expression.
        :rtype: ExpressionAggregate
        """

        # Determine the kind of literal expression based on the type of the value. If the value is a string, check if it is a boolean literal ("True" or "False") and create a BOOL_VAL expression if so; otherwise, create a STR_VAL expression. If the value is an integer or float, create a NUM_VAL expression. For any other type of value, create a NAME expression with the string representation of the value as the name.
        if isinstance(value, str):
            if value in ('True', 'False'):
                return ExpressionAggregate(
                    kind=ExprKind.BOOL_VAL,
                    value=value,
                    lineno=lineno,
                    col=col,
                )
            
            # For string literals, create a STR_VAL expression with the value of the literal as the value of the expression.
            return ExpressionAggregate(
                kind=ExprKind.STR_VAL,
                value=value,
                lineno=lineno,
                col=col,
            )
        
        # For numeric literals, create a NUM_VAL expression with the string representation of the value as the value of the expression.
        elif isinstance(value, (int, float)):
            return ExpressionAggregate(
                kind=ExprKind.NUM_VAL,
                value=str(value),
                lineno=lineno,
                col=col,
            )
        
        # For any other type of value, return a NAME expression with the string representation of the value as the name.
        else:
            return ExpressionAggregate.new_name_expr(name=str(value), lineno=lineno, col=col)
        
    # * method: new_args_list_expr
    @staticmethod
    def new_args_list_expr(args_list: 'ExpressionAggregate', arg: Optional['ExpressionAggregate'] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a list of arguments for a call expression.
        :param args_list: The existing ExpressionAggregate representing the list of arguments (if any).
        :type args_list: ExpressionAggregate
        :param arg: The new ExpressionAggregate representing a single argument to add to the list.
        :type arg: ExpressionAggregate | None
        :return: A new ExpressionAggregate instance representing the updated list of arguments.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.ARGS_LIST,
            left=args_list,
            right=arg
        )

    # * method: new_import_expr_as
    @staticmethod
    def new_import_expr_as(impt_expr: 'ExpressionAggregate', alias: str) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing an import expression with an alias.
        :param impt_expr: The expression representing the imported entity (e.g., module or object name).
        :type impt_expr: ExpressionAggregate
        :param alias: The alias for the imported entity.
        :type alias: str
        :return: A new ExpressionAggregate instance representing the import expression with alias.
        :rtype: ExpressionAggregate
        """

        # Create named expression for the alias.
        alias_expr = ExpressionAggregate.new_name_expr(alias)

        return ExpressionAggregate(
            kind=ExprKind.IMPORT_AS,
            left=impt_expr,
            right=alias_expr
        )

    # * method: new_import_expr_multi
    @staticmethod
    def new_import_expr_multi(existing_expr: 'ExpressionAggregate', new_name: str) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing multiple imports in a single statement.
        :param existing_expr: The existing import expression to which the new name will be added.
        :type existing_expr: ExpressionAggregate
        :param new_name: The name of the additional entity being imported.
        :type new_name: str
        :return: A new ExpressionAggregate instance representing the combined import expression.
        :rtype: ExpressionAggregate
        """

        # Create named expression for the new import name.
        new_name_expr = ExpressionAggregate.new_name_expr(new_name)

        return ExpressionAggregate(
            kind=ExprKind.IMPORT_MULTI,
            left=existing_expr,
            right=new_name_expr
        )
    
    # * method: new__call_expr
    @staticmethod
    def new_call_expr(caller: 'ExpressionAggregate', arguments: Optional['ExpressionAggregate'] = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a call expression.
        :param caller: The expression representing the caller.
        :type caller: ExpressionAggregate
        :param arguments: The expression representing the call arguments (optional).
        :type arguments: ExpressionAggregate | None
        :return: A new ExpressionAggregate instance representing the call expression.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.CALL,
            left=caller,
            right=arguments,
            lineno=lineno,
            col=col,
        )

    # * method: new_assign_expr
    @staticmethod
    def new_assign_expr(target: 'ExpressionAggregate', value: 'ExpressionAggregate', lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing an assignment expression.
        :param target: The name of the variable being assigned to.
        :type target: ExpressionAggregate
        :param value: The expression representing the value being assigned.
        :type value: ExpressionAggregate
        :return: A new ExpressionAggregate instance representing the assignment expression.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.ASSIGN,
            left=target,
            right=value,
            lineno=lineno,
            col=col,
        )
    
    # * method: new_operator_expr
    @staticmethod
    def new_operator_expr(operator: str, left: 'ExpressionAggregate', right: 'ExpressionAggregate', lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing an operator expression.

        :param operator: The operator symbol.
        :type operator: str
        :param left: The left operand expression.
        :type left: ExpressionAggregate
        :param right: The right operand expression.
        :type right: ExpressionAggregate
        :return: A new ExpressionAggregate instance representing the operator expression.
        :rtype: ExpressionAggregate
        """

        # Map the operator symbol to the corresponding expression kind. For example, '+' maps to an ADD expression, '-' maps to a SUB expression, etc. If the operator is not recognized as a valid operator, default to creating a NAME expression with the operator symbol as the name.
        if operator == '+':
            kind = ExprKind.ADD
        elif operator == '-':
            kind = ExprKind.SUB
        elif operator == '*':
            kind = ExprKind.MUL
        elif operator == '/':
            kind = ExprKind.DIV
        elif operator == '%':
            kind = ExprKind.MOD
        elif operator == '==':
            kind = ExprKind.EQ
        elif operator == '!=':
            kind = ExprKind.NEQ
        elif operator == '<':
            kind = ExprKind.LT
        elif operator == '<=':
            kind = ExprKind.LTE
        elif operator == '>':
            kind = ExprKind.GT
        elif operator == '>=':
            kind = ExprKind.GTE
        elif operator == '**':
            kind = ExprKind.EXP
        elif operator == '<<':
            kind = ExprKind.SHL
        elif operator == '>>':
            kind = ExprKind.SHR
        else:
            kind = ExprKind.NAME

        return ExpressionAggregate(
            kind=kind,
            value=operator,
            left=left,
            right=right,
            lineno=lineno,
            col=col,
        )

    # * method: new_comment_expr
    @staticmethod
    def new_comment_expr(comment_text: str, lineno: Optional[int] = None, col: Optional[int] = None) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a comment expression.

        :param comment_text: The text of the comment.
        :type comment_text: str
        :return: A new ExpressionAggregate instance representing the comment expression.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.COMMENT,
            value=comment_text,
            lineno=lineno,
            col=col,
        )

# ** mapper: declaration_aggregate
class DeclarationAggregate(Declaration):
    """Aggregate representing a declaration in the Tiferet AST, such as a class or method declaration."""

    # * method: set_name
    def set_name(self, name: str):
        """
        Set the name of this declaration aggregate.

        :param name: The name to set for this declaration.
        :type name: str
        """

        self.name = name

    # * method: set_next
    def set_next(self, next_decl: 'DeclarationAggregate'):
        """
        Set the next declaration in the chain for this declaration aggregate.

        :param next_decl: The next DeclarationAggregate to link to this declaration.
        :type next_decl: DeclarationAggregate
        """

        # If there is no next declaration yet, set it directly. Otherwise, delegate to the existing next declaration to set the new next declaration (creating a chain).
        if not self.next:
            self.next = next_decl
        else:
            self.next.set_next(next_decl)

    # * method: set_doc_string
    def set_doc_string(self, doc_string: str):
        """
        Set the docstring for this declaration aggregate.

        :param doc_string: The docstring to set for this declaration.
        :type doc_string: str
        """

        self.doc_string = doc_string

    # * method: new_module_decl
    @staticmethod
    def new_module_decl(name: str, code: Optional['StatementAggregate'] = None, doc_string: Optional[str] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing a module declaration.

        :param name: The name of the module being declared.
        :type name: str
        :param code: Optional StatementAggregate representing the code block of the module.
        :type code: StatementAggregate | None
        :param doc_string: Optional docstring for the module declaration.
        :type doc_string: str | None
        :return: A new DeclarationAggregate instance representing the module declaration.
        :rtype: DeclarationAggregate
        """

        return DeclarationAggregate(
            name=name,
            doc_string=doc_string,
            code=code
        )

    # * method: new_artifact
    @staticmethod
    def new_artifact_decl(name: str, type: str, lineno: Optional[int] = None, col: Optional[int] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing an artifact declaration (e.g., class or method declaration).

        :param name: The name of the artifact being declared (e.g., class name, method name).
        :type name: str
        :param type: The type of the artifact token being captured (e.g. ARTIFACT_SECTION, ARTIFACT_MEMBER).
        :type type: str
        :param lineno: Optional source line number.
        :type lineno: int | None
        :param col: Optional 0-based column offset.
        :type col: int | None
        :return: A new DeclarationAggregate instance representing the artifact declaration.
        :rtype: DeclarationAggregate
        """
        
        return DeclarationAggregate(
            name=name,
            type=TypeAggregate.new_artifact_type(),
            metadata={
                'type': type
            },
            lineno=lineno,
            col=col,
        )
    
    # * method: new_member_decl
    @staticmethod
    def new_member_decl(name: str, member_body: 'StatementAggregate' = None, annots: dict = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing a member declaration within an artifact (e.g., class attribute or method declaration).

        :param name: The name of the member being declared (e.g., attribute name, method name).
        :type name: str
        :param member_body: Optional statement body of the member.
        :type member_body: StatementAggregate | None
        :param annots: Optional annotations dict.
        :type annots: dict | None
        :param lineno: Optional source line number.
        :type lineno: int | None
        :param col: Optional 0-based column offset.
        :type col: int | None
        :return: A new DeclarationAggregate instance representing the member declaration.
        :rtype: DeclarationAggregate
        """

        # Create the declaration aggregate with the given name and artifact member type. If there is a member body (e.g., method body or attribute declaration), it will be added to the code field of the declaration aggregate. If there are annotations, they will be added to the metadata of the declaration aggregate.
        aggr = DeclarationAggregate(
            name=name,
            type=TypeAggregate.new_artifact_type(),
            metadata={
                'type': 'ARTIFACT_MEMBER'
            },
            lineno=lineno,
            col=col,
        )

        # If there is a member body (e.g., method body or attribute declaration), add it to the code field of the declaration aggregate.
        if member_body:
            aggr.code = member_body

        # If there are annotations, add them to the metadata of the declaration aggregate.
        if annots:
            aggr.metadata['annotations'] = annots

        return aggr

    # * method: new_func_decl
    @staticmethod
    def new_func_decl(name: str, type: Optional['ParamListAggregate'] = None, doc_string: Optional[str] = None, body: Optional['StatementAggregate'] = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing a function/method declaration.

        :param name: The name of the function being declared.
        :type name: str
        :param type: Optional TypeAggregate representing the function type.
        :type type: TypeAggregate | None
        :param doc_string: Optional docstring for the function declaration.
        :type doc_string: str | None
        :param body: Optional StatementAggregate representing the body of the function.
        :type body: StatementAggregate | None
        :param lineno: Optional source line number.
        :type lineno: int | None
        :param col: Optional 0-based column offset.
        :type col: int | None
        :return: A new DeclarationAggregate instance representing the function declaration.
        :rtype: DeclarationAggregate
        """
        
        return DeclarationAggregate(
            name=name,
            type=type,
            doc_string=doc_string,
            code=body,
            lineno=lineno,
            col=col,
        )
    # * method: new_class_decl
    @staticmethod
    def new_class_decl(name: str, subclasses: TypeAggregate, doc_string: str, members: 'StatementAggregate', lineno: Optional[int] = None, col: Optional[int] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing a class declaration.

        :param name: The name of the class being declared.
        :type name: str
        :param subclasses: The TypeAggregate representing base classes.
        :type subclasses: TypeAggregate
        :param doc_string: Optional docstring for the class.
        :type doc_string: str
        :param members: StatementAggregate representing the class body.
        :type members: StatementAggregate
        :param lineno: Optional source line number.
        :type lineno: int | None
        :param col: Optional 0-based column offset.
        :type col: int | None
        :return: A new DeclarationAggregate instance representing the class declaration.
        :rtype: DeclarationAggregate
        """

        return DeclarationAggregate(
            name=name,
            type=TypeAggregate.new_class_type(name, subclasses),
            doc_string=doc_string,
            code=members,
            lineno=lineno,
            col=col,
        )
    
    # * method: new_attr_decl
    @staticmethod
    def new_attr_decl(name: str, types: Optional[TypeAggregate] = None, value: Optional[ExpressionAggregate] = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing an attribute declaration.

        :param name: The name of the attribute being declared.
        :type name: str
        :param types: The TypeAggregate representing the type(s) of the attribute.
        :type types: TypeAggregate | None
        :param value: Optional expression value for the attribute.
        :type value: ExpressionAggregate | None
        :param lineno: Optional source line number.
        :type lineno: int | None
        :param col: Optional 0-based column offset.
        :type col: int | None
        :return: A new DeclarationAggregate instance representing the attribute declaration.
        :rtype: DeclarationAggregate
        """

        # Create the declaration aggregate with the given name. If there are types, set the type field of the declaration aggregate to a new class type with the given types as subclasses. If there is a value, set the value field of the declaration aggregate to the given value.
        agg = DeclarationAggregate(
            name=name,
            lineno=lineno,
            col=col,
        )

        # If there are types, set the type field of the declaration aggregate to a new class type with the given types as subclasses.
        if types:
            agg.type = types

        # If there is a value, set the value field of the declaration aggregate to the given value.
        if value:
            agg.value = value

        return agg

# ** mapper: statement_aggregate
class StatementAggregate(Statement):
    """Aggregate representing a statement in the Tiferet AST, such as an if-else or for statement."""

    # * attribute: next
    next: Optional['StatementAggregate'] = Field(
        None,
        description='The next statement in the chain, if applicable (e.g., for multiple statements in a block).'
    )

    # * method: set_next
    def set_next(self, next_stmt: 'StatementAggregate'):
        """
        Set the next statement in the chain for this statement aggregate.

        :param next_stmt: The next StatementAggregate to link to this statement.
        :type next_stmt: StatementAggregate
        """

        # If there is no next statement yet, set it directly. Otherwise, delegate to the existing next statement to set the new next statement (creating a chain).
        if not self.next:
            self.next = next_stmt
        else:
            self.next.set_next(next_stmt)

    # * method: new_import_stmt
    @staticmethod
    def new_import_stmt(import_expr: ExpressionAggregate, lineno: Optional[int] = None, col: Optional[int] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing an import statement.
        :param import_expr: The expression representing the import (e.g., module or object being imported).
        :type import_expr: ExpressionAggregate
        :return: A new StatementAggregate instance representing the import statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.IMPORT,
            expr=import_expr,
            lineno=lineno,
            col=col,
        )
    
    # * method: new_import_stmt_from
    @staticmethod
    def new_import_stmt_from(from_expr: ExpressionAggregate, import_expr: ExpressionAggregate, lineno: Optional[int] = None, col: Optional[int] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing an import-from statement.
        :param from_expr: The expression representing the module from which entities are being imported.
        :type from_expr: ExpressionAggregate
        :param import_expr: The expression representing the import (e.g., entity being imported).
        :type import_expr: ExpressionAggregate
        :return: A new StatementAggregate instance representing the import-from statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.IMPORT_FROM,
            init_expr=from_expr,
            expr=import_expr,
            lineno=lineno,
            col=col,
        )
    
    # * method: new_decl_stmt
    @staticmethod
    def new_decl_stmt(decl: DeclarationAggregate) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing a declaration statement.
        :param decl: The declaration aggregate representing the declaration being made.
        :type decl: DeclarationAggregate
        :return: A new StatementAggregate instance representing the declaration statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.DECL,
            decl=decl
        )
    
    # * method: new_artifact_stmt
    @staticmethod
    def new_artifact_stmt(section_header: DeclarationAggregate, section_body: 'StatementAggregate') -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing an artifact statement (e.g., class or method declaration).
        :param section_header: The header of the artifact section.
        :type section_header: DeclarationAggregate
        :param section_body: The body of the artifact section.
        :type section_body: StatementAggregate
        :return: A new StatementAggregate instance representing the artifact statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.ARTIFACT,
            decl=section_header,
            body=section_body
        )
    
    # * method: new_expr_stmt
    @staticmethod
    def new_expr_stmt(expr: ExpressionAggregate, lineno: Optional[int] = None, col: Optional[int] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing an expression statement.
        :param expr: The expression representing the statement.
        :type expr: ExpressionAggregate
        :return: A new StatementAggregate instance representing the expression statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.EXPR,
            expr=expr,
            lineno=lineno,
            col=col,
        )
    
    # * method: new_snippet_stmt
    @staticmethod
    def new_snippet_stmt(comments: Optional['StatementAggregate'] = None, code: Optional['StatementAggregate'] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing a snippet statement.
        :param comments: Optional comments associated with the snippet.
        :type comments: StatementAggregate | None
        :param code: Optional code statements associated with the snippet.
        :type code: StatementAggregate | None
        :return: A new StatementAggregate instance representing the snippet statement.
        :rtype: StatementAggregate
        """

        # If there are comments, they will be set as the body of the snippet statement. If there are code statements, they will be linked to the end of the comments (if any) or set as the body of the snippet statement if there are no comments.
        if comments:
            body = comments
            if code:
                body.set_next(code)
        else:
            body = code

        return StatementAggregate(
            kind=StatementKind.SNIPPET,
            body=body
        )

    # * method: new_comment_stmt
    @staticmethod
    def new_comment_stmt(comment: ExpressionAggregate, lineno: Optional[int] = None, col: Optional[int] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing a comment statement.
        :param comment: The expression representing the comment.
        :type comment: ExpressionAggregate
        :return: A new StatementAggregate instance representing the comment statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.COMMENT,
            expr=comment,
            lineno=lineno,
            col=col,
        )

    # * method: new_return_stmt
    @staticmethod
    def new_return_stmt(return_expr: Optional[ExpressionAggregate] = None, lineno: Optional[int] = None, col: Optional[int] = None) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing a return statement.
        :param return_expr: The expression representing the value being returned (optional).
        :type return_expr: ExpressionAggregate | None
        :return: A new StatementAggregate instance representing the return statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.RETURN,
            expr=return_expr,
            lineno=lineno,
            col=col,
        )
