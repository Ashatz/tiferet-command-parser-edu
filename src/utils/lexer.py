"""Utilities – BlockTracker and TiferetLexer"""

# *** imports

# ** core
import re
from types import MethodType
from typing import List, Any

# ** infra
from ply.lex import lex as Lex, LexToken

# ** app
from ..events import a
from ..interfaces import LexerService
from ..mappers import TokenAggregate

# *** utils

# ** util: block_tracker
class BlockTracker:
    '''
    Lightweight state machine that decides when and where to inject
    INDENT / DEDENT tokens while walking a flat token stream from
    the Tiferet Domain Event dialect.

    Receives the original source text so it can compute column
    positions on demand (no column attribute required on tokens).
    '''

    # * attribute: method_pattern (class)
    method_pattern = re.compile(r'#\s*\*\s+(method:|init\b)')

    # * init
    def __init__(self, text: str):
        '''
        Initialize tracker with the original source text for column calculation.
        '''
        self.text = text
        self.reset()

    # * method: reset
    def reset(self):
        '''
        Reset all tracking state.
        '''
        self.in_class_body: bool = False
        self.in_method_body: bool = False
        self.class_col: int | None = None
        self.member_col: int | None = None
        self.class_indent_stack: List[int] = []
        self.method_indent_stack: List[int] = []
        self.paren_depth: int = 0
        self.saw_class: bool = False
        self.saw_method: bool = False

    # * method: find_column
    def find_column(self, lexpos: int) -> int:
        '''
        Compute the 0-based column of a token from its lexpos.
        '''
        if lexpos == 0:
            return 0
        last_newline = self.text.rfind('\n', 0, lexpos)
        if last_newline < 0:
            return lexpos
        return lexpos - last_newline - 1

    # * method: process_token
    def process_token(self, tok: TokenAggregate) -> None:
        '''
        Update internal state based on the current token.
        '''
        ttype = tok.type
        value = tok.value
        lexpos = getattr(tok, 'lexpos', 0)
        column = self.find_column(lexpos)

        # Track parenthesis depth
        if ttype in (a.lexer.LPAREN, a.lexer.LBRACK, a.lexer.LBRACE):
            self.paren_depth += 1
        elif ttype in (a.lexer.RPAREN, a.lexer.RBRACK, a.lexer.RBRACE):
            self.paren_depth = max(0, self.paren_depth - 1)

        # CLASS detection
        if ttype == a.lexer.CLASS:
            self.saw_class = True
            self.class_col = column

        # METHOD handling
        if ttype == a.lexer.DEF:
            self.saw_method = True
            self.member_col = column

        # CLASS hard block boundaries
        elif ttype in {
            a.lexer.ARTIFACT_SECTION,
        }:
            self.close_class_body()

        # METHOD hard block boundaries
        elif ttype in {
            a.lexer.ARTIFACT_MEMBER,
        }:
            self.close_method_body()

        # Annotations after method body
        elif ttype in {a.lexer.OBSOLETE, a.lexer.TODO} and self.method_indent_stack:
            self.close_method_body()

        # COLON after CLASS
        if self.saw_class and ttype == a.lexer.COLON and self.paren_depth == 0:
            self.saw_class = False
            self.in_class_body = True

        # COLON after METHOD signature
        if self.saw_method and ttype == a.lexer.COLON and self.paren_depth == 0:
            self.saw_method = False
            self.in_method_body = True

    # * method: should_inject_class_indent
    def should_inject_class_indent(self, next_lexpos: int) -> bool:
        '''
        Return True if the next line should start a new class body indent.
        '''
        if not self.in_class_body or self.class_indent_stack:
            return False
        next_col = self.find_column(next_lexpos)
        return self.class_col is not None and next_col > self.class_col

    # * method: should_inject_method_indent
    def should_inject_method_indent(self, next_lexpos: int) -> bool:
        '''
        Return True if the next line should push a new method indent level.
        '''
        if not self.in_method_body or self.paren_depth != 0:
            return False
        next_col = self.find_column(next_lexpos)
        current = self.method_indent_stack[-1] if self.method_indent_stack else None
        return current is None or next_col > current

    # * method: get_dedents_for_column
    def get_dedents_for_column(self, next_lexpos: int) -> List[TokenAggregate]:
        '''
        Return list of DEDENT tokens when indentation level drops.
        '''
        dedents: List[TokenAggregate] = []
        next_col = self.find_column(next_lexpos)
        while self.method_indent_stack and self.method_indent_stack[-1] > next_col:
            self.method_indent_stack.pop()
            dedents.append(self.make_dedent())
        return dedents

    # * method: get_and_flush_dedents_for_boundary
    def get_and_flush_dedents_for_boundary(self) -> List[TokenAggregate]:
        '''
        Return all pending DEDENT tokens for a boundary and clear state.
        '''
        dedents: List[TokenAggregate] = []

        while self.method_indent_stack:
            dedents.append(self.make_dedent())
            self.method_indent_stack.pop()
        self.close_method_body()

        while self.class_indent_stack:
            dedents.append(self.make_dedent())
            self.class_indent_stack.pop()
        self.close_class_body()

        return dedents

    # * method: create_indent
    def create_indent(self, lineno: int, lexpos: int) -> TokenAggregate:
        '''
        Create an INDENT token and record the column on the appropriate stack.
        '''
        column = self.find_column(lexpos)
        if self.in_method_body and self.paren_depth == 0:
            self.method_indent_stack.append(column)
        elif self.in_class_body and not self.class_indent_stack:
            self.class_indent_stack.append(column)

        return TokenAggregate.new(
            type=a.lexer.INDENT,
            value='',
            lineno=lineno,
            lexpos=lexpos
        )

    # * method: make_dedent
    def make_dedent(self, lineno: int = 0, lexpos: int = 0) -> TokenAggregate:
        '''
        Create a DEDENT token.
        '''
        return TokenAggregate.new(
            type='DEDENT',
            value='',
            lineno=lineno,
            lexpos=lexpos
        )

    # * method: close_method_body
    def close_method_body(self):
        '''
        Close any open method body and clear its state.
        '''
        self.method_indent_stack.clear()
        self.in_method_body = False
        self.member_col = None

    # * method: close_class_body
    def close_class_body(self):
        '''
        Close any open class body and clear its state.
        '''
        self.class_indent_stack.clear()
        self.in_class_body = False
        self.class_col = None
        self.saw_class = False


