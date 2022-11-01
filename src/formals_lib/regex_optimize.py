from __future__ import annotations
import typing

from .regex import *
from .itree import TreeVisitor


class RegexOptimizer(TreeVisitor[Regex]):
    warn_on_generic: typing.ClassVar[bool] = True
    

    @TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> Regex:
        return node
    
    @TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> Regex:
        return node
    
    @TreeVisitor.handler(One)
    def visit_one(self, node: One) -> Regex:
        return node
    
    @TreeVisitor.handler(Concat)
    def visit_concat(self, node: Concat) -> Regex:
        result: typing.List[Regex] = []

        for child in node.get_children():
            child_regex: Regex = self.visit(child)
            
            if isinstance(child_regex, Zero):
                return child_regex
            
            if isinstance(child_regex, One):
                continue
            
            if isinstance(child_regex, Concat):
                result.extend(child_regex.get_children())
                continue
            
            result.append(child_regex)
        
        if len(result) == 0:
            return One()
        
        if len(result) == 1:
            return result[0]
        
        return Concat(*result)

    @TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> Regex:
        child_regex: Regex = self.visit(node.get_children()[0])
        
        if isinstance(child_regex, (Zero, One)):
            return One()
        
        return Star(child_regex)

    @TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> Regex:
        # Not a set because we want to preserve order
        result: typing.Dict[Regex, None] = dict()

        for child in node.get_children():
            child_regex: Regex = self.visit(child)
            
            if isinstance(child_regex, Zero):
                continue
            
            if isinstance(child_regex, Either):
                result.update(dict.fromkeys(child_regex.get_children()))
                continue
            
            result[child_regex] = None
        
        result: typing.List[Regex] = list(result.keys())
        
        if len(result) == 0:
            return Zero()
        
        if len(result) == 1:
            return result[0]
        
        return Either(*result)


def optimize_regex(regex: Regex) -> Regex:
    return RegexOptimizer().visit(regex)


__all__ = [
    "optimize_regex",
]
