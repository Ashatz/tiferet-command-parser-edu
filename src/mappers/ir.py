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


# *** constants

# ** constant: KETER_KEYWORDS
KETER_KEYWORDS = {
    'EventGroup', 'ImportGroups', 'ImportGroup', 'Imports', 'Import',
    'Events', 'Event', 'Attributes', 'Attribute',
    'Injections', 'Injection', 'Assign',
    'Execute', 'Methods', 'Method',
    'Params', 'Param', 'Returns', 'Return',
    'Snippets', 'Snippet', 'Comments', 'Comment',
    'Statements', 'Statement',
}


# *** utils

# ** util: keter_lexer
class KeterLexer:
    '''
    Minimal lexer that tokenizes a keter DSL string into a flat
    stream of (type, value) tuples.
    '''

    # * attribute: KEYWORD
    KEYWORD = 'KEYWORD'

    # * attribute: STRING
    STRING = 'STRING'

    # * attribute: IDENT
    IDENT = 'IDENT'

    # * attribute: LPAREN
    LPAREN = 'LPAREN'

    # * attribute: RPAREN
    RPAREN = 'RPAREN'

    # * attribute: COMMA
    COMMA = 'COMMA'

    # * method: tokenize (static)
    @staticmethod
    def tokenize(text: str) -> List[Tuple[str, str]]:
        '''
        Tokenize a keter DSL string into a flat list of (type, value) tuples.

        :param text: The keter DSL string.
        :type text: str
        :return: List of (token_type, token_value) tuples.
        :rtype: List[Tuple[str, str]]
        '''

        # Initialize the token list and cursor.
        tokens: List[Tuple[str, str]] = []
        i = 0

        # Walk through the text character by character.
        while i < len(text):
            ch = text[i]

            # Skip whitespace.
            if ch in ' \t\n\r':
                i += 1
                continue

            # Match single-character delimiters.
            if ch == '(':
                tokens.append((KeterLexer.LPAREN, '('))
                i += 1
                continue
            if ch == ')':
                tokens.append((KeterLexer.RPAREN, ')'))
                i += 1
                continue
            if ch == ',':
                tokens.append((KeterLexer.COMMA, ','))
                i += 1
                continue

            # Match quoted string literals.
            if ch == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    if text[j] == '\\':
                        j += 1
                    j += 1
                tokens.append((KeterLexer.STRING, text[i + 1:j]))
                i = j + 1
                continue

            # Match identifiers and keywords.
            j = i
            while j < len(text) and text[j] not in ' \t\n\r(),"':
                j += 1
            word = text[i:j]
            tok_type = KeterLexer.KEYWORD if word in KETER_KEYWORDS else KeterLexer.IDENT
            tokens.append((tok_type, word))
            i = j

        # Return the flat token stream.
        return tokens


