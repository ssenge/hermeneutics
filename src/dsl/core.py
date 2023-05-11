from __future__ import annotations

import itertools
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from numbers import Number
from typing import ClassVar, TypeAlias, TypeVar, Iterable, Callable

from tail_recurse import tail_call

from dsl.tree import Tree
from utils.utils import Deque, ident


@dataclass(eq=False)
class Expr(Tree, ABC):
    @staticmethod
    def _lift(obj: Expr | Number) -> Expr:
        match obj:
            case Number():
                return Const(obj)
            case _:  # Expr
                return obj

    def _expr(self, op: type[Op], other: Expr | Number) -> Op:
        return op(left=self, right=Expr._lift(other))

    def _rexpr(self, op: type[Op], other: Expr | Number) -> Op:
        return op(left=self._lift(other), right=self)

    def __add__(self, other: Expr | Number) -> Op:
        return self._expr(Add, other)

    def __radd__(self, other: Expr | Number) -> Op:
        return self._rexpr(Add, other)

    def __sub__(self, other: Expr | Number) -> Op:
        return self._expr(Sub, other)

    def __rsub__(self, other: Expr | Number) -> Op:
        return self._rexpr(Sub, other)

    def __mul__(self, other: Expr | Number) -> Op:
        return self._expr(Mul, other)

    def __rmul__(self, other: Expr | Number) -> Op:
        return self._rexpr(Mul, other)

    def __pow__(self, power: Expr | Number, modulo=None) -> Op:
        return self._expr(Pow, power)

    def __eq__(self, other: Expr | Number) -> Op:
        return self._expr(Eq, other)

    def __lt__(self, other: Expr | Number) -> Op:
        return self._expr(LT, other)

    def __gt__(self, other: Expr | Number) -> Op:
        return self._expr(GT, other)

    def __le__(self, other: Expr | Number) -> Op:
        return self._expr(LE, other)

    def __ge__(self, other: Expr | Number) -> Op:
        return self._expr(GE, other)

    def __neg__(self) -> Op:
        return -1 * self

    def __pos__(self) -> Expr:
        return self

    def traverse(self, t: Traverser) -> Traverser:

        def match(x, stack: Deque) -> Traverser:
            match x:
                case Const():
                    return t.const(x)
                case Var():
                    return t.var(x)
                case Aggregator():
                    return t.agg(x)
                case Op():
                    return t.op(x, *reversed((stack.pop(), stack.pop())))  # right first, then left

        go = tail_call(lambda unseen, stack=Deque(): stack.pop() if not unseen else go(unseen, stack + match(unseen.popleft(), stack)))

        return go(self.postorder())

    def set(self, var: Var, value: float = 1.0) -> Expr:
        return self.replace(var, Const(value))

    def setn(self, replacements: dict[Var, float]) -> Expr:
        return reduce(lambda expr, kv: expr.set(kv[0], kv[1]), replacements.items(), self)

    def solve(self) -> float:
        return self.traverse(CalcTraverser()).result

    def as_equation(self) -> str:
        return self.traverse(ToEquationTraverser()).result

    def vars(self) -> Iterable[Var]:
        return set(self.traverse(ToVarListTraverser()).result)

    def expand(self) -> Expr:
        return self.traverse(ExpandTraverser()).result

    def equals(self, other: Expr) -> bool:
        # Approach: two trees are equal if in- and pre- or post-order are equal
        # A comparison using == is not possible as it got overriden:
        #   ex: return self_inorder == other_inorder and self_postorder == other_postorder (would create an Eq instance instead)
        # So either it requires .equals in Ops and Terminals (the proper way) or... we just compare their attributes via __dict__ ;-)
        return len(self_inorder := self.inorder()) == len(other_inorder := other.inorder()) \
               and len(self_postorder := self.postorder()) == len(other_postorder := other.postorder()) \
               and all([tuple[0].__dict__ == tuple[1].__dict__ for tuple in zip(self_inorder, other_inorder)]) \
               and all([tuple[0].__dict__ == tuple[1].__dict__ for tuple in zip(self_postorder, other_postorder)])

    def replace(self, old: Expr, new: Expr) -> Expr:
        return self.traverse(ExprReplacer(old, new))

    def remove(self, expr: Expr) -> Expr:
        return self.replace(expr, None)

    def contains(self, expr: Expr) -> bool:
        return self.traverse(Contains(expr))

    def __str__(self) -> str:
        return self.traverse(ToEquationTraverser()).result


