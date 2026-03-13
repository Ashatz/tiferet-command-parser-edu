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

The LR(1) automaton is constructed from a **core subset** of the full grammar, capturing the three-tier artifact comment hierarchy. This subset uses 10 production rules and 5 terminals, producing 17 canonical LR(1) states.

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

### Item Sets:

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

Practical guidance for translating this grammar into a PLY `yacc` parser.

### PLY Adaptation

- **Empty list productions** — PLY idiom uses `GroupList → ε | GroupList Group` rather than the formal grammar's non-empty `GroupList → Group | GroupList Group`. Convert all list non-terminals (`GroupList`, `SectionList`, `MemberList`, `SnippetList`, `StmtList`) to use empty base cases for cleaner PLY rule functions.
- **Token catch-all** — Rule 69 (`Token`) expands to 36 alternatives. In PLY, implement as a single `p_token` function matching a tuple of terminal names.
- **Enclosed / Inner** — Rules 62–68 handle matched brackets with NEWLINE inside. In PLY, these translate to recursive `p_enclosed` and `p_inner` rules naturally.

### Precedence Declaration

To prevent shift-reduce ambiguity at structural boundaries, declare artifact tokens with `nonassoc` precedence:

```python
precedence = (
    ('nonassoc', 'ARTIFACT_START', 'ARTIFACT_SECTION', 'ARTIFACT_MEMBER',
                 'OBSOLETE', 'TODO', 'DEDENT'),
)
```

This ensures the parser prefers shifting on structural tokens over reducing generic content, preventing false reductions in `TokenSeq`, `Payload`, and `LineContent` contexts.

### Semantic Value Structure

Parser actions should build a lightweight tree:
- `{ "type": "Module", "groups": [...] }`
- `{ "type": "Group", "header": "...", "sections": [...] }`
- `{ "type": "Section", "header": "...", "annotations": [...], "members": [...] }`
- `{ "type": "Member", "kind": "attribute" | "method" | "init", "annotations": [...], "body": {...} }`
- `{ "type": "Snippet", "comment": "..." | None, "statements": [...] }`

### Acceptance Criteria

1. Parser accepts all 7 sample files (`Scanner/samples/`) without syntax errors
2. Rejects clearly malformed artifact nesting (e.g., `ARTIFACT_MEMBER` outside a section)
3. Correctly distinguishes `MethodDef` (with `SELF`) from `FuncDef` (without)
4. Identifies code snippets within method bodies — comment-headed statement groups
5. Handles multi-line parenthesized expressions without premature statement termination
6. Compound statements (if-blocks) correctly nest via `INDENT`/`DEDENT` within snippet bodies
