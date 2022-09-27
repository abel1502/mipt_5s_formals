from __future__ import annotations
import typing

from .regex import *
from .itree import TreeVisitor


class RegexOptimizer(TreeVisitor[Regex]):
    warn_on_generic: typing.ClassVar[bool] = True
    

    @itree.TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> Regex:
        return node
    
    @itree.TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> Regex:
        return node
    
    @itree.TreeVisitor.handler(One)
    def visit_one(self, node: One) -> Regex:
        return node
    
    @itree.TreeVisitor.handler(Concat)
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
        
        return Concat(*result)

    @itree.TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> Regex:
        child_regex: Regex = self.visit(node.get_children()[0])
        
        if isinstance(child_regex, (Zero, One)):
            return One()
        
        return Star(child_regex)

    @itree.TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> Regex:
        result: typing.Set[Regex] = set()

        for child in node.get_children():
            child_regex: Regex = self.visit(child)
            
            if isinstance(child_regex, Zero):
                continue
            
            if isinstance(child_regex, Either):
                result.update(child_regex.get_children())
                continue
            
            result.add(child_regex)
        
        return Either(*result)


def optimize(regex: Regex) -> Regex:
    return RegexOptimizer().visit(regex)
