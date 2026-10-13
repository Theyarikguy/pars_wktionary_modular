from functools import reduce
from typing import Callable, Iterable, TypeVar

A = TypeVar('A')


def pipe(*fns: Callable) -> Callable[[A], A]:
    """pipe(f, g, h)(x) == h(g(f(x)))"""
    return lambda x: reduce(lambda acc, f: f(acc), fns, x)


def compose(*fns: Callable) -> Callable[[A], A]:
    """compose(f, g, h)(x) == f(g(h(x)))"""
    return pipe(*reversed(fns))


def mapcat(fn: Callable, items: Iterable) -> list:
    """map + flatten на один уровень."""
    return [y for x in items for y in fn(x)]