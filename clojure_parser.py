from parsley import makeGrammar, termMaker
from terml.nodes import Term
from itertools import chain

grammar = r"""

# copied from parsley.parsley and parsley_json.py
number = ('-' | -> ''):sign (intPart:ds (floatPart(sign ds)
                            | -> int(sign + ds)))
digit = :x ?(x in '0123456789') -> x
digits = <digit*>
digit1_9 = :x ?(x in '123456789') -> x
intPart = (digit1_9:first digits:rest -> first + rest) | digit
floatPart :sign :ds = <('.' digits exponent?) | exponent>:tail
                    -> float(sign + ds + tail)
exponent = ('e' | 'E') ('+' | '-')? digits

hspace = ' ' | '\t'
vspace =  '\r' | '\n'
ws = (hspace | vspace)*
emptyline = hspace* vspace
indentation = emptyline* hspace+
noindentation = emptyline* ~~~hspace

string = '"' (escapedCharacter | ~'"' anything)*:c '"' -> termMaker.String(''.join(c))
escapedCharacter = '\\' (('"' -> '"')    |('\\' -> '\\')
                   |('/' -> '/')    |('b' -> '\b')
                   |('f' -> '\f')   |('n' -> '\n')
                   |('r' -> '\r')   |('t' -> '\t')
                   |('\'' -> '\'')  | escapedUnicode)
hexdigit = :x ?(x in '0123456789abcdefABCDEF') -> x
escapedUnicode = 'u' <hexdigit{4}>:hs -> unichr(int(hs, 16))

# my own definitions
identifier_characters = letter | :other ?(other in '_!?.+-*/<>=&%#')
identifier = <identifier_characters (identifier_characters | digit)*>:x -> termMaker.Identifier(x)
comment = ';' <(~'\n' anything)*>:x -> termMaker.Comment(x)
atom = <':' identifier>
value = identifier | number | string | character_literal | atom | expression | comment
values = value:head (ws value)*:tail -> [head] + tail

list = '(' values?:x ')' -> termMaker.List(x)
vector = '[' values?:x ']' -> termMaker.Vector(x)
map = '{' values?:x '}' -> termMaker.Map(x)
set = '#{' values?:x '}' -> termMaker.Set(x)

term = (expression | identifier)

quote = '\'' term
character_literal = '\\' letter
metadata = '^' term
deref = '@' term
syntax_quote = '`' term
unquote = '~' term
unquote_splice = '~@' term
regex = '#' string
var_quote = '#' '\'' term
fn = '#' list
ignore = '#' '_' term

expression =  list | vector | map | set | quote | character_literal | metadata | deref | syntax_quote | unquote | unquote_splice | regex | var_quote | fn | ignore

output = (comment | expression | emptyline)+

"""
LispGrammar = makeGrammar(grammar, globals(), name="lisp")

test = open('test.clj', 'r').read()
ast = LispGrammar(test).output()

start_tag = {
    'Comment': ';',
    'List': '(',
    'Vector': '[',
    'Map': '{',
    'Set': '#{',
    'String': '"',
}

end_tag = {
    # 'Comment': '\n'
    'List': ')',
    'Vector': ']',
    'Map': '}',
    'Set': '}',
    'String': '"',
}

def format_tree(item):
    if type(item) in (list, tuple):
        return ''.join([format_tree(i) for i in item if i])
    elif isinstance(item, str):
        return unicode(item)
    elif isinstance(item, Term):
        if item.tag.name == 'String':
            return '"%s" ' % item.args[0].data
        result = ''
        if item.tag.name in start_tag:
            result += start_tag[item.tag.name]
        if item.data:
            result += str(item.data)
        if item.args:
            result += format_tree(item.args)
        if item.tag.name in end_tag:
            result += end_tag[item.tag.name] + ' '
        if result and result[-1] not in ') "':
            result += ' '
        return result
    else:
        # print dir(item)
        # import ipdb; ipdb.set_trace()
        return unicode(type(item))

print format_tree(ast)