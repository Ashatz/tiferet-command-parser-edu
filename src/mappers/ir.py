"""IR Mapper Objects"""

# *** imports

# ** core
from typing import List, Tuple

# ** app
from ..domain.ir import (
    IREventGroup, IREvent, IREvents,
    IRImportGroup, IRImportGroups, IRImport,
    IRAttribute, IRAttributes,
    IRAssign, IRInjection, IRInjections,
    IRParam, IRParams,
    IRReturn, IRReturns,
    IRComment, IRComments,
    IRStatement, IRStatements,
    IRSnippet, IRSnippets,
    IRExecute, IRMethod, IRMethods,
)
from .settings import (
    KeterTransferObject,
    KT_KEYWORD,
    KT_STRING,
    KT_IDENT,
    KT_LPAREN,
    KT_RPAREN,
    KT_COMMA,
)

# *** mappers

# ** mapper: ir_event_group_aggregate
class IREventGroupAggregate(IREventGroup):
    '''
    Mutable aggregate for building an IREventGroup incrementally during IR generation.
    '''

    # * method: add_import_group
    def add_import_group(self, group: IRImportGroup) -> None:
        '''
        Append an import group to the import groups collection.

        :param group: The import group to add.
        :type group: IRImportGroup
        '''

        # Append the group to the import groups list.
        self.import_groups.groups.append(group)

    # * method: add_event
    def add_event(self, event: IREvent) -> None:
        '''
        Append an event to the events collection.

        :param event: The IR event to add.
        :type event: IREvent
        '''

        # Append the event to the events list.
        self.events.events.append(event)


