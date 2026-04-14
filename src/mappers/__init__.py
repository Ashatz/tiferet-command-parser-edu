"""Tiferet Compiler Mapper Object Exports"""

# *** exports

# ** app
from .lexer import TokenAggregate, TokenAggregate as Tok
from .ast import (
    DeclarationAggregate, 
    DeclarationAggregate as Decl,
    ExpressionAggregate,
    ExpressionAggregate as Expr,
    StatementAggregate,
    StatementAggregate as Stmt,
    TypeAggregate,
    TypeAggregate as Type,
    ParamListAggregate,
    ParamListAggregate as ParamList,
    )