from dsl.core import Var, ContVar, BinVar
from dsl.program import Min, Max


def test_simple_min():
    x = Var()
    y = Var()
    p = Min(x + y).st(x >= 1, y == 0)
    assert p.objective.equals(x + y)  # .equals() (instead of ==) since otherwise a Eq object would be created
    assert p.constraints[0].expr.equals(x >= 1)
    assert p.constraints[1].expr.equals(y == 0)
    assert p.constraints[0].name == '0'
    assert p.constraints[1].name == '1'


def test_simple_vars():
    x = Var()
    y = Var()
    p = Min(x + y).st(x >= 1)  # check if vars are picked up from obj
    assert p.vars == set([x, y])


def test_simple_max():
    x = Var()
    y = Var()
    p = Max(x + y)
    assert p.objective.equals(-(x + y))  # note: -(x+y) is used since the simpler -x+y is semantically equivalent to -(x+y) but not structurally

#
# def test_simple_gurobi_1():
#     x = ContVar()
#     y = BinVar()
#     p = Min(σ([x, y])).st(x + y >= 1, y == 0)
#     solver = GurobiBackend(p).solver
#     solver.export()
#     result = solver.solve()
#     assert result.results[x.name] == 1 and result.results[y.name] == 0
#     assert result.results[x] == 1 and result.results[y] == 0
#     assert x.val == 1 and y.val == 0
