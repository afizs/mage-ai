GRAMMAR = r'''
// Define all the queries that are allowed
query: select
select : "SELECT"i column "FROM"i CNAME ["WHERE"i expr]

DATE: /\d{4}-\d{2}-\d{2}/
TIME: /\d{2}:\d{2}(?:\:\d{2})(?:\.\d{3})?/
datetime: "date("ESCAPED_STRING")"

column_type: (ESCAPED_STRING | CNAME)
literal: (ESCAPED_STRING | SIGNED_NUMBER | datetime)
literal_set: (literal","?)+
NULL: "NULL"i

column: "*" -> all
      | ((ESCAPED_STRING | CNAME)","?)+

expr: column_type
    | SIGNED_NUMBER
    | NULL
    | datetime
    | negation
    | binop
    | parens
    | like_expr
    | null_expr
    | is_expr
    | between_expr
    | in_expr

negation: notkw expr
binop: expr binary expr
parens: lpar expr rpar
like_expr: column_type [notkw] "LIKE"i ESCAPED_STRING
null_expr: column_type null_check
is_expr: column_type "IS"i [notkw] (literal | NULL | CNAME)
between_expr: column_type [notkw] "BETWEEN"i literal "AND"i literal
in_expr: column_type [notkw] "IN"i "("literal_set")"

binary: "=" -> eq
    | ("!=" | "<>") -> neq
    | "<" -> le
    | ">" -> ge
    | "<=" -> leq
    | ">=" -> geq
    | "AND"i -> and_ct
    | "OR"i -> or_ct
null_check: "ISNULL"i -> isna
          | "NOTNULL"i -> notna
          | notkw NULL
unary: notkw
lpar: "("
rpar: ")"
notkw: "NOT"i

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.CNAME
%import common.WS
%ignore WS
'''