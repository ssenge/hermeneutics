from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import gurobipy
from gurobipy import GRB, Model

from backends.core import Backend, Status, Solver, Result
from dsl.core import Traverser, Const, Var, Op, Aggregator, VarType, Expr
from dsl.program import Program
from utils.utils import Copyable


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
class GurobiSolver(Solver, Copyable):
    model: Model

    def solve(self) -> Result:
        self.model.optimize()
        return Result(status=(status := _StatusMap.get(self.model.status, Status.UNKNOWN)),
                      values=dict(zip(self.model.getAttr('VarName', self.model.getVars()),
                                      self.model.getAttr('X', self.model.getVars()))) if Status.has_result(status) else None)

    def model_as_str(self) -> str:
        # Unfortunately, Gurobi offers no easy way to get it as a string, so let's do it the rough way: write it into a tmp file, return the content and remove the file ;-)
        fname = f'tmp_gurobi_{datetime.now():%Y-%m-%d_%H-%M-%S}.lp'
        self.model.write(fname)
        with open(fname, 'r') as file:
            content = file.read()
        os.remove(fname)
        return content


@dataclass
class GurobiTraverser(Traverser, Copyable):
    vars: dict[Var, 'GurobiVar']
    expr: Expr = None

    def const(self, c: Const) -> GurobiTraverser:
        return self.copy(expr=c.value)

    def var(self, v: Var) -> GurobiTraverser:
        return self.copy(expr=self.vars[v])

    def op(self, op: Op, left, right) -> GurobiTraverser:
        return self.copy(expr=op.op(left.expr, right.expr))

    def agg(self, a: Aggregator) -> GurobiTraverser:
        return self.copy(expr=a.expr().traverse(GurobiTraverser(vars=self.vars)).expr)


@dataclass
class Local(Backend):
    p: Program

    def _convert(self) -> GurobiSolver:
        model = gurobipy.Model()
        traverser = GurobiTraverser({v: model.addVar(name=v.name, vtype=_VarTypeMap.get(v.type, GRB.CONTINUOUS), lb=v.lb, ub=v.ub) for v in self.p.vars})

        model.setObjective(self.p.objective.traverse(traverser).expr)
        for name, c in [(c.name, c.expr.traverse(traverser).expr) for c in self.p.constraints]:
            model.addConstr(c, name)

        return GurobiSolver(model)
