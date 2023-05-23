from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import gurobipy
from gurobipy import GRB

from backends.model import Backend, Status, Result, VarReplacementTraverser
from dsl.core import VarType
from dsl.program import Program

_StatusMap = {GRB.OPTIMAL: Status.OPTIMAL,
              GRB.SUBOPTIMAL: Status.SUBOPTIMAL,
              GRB.INFEASIBLE: Status.INFEASIBLE,
              GRB.NODE_LIMIT: Status.LIMIT_REACHED,
              GRB.TIME_LIMIT: Status.LIMIT_REACHED,
              GRB.ITERATION_LIMIT: Status.LIMIT_REACHED}

_VarTypeMap = {VarType.BINARY: GRB.BINARY,
               VarType.INT: GRB.INTEGER,
               VarType.CONTINUOUS: GRB.CONTINUOUS}


@dataclass
class GurobiBackend(Backend[gurobipy.Model]):
    p: Program
    name: str = 'Gurobi'

    def _convert(self) -> gurobipy.Model:
        model = gurobipy.Model()
        traverser = VarReplacementTraverser({v: model.addVar(name=v.name, vtype=_VarTypeMap.get(v.type, GRB.CONTINUOUS), lb=v.lb, ub=v.ub) for v in self.p.vars})

        model.setObjective(self.p.objective.traverse(traverser).expr)
        for name, c in [(c.name, c.expr.traverse(traverser).expr) for c in self.p.constraints]:
            model.addConstr(c, name)

        return model

    def _solve(self) -> Result:
        self.p_.optimize()
        return Result(status=(status := _StatusMap.get(self.p_.status, Status.UNKNOWN)),
                      values=dict(zip(self.p_.getAttr('VarName', self.p_.getVars()),
                                      self.p_.getAttr('X', self.p_.getVars()))) if Status.has_result(status) else None)

    def model_as_str(self) -> str:
        # Unfortunately, Gurobi offers no easy way to get the model as a string, so let's do it the rough way: write it into a tmp file, return the content and remove the file ;-)
        fname = f'tmp_gurobi_{datetime.now():%Y-%m-%d_%H-%M-%S}.lp'
        self.p_.write(fname)
        with open(fname, 'r') as file:
            content = file.read()
        os.remove(fname)
        return content
