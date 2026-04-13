"""Tiferet Compiler AST Mapper Objects"""

# *** imports

# ** core
from typing import Optional

# ** infra
from pydantic import Field

# ** app
from os import name

from dependencies import value

from ..domain import TypeKind, ExprKind, StatementKind, Type, Declaration, Expression, Statement

# *** mappers

# ** mapper: type_aggregate
class TypeAggregate(Type):
    """Aggregate representing a type in the Tiferet AST, such as a class or method type."""

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
    
class ExpressionAggregate(Expression):

    # * method: new_name_expr
    @staticmethod
    def new_name_expr(name: str) -> 'ExpressionAggregate':
        """
        Create a new ExpressionAggregate representing a named expression (e.g., variable reference).
        :param name: The name of the expression (e.g., variable name).
        :type name: str
        :return: A new ExpressionAggregate instance representing the named expression.
        :rtype: ExpressionAggregate
        """

        return ExpressionAggregate(
            kind=ExprKind.NAME,
            name=name
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

# ** mapper: declaration_aggregate
class DeclarationAggregate(Declaration):
    """Aggregate representing a declaration in the Tiferet AST, such as a class or method declaration."""

    # * method: new_artifact
    @staticmethod
    def new_artifact_decl(name: str, type: str) -> 'DeclarationAggregate':
        """
        Create a new DeclarationAggregate representing an artifact declaration (e.g., class or method declaration).

        :param name: The name of the artifact being declared (e.g., class name, method name).
        :type name: str
        :param type: The type of the artifact token being captured (e.g. ARTIFACT_SECTION, ARTIFACT_MEMBER).
        :type type: str
        :return: A new DeclarationAggregate instance representing the artifact declaration.
        :rtype: DeclarationAggregate
        """
        
        return DeclarationAggregate(
            name=name,
            type=TypeAggregate.new_artifact_type(),
            metadata={
                'type': type
            }
        )

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
    def new_import_stmt(import_expr: ExpressionAggregate) -> 'StatementAggregate':
        """
        Create a new StatementAggregate representing an import statement.
        :param import_expr: The expression representing the import (e.g., module or object being imported).
        :type import_expr: ExpressionAggregate
        :return: A new StatementAggregate instance representing the import statement.
        :rtype: StatementAggregate
        """

        return StatementAggregate(
            kind=StatementKind.IMPORT,
            expr=import_expr
        )
    
    # * method: new_import_stmt_from
    @staticmethod
    def new_import_stmt_from(from_expr: ExpressionAggregate, import_expr: ExpressionAggregate) -> 'StatementAggregate':
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
            expr=import_expr
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