# ** util: keter_transfer_base
class KeterTransferObject:
    '''
    Base class providing shared token-stream traversal helpers
    for all Keter* transfer objects.
    '''

    # * method: consume (static)
    @staticmethod
    def consume(tokens: List[Tuple[str, str]],
            pos: List[int],
            expected_type: str = None,
            expected_value: str = None,
        ) -> Tuple[str, str]:
        '''
        Consume and return the current token, optionally asserting type/value.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :param expected_type: Expected token type.
        :type expected_type: str
        :param expected_value: Expected token value.
        :type expected_value: str
        :return: The consumed (type, value) tuple.
        :rtype: Tuple[str, str]
        '''

        # Validate bounds.
        if pos[0] >= len(tokens):
            raise ValueError(
                f'Unexpected end of keter input'
                f' (expected {expected_type}:{expected_value})'
            )

        # Get the current token.
        tok = tokens[pos[0]]

        # Assert type if specified.
        if expected_type and tok[0] != expected_type:
            raise ValueError(
                f'Expected {expected_type} but got'
                f' {tok[0]}:"{tok[1]}" at position {pos[0]}'
            )

        # Assert value if specified.
        if expected_value and tok[1] != expected_value:
            raise ValueError(
                f'Expected "{expected_value}" but got'
                f' "{tok[1]}" at position {pos[0]}'
            )

        # Advance and return.
        pos[0] += 1
        return tok

    # * method: peek (static)
    @staticmethod
    def peek(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> Tuple[str, str] | None:
        '''
        Peek at the current token without consuming it.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The current token, or None if exhausted.
        :rtype: Tuple[str, str] | None
        '''

        # Return the current token if within bounds.
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None

    # * method: skip_comma (static)
    @staticmethod
    def skip_comma(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> None:
        '''
        Consume a comma token if the current token is one.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        '''

        # Skip an optional trailing comma.
        cur = KeterTransferObject.peek(tokens, pos)
        if cur and cur[0] == KeterLexer.COMMA:
            pos[0] += 1

    # * method: collect_balanced (static)
    @staticmethod
    def collect_balanced(tokens: List[Tuple[str, str]],
            pos: List[int],
        ) -> str:
        '''
        Collect tokens until the matching closing paren at depth 0,
        reconstructing the raw expression string.

        :param tokens: The flat token stream.
        :type tokens: List[Tuple[str, str]]
        :param pos: Single-element list holding the current cursor position.
        :type pos: List[int]
        :return: The raw expression string.
        :rtype: str
        '''

        # Track parenthesis depth and accumulate parts.
        depth = 0
        parts: List[str] = []

        while pos[0] < len(tokens):
            tok = tokens[pos[0]]

            # Stop at the matching closing paren.
            if tok[0] == KeterLexer.RPAREN and depth == 0:
                break

            # Track nested parens.
            if tok[0] == KeterLexer.LPAREN:
                depth += 1
                parts.append('(')
            elif tok[0] == KeterLexer.RPAREN:
                depth -= 1
                parts.append(')')
            elif tok[0] == KeterLexer.COMMA:
                parts.append(', ')
            elif tok[0] == KeterLexer.STRING:
                parts.append(f'"{tok[1]}"')
            else:
                parts.append(tok[1])

            pos[0] += 1

        # Return the reconstructed expression.
        return ''.join(parts)

    # * method: decode_param_spec (static)
    @staticmethod
    def decode_param_spec(spec: str) -> dict:
        '''
        Decode a colon-delimited param spec into a dict of IRParam fields.

        :param spec: The colon-delimited string (name:type:required:default:description).
        :type spec: str
        :return: Dict with name, type, required, default, description keys.
        :rtype: dict
        '''

        # Split and assign positionally.
        parts = spec.split(':')
        return dict(
            name=parts[0] if len(parts) > 0 else '',
            type=parts[1] if len(parts) > 1 else '',
            required=parts[2].lower() == 'true' if len(parts) > 2 else True,
            default=parts[3] if len(parts) > 3 else '',
            description=':'.join(parts[4:]) if len(parts) > 4 else '',
        )

    # * method: decode_return_spec (static)
    @staticmethod
    def decode_return_spec(spec: str) -> dict:
        '''
        Decode a colon-delimited return spec into a dict of IRReturn fields.

        :param spec: The colon-delimited string (type_name:description).
        :type spec: str
        :return: Dict with type_name and description keys.
        :rtype: dict
        '''

        # Split on first colon only.
        parts = spec.split(':', 1)
        return dict(
            type_name=parts[0] if len(parts) > 0 else '',
            description=parts[1] if len(parts) > 1 else '',
        )


# *** keter transfer objects

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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Comment')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        text = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Comments')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        comments: List[IRComment] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Comment':
            comments.append(KeterIRComment.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Statement')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        expr = KeterTransferObject.collect_balanced(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Statements')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        statements: List[IRStatement] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Statement':
            statements.append(KeterIRStatement.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Snippet')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        comments = KeterIRComments.from_data(tokens, pos)
        statements = KeterIRStatements.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Snippets')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        snippets: List[IRSnippet] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Snippet':
            snippets.append(KeterIRSnippet.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Param')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Params')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        params: List[IRParam] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Param':
            params.append(KeterIRParam.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Return')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Returns')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        returns: List[IRReturn] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Return':
            returns.append(KeterIRReturn.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Execute')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        params = KeterIRParams.from_data(tokens, pos)
        returns = KeterIRReturns.from_data(tokens, pos)
        snippets = KeterIRSnippets.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Method')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        params = KeterIRParams.from_data(tokens, pos)
        returns = KeterIRReturns.from_data(tokens, pos)
        snippets = KeterIRSnippets.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Methods')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        methods: List[IRMethod] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Method':
            methods.append(KeterIRMethod.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Attribute')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]

        # Check for optional type argument (2-arg form).
        attr_type = ''
        cur = KeterTransferObject.peek(tokens, pos)
        if cur and cur[0] == KeterLexer.COMMA:
            KeterTransferObject.skip_comma(tokens, pos)
            nxt = KeterTransferObject.peek(tokens, pos)
            if nxt and nxt[0] == KeterLexer.IDENT:
                attr_type = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Attributes')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        attrs: List[IRAttribute] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Attribute':
            attrs.append(KeterIRAttribute.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Assign')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        target_attr = KeterIRAttribute.from_data(tokens, pos)
        source = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Injection')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        spec = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        assign = KeterIRAssign.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Injections')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        injections: List[IRInjection] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Injection':
            injections.append(KeterIRInjection.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Import')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        module_path = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        symbol = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'ImportGroup')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        category = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Parse the inline Imports collection.
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Imports')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        imports: List[IRImport] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Import':
            imports.append(KeterIRImport.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
        KeterTransferObject.skip_comma(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'ImportGroups')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        groups: List[IRImportGroup] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'ImportGroup':
            groups.append(KeterIRImportGroup.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Event')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        artifact_name = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        class_name = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        doc_string = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Delegate to child transfer objects.
        attributes = KeterIRAttributes.from_data(tokens, pos)
        injections = KeterIRInjections.from_data(tokens, pos)
        execute = KeterIRExecute.from_data(tokens, pos)
        methods = KeterIRMethods.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'Events')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        events: List[IREvent] = []
        while KeterTransferObject.peek(tokens, pos) and \
                KeterTransferObject.peek(tokens, pos)[1] == 'Event':
            events.append(KeterIREvent.from_data(tokens, pos))
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)
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

        # Tokenize the keter DSL.
        tokens = KeterLexer.tokenize(text)
        pos = [0]

        # Consume EventGroup( name, "description", ImportGroups(...), Events(...) )
        KeterTransferObject.consume(tokens, pos, KeterLexer.KEYWORD, 'EventGroup')
        KeterTransferObject.consume(tokens, pos, KeterLexer.LPAREN)
        name = KeterTransferObject.consume(tokens, pos, KeterLexer.IDENT)[1]
        KeterTransferObject.skip_comma(tokens, pos)
        description = KeterTransferObject.consume(tokens, pos, KeterLexer.STRING)[1]
        KeterTransferObject.skip_comma(tokens, pos)

        # Delegate to child transfer objects.
        import_groups = KeterIRImportGroups.from_data(tokens, pos)
        events = KeterIREvents.from_data(tokens, pos)
        KeterTransferObject.consume(tokens, pos, KeterLexer.RPAREN)

        # Build and return the IREventGroup.
        return IREventGroup(
            name=name,
            description=description,
            import_groups=import_groups,
            events=events,
        )
