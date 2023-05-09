from dsl.aggregators import Σ, Dot, σ
from dsl.core import Var, Const, LT, GT, LE, GE, Eq

x = Var()
y = Var()
z = Var()
expr0 = (x * 4 + 1 * (5 * y)) ** z
expr1 = expr0.setn({x: 2, y: 1, z: 3})
expr3 = (1+y*x+1).replace(1 + y * x, z)


def test_var_creation():
    a = Var('a')
    assert a.name == 'a'

    assert x.name == 'x0'
    assert y.name == 'x1'
    assert z.name == 'x2'


def test_var_creation_dict():
    vs = Var.new('v_{}_{}_{}', 2, 3, 4)
    assert vs[0][0][0].name == 'v_0_0_0'
    assert vs[1][2][3].name == 'v_1_2_3'
    assert len(vs) == 2
    assert len(vs[0]) == 3
    assert len(vs[0][0]) == 4


def test_expr_creation():
    assert expr0.as_equation() == '(((x0*4)+(1*(5*x1)))**x2)'


def test_expr_replace_1():
    assert expr1.as_equation() == '(((2*4)+(1*(5*1)))**3)'


def test_expr_solve():
    assert expr1.solve() == 2197


def test_expr_cmp():
    assert Const(5).equals(Const(5))
    assert not Const(5).equals(Const(6))
    assert x.equals(x)
    assert expr1.equals(expr1)
    assert not expr1.equals(expr0)
    assert expr0.equals((x * 4 + 1 * (5 * y)) ** z)


def test_expr_contains():
    assert expr0.contains(x)
    assert expr0.contains(x*4)
    assert not expr0.contains(x*5)
    assert expr0.contains(1*(5*y))


def test_expr_replace_2():
    assert expr3.equals(z+1)
    assert not expr3.equals(z+2)


def test_expr_remove():
    assert expr3.remove(z).remove(Const(1)) is None


def test_expr_eqs():
    assert (Var('x') < Const(0)).equals(LT(left=Var('x'), right=Const(0)))
    assert (Var('x') > Const(0)).equals(GT(left=Var('x'), right=Const(0)))
    assert (Var('x') <= Const(0)).equals(LE(left=Var('x'), right=Const(0)))
    assert (Var('x') >= Const(0)).equals(GE(left=Var('x'), right=Const(0)))
    assert (Var('x') == Const(0)).equals(Eq(left=Var('x'), right=Const(0)))


def test_simple_sum_1():
    x = Var()
    y = Var()
    vs = {1: x, 2: y}
    assert Σ([1, 2])(lambda i: vs[i]).expand().equals(x + y)


def test_simple_sum_2():
    x = Var()
    y = Var()
    assert Σ([x, y])().expand().equals(x + y)


def test_simple_sum_3():
    x = Var()
    y = Var()
    assert Σ([x, y])().expand().equals(σ([x, y]).expand())


def test_simple_dot_1():
    x = Var()
    y = Var()
    expr = Dot([x], [y])
    assert expr.expand().equals(x * y)


def test_simple_dot_2():
    x = Var()
    y = Var()
    expr = Dot([x, y], [y, x])
    assert expr.expand().equals(x * y + y * x)
