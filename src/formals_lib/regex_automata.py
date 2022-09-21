from __future__ import annotations
import typing
import dataclasses
from collections import deque


from .automata import *
from .automata_ops import *
from .regex import *
from .itree import TreeVisitor
# from .automata_determ import make_edges_1


class RegexToAutomataConverter(TreeVisitor[Regex]):
    @TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> Automata:
        result = Automata(node.letter)
        
        result.link(result.start, result.make_node(term=True), node.letter)
        
        return result
    
    @TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> Automata:
        result = Automata("")
        
        return result
    
    @TreeVisitor.handler(One)
    def visit_one(self, node: One) -> Automata:
        result = Automata("")
        
        result.start.is_term = True
        
        return result
    
    @TreeVisitor.handler(Concat)
    def visit_concat(self, node: Concat) -> Automata:
        children: typing.Iterable[Regex] = node.get_children()
        
        if len(children) == 0:
            return self.visit(One())
        
        children: typing.Iterator[Regex] = iter(children)
        
        result: Automata = self.visit(next(children))
        for child in children:
            result = concat(result, self.visit(child))
        
        return result

    @TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> Automata:
        return star(self.visit(node.get_children()[0]))

    @TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> Automata:
        children: typing.Iterable[Regex] = node.get_children()
        
        if len(children) == 0:
            return self.visit(Zero())
        
        children: typing.Iterator[Regex] = iter(children)
        
        result: Automata = self.visit(next(children))
        for child in children:
            result = join(result, self.visit(child))
        
        return result


# TODO: Maybe implement later
# class AutomataToRegexConverter:
#     aut: Automata
#     
#     def __init__(self, aut: Automata):
#         self.aut = make_edges_1(aut)
#     
#     def _convert_to_re_automata(self) -> None:
#         # Very dirty, but works(...
#         
#         # Copying to avoid messing up the iteration
#         for edge in list(self.aut.get_edges()):
#             self.aut.unlink(edge)
#             self.aut.link(edge.src, edge.dst, Letter(edge.label))
#         
#         for node in self.aut.get_nodes():
#             self._add_loop(node)
#     
#     def _add_loop(self, node: Node) -> None:
#         for edge in node.get_edges():
#             if edge.dst is node:
#                 return
#         
#         self.aut.link(node, node, Zero())
#     
#     def apply(self) -> Regex:
#         while len(self.aut) > 2:
#             self.step()
        

def regex_to_automata(regex: Regex) -> Automata:
    return RegexToAutomataConverter().visit(regex)
