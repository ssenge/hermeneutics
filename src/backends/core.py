from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from dsl.core import Var
from dsl.program import Program


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


class Solver(ABC):
    @abstractmethod
    def solve(self) -> Result:
        raise NotImplementedError

    @abstractmethod
    def model_as_str(self):
        raise NotImplementedError


@dataclass
class Backend(ABC):
    p: Program

    def __post_init__(self):
        self.solver = self._convert()

    def _convert(self) -> Solver:
        raise NotImplementedError

    def solve(self, mutate_vars: bool = False) -> Result:
        result = self.solver.solve()
        if mutate_vars and result.values:
            for var in self.p.vars:
                var.val = result.values[var.name]  # side-effect
        return result

    def model_as_str(self):
        return self.solver.model_as_str()
