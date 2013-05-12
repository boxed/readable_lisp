from readable_lisp import *

def canonize(s):
    s = s.replace('\n', ' ').replace(') )', '))').replace(') )', '))').replace(') ]', ')]').replace(') }', ')}')
    return re.sub(r'[\t ]+', ' ', s).strip()

def test_foo():
    orig = '(ns timelike.node (:refer-clojure :exclude [time future]) (:import (java.util.concurrent ConcurrentSkipListSet CountDownLatch LinkedBlockingQueue LinkedTransferQueue TimeUnit)) (:use timelike.scheduler clojure.math.numeric-tower [incanter.distributions :only [draw exponential-distribution]]))'

    assert canonize(Formatter().format(parse(orig))) == orig

def test_indented_line():
    import pytest
    with pytest.raises(IndentationError):
        ReadableLispGrammar('''    (foo bar)''').indented_line()
        assert False


def test_paren_indent_equivalence():
    a = Formatter().format(parse("(foo bar baz (asd qwe) fizz)"))
    b = Formatter().format(parse("foo bar baz (asd qwe) fizz"))
    assert a == b
    c = Formatter().format(parse("""foo bar baz
    (asd qwe)
    fizz"""))
    assert b == c
    d = Formatter().format(parse("""foo bar baz\n    asd qwe\n    fizz"""))
    assert c == d
    e = Formatter().format(parse("""foo
    bar
    baz
    asd
        qwe
    fizz"""))
    assert d == e
    f = Formatter().format(parse("""foo bar baz
    (asd
                      qwe)
    fizz"""))
    assert e == f

def test_readable_same_as_classic():
    a = Formatter().format(parse(open('test.clj', 'r').read()))
    b = Formatter().format(parse(open('test.clj-readable', 'r').read()))
    for x, y in zip([x for x in a.split('\n') if x], [x for x in b.split('\n') if x]):
        x, y = x.strip(), y.strip()
        print repr(x)
        print repr(y)
        assert x == y

def test_zero():
    assert Formatter().format(parse('(< 0 n)')).strip() == '(< 0 n)'

def test_parsing_formatting_equality():
    orig = unicode(open('test.clj', 'r').read())
    formatted = Formatter().format(parse(orig))

    a = canonize(orig)
    b = canonize(formatted)

    for x, y in zip([x for x in a.split('(') if x], [x for x in b.split('(') if x]):
        x, y = x.strip(), y.strip()
        print repr(x)
        print repr(y)
        assert x == y

if __name__ == '__main__':
    import pytest
    pytest.main(__file__)
