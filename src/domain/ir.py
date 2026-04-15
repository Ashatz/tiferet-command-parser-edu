"""IR Domain Objects"""

# *** imports

# ** core
from typing import List, Optional

# ** infra
from pydantic import BaseModel, Field

# *** constants

INDENT = '    '

# *** objects

# ** object: ir_import
class IRImport(BaseModel):
    """A single import statement in the IR."""

    # * attribute: module_path
    module_path: str = Field(
        ...,
        description='The module path of the import (e.g. ".settings", "tiferet.events").'
    )

    # * attribute: symbol
    symbol: str = Field(
        ...,
        description='The imported symbol name (e.g. "DomainEvent").'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the Import constructor string.
        # Both module path and symbol are identifiers in the keter DSL — no quotes.
        pad = INDENT * indent
        return f'{pad}Import({self.module_path}, {self.symbol}),'


# ** object: ir_import_group
class IRImportGroup(BaseModel):
    """A group of imports under a single artifact category label."""

    # * attribute: category
    category: str = Field(
        ...,
        description='The artifact category label (e.g. "core", "infra", "app").'
    )

    # * attribute: imports
    imports: List[IRImport] = Field(
        default_factory=list,
        description='The imports in this group.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the ImportGroup constructor with nested imports.
        # Category is an artifact label identifier — no quotes.
        pad = INDENT * indent
        lines = [f'{pad}ImportGroup({self.category}, Imports(']
        for imp in self.imports:
            lines.append(imp.to_keter(indent + 1))
        lines.append(f'{pad})),')
        return '\n'.join(lines)


# ** object: ir_import_groups
class IRImportGroups(BaseModel):
    """Collection of import groups for the module."""

    # * attribute: groups
    groups: List[IRImportGroup] = Field(
        default_factory=list,
        description='The import groups.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the ImportGroups constructor with nested groups.
        pad = INDENT * indent
        lines = [f'{pad}ImportGroups(']
        for group in self.groups:
            lines.append(group.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_attribute
class IRAttribute(BaseModel):
    """A class-level attribute declaration."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The attribute name.'
    )

    # * attribute: type
    type: str = Field(
        ...,
        description='The attribute type (e.g. "str", "ErrorService").'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the Attribute constructor string.
        # Name and type are identifiers — no quotes.
        pad = INDENT * indent
        return f'{pad}Attribute({self.name}, {self.type}),'


# ** object: ir_attributes
class IRAttributes(BaseModel):
    """Collection of class-level attribute declarations."""

    # * attribute: attributes
    attributes: List[IRAttribute] = Field(
        default_factory=list,
        description='The class attributes.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Attributes constructor with nested attribute entries.
        pad = INDENT * indent
        lines = [f'{pad}Attributes(']
        for attr in self.attributes:
            lines.append(attr.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_assign
class IRAssign(BaseModel):
    """An assignment expression within an injection body."""

    # * attribute: target
    target: str = Field(
        ...,
        description='The self attribute being assigned (e.g. "error_service").'
    )

    # * attribute: source
    source: str = Field(
        ...,
        description='The constructor parameter being bound (e.g. "error_service").'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the Assign expression string.
        # Target and source are identifiers — no quotes.
        pad = INDENT * indent
        return f'{pad}Assign(Attribute({self.target}), {self.source})'


# ** object: ir_injection
class IRInjection(BaseModel):
    """A constructor injection mapping encoded as a param string + assignment."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The parameter name.'
    )

    # * attribute: type
    type: str = Field(
        ...,
        description='The parameter type (e.g. "ErrorService").'
    )

    # * attribute: required
    required: bool = Field(
        True,
        description='Whether the parameter is required (always True for injections).'
    )

    # * attribute: default
    default: str = Field(
        '',
        description='Default value literal, or empty string (always empty for injections).'
    )

    # * attribute: description
    description: str = Field(
        '',
        description='Human-readable description from the init docstring.'
    )

    # * attribute: assign
    assign: IRAssign = Field(
        ...,
        description='The self-assignment expression for this injection.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Injection constructor: param string + Assign expression.
        # Param string mirrors the Param colon-delimited encoding.
        pad = INDENT * indent
        req = 'true' if self.required else 'false'
        param_str = f'{self.name}:{self.type}:{req}:{self.default}:{self.description}'
        assign_str = self.assign.to_keter(indent + 1)
        return f'{pad}Injection("{param_str}",\n{assign_str}\n{pad}),'


# ** object: ir_injections
class IRInjections(BaseModel):
    """Collection of constructor injections from the init block."""

    # * attribute: injections
    injections: List[IRInjection] = Field(
        default_factory=list,
        description='The constructor injections.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Injections constructor with nested injection entries.
        pad = INDENT * indent
        lines = [f'{pad}Injections(']
        for inj in self.injections:
            lines.append(inj.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_param
class IRParam(BaseModel):
    """A method parameter encoded as a colon-delimited string."""

    # * attribute: name
    name: str = Field(
        ...,
        description='Parameter name.'
    )

    # * attribute: type
    type: str = Field(
        ...,
        description='Parameter type (e.g. "str", "int", "dict").'
    )

    # * attribute: required
    required: bool = Field(
        True,
        description='Whether the parameter is required.'
    )

    # * attribute: default
    default: str = Field(
        '',
        description='Default value literal, or empty string if none.'
    )

    # * attribute: description
    description: str = Field(
        '',
        description='Human-readable description from the method docstring.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the colon-delimited Param string.
        pad = INDENT * indent
        req = 'true' if self.required else 'false'
        return f'{pad}Param("{self.name}:{self.type}:{req}:{self.default}:{self.description}"),'


# ** object: ir_params
class IRParams(BaseModel):
    """Collection of method parameters."""

    # * attribute: params
    params: List[IRParam] = Field(
        default_factory=list,
        description='The method parameters (excluding self).'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Params constructor with nested parameter entries.
        pad = INDENT * indent
        lines = [f'{pad}Params(']
        for param in self.params:
            lines.append(param.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_return
class IRReturn(BaseModel):
    """A return type entry encoded as type_name:description."""

    # * attribute: type_name
    type_name: str = Field(
        ...,
        description='The return type name (e.g. "str", "Error").'
    )

    # * attribute: description
    description: str = Field(
        '',
        description='Human-readable description from the method docstring.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the colon-delimited Return string.
        pad = INDENT * indent
        return f'{pad}Return("{self.type_name}:{self.description}"),'


# ** object: ir_returns
class IRReturns(BaseModel):
    """Collection of return type entries for a method."""

    # * attribute: returns
    returns: List[IRReturn] = Field(
        default_factory=list,
        description='The return type entries.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Returns constructor with nested return entries.
        pad = INDENT * indent
        lines = [f'{pad}Returns(']
        for ret in self.returns:
            lines.append(ret.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_comment
class IRComment(BaseModel):
    """A comment line within a code snippet."""

    # * attribute: text
    text: str = Field(
        ...,
        description='The comment text (without leading # or whitespace).'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the Comment constructor string.
        pad = INDENT * indent
        return f'{pad}Comment("{self.text}"),'


# ** object: ir_comments
class IRComments(BaseModel):
    """Collection of comment lines in a snippet."""

    # * attribute: comments
    comments: List[IRComment] = Field(
        default_factory=list,
        description='The comment lines.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Comments constructor with nested comment entries.
        pad = INDENT * indent
        lines = [f'{pad}Comments(']
        for comment in self.comments:
            lines.append(comment.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_statement
class IRStatement(BaseModel):
    """A statement encoded as a string-serialized expression."""

    # * attribute: expr
    expr: str = Field(
        ...,
        description='String-encoded expression (e.g. "Assign(...)", "Return(...)").'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build and return the Statement constructor string.
        # Expr is a DSL expression, not a text string — no quotes.
        pad = INDENT * indent
        return f'{pad}Statement({self.expr}),'


# ** object: ir_statements
class IRStatements(BaseModel):
    """Collection of statements in a snippet."""

    # * attribute: statements
    statements: List[IRStatement] = Field(
        default_factory=list,
        description='The statements.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Statements constructor with nested statement entries.
        pad = INDENT * indent
        lines = [f'{pad}Statements(']
        for stmt in self.statements:
            lines.append(stmt.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_snippet
class IRSnippet(BaseModel):
    """A code snippet pairing comments with statements."""

    # * attribute: comments
    comments: IRComments = Field(
        default_factory=IRComments,
        description='The comment lines preceding the statements.'
    )

    # * attribute: statements
    statements: IRStatements = Field(
        default_factory=IRStatements,
        description='The executable statements in this snippet.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Snippet constructor with nested comments and statements.
        pad = INDENT * indent
        lines = [f'{pad}Snippet(']
        lines.append(self.comments.to_keter(indent + 1))
        lines.append(self.statements.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_snippets
class IRSnippets(BaseModel):
    """Collection of code snippets in a method body."""

    # * attribute: snippets
    snippets: List[IRSnippet] = Field(
        default_factory=list,
        description='The code snippets.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Snippets constructor with nested snippet entries.
        pad = INDENT * indent
        lines = [f'{pad}Snippets(']
        for snippet in self.snippets:
            lines.append(snippet.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_execute
class IRExecute(BaseModel):
    """The execute method of a domain event."""

    # * attribute: name
    name: str = Field(
        'execute',
        description='Always "execute" — the primary entry point of a DomainEvent.'
    )

    # * attribute: params
    params: IRParams = Field(
        default_factory=IRParams,
        description='The execute method parameters (excluding self).'
    )

    # * attribute: returns
    returns: IRReturns = Field(
        default_factory=IRReturns,
        description='The return type entries.'
    )

    # * attribute: snippets
    snippets: IRSnippets = Field(
        default_factory=IRSnippets,
        description='The method body snippets.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Execute constructor with params, returns, and snippets.
        pad = INDENT * indent
        lines = [f'{pad}Execute(']
        lines.append(self.params.to_keter(indent + 1))
        lines.append(self.returns.to_keter(indent + 1))
        lines.append(self.snippets.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_method
class IRMethod(BaseModel):
    """A helper method on a domain event (non-execute)."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The method name (e.g. "verify_number").'
    )

    # * attribute: params
    params: IRParams = Field(
        default_factory=IRParams,
        description='The method parameters (excluding self).'
    )

    # * attribute: returns
    returns: IRReturns = Field(
        default_factory=IRReturns,
        description='The return type entries.'
    )

    # * attribute: snippets
    snippets: IRSnippets = Field(
        default_factory=IRSnippets,
        description='The method body snippets.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Method constructor with params, returns, and snippets.
        # Name is an identifier — no quotes.
        pad = INDENT * indent
        lines = [f'{pad}Method({self.name},']
        lines.append(self.params.to_keter(indent + 1))
        lines.append(self.returns.to_keter(indent + 1))
        lines.append(self.snippets.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_methods
class IRMethods(BaseModel):
    """Collection of helper methods (non-execute) on a domain event."""

    # * attribute: methods
    methods: List[IRMethod] = Field(
        default_factory=list,
        description='The helper methods.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Emit empty Methods() when there are no helper methods.
        pad = INDENT * indent
        if not self.methods:
            return f'{pad}Methods()'

        # Build the Methods constructor with nested method entries.
        lines = [f'{pad}Methods(']
        for method in self.methods:
            lines.append(method.to_keter(indent + 1))
        lines.append(f'{pad})')
        return '\n'.join(lines)


# ** object: ir_event
class IREvent(BaseModel):
    """A domain event class in the IR."""

    # * attribute: artifact_name
    artifact_name: str = Field(
        ...,
        description='The artifact section name (e.g. "get_error" from "# ** event: get_error").'
    )

    # * attribute: class_name
    class_name: str = Field(
        ...,
        description='The event class name (e.g. "GetError").'
    )

    # * attribute: doc_string
    doc_string: str = Field(
        '',
        description='The class-level docstring (stripped of triple quotes).'
    )

    # * attribute: attributes
    attributes: IRAttributes = Field(
        default_factory=IRAttributes,
        description='The class-level attribute declarations.'
    )

    # * attribute: injections
    injections: IRInjections = Field(
        default_factory=IRInjections,
        description='The constructor injections.'
    )

    # * attribute: execute
    execute: IRExecute = Field(
        default_factory=IRExecute,
        description='The execute method.'
    )

    # * attribute: methods
    methods: IRMethods = Field(
        default_factory=IRMethods,
        description='The helper methods (non-execute).'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Event constructor with all member sections.
        # Artifact name and class name are identifiers; doc_string is text content — keep its quotes.
        pad = INDENT * indent
        lines = [f'{pad}Event({self.artifact_name}, {self.class_name}, "{self.doc_string}",']
        lines.append(self.attributes.to_keter(indent + 1))
        lines.append(self.injections.to_keter(indent + 1))
        lines.append(self.execute.to_keter(indent + 1))
        lines.append(self.methods.to_keter(indent + 1))
        lines.append(f'{pad}),')
        return '\n'.join(lines)


# ** object: ir_events
class IREvents(BaseModel):
    """Collection of domain events in a module."""

    # * attribute: events
    events: List[IREvent] = Field(
        default_factory=list,
        description='The domain events.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize to keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the Events constructor with nested event entries.
        pad = INDENT * indent
        lines = [f'{pad}Events(']
        for event in self.events:
            lines.append(event.to_keter(indent + 1))
        lines.append(f'{pad})')
        return '\n'.join(lines)


# ** object: ir_event_group
class IREventGroup(BaseModel):
    """Root IR node representing a module of domain events."""

    # * attribute: name
    name: str = Field(
        ...,
        description='The module/group name (e.g. "pass_multiple_operator_events").'
    )

    # * attribute: description
    description: str = Field(
        '',
        description='Human-readable label from the module docstring.'
    )

    # * attribute: import_groups
    import_groups: IRImportGroups = Field(
        default_factory=IRImportGroups,
        description='The grouped imports.'
    )

    # * attribute: events
    events: IREvents = Field(
        default_factory=IREvents,
        description='The domain events.'
    )

    # * method: to_keter
    def to_keter(self, indent: int = 0) -> str:
        '''
        Serialize the full IR tree to a keter DSL string.

        :param indent: Indentation level.
        :type indent: int
        :return: Keter DSL string.
        :rtype: str
        '''

        # Build the EventGroup root constructor.
        # Name is an identifier; description is text content — keep its quotes.
        pad = INDENT * indent
        lines = [f'{pad}EventGroup({self.name}, "{self.description}",']
        lines.append(self.import_groups.to_keter(indent + 1))
        lines.append(self.events.to_keter(indent + 1))
        lines.append(f'{pad})')
        return '\n'.join(lines)
