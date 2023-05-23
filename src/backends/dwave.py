from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Callable

import dimod
from dimod import ExactSolver, ExactCQMSolver, RandomSampler, SimulatedAnnealingSampler, ConstrainedQuadraticModel, QuadraticModel
from dwave.samplers import PlanarGraphSolver, SteepestDescentSolver, TabuSampler, TreeDecompositionSolver
from dwave.system import LeapHybridCQMSampler, LeapHybridSampler

from backends.model import Backend, Result, Status, VarReplacementTraverser
from dsl.core import VarType
from dsl.program import Program
from utils.utils import ident


@dataclass
class LeapCQMBackend(Backend[ConstrainedQuadraticModel], ABC):
    p: Program
    name: str = ''
    _inverter: Callable[[dict[str, float]], dict[str, float]] = ident

    def _convert(self) -> ConstrainedQuadraticModel:
        var_type_map = {VarType.BINARY: dimod.Binary,
                       VarType.INT: dimod.Integer,
                       VarType.CONTINUOUS: dimod.Real}

        self.cqm = ConstrainedQuadraticModel()
        vars_dict = {v: var_type_map.get(v.type, dimod.Real)(v.name) for v in self.p.vars}
        traverser = VarReplacementTraverser(vars_dict)

        self.cqm.set_objective(self.p.objective.traverse(traverser).expr)
        for name, c in [(c.name, c.expr.traverse(traverser).expr) for c in self.p.constraints]:
            self.cqm.add_constraint(c, label=name, weight=None)

        return self.cqm

    def _solve(self) -> Result:
        return Result(Status.UNKNOWN, self._inverter(self._sample(self._solver()).first.sample))

    _sample = lambda self, solver: solver.sample_cqm(self.p_)

    def cqm_as_str(self) -> str:
        return dimod.lp.dumps(self.cqm)

    def bqm_as_str(self) -> str:
        return dimod.cqm_to_bqm(self.cqm)[0].to_polystring()

    def model_as_str(self) -> str:
        return self.cqm_as_str()


@dataclass
class LeapBQMBackend(LeapCQMBackend):
    def _convert(self) -> QuadraticModel:  # will not typecheck
        cqm = super()._convert()
        self.bqm, self._inverter = dimod.cqm_to_bqm(cqm)
        return self.bqm

    _sample = lambda self, solver: solver.sample(self.p_)


class HybridBQMBackend(LeapBQMBackend):
    name: str = 'HybridBQMBackend'
    _solver = lambda self: LeapHybridSampler()


class HybridCQMBackend(LeapCQMBackend):
    name: str = 'HybridCQMBackend'
    _solver = lambda self: LeapHybridCQMSampler()


class ExactBQMBackend(LeapBQMBackend):
    _solver = lambda self: ExactSolver()


class ExactCQMBackend(LeapCQMBackend):
    _solver = lambda self: ExactCQMSolver()


class RandomBQMBackend(LeapBQMBackend):
    _solver = lambda self: RandomSampler()


class SimulatedAnnealingBQMBackend(LeapBQMBackend):
    _solver = lambda self: SimulatedAnnealingSampler()


class PlanarGraphBQMBackend(LeapBQMBackend):
    _solver = lambda self: PlanarGraphSolver()


class SteepestDescentBQMBackend(LeapBQMBackend):
    _solver = lambda self: SteepestDescentSolver()


class TabuBQMBackend(LeapBQMBackend):
    _solver = lambda self: TabuSampler()


class TreeDecompositionBQMBackend(LeapBQMBackend):
    _solver = lambda self: TreeDecompositionSolver()

