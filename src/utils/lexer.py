"""Utilities - BlockTracker and TiferetLexer"""

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

# *** constants

# ** constant: tab_size
TAB_SIZE = 4

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

    # * attribute: class_pattern
    class_pattern = re.compile(r'#\s*\*\s+(events:\b)')

    # * attribute: paren_depth
    paren_depth: int

    # * attribute: saw_class
    saw_class: bool

    # * attribute: saw_method
    saw_method: bool

    # * attribute: current_col
    current_col: int

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

        self.paren_depth: int = 0
        self.saw_class: bool = False
        self.saw_method: bool = False
        self.current_col: int = 0

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
    def process_token(self, tok: TokenAggregate, result: List[TokenAggregate] = []) -> None:
        '''
        Update internal state based on the current token.
        
        :param tok: The current token being processed.
        :type tok: TokenAggregate
        :param result: The list of tokens to which any injected INDENT/DEDENT tokens should be appended.
        :type result: List[TokenAggregate]
        '''
        
        ttype = tok.type
        lineno = tok.lineno
        lexpos = getattr(tok, 'lexpos', 0)
        column = self.find_column(lexpos)

        # Track parenthesis depth
        if ttype in (a.lexer.LPAREN, a.lexer.LBRACK, a.lexer.LBRACE):
            self.paren_depth += 1
        elif ttype in (a.lexer.RPAREN, a.lexer.RBRACK, a.lexer.RBRACE):
            self.paren_depth = max(0, self.paren_depth - 1)

        # CLASS detection
        if ttype == a.lexer.CLASS or (ttype == a.lexer.ARTIFACT_SECTION and self.class_pattern.match(tok.value)):
            if not self.saw_class:
                self.saw_class = True

        # METHOD handling
        if ttype == a.lexer.DEF or (ttype == a.lexer.ARTIFACT_MEMBER and self.method_pattern.match(tok.value)):
            if not self.saw_method:
                self.saw_method = True

    # * method: apply_block
    def apply_block(self, next_lexpos: int, lineno: int, result: List[TokenAggregate]) -> None:
        '''
        Apply any necessary INDENT/DEDENT tokens based on the next token's lexpos.
        '''
        
        # Get the current column for the next token.
        current_col = self.find_column(next_lexpos)

        # If this token is less than self.current_col, we need to inject DEDENT(s) for each level of indentation we've exited.
        if current_col < self.current_col:
            no_of_dedents = (self.current_col - current_col) // TAB_SIZE
            result.extend([TokenAggregate.new_dedent(lineno, next_lexpos)] * no_of_dedents)

            # Update current_col to the next token's column after processing.
            self.current_col = current_col

        # If this token is greater than self.current_col, we need to check if we should inject an INDENT for a new class or method body.
        elif current_col > self.current_col:

            # If we previously saw a class or method declaration before the new line, inject an INDENT for it.
            if self.saw_class or self.saw_method:
                result.append(TokenAggregate.new_indent(lineno, next_lexpos))
                self.saw_class = False
                self.saw_method = False

                # Update current_col to the next token's column after processing.
                self.current_col = current_col

    # * method: flush_dedents_for_boundary
    def flush_dedents_for_boundary(self) -> List[TokenAggregate]:
        '''
        Return all pending DEDENT tokens for a boundary and clear state.
        '''
        dedents: List[TokenAggregate] = []

        # If we are at the end of the file and there are still open indents, we need to close them all.
        if self.current_col > 0:
            dedents.extend([TokenAggregate.new_dedent()] * (self.current_col // TAB_SIZE))
            self.current_col = 0

        return dedents

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
    def __init__(self, include_indent_dedent: bool = True):
        '''
        Initialize the TiferetLexer and build the PLY lexer instance.

        :param include_indent_dedent: Whether to include INDENT/DEDENT tokens in the output stream.
        :type include_indent_dedent: bool
        '''

        self.include_indent_dedent = include_indent_dedent

        # Load rules dynamically from the assets mapping.
        for name, rule in a.lexer.RULES.items():
            if callable(rule):
                setattr(self, name, MethodType(rule, self))
            else:
                setattr(self, name, rule)

        # Build the PLY lexer from this module's token rules.
        self.lexer = Lex(module=self)

    # * method: t_error
    def t_error(self, t: LexToken) -> LexToken:
        '''
        Handle unrecognized characters by emitting UNKNOWN tokens.
        
        :param t: The LexToken that caused the error.
        :type t: LexToken
        :return: An UNKNOWN token with the same value and position as the original token.
        :rtype: LexToken
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
            tracker.process_token(token, result)

            # If we are configured to include INDENT/DEDENT tokens and this token starts a new line,
            # check if we need to inject INDENT/DEDENT before adding the token itself.
            if self.include_indent_dedent and token.lineno > prev_lineno:

                # Continue the loop if the token is a NEWLINE, as we want to inject INDENT after it, not before.
                if token.type == a.lexer.NEWLINE:
                    prev_lineno = token.lineno
                    result.append(token)
                    continue

                # Apply block logic for the new line before appending the token.
                tracker.apply_block(token.lexpos, token.lineno, result)

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

        result.extend(tracker.flush_dedents_for_boundary())
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