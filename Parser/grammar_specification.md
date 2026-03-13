# Context-Free Grammar Specification

This grammar defines the **Tiferet Domain Event dialect** — a highly structured subset of Python 3.10+ used within the Tiferet framework for Domain-Driven Design. The grammar is organized around Tiferet's three-tier artifact comment hierarchy (`# ***` groups → `# **` sections → `# *` members), with class definitions, method definitions, standalone function definitions, attribute declarations, and import statements as the structural building blocks. Method and function bodies are parsed as sequences of **code snippets** — optional `LINE_COMMENT` headers followed by one or more statements — rather than full expression trees. Statement internals use a generic flat token sequence (`TokenSeq`) with matched bracket groups to handle multi-line parenthesized expressions.

The grammar distinguishes **MethodDef** (inside a class, parameter list must begin with `SELF`) from **FuncDef** (standalone at the section level, no `SELF` requirement). `OBSOLETE` and `TODO` annotations are modeled as optional prefixes at both the section and member tiers. Synthetic `INDENT`/`DEDENT` tokens serve as block delimiters for class bodies, method bodies, and compound statements (e.g., if-blocks).


## Formal Definition

The grammar G is a 4-tuple (V, Σ, R, S):

### V (Variables/Non-terminals):

```
V = { Module, GroupList, Group, GroupHeader,
      SectionList, Section, SectionHeader, Annots, Annot,
      SectionBody, ImportBlock, ImportStmt,
      ClassDef, ClassBody, NameList,
      MemberList, Member, MemberBody,
      AttrDecl, MethodDef, MethodName, ParamTail, RetAnnot, Decorator,
      FuncDef, ParamBody,
      Body, SnippetList, Snippet, StmtList, Stmt,
      TokenSeq, TokenItem, Enclosed, Inner, InnerItem, Token }
```

**36 non-terminals** organized into four layers:
- **Tier 1 (Module/Groups):** Module, GroupList, Group, GroupHeader
- **Tier 2 (Sections):** SectionList, Section, SectionHeader, Annots, Annot, SectionBody, ImportBlock, ImportStmt
- **Tier 3 (Members):** MemberList, Member, MemberBody, AttrDecl, MethodDef, MethodName, Decorator, FuncDef
- **Body/Snippet/Token:** Body, SnippetList, Snippet, StmtList, Stmt, TokenSeq, TokenItem, Enclosed, Inner, InnerItem, Token

### Σ (Terminals):

All 53 token types produced by the scanner (including synthetic INDENT/DEDENT):

```
Σ = { ARTIFACT_IMPORTS_START, ARTIFACT_IMPORT_GROUP, ARTIFACT_START,
      ARTIFACT_SECTION, ARTIFACT_MEMBER, OBSOLETE, TODO,
      DOCSTRING, LINE_COMMENT,
      CLASS, DEF, INIT, RETURN, SELF,
      PYTHON_KEYWORD, IDENTIFIER, STRING_LITERAL, NUMBER_LITERAL,
      DOUBLESTAR, PLUS, MINUS, STAR, SLASH, DOUBLESLASH, PERCENT,
      PIPE, AMPERSAND, TILDE, CARET, LSHIFT, RSHIFT,
      EQEQ, NOTEQ, LTEQ, GTEQ, LT, GT, AT,
      LPAREN, RPAREN, LBRACK, RBRACK, LBRACE, RBRACE,
      COMMA, COLON, ARROW, DOT, EQUALS,
      NEWLINE, UNKNOWN, INDENT, DEDENT }
```

Terminals are partitioned into two roles:
- **Structural terminals** — appear explicitly in grammar productions as delimiters, headers, or keywords: all ARTIFACT_* tokens, OBSOLETE, TODO, DOCSTRING, LINE_COMMENT, CLASS, DEF, INIT, SELF, AT, LPAREN, RPAREN, LBRACK, RBRACK, LBRACE, RBRACE, COLON, ARROW, COMMA, NEWLINE, INDENT, DEDENT.
- **Content terminals** — consumed by the `Token` non-terminal as generic content within `TokenSeq`: IDENTIFIER, RETURN, PYTHON_KEYWORD, STRING_LITERAL, NUMBER_LITERAL, DOT, EQUALS, all operators, UNKNOWN, and structural keywords when they appear inside token sequences.

### S (Start Symbol):

```
S = Module
```

### R (Production Rules):

#### Tier 1 — Module / Artifact Groups

```ebnf
(1)  Module       --> GroupList
(2)  GroupList    --> Group
(3)  GroupList    --> GroupList Group
(4)  Group        --> GroupHeader NEWLINE SectionList
(5)  GroupHeader  --> ARTIFACT_IMPORTS_START
(6)  GroupHeader  --> ARTIFACT_START
```

#### Tier 2 — Artifact Sections

```ebnf
(7)  SectionList  --> Section
(8)  SectionList  --> SectionList Section
(9)  Section      --> SectionHeader NEWLINE SectionBody
(10) Section      --> Annots SectionHeader NEWLINE SectionBody
(11) SectionHeader --> ARTIFACT_SECTION
(12) SectionHeader --> ARTIFACT_IMPORT_GROUP
(13) Annots       --> Annot
(14) Annots       --> Annots Annot
(15) Annot        --> OBSOLETE NEWLINE
(16) Annot        --> TODO NEWLINE
```

#### Section Body

```ebnf
(17) SectionBody  --> ClassDef
(18) SectionBody  --> FuncDef
(19) SectionBody  --> ImportBlock
(20) ImportBlock  --> ImportStmt
(21) ImportBlock  --> ImportBlock ImportStmt
(22) ImportStmt   --> PYTHON_KEYWORD TokenSeq NEWLINE
```

