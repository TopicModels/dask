import os

from dask.utils import (textblock, filetext, takes_multiple_arguments,
                        Dispatch, tmpfile, next_newline)


def test_textblock():
    text = b'123 456 789 abc def ghi'.replace(b' ', os.linesep.encode())
    with filetext(text, mode='wb') as fn:
        with open(fn, 'rb') as f:
            text = textblock(f, 1, 11)
            assert text == ('456 789 '.replace(' ', os.linesep)).encode()
            assert set(map(len, text.split())) == set([3])

            assert textblock(f, 1, 10) == textblock(fn, 1, 10)

            assert textblock(f, 0, 3) == ('123' + os.linesep).encode()
            assert textblock(f, 3 + len(os.linesep), 6) == ('456' + os.linesep).encode()


def test_takes_multiple_arguments():
    assert takes_multiple_arguments(map)
    assert not takes_multiple_arguments(sum)

    def multi(a, b, c):
        return a, b, c

    class Singular(object):
        def __init__(self, a):
            pass

    class Multi(object):
        def __init__(self, a, b):
            pass

    assert takes_multiple_arguments(multi)
    assert not takes_multiple_arguments(Singular)
    assert takes_multiple_arguments(Multi)


def test_dispatch():
    foo = Dispatch()
    foo.register(int, lambda a: a + 1)
    foo.register(float, lambda a: a - 1)
    foo.register(tuple, lambda a: tuple(foo(i) for i in a))
    foo.register(object, lambda a: a)

    class Bar(object):
        pass
    b = Bar()
    assert foo(1) == 2
    assert foo(1.0) == 0.0
    assert foo(b) == b
    assert foo((1, 2.0, b)) == (2, 1.0, b)


def test_nextnewline():
    encoding = 'utf-16-le'

    euro = u'\u20ac'
    yen = u'\u00a5'

    bin_euro = u'\u20ac'.encode(encoding)
    bin_yen = u'\u00a5'.encode(encoding)
    bin_newline = '\n'.encode(encoding)

    data = (euro * 10) + '\n' + (yen * 10) + '\n' + (euro * 10)
    bin_data = data.encode(encoding)

    with tmpfile() as fn:
        with open(fn, 'w+b') as f:
            f.write(bin_data)
            f.seek(0)

            start, stop = next_newline(f, 2, encoding)
            assert start == len(bin_euro) * 10
            assert stop == len(bin_euro) * 10 + len('\n'.encode(encoding))

            start, stop = next_newline(f, len(bin_euro)*11, encoding)
            assert start == len(bin_euro) * 20 + len(bin_newline)
            assert stop == len(bin_euro) * 20 + len(bin_newline) * 2


def test_gh606():
    encoding = 'utf-16-le'
    euro = u'\u20ac'
    yen = u'\u00a5'
    bin_euro = u'\u20ac'.encode(encoding)
    bin_yen = u'\u00a5'.encode(encoding)

    data = (euro * 10) + '\n' + (yen * 10) + '\n' + (euro * 10)
    bin_data = data.encode(encoding)

    with tmpfile() as fn:
        with open(fn, 'w+b') as f:
            f.write(bin_data)
            f.seek(0)

            stop = len(bin_euro) * 10 + len('\n'.encode(encoding))
            res = textblock(f, 1, stop, encoding=encoding)
            assert res == ((yen * 10) + '\n').encode(encoding)

            stop = len(bin_euro) * 10 + len('\n'.encode(encoding))
            res = textblock(f, 0, stop, encoding=encoding)
            assert res == ((euro * 10) + '\n' + (yen * 10) + '\n').encode(encoding)
