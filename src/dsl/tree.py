from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Callable
from tail_recurse import tail_call


from utils.utils import Copyable, Deque


@dataclass(eq=True, frozen=False, kw_only=True)
class Tree(Copyable, ABC):
    left: Tree | None = None
    right: Tree | None = None
    _visited: bool = False

    @dataclass
    class _Wrapper(Copyable):
        payload: Tree | None
        visited: bool = False

    def _dfs_(self, order: Callable[[_Wrapper], list[_Wrapper]]) -> list[Tree]:
        go = tail_call(lambda stack, acc=Deque(): (
            acc if not stack  # base case
            else go(stack, acc) if (x := stack.popleft()).payload is None  # leaf reached
            else go(stack, acc + x.payload) if x.visited  # visited nodes can be stored
            else go(order(x) + stack, acc)))  # otherwise, visit the nodes

        return go(Deque([Tree._Wrapper(self)]))

    def _dfs(self, order: Callable[[_Wrapper], list[_Wrapper]]) -> list[Tree]:
        #go = tail_call(lambda stack, acc=Deque(): (
        @tail_call
        def go(stack, acc=Deque()):
            return (
                acc if not stack  # base case
                else go(stack, acc) if (x := stack.popleft()) is None  # leaf reached
                else go(stack, acc + x) if x._visited  # visited nodes can be stored
                else go(order(x) + stack, acc))  # otherwise, visit the nodes

        res = go(Deque([self]))
        #print(res)
        #res2 = []
        for expr in res:
            expr._visited=False
            #res2.append(expr)
        return res


    def _dfs_list(self, order: Callable[[_Wrapper], list[_Wrapper]]) -> list[Tree]:
        go = tail_call(lambda stack, acc=[]: (
            acc if not stack  # base case
            else go(stack, acc) if (x := stack.pop(0)).payload is None  # leaf reached
            else go(stack, acc + [x.payload]) if x.visited  # visited nodes can be stored
            else go(order(x) + stack, acc)))  # otherwise, visit the nodes

        return go([Tree._Wrapper(self)])

    def preorder(self) -> list[Tree]:
        return self._dfs_(lambda x: [x.copy(visited=True), Tree._Wrapper(x.payload.left), Tree._Wrapper(x.payload.right)])

    def inorder(self) -> list[Tree]:
        return self._dfs_(lambda x: [Tree._Wrapper(x.payload.left), x.copy(visited=True), Tree._Wrapper(x.payload.right)])

    def postorder(self) -> list[Tree]:
        return self._dfs_(lambda x: [Tree._Wrapper(x.payload.left), Tree._Wrapper(x.payload.right), x.copy(visited=True)])
        #def order(x):
        #    x._visited = True
        #    return [x.left, x.right, x.copy(_visited=True)]
        #return self._dfs(order)