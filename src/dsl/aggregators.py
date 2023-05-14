from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Callable

from dsl.core import Aggregator, V
from utils.utils import ident, isum, iprod


@dataclass
class Sum(Aggregator):
    def __post_init__(self):
        self.expr = lambda: isum(V(*self.lst)(self.f))


def rsum(*it: Iterable[float]) -> Callable[[Callable[[float], float]], Sum]:
    return lambda f=ident: Sum(lst=it, f=f)


Σ = Sigma = rsum


def sum(*it: Iterable[float]) -> Sum:
    return Σ(*it)()


σ = sigma = sum


@dataclass
class Dot(Aggregator):
    def __post_init__(self):
        self.expr = lambda: Σ(*[zip(*self.lst)])(iprod).expr()


def dot(*it: Iterable[int]) -> Dot:
    return Dot(lst=it)


o = dot


@dataclass
class Mult(Aggregator):
    def __post_init__(self):
        self.expr = lambda: iprod(V(*self.lst)(self.f))


def mult(*it: Iterable[float]) -> Mult:
    return Mult(lst=it)


x = mult