# ** util: tiferet_lexer
class TiferetLexer(LexerService):
    '''
    PLY-based lexer for the Tiferet Domain Event dialect.
    Implements LexerService and automatically injects INDENT / DEDENT
    tokens using BlockTracker.
    '''

    # * attribute: lexer
    lexer: Any

    # * attribute: tokens
    tokens = a.lexer.TOKENS

    # * attribute: t_ignore
    t_ignore = ' \t'

    # * init
    def __init__(self):
        '''
        Initialize the TiferetLexer and build the PLY lexer instance.
        '''

        # Load rules dynamically from the assets mapping.
        for name, rule in a.lexer.RULES.items():
            if callable(rule):
                setattr(self, name, MethodType(rule, self))
            else:
                setattr(self, name, rule)

        # Build the PLY lexer from this module's token rules.
        self.lexer = Lex(module=self)

    # * rule: t_error
    def t_error(self, t: LexToken) -> LexToken:
        '''
        Handle unrecognized characters by emitting UNKNOWN tokens.
        '''

        t.type = 'UNKNOWN'
        t.value = t.value[0]
        t.lexer.skip(1)
        return t

    # -- Public interface

        # * method: tokenize
    def tokenize(self, text: str) -> List[TokenAggregate]:
        '''
        Tokenize the provided source text and automatically inject
        INDENT / DEDENT tokens for class and method bodies.
        '''
        self.lexer.lineno = 1
        self.lexer.input(text)

        tracker = BlockTracker(text)
        result: List[TokenAggregate] = []
        prev_lineno = 0

        for t in self.lexer:
            token = self.map_lex_token(t)
            tracker.process_token(token)

            # If this token starts a new line, check if we need to inject INDENT/DEDENT
            # before adding the token itself.
            if token.lineno > prev_lineno:
                # New line started — use this token's column for decision
                if tracker.should_inject_class_indent(token.lexpos):
                    result.append(tracker.create_indent(token.lineno, token.lexpos))

                elif tracker.in_method_body:
                    if tracker.should_inject_method_indent(token.lexpos):
                        result.append(tracker.create_indent(token.lineno, token.lexpos))
                    else:
                        dedents = tracker.get_dedents_for_column(token.lexpos)
                        result.extend(dedents)

                prev_lineno = token.lineno

            # Always append the current token after possible injection
            result.append(token)

        # Final cleanup at end of stream
        if result and result[-1].type != a.lexer.NEWLINE:
            last_line = result[-1].lineno if result else 1
            result.append(TokenAggregate.new(
                type=a.lexer.NEWLINE,
                value='\n',
                lineno=last_line,
                lexpos=len(text)
            ))

        result.extend(tracker.get_and_flush_dedents_for_boundary())
        return result

    # * method: map_lex_token
    def map_lex_token(self, t: LexToken) -> TokenAggregate:
        '''
        Convert a PLY LexToken to our lean TokenAggregate.
        '''
        return TokenAggregate.new(
            type=t.type,
            value=t.value,
            lineno=t.lineno,
            lexpos=t.lexpos
        )