@dataclass(eq=False)
class Op(Expr, ABC):
    symb: str | None = None

    @abstractmethod
    def op(self, a: Number, b: Number) -> Number:
        return NotImplementedError()


@dataclass(eq=False)
class Add(Op):
    symb: str = '+'

    def op(self, a: Number, b: Number) -> Number:
        return a + b


@dataclass(eq=False)
class Pow(Op):
    symb: str = '**'

    def op(self, a: Number, b: Number) -> Number:
        return a ** b


@dataclass(eq=False)
class Sub(Op):
    symb: str = '-'

    def op(self, a: Number, b: Number) -> Number:
        return a - b


@dataclass(eq=False)
class Mul(Op):
    symb: str = '*'

    def op(self, a: Number, b: Number) -> Number:
        return a * b


@dataclass(eq=False)
class Eq(Op):
    symb: str = '='

    def op(self, a: Number, b: Number) -> Number:
        return a == b


@dataclass(eq=False)
class LT(Op):
    symb: str = '<'

    def op(self, a: Number, b: Number) -> bool:
        return a < b


@dataclass(eq=False)
class LE(Op):
    symb: str = '<='

    def op(self, a: Number, b: Number):
        return a <= b


@dataclass(eq=False)
class GT(Op):
    symb: str = '>'

    def op(self, a: Number, b: Number):
        return a > b


@dataclass(eq=False)
class GE(Op):
    symb: str = '>='

    def op(self, a: Number, b: Number):
        return a >= b


@dataclass(eq=False)
class Terminal(Expr, ABC):
    pass


@dataclass(eq=False)
class Const(Terminal):
    value: float = 1.0


class VarType(Enum):
    CONTINUOUS = "Continuous"
    INT = "Integer"
    BINARY = "Binary"


@dataclass(eq=False)
class Var(Terminal):
    name: str | None = None
    type: VarType = VarType.CONTINUOUS
    lb: float = sys.float_info.min
    ub: float = sys.float_info.max
    val: float | None = None
    cnt: ClassVar[int] = itertools.count()

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = 'x' + str(next(Var.cnt))

    @staticmethod
    def new(prefix: str, *reps: int, type: VarType = VarType.CONTINUOUS, lb: float | None = None, ub: float | None = None) -> dict:
        def new_(prefix, nums: list[int], path: list[int] = [], type=type, lb=lb, ub=ub):
            return {num: new_(prefix, nums[1:], path=path + [num]) if nums[1:] else Var(f'{prefix.format(*path, num)}', type, lb, ub) for num in range(nums[0])}

        return new_(prefix, reps, type=type, lb=lb, ub=ub)

    def __str__(self) -> str:
        return f'{self.type.value}Var(\'{self.name}\'){"=" + str(self.val) if self.val else ""}'

    def __hash__(self) -> int:
        return hash(self.name)

    def __call__(self, *args, **kwargs) -> float:
        return args[0](self.val) if args and self.val else self.val


ContVar: TypeAlias = Var


@dataclass(eq=False)
class IntVar(Var):
    type: VarType = VarType.INT

    @staticmethod
    def new(prefix: str, *reps, lb, ub) -> dict:
        return Var.new(prefix, *reps, lb=lb, ub=ub, type=VarType.INT)


