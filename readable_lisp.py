# Implementation of a subset of the Readable Lisp project (http://readable.sourceforge.net/)
# TODO: a formatter that prints sweetened output to turn normal lisp into sweetened lisp
# TODO: curly infix notation: {1 + 2 + 3} -> (+ 1 2 3)
# TODO: neoteric-expressions: foo(1 2) -> (foo 1 2)
import re

import sys
sys.path.append('parsley')

from parsley import makeGrammar, termMaker
from terml.nodes import Term

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

string = '"' (escapedCharacter | ~'"' anything)*:c '"' -> termMaker.String(''.join(c))
escapedCharacter = '\\' (('"' -> '"')    |('\\' -> '\\')
                   |('/' -> '/')    |('b' -> '\b')
                   |('f' -> '\f')   |('n' -> '\n')
                   |('r' -> '\r')   |('t' -> '\t')
                   |('\'' -> '\'')  | escapedUnicode)
hexdigit = :x ?(x in '0123456789abcdefABCDEF') -> x
escapedUnicode = 'u' <hexdigit{4}>:hs -> unichr(int(hs, 16))

# my own definitions
endline = hspace* ('\n' | end)
identifier_characters = letter | :other ?(other in '_!?.+-*/<>=&%#')
identifier = <identifier_characters (identifier_characters | digit)*>:x -> termMaker.Identifier(x)
anything_except_newline = ~'\n' anything
comment = hspace* ';' <anything_except_newline*>:x -> termMaker.Comment(x)
atom = <':' identifier>:x -> termMaker.Atom(x)
expression = list | expression_not_list
expression_not_list = vector | map | set | quote | character_literal | metadata | deref | syntax_quote | unquote | unquote_splice | regex | var_quote | fn | ignore
value = expression | identifier | number | string | character_literal | atom | comment
value_not_list = expression_not_list | identifier | number | string | character_literal | atom | comment
values = value:head (ws value)*:tail -> [head] + tail

list = '(' values?:x ')' -> termMaker.List(*x) if x else termMaker.List()
vector = '[' values?:x ']' -> termMaker.Vector(*x) if x else termMaker.Vector()
map = '{' values?:x '}' -> termMaker.Map(*x) if x else termMaker.Map()
set = '#{' values?:x '}' -> termMaker.Set(*x) if x else termMaker.Set()

list_like = list | vector | map | set

term = (expression | identifier)

quote = '\'' (term | list_like):x -> termMaker.Quote(x)
character_literal = '\\' letter:x -> termMaker.CharacterLiteral(x)
metadata = '^' (term | list_like):x -> termMaker.MetaData(x)
deref = '@' (term | list_like):x -> termMaker.Deref(x)
syntax_quote = '`' (term | list_like):x -> termMaker.SyntaxQuote(x)
unquote = '~' (term | list_like):x -> termMaker.UnQuote(x)
unquote_splice = '~@' (term | list_like):x -> termMaker.UnQuoteSplice(x)
regex = '#' string:x -> termMaker.Regex(x)
var_quote = '#' '\'' (term | list_like):x -> termMaker.VarQuote(x)
fn = '#' list:x -> termMaker.FunctionDefinition(x)
ignore = '#' '_' (term | list_like):x -> termMaker.Ignore(x)

output = (comment | expression | emptyline)*

# Readable Lisp
indented_line = '    '+:x (identifier | value):y (hspace value)*:extra_terms <(comment | endline)>:comment -> indent_state.handle(len(x), y, comment, extra_terms)

non_indented_line = (identifier | value_not_list):y (hspace value)*:extra_terms <(comment | endline)>:comment -> indent_state.handle(0, y, comment, extra_terms)

sweet_output = (indented_line | non_indented_line | list | emptyline | comment)*

