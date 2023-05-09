from __future__ import annotations

from typing import Iterable, Callable

from dsl.core import Aggregator, Expr, V
from utils.utils import ident, isum, iprod


class Sum(Aggregator):
    def __init__(self, *lst, f=ident) -> None:
        self.lst = lst
        self.f = f
        self.expr = self.expandit()   ### substitute by actual expandit -- then lst, f is not required to be stored... wrong, as it is required for the convertrs

    def expandit(self) -> Expr:
        return isum(V(*self.lst)(self.f))


def Σ(*it: Iterable[int]) -> Callable[[Callable[[int], int]], Sum]:
    return lambda f=ident: Sum(*it, f=f)


class sum(Aggregator):
    def __init__(self, *lst) -> None:
        self.lst = lst
        self.f = ident
        self.expr = self.expandit()

    def expandit(self) -> Expr:
        return Σ(*self.lst)(ident).expr


def σ(*it: Iterable[int]) -> sum:
    return sum(*it)


class Dot(Aggregator):
    def __init__(self, *lsts) -> None:
        self.lsts = lsts
        self.expr = self.expandit()

    def expandit(self) -> Expr:
        return Σ(*[zip(*self.lsts)])(iprod).expr
