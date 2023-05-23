from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, TypeVar, Generic, Self

from dsl.core import Var, Traverser, Expr, Const, Aggregator, Op
from dsl.program import Program
from utils.utils import Copyable


class Status(Enum):
    OPTIMAL = auto()
    SUBOPTIMAL = auto()
    INFEASIBLE = auto()
    LIMIT_REACHED = auto()
    UNKNOWN = auto()
    NO_SOLUTION = auto()

    @staticmethod
    def has_result(status: Status) -> bool:
        return status in [Status.OPTIMAL, Status.SUBOPTIMAL, Status.LIMIT_REACHED]


@dataclass
class Result:
    status: Status = Status.UNKNOWN
    values: dict[Var, float] | None = None


# class Solver(ABC):
#     @abstractmethod
#     def solve(self) -> Result:
#         raise NotImplementedError

BMT = TypeVar('BackendModelType')

@dataclass
class Backend(ABC, Generic[BMT]):
    p: Program
    name: str

    def __post_init__(self) -> None:
        self.p_ = self._convert()

    def _convert(self) -> BMT:
        raise NotImplementedError

    def solve(self, mutate_vars: bool = False) -> Result:
        result = self._solve()
        if mutate_vars and result.values:
            for var in self.p.vars:
                var.val = result.values[var.name]  # side-effect
        return result

    @abstractmethod
    def model_as_str(self) -> str:
        raise NotImplementedError


CVT = TypeVar('ConvertedVarType')

@dataclass
class VarReplacementTraverser(Traverser, Copyable, Generic[CVT]):
    vars: dict[Var, CVT]
    expr: Expr | None = None

    def const(self, c: Const) -> Self:
        return self.copy(expr=c.value)

    def var(self, v: Var) -> Self:
        return self.copy(expr=self.vars[v])

    def op(self, op: Op, left: Self, right: Self) -> Self:
        return self.copy(expr=op.op(left.expr, right.expr))

    def agg(self, a: Aggregator) -> Self:
        return self.copy(expr=a.expr().traverse(VarReplacementTraverser[CVT](vars=self.vars)).expr)