@dataclass(eq=False)
class BinVar(Var):
    type: VarType = VarType.BINARY

    @staticmethod
    def new(prefix: str, *reps) -> dict:
        return Var.new(prefix, *reps, lb=0, ub=1, type=VarType.BINARY)


CVar: TypeAlias = ContVar
IVar: TypeAlias = IntVar
BVar: TypeAlias = BinVar


@dataclass
class Traverser(ABC):
    @abstractmethod
    def const(self, c: Const) -> Traverser:
        return NotImplementedError

    @abstractmethod
    def var(self, v: Var) -> Traverser:
        return NotImplementedError

    @abstractmethod
    def op(self, op: Op, left, right) -> Traverser:
        return NotImplementedError

    @abstractmethod
    def agg(self, a: Aggregator) -> Traverser:
        return NotImplementedError


@dataclass
class ToEquationTraverser(Traverser):
    result: str = ''

    def const(self, c: Const):
        return ToEquationTraverser(str(c.value))

    def var(self, v: Var):
        return ToEquationTraverser(v.name)

    def op(self, op: Op, left, right):
        return ToEquationTraverser('(' + left.result + op.symb + right.result + ')')

    def agg(self, a: Aggregator):
        return ToEquationTraverser(a.expr().traverse(ToEquationTraverser()).result)


@dataclass
class ToVarListTraverser(Traverser):
    result: list[Var] = field(default_factory=list)

    def const(self, c: Const):
        return self

    def var(self, v: Var):
        return ToVarListTraverser(self.result + [v])

    def op(self, op: Op, left, right):
        return ToVarListTraverser(left.result + right.result)

    def agg(self, a: Aggregator):
        return ToVarListTraverser(self.result + a.expr().traverse(ToVarListTraverser()).result)


@dataclass
class ExpandTraverser(Traverser):
    result: Expr | None = None

    def const(self, c: Const):
        return ExpandTraverser(c.value)

    def var(self, v: Var):
        return ExpandTraverser(v)

    def op(self, op: Op, left, right):
        return ExpandTraverser(op.op(left.result, right.result))

    def agg(self, a: Aggregator):
        return ExpandTraverser(a.expr())
        #return ExpandTraverser((ae := a.expr).op(ae.left.traverse(ExpandTraverser()).result, ae.right.traverse(ExpandTraverser()).result))


@dataclass
class CalcTraverser(Traverser):
    result: float = 0.0

    def const(self, c: Const):
        return CalcTraverser(c.value)

    def var(self, v: Var):
        return self

    def op(self, op: Op, left, right):
        return CalcTraverser(op.op(left.result, right.result))

    def agg(self, a: Aggregator):
        return CalcTraverser(a.expr().traverse(CalcTraverser()).result)


@dataclass
class ExprReplacer(Traverser):
    old: Expr = None
    new: Expr = None

    def const(self, c: Const):
        return self.new if c.equals(self.old) else c

    def var(self, v: Var):
        return self.new if v.equals(self.old) else v

    def op(self, op: Op, left, right):
        return right if left is None else left if right is None else self.new if op.equals(self.old) else op.__class__(left=left, right=right)

    def agg(self, a: Aggregator):
        return self.new if a.equals(self.old) else a


@dataclass
class Contains(Traverser):
    expr: Expr = None
    found: bool = False

    def const(self, c: Const):
        return c.equals(self.expr)

    def var(self, v: Var):
        return v.equals(self.expr)

    def op(self, op: Op, left, right):
        return op.equals(self.expr) or left or right

    def agg(self, a: Aggregator):
        return a.equals(self.expr)


@dataclass(eq=False)
class Aggregator(Terminal, ABC):
    lst: Iterable = field(default_factory=list)
    f: Callable = ident
    expr: Callable = ident


X = TypeVar('X')
Y = TypeVar('Y')


def V(*it: Iterable[X]) -> Callable[[Callable[[Iterable[X]], Y]], Iterable[Y]]:
    return lambda f: [f(*p) for p in itertools.product(*it)]
