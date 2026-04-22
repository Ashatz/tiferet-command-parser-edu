# Context-Free Grammar Specification

This grammar defines the **Tiferet Domain Event dialect** — a highly structured subset of Python 3.10+ used within the Tiferet framework for Domain-Driven Design. The grammar is organized around Tiferet's three-tier artifact comment hierarchy (`# ***` groups → `# **` sections → `# *` members), with class definitions, methods, typed attribute declarations, and import statements as the structural building blocks. Method bodies are parsed as sequences of **code snippets** — optional `LINE_COMMENT` headers followed by one or more statements — and statement internals are parsed with a full **PEMDAS-correct expression hierarchy** that includes bitwise shift operators (`<<`, `>>`), comparison operators, call expressions, assignments, and dotted name references.

The grammar distinguishes ordinary imports (`IMPORT ImportExpr`) from relative / `from`-imports (`FROM FromExpr IMPORT ImportExpr`) and decomposes each into structured expression nodes. `OBSOLETE` and `TODO` annotations are modeled as optional prefixes or suffixes at both the section and member tiers. Synthetic `INDENT`/`DEDENT` tokens — injected by `BlockTracker` during lexing — serve as block delimiters for class bodies and method bodies.

## Formal Definition

The grammar G is a 4-tuple (V, Σ, R, S):

### V (Variables/Non-terminals):

```
V = { Module,
      GroupList, Group, GroupHeader,
      SectionList, Section, SectionHeader, Annots, Annot,
      SectionBody, ImportBlock, ImportStmt, ImportExpr, FromExpr,
      ClassDef, ClassBody, SuperClsList, SuperCls,
      MemberList, Member, MemberStmt,
      AttrDecl, AttrTypes,
      Decorator, DecoratorCall, DecoratorIdent, DecoratorArgs, DecoratorArg,
      MethodDecl, MethodName, MethodType, MethodDocString,
      MethodParamList, ParamList, Param, ParamTypes,
      RetAnnot, RetTypes,
      SnippetList, Snippet, CommentList, CommentStmt,
      StmtList, Stmt, AssignExpr, AssignRHS, ReturnExpr,
      OperationExpr, ComparisonExpr, CompOp,
      ShiftExpr, AdditiveExpr, MultiplicativeExpr, ExponentialExpr,
      CallExpr, CallArgs, CallArg,
      NameOrLiteral, LiteralExpr, IdentExpr, Ident, IdentDot }
```

**62 non-terminals** organized into six layers. The table below groups them by role:

| Non-terminal | Layer | Description |
|---|---|---|
| Module | Tier 1 | Root of the parse tree; represents an entire source file (optionally preceded by a module docstring). |
| GroupList | Tier 1 | Zero or more top-level artifact groups. |
| Group | Tier 1 | A single `# ***` artifact group with its header and child sections. |
| GroupHeader | Tier 1 | The opening marker of a group (`ARTIFACT_IMPORTS_START` or `ARTIFACT_START`). |
| SectionList | Tier 2 | Zero or more artifact sections within a group. |
| Section | Tier 2 | A single `# **` artifact section with optional annotations, header, and body. |
| SectionHeader | Tier 2 | The opening marker of a section (`ARTIFACT_SECTION` or `ARTIFACT_IMPORT_GROUP`). |
| Annots | Tier 2 | One or more annotations (`OBSOLETE`/`TODO`) attached before or after a section or member header. |
| Annot | Tier 2 | A single annotation marker — either `OBSOLETE` or `TODO`. |
| SectionBody | Tier 2 | The content of a section: a class definition or an import block. |
| ImportBlock | Tier 2 | One or more import statements within an import-group section. |
| ImportStmt | Tier 2 | A single `import` or `from … import` statement. |
| ImportExpr | Tier 2 | The imported name(s): a bare identifier, an aliased identifier, or a comma-separated multi-import. |
| FromExpr | Tier 2 | The module path in a `from … import` statement, supporting leading dots (relative imports) and dotted paths. |
| ClassDef | Tier 3 | A class definition with inheritance list, optional docstring, and member list. |
| ClassBody | Tier 3 | The interior of a class: optional docstring followed by artifact members. |
| SuperClsList | Tier 3 | The base-class list inside the class signature (may be empty). |
| SuperCls | Tier 3 | A single base class identifier (or comma-chained sequence). |
| MemberList | Tier 3 | Zero or more `# *` artifact members within a class body. |
| Member | Tier 3 | A single artifact member with optional annotations and its body. |
| MemberStmt | Tier 3 | The content of a member: an attribute declaration, a method declaration, or a decorator chain wrapping another member statement. |
| AttrDecl | Tier 3 | An attribute declaration (name, optional `:` type annotation). |
| AttrTypes | Tier 3 | A pipe-separated union type annotation on an attribute (e.g. `int | str`). |
| Decorator | Tier 3 | A decorator line (`@` followed by a call expression). |
| DecoratorCall | Tier 3 | The call form of a decorator: `ident(args)`. |
| DecoratorIdent | Tier 3 | The decorator's target name, with optional dotted access (`a.b.c`). |
| DecoratorArgs | Tier 3 | Zero or more comma-separated decorator arguments. |
| DecoratorArg | Tier 3 | A single decorator argument (name or literal). |
| MethodDecl | Tier 3 | A method declaration: `def`, name, parameter list, optional return annotation, body. |
| MethodName | Tier 3 | The name of a method: an `IDENTIFIER` or the `INIT` keyword. |
| MethodType | Tier 3 | The parenthesized parameter list plus return annotation (the method's type signature). |
| MethodDocString | Tier 3 | An optional `DOCSTRING` at the head of the method body. |
| MethodParamList | Tier 3 | The parameter list with `SELF` as the mandatory first parameter. |
| ParamList | Tier 3 | A linked list of parameters (after `SELF`). |
| Param | Tier 3 | A single parameter: name, optional type annotation, optional default, or `*args`/`**kwargs`. |
| ParamTypes | Tier 3 | A pipe-separated union type annotation on a parameter. |
| RetAnnot | Tier 3 | Optional return-type annotation (`-> type` or ε). |
| RetTypes | Tier 3 | A pipe-separated union return type list. |
| SnippetList | Body | Zero or more code snippets within a method body, tolerating blank lines. |
| Snippet | Body | A logical code unit: an optional `LINE_COMMENT` header followed by statements. |
| CommentList | Body | One or more `LINE_COMMENT` lines that head a snippet. |
| CommentStmt | Body | A single `LINE_COMMENT` followed by a `NEWLINE`. |
| StmtList | Body | Zero or more statements inside a snippet. |
| Stmt | Body | A single statement: `return`, assignment, operation expression, or call. |
| AssignExpr | Expr | An assignment expression `target = rhs`. |
| AssignRHS | Expr | The right-hand side of an assignment (operation or call). |
| ReturnExpr | Expr | The expression returned by a `return` statement (operation, call, or empty). |
| OperationExpr | Expr | The top of the expression precedence hierarchy — currently aliases `ComparisonExpr`. |
| ComparisonExpr | Expr | Comparison-precedence expression (`==`, `!=`, `<`, `>`, `<=`, `>=`, `|`, `&`). |
| CompOp | Expr | A single comparison operator terminal. |
| ShiftExpr | Expr | Bitwise shift precedence (`<<`, `>>`), left-associative; sits between comparison and additive precedence. |
| AdditiveExpr | Expr | Additive precedence (`+`, `-`), left-associative. |
| MultiplicativeExpr | Expr | Multiplicative precedence (`*`, `/`, `%`), left-associative. |
| ExponentialExpr | Expr | Exponentiation (`**`), right-associative. |
| CallExpr | Expr | A call expression `ident(args)`. |
| CallArgs | Expr | Zero or more comma-separated call arguments. |
| CallArg | Expr | A single call argument (operation or nested call). |
| NameOrLiteral | Expr | Atom level: either an identifier expression or a literal. |
| LiteralExpr | Expr | A literal: `STRING_LITERAL`, `NUMBER_LITERAL`, `TRUE`, `FALSE`. |
| IdentExpr | Expr | An identifier expression — a plain `Ident` or a dotted `IdentDot`. |
| Ident | Expr | A bare identifier: `IDENTIFIER` or `SELF`. |
| IdentDot | Expr | A dotted name chain (`a.b.c`, `self.x.y`). |

#### Non-terminal Examples

The following examples illustrate what the non-terminals match in real Tiferet source code.

**Tier 1 — Module / Groups**

A source file is a **Module** containing a **GroupList** of two **Groups**, each opened by a **GroupHeader**:

```python path=null start=null
# *** imports          ← GroupHeader (ARTIFACT_IMPORTS_START), begins Group 1
  ...sections...
# *** events           ← GroupHeader (ARTIFACT_START), begins Group 2
  ...sections...
```

The entire file from the first `# ***` to EOF is the Module. An optional module-level `DOCSTRING` may precede the first group.

**Tier 2 — Sections / Imports / Annotations**

Within the `# *** imports` group, each import category is a **Section** opened by a **SectionHeader**. Its **SectionBody** is an **ImportBlock** of one or more **ImportStmts**, each fully decomposed into an **ImportExpr** (and, for `from`-imports, a **FromExpr**):

```python path=null start=null
# ** core                              ← SectionHeader (ARTIFACT_IMPORT_GROUP)
from typing import List, Dict, Any     ← ImportStmt → FROM FromExpr IMPORT ImportExpr
                                            FromExpr   = "typing"
                                            ImportExpr = "List, Dict, Any"

# ** app                               ← SectionHeader (ARTIFACT_IMPORT_GROUP)
from .settings import DomainEvent, a   ← FromExpr = ".settings", ImportExpr = "DomainEvent, a"
from ..domain import Error             ← FromExpr = "..domain",  ImportExpr = "Error"
import tiferet as tif                  ← ImportStmt → IMPORT ImportExpr(ident AS ident)
```

Annotations (**Annots** / **Annot**) may appear either *before* or *after* a section or member header:

```python path=null start=null
# -- obsolete: superseded by ErrorAggregate.rename()   ← Annot (OBSOLETE NEWLINE)
# ** event: rename_error                               ← SectionHeader
```

Post-header annotations appear between the header and the body:

```python path=null start=null
# ** event: rename_error                               ← SectionHeader
# -- obsolete: superseded by ErrorAggregate.rename()   ← Annot (post-header)
class RenameError(DomainEvent):                        ← SectionBody → ClassDef
```

**Tier 3 — Class / Members / Attributes / Methods**

Inside the `# *** events` group, a **Section** whose body is a **ClassDef**. The **SuperClsList** captures base classes. The **ClassBody** contains a `DOCSTRING` followed by a **MemberList**:

```python path=null start=null
# ** event: add_error                              ← Section header
class AddError(DomainEvent):                       ← ClassDef (SuperClsList = [DomainEvent])
    """Command to add a new Error..."""            ← DOCSTRING (part of ClassBody)

    # * attribute: error_service                   ← Member header (ARTIFACT_MEMBER)
    error_service: ErrorService                    ← MemberStmt → AttrDecl
                                                        AttrDecl → IDENTIFIER COLON AttrTypes

    # * init                                       ← Member header
    def __init__(self, error_service: ErrorService):  ← MemberStmt → MethodDecl
                                                          MethodName = INIT
                                                          MethodParamList = SELF COMMA ParamList
        ...

    # * method: execute                            ← Member header
    @DomainEvent.parameters_required(...)          ← Decorator (AT DecoratorCall)
    def execute(self, id: str, ...) -> None:       ← MethodDecl with RetAnnot = "-> None"
        ...                                            MethodName = IDENTIFIER("execute")
```

**Body / Snippets / Statements / Expressions**

Inside the `execute` method, the body begins with an optional `DOCSTRING` (captured by **MethodDocString**) followed by a **SnippetList**. Each **Snippet** is an optional **CommentList** header and a **StmtList**:

```python path=null start=null
        """Add a new Error to the app..."""       ← MethodDocString (DOCSTRING NEWLINE)

        # Check if an error with the same ID already exists.   ← CommentStmt (Snippet header)
        exists = self.error_service.exists(id)                 ← Stmt → AssignExpr NEWLINE
                                                                   target = IdentExpr("exists")
                                                                   rhs = CallExpr(self.error_service.exists, [id])

        # Create the Error aggregate.                          ← CommentStmt (next Snippet header)
        result = x + y * 3 - 2                                 ← Stmt with PEMDAS expression
                                                                   AdditiveExpr(AdditiveExpr(x, +, MultiplicativeExpr(y, *, 3)), -, 2)
```

**Expression Layer**

A statement like `result = (a << 2) + b * c ** 2` decomposes through the precedence hierarchy as:

```
AssignExpr
 ├── IdentExpr("result")
 └── AdditiveExpr
      ├── ShiftExpr(IdentExpr("a"), LSHIFT, LiteralExpr(2))
      └── MultiplicativeExpr
           ├── IdentExpr("b")
           └── ExponentialExpr(IdentExpr("c"), DOUBLESTAR, LiteralExpr(2))
```

Each precedence level corresponds to a distinct non-terminal; recursion direction determines associativity (`ShiftExpr`, `AdditiveExpr`, `MultiplicativeExpr` are left-recursive; `ExponentialExpr` is right-recursive).

### Σ (Terminals):

All 58 token types produced by the scanner, including synthetic `INDENT`/`DEDENT`:

```
Σ = { ARTIFACT_IMPORTS_START, ARTIFACT_IMPORT_GROUP, ARTIFACT_START,
      ARTIFACT_SECTION, ARTIFACT_MEMBER, OBSOLETE, TODO,
      DOCSTRING, LINE_COMMENT,
      FROM, IMPORT, AS,
      CLASS, DEF, INIT, RETURN, SELF,
      PYTHON_KEYWORD, IDENTIFIER, STRING_LITERAL, NUMBER_LITERAL,
      TRUE, FALSE,
      DOUBLESTAR, PLUS, MINUS, STAR, SLASH, DOUBLESLASH, PERCENT,
      PIPE, AMPERSAND, TILDE, CARET, LSHIFT, RSHIFT,
      EQEQ, NOTEQ, LTEQ, GTEQ, LT, GT, AT,
      LPAREN, RPAREN, LBRACK, RBRACK, LBRACE, RBRACE,
      COMMA, COLON, ARROW, DOT, EQUALS,
      NEWLINE, UNKNOWN, INDENT, DEDENT }
```

Terminals are partitioned by role:

- **Structural tier markers** — `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`, `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`. These are the tier-1/2/3 hierarchy delimiters.
- **Annotation markers** — `OBSOLETE`, `TODO`.
- **Keywords** — `CLASS`, `DEF`, `INIT`, `RETURN`, `SELF`, `FROM`, `IMPORT`, `AS`, `TRUE`, `FALSE`. `PYTHON_KEYWORD` catches all other Python keywords (`if`, `else`, `for`, etc.), currently reserved for future extension.
- **Atoms** — `IDENTIFIER`, `STRING_LITERAL`, `NUMBER_LITERAL`, `DOCSTRING`.
- **Operators** — arithmetic (`PLUS`, `MINUS`, `STAR`, `SLASH`, `DOUBLESLASH`, `PERCENT`, `DOUBLESTAR`), bitwise (`PIPE`, `AMPERSAND`, `TILDE`, `CARET`, `LSHIFT`, `RSHIFT`), comparison (`EQEQ`, `NOTEQ`, `LT`, `GT`, `LTEQ`, `GTEQ`), and other (`AT`).
- **Delimiters** — `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`, `COMMA`, `COLON`, `ARROW`, `DOT`, `EQUALS`.
- **Layout** — `NEWLINE`, `INDENT`, `DEDENT` (the latter two synthesized by `BlockTracker`).
- **Documentation / comments** — `LINE_COMMENT`, `DOCSTRING`.
- **Misc** — `UNKNOWN` (reserved for unrecognized input).

`DOUBLESLASH`, `TILDE`, and `CARET` are tokenized by the lexer but currently unused by the parser; they are reserved for future grammar extensions (floor division, bitwise not, xor).

### S (Start Symbol):

```
S = Module
```

### R (Production Rules):

#### Tier 1 — Module / Artifact Groups

```ebnf
(1)  Module       --> GroupList
(2)  Module       --> DOCSTRING NEWLINE Module
(3)  GroupList    --> GroupList Group
(4)  GroupList    --> ε
(5)  Group        --> GroupHeader NEWLINE SectionList
(6)  GroupHeader  --> ARTIFACT_IMPORTS_START
(7)  GroupHeader  --> ARTIFACT_START
```

#### Tier 2 — Artifact Sections and Annotations

```ebnf
(8)  SectionList  --> SectionList Section
(9)  SectionList  --> ε
(10) Section      --> SectionHeader NEWLINE SectionBody
(11) Section      --> Annots SectionHeader NEWLINE SectionBody
(12) Section      --> SectionHeader NEWLINE Annots SectionBody
(13) SectionHeader --> ARTIFACT_SECTION
(14) SectionHeader --> ARTIFACT_IMPORT_GROUP
(15) Annots       --> Annot
(16) Annots       --> Annots Annot
(17) Annot        --> OBSOLETE NEWLINE
(18) Annot        --> TODO NEWLINE
```

#### Section Body

```ebnf
(19) SectionBody  --> ClassDef
(20) SectionBody  --> ImportBlock
```

#### Import Statements

```ebnf
(21) ImportBlock  --> ImportStmt
(22) ImportBlock  --> ImportBlock ImportStmt
(23) ImportStmt   --> IMPORT ImportExpr NEWLINE
(24) ImportStmt   --> FROM FromExpr IMPORT ImportExpr NEWLINE
(25) ImportExpr   --> IDENTIFIER
(26) ImportExpr   --> ImportExpr AS IDENTIFIER
(27) ImportExpr   --> ImportExpr COMMA IDENTIFIER
(28) FromExpr     --> IDENTIFIER
(29) FromExpr     --> DOT FromExpr
(30) FromExpr     --> FromExpr DOT IDENTIFIER
```

Rule 29 captures the leading-dot prefix used in relative imports (e.g. `from .settings`, `from ..domain`); rule 30 chains the module path (`a.b.c`); rule 27 captures multi-import lists (`import a, b, c`).

#### Class Definition

```ebnf
(31) ClassDef     --> CLASS IDENTIFIER LPAREN SuperClsList RPAREN COLON NEWLINE INDENT ClassBody DEDENT
(32) ClassBody    --> DOCSTRING NEWLINE MemberList
(33) ClassBody    --> MemberList
(34) SuperClsList --> ε
(35) SuperClsList --> SuperCls
(36) SuperCls     --> IDENTIFIER
(37) SuperCls     --> SuperCls COMMA SuperCls
```

#### Tier 3 — Artifact Members

```ebnf
(38) MemberList   --> Member
(39) MemberList   --> MemberList Member
(40) MemberList   --> ε
(41) Member       --> ARTIFACT_MEMBER NEWLINE MemberStmt
(42) Member       --> Annots ARTIFACT_MEMBER NEWLINE MemberStmt
(43) Member       --> ARTIFACT_MEMBER NEWLINE Annots MemberStmt
(44) MemberStmt   --> AttrDecl
(45) MemberStmt   --> MethodDecl
(46) MemberStmt   --> Decorator NEWLINE MemberStmt
```

Rule 46 recurses, allowing any number of decorators to stack above an attribute or method body.

#### Attribute Declaration

```ebnf
(47) AttrDecl     --> IDENTIFIER NEWLINE
(48) AttrDecl     --> IDENTIFIER COLON AttrTypes NEWLINE
(49) AttrTypes    --> IDENTIFIER
(50) AttrTypes    --> AttrTypes PIPE IDENTIFIER
```

#### Decorators

```ebnf
(51) Decorator      --> AT DecoratorCall
(52) DecoratorCall  --> DecoratorIdent LPAREN DecoratorArgs RPAREN
(53) DecoratorIdent --> IDENTIFIER
(54) DecoratorIdent --> DecoratorIdent DOT IDENTIFIER
(55) DecoratorArgs  --> DecoratorArg
(56) DecoratorArgs  --> DecoratorArgs COMMA DecoratorArg
(57) DecoratorArg   --> NameOrLiteral
```

#### Method Definition

```ebnf
(58) MethodDecl       --> DEF MethodName MethodType COLON NEWLINE INDENT MethodDocString SnippetList DEDENT
(59) MethodName       --> IDENTIFIER
(60) MethodName       --> INIT
(61) MethodType       --> LPAREN MethodParamList RPAREN RetAnnot
(62) MethodDocString  --> DOCSTRING NEWLINE
(63) MethodDocString  --> ε
```

#### Parameters and Type Annotations

```ebnf
(64) MethodParamList --> SELF
(65) MethodParamList --> SELF COMMA ParamList
(66) ParamList       --> Param
(67) ParamList       --> ParamList COMMA Param
(68) Param           --> IDENTIFIER
(69) Param           --> STAR IDENTIFIER
(70) Param           --> DOUBLESTAR IDENTIFIER
(71) Param           --> Param COLON ParamTypes
(72) Param           --> Param EQUALS NameOrLiteral
(73) Param           --> NEWLINE Param
(74) ParamTypes      --> IDENTIFIER
(75) ParamTypes      --> ParamTypes PIPE IDENTIFIER
(76) RetAnnot        --> ARROW RetTypes
(77) RetAnnot        --> ε
(78) RetTypes        --> IDENTIFIER
(79) RetTypes        --> RetTypes PIPE IDENTIFIER
```

Rule 73 tolerates `NEWLINE` between parameters, supporting multi-line signatures.

#### Method Body — Snippets

```ebnf
(80) SnippetList  --> SnippetList Snippet
(81) SnippetList  --> SnippetList NEWLINE
(82) SnippetList  --> ε
(83) Snippet      --> CommentList StmtList
(84) Snippet      --> StmtList
(85) CommentList  --> CommentStmt
(86) CommentList  --> CommentList CommentStmt
(87) CommentStmt  --> LINE_COMMENT NEWLINE
```

Rule 81 consumes stray blank lines between snippets; rule 80 is the productive recursion.

#### Statements

```ebnf
(88) StmtList     --> Stmt
(89) StmtList     --> StmtList Stmt
(90) StmtList     --> ε
(91) Stmt         --> RETURN ReturnExpr NEWLINE
(92) Stmt         --> AssignExpr NEWLINE
(93) Stmt         --> OperationExpr NEWLINE
(94) Stmt         --> CallExpr NEWLINE
```

#### Expressions — Assignment and Return

```ebnf
(95)  AssignExpr  --> IdentExpr EQUALS AssignRHS
(96)  AssignRHS   --> OperationExpr
(97)  AssignRHS   --> CallExpr
(98)  ReturnExpr  --> OperationExpr
(99)  ReturnExpr  --> CallExpr
(100) ReturnExpr  --> ε
```

#### Expressions — PEMDAS Hierarchy with Bitwise Shift

```ebnf
(101) OperationExpr      --> ComparisonExpr
(102) ComparisonExpr     --> ShiftExpr CompOp ShiftExpr
(103) ComparisonExpr     --> ShiftExpr
(104) CompOp             --> EQEQ | NOTEQ | LT | GT | LTEQ | GTEQ | PIPE | AMPERSAND

(105) ShiftExpr          --> ShiftExpr LSHIFT AdditiveExpr         (* left-associative *)
(106) ShiftExpr          --> ShiftExpr RSHIFT AdditiveExpr
(107) ShiftExpr          --> AdditiveExpr

(108) AdditiveExpr       --> AdditiveExpr PLUS MultiplicativeExpr  (* left-associative *)
(109) AdditiveExpr       --> AdditiveExpr MINUS MultiplicativeExpr
(110) AdditiveExpr       --> MultiplicativeExpr

(111) MultiplicativeExpr --> MultiplicativeExpr STAR ExponentialExpr  (* left-associative *)
(112) MultiplicativeExpr --> MultiplicativeExpr SLASH ExponentialExpr
(113) MultiplicativeExpr --> MultiplicativeExpr PERCENT ExponentialExpr
(114) MultiplicativeExpr --> ExponentialExpr

(115) ExponentialExpr    --> NameOrLiteral DOUBLESTAR ExponentialExpr  (* right-associative *)
(116) ExponentialExpr    --> NameOrLiteral
```

Precedence from lowest to highest: **comparison → shift → additive → multiplicative → exponential → call → atom**. The `ShiftExpr` layer was introduced to support AST-level strength reduction (rewriting multiplication/division by a power of two into `<<` / `>>`).

#### Expressions — Calls and Atoms

```ebnf
(117) CallExpr       --> IdentExpr LPAREN CallArgs RPAREN
(118) CallArgs       --> ε
(119) CallArgs       --> CallArg
(120) CallArgs       --> CallArgs COMMA CallArg
(121) CallArg        --> OperationExpr
(122) CallArg        --> CallExpr

(123) NameOrLiteral  --> IdentExpr
(124) NameOrLiteral  --> LiteralExpr
(125) LiteralExpr    --> STRING_LITERAL
(126) LiteralExpr    --> NUMBER_LITERAL
(127) LiteralExpr    --> TRUE
(128) LiteralExpr    --> FALSE

(129) IdentExpr      --> Ident
(130) IdentExpr      --> IdentDot
(131) Ident          --> IDENTIFIER
(132) Ident          --> SELF
(133) IdentDot       --> Ident DOT IDENTIFIER
(134) IdentDot       --> IdentDot DOT IDENTIFIER
```

Rule 133/134 support arbitrarily long dotted chains (`a.b.c.d`, `self.service.method`).

## LR(1) Automaton

The full grammar has 134 productions. For pedagogical purposes, the LR(1) automaton is constructed from a **core subset** capturing the three-tier artifact comment hierarchy. This subset uses 10 production rules and 5 terminals, producing 17 canonical LR(1) states.

### Core Subset Grammar

The following subset extracts the structural skeleton of the full grammar — groups contain sections, sections contain members:

```ebnf
(0)  S'          --> Module
(1)  Module      --> GroupList
(2)  GroupList   --> Group
(3)  GroupList   --> GroupList Group
(4)  Group       --> ARTIFACT_START NEWLINE SectionList
(5)  SectionList --> Section
(6)  SectionList --> SectionList Section
(7)  Section     --> ARTIFACT_SECTION NEWLINE MemberList
(8)  MemberList  --> Member
(9)  MemberList  --> MemberList Member
(10) Member      --> ARTIFACT_MEMBER NEWLINE
```

**Terminals:** `{ ARTIFACT_START, ARTIFACT_SECTION, ARTIFACT_MEMBER, NEWLINE, $ }`
**Non-terminals:** `{ Module, GroupList, Group, SectionList, Section, MemberList, Member }`

Abbreviations used below: **AS** = ARTIFACT_START, **ASEC** = ARTIFACT_SECTION, **AM** = ARTIFACT_MEMBER, **NL** = NEWLINE.

### FIRST and FOLLOW Sets

```
FIRST(Module)      = { AS }
FIRST(GroupList)   = { AS }
FIRST(Group)       = { AS }
FIRST(SectionList) = { ASEC }
FIRST(Section)     = { ASEC }
FIRST(MemberList)  = { AM }
FIRST(Member)      = { AM }

FOLLOW(Module)      = { $ }
FOLLOW(GroupList)   = { $, AS }
FOLLOW(Group)       = { $, AS }
FOLLOW(SectionList) = { $, AS, ASEC }
FOLLOW(Section)     = { $, AS, ASEC }
FOLLOW(MemberList)  = { $, AS, ASEC, AM }
FOLLOW(Member)      = { $, AS, ASEC, AM }
```

### Canonical LR(1) Item Sets

**State I0** — Initial state
```
[S' → • Module, $]
[Module → • GroupList, $]
[GroupList → • Group, {$, AS}]
[GroupList → • GroupList Group, {$, AS}]
[Group → • AS NL SectionList, {$, AS}]
```
Transitions: Module → I1, GroupList → I2, Group → I3, AS → I4

**State I1** — Accept
```
[S' → Module •, $]
```
Action: **accept** on $

**State I2** — GroupList complete or continuing
```
[Module → GroupList •, $]
[GroupList → GroupList • Group, {$, AS}]
[Group → • AS NL SectionList, {$, AS}]
```
Transitions: AS → I4, Group → I14

**State I3** — Single Group reduced
```
[GroupList → Group •, {$, AS}]
```
Action: reduce (2) on {$, AS}

**State I4** — Shifted ARTIFACT_START
```
[Group → AS • NL SectionList, {$, AS}]
```
Transitions: NL → I5

**State I5** — Inside Group, expecting SectionList
```
[Group → AS NL • SectionList, {$, AS}]
[SectionList → • Section, {$, AS, ASEC}]
[SectionList → • SectionList Section, {$, AS, ASEC}]
[Section → • ASEC NL MemberList, {$, AS, ASEC}]
```
Transitions: SectionList → I6, Section → I7, ASEC → I8

**State I6** — SectionList complete or continuing
```
[Group → AS NL SectionList •, {$, AS}]
[SectionList → SectionList • Section, {$, AS, ASEC}]
[Section → • ASEC NL MemberList, {$, AS, ASEC}]
```
Transitions: ASEC → I8, Section → I15

**State I7** — Single Section reduced
```
[SectionList → Section •, {$, AS, ASEC}]
```
Action: reduce (5) on {$, AS, ASEC}

**State I8** — Shifted ARTIFACT_SECTION
```
[Section → ASEC • NL MemberList, {$, AS, ASEC}]
```
Transitions: NL → I9

**State I9** — Inside Section, expecting MemberList
```
[Section → ASEC NL • MemberList, {$, AS, ASEC}]
[MemberList → • Member, {$, AS, ASEC, AM}]
[MemberList → • MemberList Member, {$, AS, ASEC, AM}]
[Member → • AM NL, {$, AS, ASEC, AM}]
```
Transitions: MemberList → I10, Member → I11, AM → I12

**State I10** — MemberList complete or continuing
```
[Section → ASEC NL MemberList •, {$, AS, ASEC}]
[MemberList → MemberList • Member, {$, AS, ASEC, AM}]
[Member → • AM NL, {$, AS, ASEC, AM}]
```
Transitions: AM → I12, Member → I16

**State I11** — Single Member reduced
```
[MemberList → Member •, {$, AS, ASEC, AM}]
```
Action: reduce (8) on {$, AS, ASEC, AM}

**State I12** — Shifted ARTIFACT_MEMBER
```
[Member → AM • NL, {$, AS, ASEC, AM}]
```
Transitions: NL → I13

**State I13** — Member complete
```
[Member → AM NL •, {$, AS, ASEC, AM}]
```
Action: reduce (10) on {$, AS, ASEC, AM}

**State I14** — GroupList extended by Group
```
[GroupList → GroupList Group •, {$, AS}]
```
Action: reduce (3) on {$, AS}

**State I15** — SectionList extended by Section
```
[SectionList → SectionList Section •, {$, AS, ASEC}]
```
Action: reduce (6) on {$, AS, ASEC}

**State I16** — MemberList extended by Member
```
[MemberList → MemberList Member •, {$, AS, ASEC, AM}]
```
Action: reduce (9) on {$, AS, ASEC, AM}

### State Transition Diagram

```
                    Module        GroupList         Group
          I0 ──────────► I1    I0 ──────────► I2    I0 ─────► I3
                (accept)        │                   (r2)
                                │ AS
          ┌─────────────────────┼──────────────────────────────┐
          │                     ▼                              │
          │                    I4 ──NL──► I5                   │
          │                                │                   │
          │               SectionList      │ Section    ASEC   │
          │              ┌─► I6 ◄──────────┼──► I7    ──► I8   │
          │              │   │             │   (r5)       │    │
          │              │   │ ASEC        │              NL   │
          │              │   ├─────────► I8 ◄─────────────┘    │
          │              │   │ Section     │                   │
          │              │   └──► I15      │                   │
          │              │       (r6)      │                   │
          │              │                 │                   │
          │              │         NL      ▼                   │
          │              │       I8 ────► I9                   │
          │              │                 │                   │
          │              │    MemberList   │ Member     AM     │
          │              │   ┌─► I10 ◄─────┼──► I11   ──► I12  │
          │              │   │   │         │   (r8)       │    │
          │              │   │   │ AM      │              NL   │
          │              │   │   └──► I12 ◄───────────────┘    │
          │              │   │   │ Member  │                   │
          │              │   │   └──► I16  │                   │
          │              │   │       (r9)  │                   │
          │              │   │             │                   │
          │              │   │         NL  ▼                   │
          │              │   │       I12 ─► I13                │
          │              │   │             (r10)               │
          │              │                                     │
          │  Group       │                                     │
          I2 ─────────► I14                                    │
          │             (r3)                                   │
          │ AS                                                 │
          └────────────────────────────────────────────────────┘
                              (shared I4)
```

## LALR Verification

### Item Sets

To merge LR(1) states into LALR states, we look for states with **identical cores** (same items ignoring lookaheads) but **different lookahead sets**.

Examining all 17 states:

| State | Core (dot position) | Lookaheads |
|-------|---------------------|------------|
| I0 | S' → • Module; Module → • GroupList; ... | {$}, {$}, {$,AS}, ... |
| I1 | S' → Module • | {$} |
| I2 | Module → GroupList •; GroupList → GroupList • Group; ... | {$}, {$,AS}, ... |
| I3 | GroupList → Group • | {$, AS} |
| I4 | Group → AS • NL SectionList | {$, AS} |
| I5 | Group → AS NL • SectionList; ... | {$,AS}, ... |
| I6 | Group → AS NL SectionList •; ... | {$,AS}, ... |
| I7 | SectionList → Section • | {$, AS, ASEC} |
| I8 | Section → ASEC • NL MemberList | {$, AS, ASEC} |
| I9 | Section → ASEC NL • MemberList; ... | {$,AS,ASEC}, ... |
| I10 | Section → ASEC NL MemberList •; ... | {$,AS,ASEC}, ... |
| I11 | MemberList → Member • | {$, AS, ASEC, AM} |
| I12 | Member → AM • NL | {$, AS, ASEC, AM} |
| I13 | Member → AM NL • | {$, AS, ASEC, AM} |
| I14 | GroupList → GroupList Group • | {$, AS} |
| I15 | SectionList → SectionList Section • | {$, AS, ASEC} |
| I16 | MemberList → MemberList Member • | {$, AS, ASEC, AM} |

**Result: All 17 states have unique cores.** No two states share the same core with different lookaheads.

This is a consequence of the grammar's clean hierarchical structure — each tier (Group, Section, Member) uses distinct terminal tokens (`ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`), so the parser never reaches the same dot position from different contexts that would produce mergeable states.

**No states can be merged. The LALR automaton is identical to the LR(1) automaton (17 states).**

### Parse Table and Conflict Check

**Action Table** (shift `sN` = shift and go to state N; reduce `rN` = reduce by rule N; `acc` = accept):

```
State │  AS    ASEC    AM     NL     $
──────┼──────────────────────────────────
 I0   │  s4     —      —      —      —
 I1   │  —      —      —      —     acc
 I2   │  s4     —      —      —     r1
 I3   │  r2     —      —      —     r2
 I4   │  —      —      —     s5      —
 I5   │  —     s8      —      —      —
 I6   │  r4    s8      —      —     r4
 I7   │  r5    r5      —      —     r5
 I8   │  —      —      —     s9      —
 I9   │  —      —     s12     —      —
 I10  │  r7    r7     s12     —     r7
 I11  │  r8    r8     r8      —     r8
 I12  │  —      —      —     s13     —
 I13  │ r10   r10    r10      —    r10
 I14  │  r3     —      —      —     r3
 I15  │  r6    r6      —      —     r6
 I16  │  r9    r9     r9      —     r9
```

**Goto Table** (state transitions on non-terminals):

```
State │ Module  GroupList  Group  SectionList  Section  MemberList  Member
──────┼─────────────────────────────────────────────────────────────────────
 I0   │   1        2        3         —          —          —         —
 I2   │   —        —       14         —          —          —         —
 I5   │   —        —        —         6          7          —         —
 I6   │   —        —        —         —         15          —         —
 I9   │   —        —        —         —          —         10        11
 I10  │   —        —        —         —          —          —        16
```

(All other Goto entries are blank / error.)

**Conflict Check:**

Every cell in the Action table contains **at most one action**. There are:
- **No shift-reduce conflicts** — no cell contains both a shift and a reduce.
- **No reduce-reduce conflicts** — no cell contains two different reduce actions.

The key decisions that could have caused conflicts are cleanly resolved by LR(1) lookaheads:
- **I2** on `AS`: shift (start new Group) vs. reduce (Module → GroupList). Resolved: shift on `AS`, reduce on `$`.
- **I6** on `ASEC`: shift (start new Section) vs. reduce (Group complete). Resolved: shift on `ASEC`, reduce on `{$, AS}`.
- **I10** on `AM`: shift (start new Member) vs. reduce (Section complete). Resolved: shift on `AM`, reduce on `{$, AS, ASEC}`.

This pattern reflects the grammar's design: at each tier boundary, the **next-tier token** triggers a shift (deeper nesting), while **same-tier or parent-tier tokens** trigger a reduce (close the current structure).

**The grammar is LALR(1) with zero conflicts.**

### LALR Automaton

Since no states were merged (all 17 LR(1) states have unique cores), the **LALR automaton is identical to the LR(1) automaton** shown above. The 17-state diagram and parse table apply without modification.

## Implementation Notes

Practical guidance for translating this grammar into a PLY `yacc` parser. The authoritative implementation lives in `src/utils/parser.py` — `ParserBase` + `TiferetParser`. See also `Parser/README.md` § 4 for a narrative walkthrough of the PLY conventions in use.

### PLY Adaptation

- **Rule-per-method convention.** Each production is a `p_*` method whose **docstring** holds the rule. PLY parses the docstring (not the method body) to build the LALR(1) automaton; the method body is the semantic action that runs on reduction.
- **Epsilon / empty list rules.** The PLY idiom for list non-terminals uses `list : list item | ε` with the empty alternative as its own `p_*` method (e.g. `p_group_list_empty`, `p_section_list_empty`). Rules 4, 9, 34, 40, 63, 77, 82, 90, 100, and 118 above correspond to these empty productions.
- **Alternative rules.** Multiple right-hand sides for the same non-terminal may share a single `p_*` method (with `|` inside the docstring) when the semantic action is uniform, or be split across several methods when the actions differ. This is a purely stylistic choice; PLY collapses same-name rules at automaton build time.
- **Operator precedence.** The expression grammar encodes precedence **structurally** through the `ComparisonExpr → ShiftExpr → AdditiveExpr → MultiplicativeExpr → ExponentialExpr` chain. Recursion direction selects associativity (left vs. right).

### Precedence Declaration

To prevent shift-reduce ambiguity at structural boundaries, artifact and layout tokens are declared `nonassoc`:

```python path=null start=null
precedence = (
    ('right', 'COLON'),
    ('right', 'ARROW'),
    ('nonassoc', 'ARTIFACT_START', 'ARTIFACT_SECTION', 'ARTIFACT_MEMBER',
                 'OBSOLETE', 'TODO', 'DEDENT'),
)
```

This ensures the parser prefers shifting on structural tokens over reducing, preventing false reductions at tier boundaries.

### Semantic Actions

Parser actions produce a structured intermediate representation via mapper aggregates. AST node structure, type enumerations, and linked-list chaining are documented separately in `SemanticRoutines/README.md` to keep this grammar specification focused on syntax.

Positions (`lineno`, `col`) are stamped on every constructed node using the `pos(p, k)` helper on `ParserBase`, which combines `p.lineno(k)` with a column computed from `p.lexpos(k)` against the stored source text.

### Acceptance Criteria

1. Parser accepts all parser pass samples (`Parser/samples/pass_*.py`) without syntax errors.
2. Parser rejects all parser fail samples with a descriptive `SyntaxError`.
3. Expression precedence is honoured: `x + y * 3 - 2` reduces as `(x + (y * 3)) - 2`, `a * 2**k` reduces as `a * (2**k)`, `a << 2 + b` reduces as `a << (2 + b)`.
4. `from ... import` correctly decomposes leading dots (`from ..domain import Error`) and multi-imports (`from typing import List, Dict, Any`).
5. Typed attribute declarations parse both simple (`error_service: ErrorService`) and union (`value: int | str`) annotations.
6. Method signatures accept `self`-prefixed parameter lists with typed, defaulted, `*args`, and `**kwargs` parameters, across multiple lines.
7. Decorators stack above attribute or method members via the recursive `MemberStmt → Decorator NEWLINE MemberStmt` rule.

## Sample Files

Parser-specific sample files live in `Parser/samples/`. Each file is a focused test case that exercises one or more grammar features.

### Passing Samples

These files conform to the grammar and should be accepted without errors.

| File | Description |
|---|---|
| `pass_imports_only.py` | Imports-only module with `core` and `app` import groups — no event definitions. Exercises Tier 1–2 structure plus full `ImportStmt` / `FromExpr` / `ImportExpr` decomposition (dotted paths, multi-imports). |
| `pass_minimal_event.py` | Simplest valid three-tier program: one import group, one event class with a single `execute` method. Exercises the core Group → Section → Member hierarchy. |
| `pass_minimal_injection_event.py` | Event with attribute, `__init__` member (using the `INIT` keyword), and `execute` method. Exercises `AttrDecl`, `MethodDecl` with `INIT`, `SELF`-prefixed parameter lists, and assignment expressions. |
| `pass_multiple_operator_events.py` | Six arithmetic events (`Add`, `Subtract`, `Multiply`, `Divide`, `Modulus`, `Exponentiate`). Exercises multi-section parsing and every PEMDAS operator (`+`, `-`, `*`, `/`, `%`, `**`). |
| `pass_helper_method_event.py` | Event with a helper method alongside `execute`; body contains chained arithmetic expressions parsed with correct precedence (`x + y * 3 - 2`) and call RHS in assignments. |

### Failing Samples

These files violate the artifact hierarchy and should produce `SyntaxError`. Each targets a specific structural rule.

| File | Violation | Expected Error |
|---|---|---|
| `fail_import_no_group.py` | `from` statement appears directly under `# *** imports` with no `# **` import group header. | SectionList expects ARTIFACT_SECTION or ARTIFACT_IMPORT_GROUP; receives `FROM`. |
| `fail_bare_function.py` | `def` appears directly under `# ***` with no `# **` section header. | SectionList expects ARTIFACT_SECTION; receives `DEF`. |
| `fail_class_no_section.py` | `class` appears directly under `# ***` with no `# **` section header. | SectionList expects ARTIFACT_SECTION; receives `CLASS`. |
| `fail_class_bare_attribute.py` | Typed attribute inside a class with no `# *` member header. | MemberList expects ARTIFACT_MEMBER; receives `IDENTIFIER`. |
| `fail_class_bare_method.py` | `def` inside a class with no `# *` member header. | MemberList expects ARTIFACT_MEMBER; receives `DEF`. |
| `fail_missing_group_header.py` | Content without any `# ***` group header. | Module expects ARTIFACT_START; receives `LINE_COMMENT`. |
| `fail_missing_member_artifact.py` | Method body without `# *` member artifact comment inside a class. | MemberList expects ARTIFACT_MEMBER; receives `LINE_COMMENT`. |