#### Class Definition

```ebnf
(23) ClassDef     --> CLASS IDENTIFIER LPAREN NameList RPAREN COLON NEWLINE INDENT ClassBody DEDENT
(24) ClassBody    --> DOCSTRING NEWLINE MemberList
(25) ClassBody    --> MemberList
(26) NameList     --> IDENTIFIER
(27) NameList     --> NameList COMMA IDENTIFIER
```

#### Tier 3 — Artifact Members

```ebnf
(28) MemberList   --> Member
(29) MemberList   --> MemberList Member
(30) Member       --> ARTIFACT_MEMBER NEWLINE MemberBody
(31) Member       --> Annots ARTIFACT_MEMBER NEWLINE MemberBody
(32) MemberBody   --> AttrDecl
(33) MemberBody   --> MethodDef
(34) AttrDecl     --> IDENTIFIER COLON TokenSeq NEWLINE
```

#### Method Definition (inside class — requires SELF)

```ebnf
(35) MethodDef    --> DEF MethodName LPAREN SELF ParamTail RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
(36) MethodDef    --> Decorator DEF MethodName LPAREN SELF ParamTail RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
(37) MethodName   --> IDENTIFIER
(38) MethodName   --> INIT
(39) ParamTail    --> COMMA TokenSeq
(40) ParamTail    --> ε
(41) RetAnnot     --> ARROW TokenSeq
(42) RetAnnot     --> ε
(43) Decorator    --> AT TokenSeq NEWLINE
```

#### Function Definition (standalone at section level — no SELF)

```ebnf
(44) FuncDef      --> DEF IDENTIFIER LPAREN ParamBody RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
(45) FuncDef      --> Decorator DEF IDENTIFIER LPAREN ParamBody RPAREN RetAnnot COLON NEWLINE INDENT Body DEDENT
(46) ParamBody    --> TokenSeq
(47) ParamBody    --> ε
```

#### Method/Function Body — Snippets

```ebnf
(48) Body         --> DOCSTRING NEWLINE SnippetList
(49) Body         --> SnippetList
(50) SnippetList  --> Snippet
(51) SnippetList  --> SnippetList Snippet
(52) Snippet      --> LINE_COMMENT NEWLINE StmtList
(53) Snippet      --> StmtList
(54) StmtList     --> Stmt
(55) StmtList     --> StmtList Stmt
(56) Stmt         --> TokenSeq NEWLINE
(57) Stmt         --> TokenSeq NEWLINE INDENT StmtList DEDENT
```

Rule 56 covers simple statements (assignments, return, expression calls). Rule 57 covers compound statements (if-blocks, for-loops, etc.) where the header line is followed by an indented body.

#### Token Sequence — Generic Content

```ebnf
(58) TokenSeq     --> TokenItem
(59) TokenSeq     --> TokenSeq TokenItem
(60) TokenItem    --> Token
(61) TokenItem    --> Enclosed
(62) Enclosed     --> LPAREN Inner RPAREN
(63) Enclosed     --> LBRACK Inner RBRACK
(64) Enclosed     --> LBRACE Inner RBRACE
(65) Inner        --> InnerItem Inner
(66) Inner        --> ε
(67) InnerItem    --> TokenItem
(68) InnerItem    --> NEWLINE
```

`Enclosed` handles multi-line parenthesized expressions by allowing `NEWLINE` inside matched brackets (rules 62–68). Outside brackets, `NEWLINE` terminates a statement (rule 56–57).

#### Token — Content Terminals

```ebnf
(69) Token --> IDENTIFIER | SELF | INIT | RETURN | CLASS | DEF
            | STRING_LITERAL | NUMBER_LITERAL | DOCSTRING
            | PYTHON_KEYWORD
            | DOT | COMMA | COLON | EQUALS | ARROW
            | PLUS | MINUS | STAR | DOUBLESTAR | SLASH | DOUBLESLASH | PERCENT
            | PIPE | AMPERSAND | TILDE | CARET | LSHIFT | RSHIFT
            | EQEQ | NOTEQ | LTEQ | GTEQ | LT | GT | AT
            | UNKNOWN
```

`Token` accepts **any terminal except** the following structural delimiters (which serve as boundaries in the grammar):
- Layout: `NEWLINE`, `INDENT`, `DEDENT`
- Brackets: `LPAREN`, `RPAREN`, `LBRACK`, `RBRACK`, `LBRACE`, `RBRACE`
- Artifact markers: `ARTIFACT_IMPORTS_START`, `ARTIFACT_IMPORT_GROUP`, `ARTIFACT_START`, `ARTIFACT_SECTION`, `ARTIFACT_MEMBER`
- Annotations: `OBSOLETE`, `TODO`
- Documentation: `LINE_COMMENT`

Note: Terminals like `CLASS`, `DEF`, `INIT`, `SELF`, `RETURN`, `AT`, `COLON`, `COMMA`, and `ARROW` appear both in explicit structural productions (e.g., ClassDef, MethodDef) **and** in the `Token` catch-all. This is unambiguous because the parser is in a different LR state when processing structural positions vs. generic token sequences.


## LR(1) Automaton

*(Phase 2 — to be constructed from the grammar above)*


## LALR Verification

### Item Sets:

*(Phase 3 — states that can be merged)*


### Parse Table and Conflict Check

*(Phase 3 — LALR parse table and shift-reduce conflict analysis)*


### LALR Automaton

*(Phase 3 — LR(1) automaton after merging states)*