"""

class IndentState(object):
    def __init__(self):
        self.stack = []

    def indent_level(self):
        return len(self.stack)

    def _add_term(self, term):
        # print '\tadded', term, 'to', self.stack[-1]
        self.stack[-1].args = list(self.stack[-1].args) + [term]

    def _push_term(self):
        # print 'push', self.stack[-1].args[-1]
        if not self.stack:
            raise IndentationError('Syntax error: invalid tabs')
        l = termMaker.List(self.stack[-1].args[-1])
        self.stack[-1].args[-1] = l
        self.stack.append(l)

    def handle(self, indent, identifier_or_value, comment, extra_terms=None):
        if identifier_or_value.tag.name == 'Comment':
            return identifier_or_value
        assert type(identifier_or_value) == Term
        comment = comment.strip(' \n')[1:]
        while indent < self.indent_level():
            self.stack.pop()

        if indent > self.indent_level():
            self._push_term()

        result = None
        if extra_terms:
            identifier_or_value = termMaker.List(*([identifier_or_value]+extra_terms))

        if indent == 0:
            if not extra_terms:
                identifier_or_value = termMaker.List(identifier_or_value)
            self.stack.append(identifier_or_value)
            result = self.stack[-1]
        else:
            assert indent == self.indent_level()
            self._add_term(identifier_or_value)

        if comment:
            self._add_term(termMaker.Comment(comment))

        return result

indent_state = IndentState()

bindings = dict(
    indent_state=indent_state,
    termMaker=termMaker,
)
ReadableLispGrammar = makeGrammar(grammar, bindings, name="readable_lisp")


def parse(s):
    return [x for x in ReadableLispGrammar(s).sweet_output() if x is not None]


class Formatter(object):
    def format(self, l):
        assert isinstance(l, list)
        return ''.join([self.format_item(i) for i in l if i])

    def basic_format(self, item):
        result = ''
        if item.data is not None:
            result += str(item.data)
        if item.args:
            result += self.format_item(item.args)
        return result

    def format_item(self, item):
        item_type = item.__class__.__name__
        formatter = 'format_%s' % item_type
        if hasattr(self, formatter):
            return getattr(self, formatter)(item)
        return unicode(item)

    def format_list(self, item):
        return ' '.join([self.format_item(i) for i in item if i])

    def format_Term_Comment(self, item):
        assert len(item.args) == 1
        return '; %s\n' % item.args[0].data

    def format_Term_String(self, item):
        assert len(item.args) == 1
        return '"%s"' % item.args[0].data

    def format_Term_Vector(self, item):
        return '[%s]' % self.format_item(item.args)

    def format_Term_List(self, item):
        return '(%s)\n' % self.format_item(item.args)

    def format_Term_Map(self, item):
        return '{%s}' % self.format_item(item.args)

    def format_Term_Set(self, item):
        return '#{%s}' % self.format_item(item.args)

    def format_Term_Identifier(self, item):
        return self.basic_format(item)

    def format_Term_Atom(self, item):
        return self.basic_format(item)

    def format_Term_Quote(self, item):
        return '\''+self.basic_format(item)

    def format_Term_UnQuote(self, item):
        return '~'+self.basic_format(item)

    def format_Term_Deref(self, item):
        return '@'+self.basic_format(item)

    def format_Term_FunctionDefinition(self, item):
        return '#'+self.basic_format(item)

    def format_Term_SyntaxQuote(self, item):
        return '`'+self.basic_format(item)

    def format_Term_CharacterLiteral(self, item):
        return '\\'+self.basic_format(item)

    def format_Term_MetaData(self, item):
        return '^'+self.basic_format(item)

    def format_Term_Ignore(self, item):
        return '#_'+self.basic_format(item)

    def format_Term(self, item):
        item_type = item.__class__.__name__
        formatter = 'format_%s_%s' % (item_type, item.tag.name)
        if hasattr(self, formatter):
            return getattr(self, formatter)(item)

        if item.tag.name.startswith('.') and item.tag.name.endswith('.'):
            return self.basic_format(item)

        raise Exception('Unhandled term type %s with value %s' % (item.tag.name, self.basic_format(item)))


class IndentFormatter(Formatter):
    def __init__(self):
        self._indent = 0

    def indent(self):
        return '    '*self._indent

    def format(self, item):
        foo = super(IndentFormatter, self).format_item(item)
        if foo == '\n':
            return ''
        return foo

    def format_Term_List(self, item):
        if len(item.args) == 1:
            return super(IndentFormatter, self).format_Term_List(item)
        result = self.format(item.args[0])
        if not result.endswith('\n'):
            result += '\n'
        self._indent += 1
        for i in item.args[1:]:
            result += self.indent() + self.format(i)
            if not result.endswith('\n'):
                result += '\n'
        self._indent -= 1
        if self._indent == 0 and not result.endswith('\n'):
            result += '\n'
        return result
