from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import reduce
from typing import Callable, Iterable, ClassVar

from dsl.core import Eq, LE, GE, Expr, Var
from dsl.core import V
from utils.utils import Copyable


@dataclass
class Constraint(Copyable):
    name: str
    expr: Eq | LE | GE  # LT | GT not allowed


@dataclass
class Program(Copyable, ABC):
    objective: Expr
    constraints: list[Constraint] = field(default_factory=list)
    max: bool = False
    vars: list[Var] | None = None

    def __post_init__(self) -> None:
        if not self.vars:
            self.vars = self.objective.vars()


    def con(self, name: str, expr: Expr) -> Program:
        return self.copy(constraints=self.constraints + [c := Constraint(name=name, expr=expr)], vars=self.vars+list(c.expr.vars()))


    # Add constraints to the model (via the previous "V/for all")
    def rcon(self, *ranges: Iterable[object]) -> Callable[[tuple[object]], tuple[str, Expr]]:
        return lambda f: reduce(lambda m, c: m.con(name=c[0], expr=c[1]), V(*ranges)(f), self)

    @staticmethod
    def impute(cs: object) -> list[tuple[list[list], Callable[[list[object]], tuple[str, Expr]]]]:
        def _impute(i: int, c: Expr | tuple[list[list], Callable[[list[object]], tuple[str, Expr]]]) -> tuple[list[list], Callable[[list[object]], tuple[str, Expr]]]:
            match c:
                case Expr():
                    return [[None]], lambda _: (str(i), c)
                case tuple():  # tuple[list[range], Callable]
                    return c

        return [_impute(i, c) for i, c in enumerate(cs)]


    def st(self, *cs) -> Program:
        # This is a nice recursive approach which is unfortunately too slow for larger programs (due to excessive list creation)...
        #return reduce(lambda m, c: m._range_con(*c[0])(c[1]), Program.impute(cs), self)
        # ...will be fixed later on, so let's do it iteratively for now
        return self.copy(constraints=(cons := [Constraint(name, expr) for r, c in Program.impute(cs) for name, expr in V(*r)(c)]),
                         vars=self.vars.union(itertools.chain.from_iterable([c.expr.vars() for c in cons])))

    def expand(self) -> Program:
        return self.copy(objective=self.objective.expand(), constraints=[Constraint(c.name, c.expr.expand()) for c in self.constraints])

    def export(self) -> None:
        self._backend.export()


@dataclass
class Min(Program):
    pass


@dataclass
class Max(Program):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.max:
            self.objective = -self.objective
            self.max = True