# ** mapper: keter_ir_comment
class KeterIRComment(IRComment, KeterTransferObject):
    '''
    Transfer object that maps a keter Comment("text") back into an IRComment.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRComment:
        '''
        Parse a Comment("text") constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRComment.
        :rtype: IRComment
        '''

        # Consume Comment( "text" )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Comment')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        text = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the comment.
        return IRComment(text=text)


# ** mapper: keter_ir_comments
class KeterIRComments(IRComments, KeterTransferObject):
    '''
    Transfer object that maps a keter Comments(...) back into an IRComments.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRComments:
        '''
        Parse a Comments(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRComments.
        :rtype: IRComments
        '''

        # Consume Comments( Comment, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Comments')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        comments: List[IRComment] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Comment':
            comments.append(KeterIRComment.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRComments(comments=comments)


# ** mapper: keter_ir_statement
class KeterIRStatement(IRStatement, KeterTransferObject):
    '''
    Transfer object that maps a keter Statement(expr) back into an IRStatement.
    Uses collect_balanced() to capture the raw expression content.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRStatement:
        '''
        Parse a Statement(expr) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRStatement.
        :rtype: IRStatement
        '''

        # Consume Statement( <raw_expression> )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Statement')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        expr = KeterTransferObject.collect_balanced(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the statement.
        return IRStatement(expr=expr)


# ** mapper: keter_ir_statements
class KeterIRStatements(IRStatements, KeterTransferObject):
    '''
    Transfer object that maps a keter Statements(...) back into an IRStatements.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRStatements:
        '''
        Parse a Statements(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRStatements.
        :rtype: IRStatements
        '''

        # Consume Statements( Statement, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Statements')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        statements: List[IRStatement] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Statement':
            statements.append(KeterIRStatement.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRStatements(statements=statements)


# ** mapper: keter_ir_snippet
class KeterIRSnippet(IRSnippet, KeterTransferObject):
    '''
    Transfer object that maps a keter Snippet(Comments, Statements) back into an IRSnippet.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRSnippet:
        '''
        Parse a Snippet(Comments, Statements) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRSnippet.
        :rtype: IRSnippet
        '''

        # Consume Snippet( Comments(...), Statements(...) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Snippet')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        comments = KeterIRComments.from_data(tokens, pos)
        statements = KeterIRStatements.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the snippet.
        return IRSnippet(comments=comments, statements=statements)


# ** mapper: keter_ir_snippets
class KeterIRSnippets(IRSnippets, KeterTransferObject):
    '''
    Transfer object that maps a keter Snippets(...) back into an IRSnippets.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRSnippets:
        '''
        Parse a Snippets(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRSnippets.
        :rtype: IRSnippets
        '''

        # Consume Snippets( Snippet, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Snippets')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        snippets: List[IRSnippet] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Snippet':
            snippets.append(KeterIRSnippet.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRSnippets(snippets=snippets)


# ** mapper: keter_ir_param
class KeterIRParam(IRParam, KeterTransferObject):
    '''
    Transfer object that maps a keter Param("spec") back into an IRParam.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRParam:
        '''
        Parse a Param("spec") constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRParam.
        :rtype: IRParam
        '''

        # Consume Param( "name:type:required:default:description" )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Param')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Decode and return.
        fields = KeterTransferObject.decode_param_spec(spec)
        return IRParam(**fields)


# ** mapper: keter_ir_params
class KeterIRParams(IRParams, KeterTransferObject):
    '''
    Transfer object that maps a keter Params(...) back into an IRParams.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRParams:
        '''
        Parse a Params(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRParams.
        :rtype: IRParams
        '''

        # Consume Params( Param, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Params')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        params: List[IRParam] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Param':
            params.append(KeterIRParam.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRParams(params=params)


# ** mapper: keter_ir_return
class KeterIRReturn(IRReturn, KeterTransferObject):
    '''
    Transfer object that maps a keter Return("spec") back into an IRReturn.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRReturn:
        '''
        Parse a Return("spec") constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRReturn.
        :rtype: IRReturn
        '''

        # Consume Return( "type_name:description" )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Return')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Decode and return.
        fields = KeterTransferObject.decode_return_spec(spec)
        return IRReturn(**fields)


# ** mapper: keter_ir_returns
class KeterIRReturns(IRReturns, KeterTransferObject):
    '''
    Transfer object that maps a keter Returns(...) back into an IRReturns.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRReturns:
        '''
        Parse a Returns(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRReturns.
        :rtype: IRReturns
        '''

        # Consume Returns( Return, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Returns')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        returns: List[IRReturn] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Return':
            returns.append(KeterIRReturn.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRReturns(returns=returns)


# ** mapper: keter_ir_execute
class KeterIRExecute(IRExecute, KeterTransferObject):
    '''
    Transfer object that maps a keter Execute(Params, Returns, Snippets) back into an IRExecute.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRExecute:
        '''
        Parse an Execute(Params, Returns, Snippets) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRExecute.
        :rtype: IRExecute
        '''

        # Consume Execute( Params(...), Returns(...), Snippets(...) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Execute')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        params = KeterIRParams.from_data(tokens, pos)
        returns = KeterIRReturns.from_data(tokens, pos)
        snippets = KeterIRSnippets.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the execute.
        return IRExecute(params=params, returns=returns, snippets=snippets)


# ** mapper: keter_ir_method
class KeterIRMethod(IRMethod, KeterTransferObject):
    '''
    Transfer object that maps a keter Method(name, Params, Returns, Snippets) back into an IRMethod.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRMethod:
        '''
        Parse a Method(name, Params, Returns, Snippets) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRMethod.
        :rtype: IRMethod
        '''

        # Consume Method( name, Params(...), Returns(...), Snippets(...) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Method')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        params = KeterIRParams.from_data(tokens, pos)
        returns = KeterIRReturns.from_data(tokens, pos)
        snippets = KeterIRSnippets.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the method.
        return IRMethod(name=name, params=params, returns=returns, snippets=snippets)


# ** mapper: keter_ir_methods
class KeterIRMethods(IRMethods, KeterTransferObject):
    '''
    Transfer object that maps a keter Methods(...) or Methods() back into an IRMethods.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRMethods:
        '''
        Parse a Methods(...) or Methods() constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRMethods.
        :rtype: IRMethods
        '''

        # Consume Methods( Method, ... ) or Methods()
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Methods')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        methods: List[IRMethod] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Method':
            methods.append(KeterIRMethod.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRMethods(methods=methods)


# ** mapper: keter_ir_attribute
class KeterIRAttribute(IRAttribute, KeterTransferObject):
    '''
    Transfer object that maps a keter Attribute(name, type) back into an IRAttribute.
    Handles both 2-arg (Attributes section) and 1-arg (Assign target) forms.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRAttribute:
        '''
        Parse an Attribute(name, type) or Attribute(name) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRAttribute.
        :rtype: IRAttribute
        '''

        # Consume Attribute( name [, type] )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Attribute')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]

        # Check for optional type argument (2-arg form).
        attr_type = ''
        cur = KeterTransferObject.peek(tokens, pos)
        if cur and cur[0] == KT_COMMA:
            KeterTransferObject.skip_comma(tokens, pos)
            nxt = KeterTransferObject.peek(tokens, pos)
            if nxt and nxt[0] == KT_IDENT:
                attr_type = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the attribute.
        return IRAttribute(name=name, type=attr_type)


# ** mapper: keter_ir_attributes
class KeterIRAttributes(IRAttributes, KeterTransferObject):
    '''
    Transfer object that maps a keter Attributes(...) back into an IRAttributes.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRAttributes:
        '''
        Parse an Attributes(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRAttributes.
        :rtype: IRAttributes
        '''

        # Consume Attributes( Attribute, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Attributes')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        attrs: List[IRAttribute] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Attribute':
            attrs.append(KeterIRAttribute.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRAttributes(attributes=attrs)


# ** mapper: keter_ir_assign
class KeterIRAssign(IRAssign, KeterTransferObject):
    '''
    Transfer object that maps a keter Assign(Attribute(target), source) back into an IRAssign.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRAssign:
        '''
        Parse an Assign(Attribute(target), source) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRAssign.
        :rtype: IRAssign
        '''

        # Consume Assign( Attribute(target), source )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Assign')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        target_attr = KeterIRAttribute.from_data(tokens, pos)
        source = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the assign.
        return IRAssign(target=target_attr.name, source=source)


# ** mapper: keter_ir_injection
class KeterIRInjection(IRInjection, KeterTransferObject):
    '''
    Transfer object that maps a keter Injection("spec", Assign(...)) back into an IRInjection.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRInjection:
        '''
        Parse an Injection("spec", Assign(...)) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRInjection.
        :rtype: IRInjection
        '''

        # Consume Injection( "param_spec", Assign(...) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Injection')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        assign = KeterIRAssign.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Decode the colon-delimited param spec.
        fields = KeterTransferObject.decode_param_spec(spec)

        # Return the injection.
        return IRInjection(
            name=fields['name'],
            type=fields['type'],
            required=fields['required'],
            default=fields['default'],
            description=fields['description'],
            assign=assign,
        )


# ** mapper: keter_ir_injections
class KeterIRInjections(IRInjections, KeterTransferObject):
    '''
    Transfer object that maps a keter Injections(...) back into an IRInjections.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRInjections:
        '''
        Parse an Injections(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRInjections.
        :rtype: IRInjections
        '''

        # Consume Injections( Injection, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Injections')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        injections: List[IRInjection] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Injection':
            injections.append(KeterIRInjection.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRInjections(injections=injections)


# ** mapper: keter_ir_import
class KeterIRImport(IRImport, KeterTransferObject):
    '''
    Transfer object that maps a keter Import(module_path, symbol) back into an IRImport.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRImport:
        '''
        Parse an Import(module_path, symbol) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRImport.
        :rtype: IRImport
        '''

        # Consume Import( module_path, symbol )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Import')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        module_path = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        symbol = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the import.
        return IRImport(module_path=module_path, symbol=symbol)


# ** mapper: keter_ir_import_group
class KeterIRImportGroup(IRImportGroup, KeterTransferObject):
    '''
    Transfer object that maps a keter ImportGroup(category, Imports(...)) back into an IRImportGroup.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRImportGroup:
        '''
        Parse an ImportGroup(category, Imports(...)) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRImportGroup.
        :rtype: IRImportGroup
        '''

        # Consume ImportGroup( category, Imports( Import, ... ) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'ImportGroup')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        category = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Parse the inline Imports collection.
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Imports')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        imports: List[IRImport] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Import':
            imports.append(KeterIRImport.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the import group.
        return IRImportGroup(category=category, imports=imports)


# ** mapper: keter_ir_import_groups
class KeterIRImportGroups(IRImportGroups, KeterTransferObject):
    '''
    Transfer object that maps a keter ImportGroups(...) back into an IRImportGroups.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IRImportGroups:
        '''
        Parse an ImportGroups(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IRImportGroups.
        :rtype: IRImportGroups
        '''

        # Consume ImportGroups( ImportGroup, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'ImportGroups')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        groups: List[IRImportGroup] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'ImportGroup':
            groups.append(KeterIRImportGroup.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IRImportGroups(groups=groups)


# ** mapper: keter_ir_event
class KeterIREvent(IREvent, KeterTransferObject):
    '''
    Transfer object that maps a keter Event(...) back into an IREvent.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IREvent:
        '''
        Parse an Event(artifact_name, class_name, doc_string, ...) constructor.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IREvent.
        :rtype: IREvent
        '''

        # Consume Event( artifact_name, class_name, "doc_string", ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Event')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        artifact_name = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        class_name = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        doc_string = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Delegate to child transfer objects.
        attributes = KeterIRAttributes.from_data(tokens, pos)
        injections = KeterIRInjections.from_data(tokens, pos)
        execute = KeterIRExecute.from_data(tokens, pos)
        methods = KeterIRMethods.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the event.
        return IREvent(
            artifact_name=artifact_name,
            class_name=class_name,
            doc_string=doc_string,
            attributes=attributes,
            injections=injections,
            execute=execute,
            methods=methods,
        )


# ** mapper: keter_ir_events
class KeterIREvents(IREvents, KeterTransferObject):
    '''
    Transfer object that maps a keter Events(...) back into an IREvents.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(tokens: List[Tuple[str, str]], pos: List[int]) -> IREvents:
        '''
        Parse an Events(...) constructor from the token stream.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The parsed IREvents.
        :rtype: IREvents
        '''

        # Consume Events( Event, ... )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'Events')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        events: List[IREvent] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Event':
            events.append(KeterIREvent.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)

        # Return the collection.
        return IREvents(events=events)


# ** mapper: keter_ir_event_group
class KeterIREventGroup(IREventGroup, KeterTransferObject):
    '''
    Root transfer object that maps a full keter DSL string back into an IREventGroup.
    Entry point for keter-to-IR deserialization.
    '''

    # * method: from_data (static)
    @staticmethod
    def from_data(text: str) -> IREventGroup:
        '''
        Parse a keter DSL string into an IREventGroup.
        Tokenizes the text via KeterLexer, then recursively descends
        through child transfer objects.

        :param text: The keter DSL string.
        :type text: str
        :return: The parsed IREventGroup.
        :rtype: IREventGroup
        '''

        # Lazy import of KeterLexer to avoid triggering the utils package
        # __init__ at mapper module load time (circular import).
        from ..utils.lexer_keter import KeterLexer

        # Tokenize the keter DSL.
        tokens = KeterLexer.tokenize(text)
        pos = [0]

        # Consume EventGroup( name, "description", ImportGroups(...), Events(...) )
        KeterTransferObject.consume(tokens, pos, KT_KEYWORD, 'EventGroup')
        KeterTransferObject.consume(tokens, pos, KT_LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KT_IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        description = KeterTransferObject.consume(tokens, pos, KT_STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Delegate to child transfer objects.
        import_groups = KeterIRImportGroups.from_data(tokens, pos)
        events = KeterIREvents.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KT_RPAREN)

        # Build and return the IREventGroup.
        return IREventGroup(
            name=name,
            description=description,
            import_groups=import_groups,
            events=events,
        )
