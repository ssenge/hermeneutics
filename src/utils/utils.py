from __future__ import annotations

from abc import ABC
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, replace
from functools import reduce
from typing import TypeVar, Generic

ident = lambda x: x
identm = lambda self, x: x
isum = lambda it: reduce(lambda x, y: x + y, it)
iprod = lambda it: reduce(lambda x, y: x * y, it)


@dataclass
class Copyable(ABC):
    def copy(self, **kwargs):
        return replace(self, **kwargs)


T = TypeVar('T')


class Deque(deque, Generic[T]):
    def __init__(self, it: Iterable[T] = []):
        super().__init__(it)

    def __add__(self, item: T) -> Deque[T]:
        match item:
            case Iterable():
                self.extend(item)
            case _:
                self.append(item)
        return self

    def __radd__(self, item: T) -> Deque[T]:
        match item:
            case Iterable():
                self.extendleft(reversed(item))
            case _:
                self.appendleft(item)
        return self


