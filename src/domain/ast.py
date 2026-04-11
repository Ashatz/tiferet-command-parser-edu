"""Tiferet Compiler AST Domain Objects"""

# *** imports

# ** core
from enum import Enum
from typing import Optional, List, Dict, Any

# ** infra
from pydantic import BaseModel, Field

# *** enums

# ** enum: type_kind
class TypeKind(str, Enum):
    '''Enumeration of valid type kinds in the Tiferet AST.'''

    NONE = 'None'
    BOOL = 'bool'
    STR = 'str'
    INT = 'int'
    FLOAT = 'float'
    LIST = 'list'
    DICT = 'dict'
    CLASS = 'class'
    FUNC = 'func'

# ** enum: statement_kind
class StatementKind(str, Enum):
    '''Enumeration of valid statement kinds in the Tiferet AST.'''

    DECL = 'decl'
    EXPR = 'expr'
    IF_ELSE = 'if_else'
    FOR = 'for'
    WHILE = 'while'
    PRINT = 'print'
    RETURN = 'return'
    BLOCK = 'block'

# ** enum: expr_kind
class ExprKind(str, Enum):
    '''Enumeration of valid expression kinds in the Tiferet AST.'''

    ADD = 'add'
    SUB = 'sub'
    MUL = 'mul'
    DIV = 'div'
    NAME = 'name'
    INT_VAL = 'int_val'
    STR_VAL = 'str_val'
    ASSIGN = 'assign'
    CALL = 'call'

# *** objects

# ** object: type
class Type(BaseModel):
    """A type in the Tiferet AST, representing the type of a declaration (e.g., class type, method return type, constant type)"""

    # * attribute: name
    name: str = Field(
        ...,
        description='The name of the type (e.g., class name for class types, return type for methods).'
    )

    # * attribute: kind
    kind: TypeKind = Field(
        ...,
        description='The kind of the type (e.g., "class", "function", "int", "str").'
    )

    # * attribute: subtype
    subtype: Optional['Type'] = Field(
        ...,
        description='The subtype of the type, if applicable (e.g., element type for list types).'
    )

    # * attribute: params
    params: List['ParamList'] = Field(
        ...,
        description='The list of parameters for function types, if applicable.'
    )
    
# ** object: param_list
class ParamList(BaseModel):
    """A parameter in the Tiferet AST, representing a parameter in a method or function declaration"""

    # * attribute: name
    name: str = Field(
        ...,
        description='The name of the current parameter on the list.'
    )

    # * attribute: type
    type: Type = Field(
        ...,
        description='The type of the parameter currently on the list.'
    )

    # * attribute: required
    required: bool = Field(
        False,
        description='Indicates whether the parameter is required.'
    )

    # * attribute: default
    default: Optional['Expression'] = Field(
        None,
        description='The default value of the parameter, if it is optional.'
    )

    # * attribute: next
    next: Optional['ParamList'] = Field(
        None,
        description='The next parameter in the list, if applicable (for multiple parameters).'
    )


# ** object: expression
class Expression(BaseModel):
    """An expression in the Tiferet AST, representing a value, variable, operation, or function call."""

    # * attribute: kind
    kind: ExprKind = Field(
        ...,
        description='The kind of the expression (e.g., "add", "name", "call").'
    )

    # * attribute: value
    value: Optional[str] = Field(
        None,
        description='The value of the expression, if applicable (e.g., for "int_val", "str_val" expressions).'
    )

    # * attribute: name
    name: Optional[str] = Field(
        None,
        description='The name of the variable or function being referenced, if applicable (e.g., for "name" and "call" expressions).'
    )

    # * attribute: left
    left: Optional['Expression'] = Field(
        None,
        description='The left operand of the expression, if applicable (e.g., for binary operations like "add", "sub").'
    )

    # * attribute: right
    right: Optional['Expression'] = Field(
        None,
        description='The right operand of the expression, if applicable (e.g., for binary operations like "add", "sub").'
    )

# ** object: declaration
class Declaration(BaseModel):
    """A declaration in the Tiferet AST, representing a constant, class, attribute, method, or function"""

    # * attribute: name
    name: str = Field(
        ...,
        description='The name of the declaration (e.g., class name, method name, constant name).'
    )

    # * attribute: type
    type: Type = Field(
        ...,
        description='The type of the declaration (e.g., class type, method return type, constant type).'
    )

    # * metadata
    metadata: Dict[str, Any] = Field(
        ...,
        description='Additional metadata about the declaration (e.g., parameter names and types for methods, class attributes for classes).'
    )

    # * attribute: doc_string
    doc_string: Optional[str] = Field(
        None,
        description='The docstring of the declaration, if applicable (e.g., for classes and methods).'
    )

    # * attribute: value
    value: Optional['Expression'] = Field(
        None,
        description='The value of the declaration, if applicable (e.g., for constants).'
    )

    # * attribute: code
    code: Optional['Statement'] = Field(
        None,
        description='The code block of the declaration, if applicable (e.g., for classes and methods).'
    )

    # * attribute: next
    next: Optional['Declaration'] = Field(
        None,
        description='The next declaration in the chain, if applicable (e.g., for multiple declarations).'
    )

# ** object: statement
class Statement(BaseModel):
    """A statement in the Tiferet AST, representing a line of code or a block of code within a declaration."""

    # * attribute: kind
    kind: StatementKind = Field(
        ...,
        description='The kind of the statement (e.g., "decl", "expr", "if_else").'
    )

    # * attribute: decl
    decl: Optional[Declaration] = Field(
        None,
        description='The declaration associated with this statement, if applicable (e.g., for "decl" statements).'
    )

    # * attribute: inner_expr
    inner_expr: Optional[Expression] = Field(
        None,
        description='The inner expression of the statement, if applicable (e.g., for "expr" statements).'
    )

    # * attribute: expr
    expr: Optional['Expression'] = Field(
        None,
        description='The expression of the statement, if applicable (e.g., for "if_else", "for", "while" statements).'
    )

    # * attribute: next_expr
    next_expr: Optional['Expression'] = Field(
        None,
        description='The next expression in the statement, if applicable (e.g., for "if_elif_else" statements).'
    )

    # * attribute: body
    body: Optional['Statement'] = Field(
        None,
        description='The body of the statement, if applicable (e.g., for "if_else", "for", "while" statements).'
    )

    # * attribute: else_body
    else_body: Optional['Statement'] = Field(
        None,
        description='The else body of the statement, if applicable (e.g., for "if_else" statements).'
    )

    # * attribute: next
    next: Optional['Statement'] = Field(
        None,
        description='The next statement in a list of statements, if applicable (e.g., for multiple statements within a block).'
    )