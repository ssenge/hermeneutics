from dataclasses import dataclass
from typing import Iterable

from backends.core import Backend, Result, Status, Solver
from dsl.core import Var
from dsl.program import Program


@dataclass
class NOPSolver(Solver):
    vars: Iterable[Var]
    value: float = 0.0

    def solve(self) -> Result:
        return Result(status=Status.OPTIMAL, values={v: self.value for v in self.vars})

    def model_as_str(self):
        return ''


@dataclass
class NOP(Backend):
    p: Program

    def _convert(self) -> Solver:
        return NOPSolver(self.p.vars)
