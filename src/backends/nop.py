from dataclasses import dataclass
from typing import Iterable

from backends.model import Backend, Result, Status
from dsl.core import Var
from dsl.program import Program


# @dataclass
# class NOPSolver(Solver):
#     vars: Iterable[Var]
#     value: float = 0.0
#
#     def solve(self) -> Result:
#         return Result(status=Status.OPTIMAL, values={v: self.value for v in self.vars})
#
#


@dataclass
class NOP(Backend[Program]):
    p: Program
    name: str = 'NOP'

    def _convert(self) -> Program:
        return self.p

    def _solve(self) -> Result:
        return Result(status=Status.OPTIMAL, values={v: 0.0 for v in self.p.vars})

    def model_as_str(self) -> str:
        return ''
