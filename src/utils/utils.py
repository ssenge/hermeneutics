from abc import ABC
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, replace
from functools import reduce
from typing import Any, Callable

ident = lambda x: x
isum = lambda it: reduce(lambda x, y: x + y, it)
iprod = lambda it: reduce(lambda x, y: x * y, it)


@dataclass
class Copyable(ABC):
    def copy(self, **kwargs):
        return replace(self, **kwargs)


class Deque(deque):
    def __init__(self, it=[]):
        super().__init__(it)

    def __add__(self, other):
        match other:
            case Iterable():
                self.extend(other)
            case _:
                self.append(other)
        return self

    def __radd__(self, other):
        match other:
            case Iterable():
                self.extendleft(reversed(other))
            case _:
                self.appendleft(other)
        return self


