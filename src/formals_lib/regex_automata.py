from __future__ import annotations
import typing
import dataclasses
from collections import deque
import itertools

from .automata import *
from .automata_ops import *
from .regex import *
from .itree import TreeVisitor
from .automata_determ import make_edges_1, unify_term
from .regex_optimize import optimize


class RegexToAutomataConverter(TreeVisitor[Regex]):
    warn_on_generic: typing.ClassVar[bool] = True
    
    _alphabet: str | None
    
    
    def __init__(self, alphabet: str | None = None):
        super().__init__()
        
        self._alphabet = alphabet
    
    def apply(self, regex: Regex) -> Automata:
        result: Automata = self.visit(regex)
        
        if self._alphabet is not None:
            assert set(result.alphabet).issubset(set(self._alphabet)), "Unspecified alphabet used!"
            
            result.alphabet = self._alphabet
        
        return result
    
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


class AutomataToRegexConverter:
    aut: Automata
    
    def __init__(self, aut: Automata):
        self.aut = aut
    
    def apply(self) -> Regex:
        self._prepare()
        
        self._merge_parallel_edges()
        
        while len(self.aut) > 2:
            self._step()
        
        if self.aut.start.is_term and len(self.aut) == 2:
            self._step()
        
        # return self._finalize()
        return optimize(self._finalize())
    
    def _prepare(self) -> None:
        self.aut = make_edges_1(self.aut)
        self.aut = unify_term(self.aut)
        self.aut = trim(self.aut)
        
        self._convert_to_re_automata()
    
        # TODO: Some assertions (?)
    
    def _convert_to_re_automata(self) -> None:
        # Very dirty, but works:
        # Internally, we simply use Regex'es for
        # automata edge labels. Have to be careful with 
        
        # Copying to avoid messing up the iteration
        for edge in list(self.aut.get_edges()):
            self.aut.unlink(edge)
            regex: Regex = Letter(edge.label) if edge.label else One()
            self.aut.link(edge.src, edge.dst, regex)
        
        for node in self.aut.get_nodes():
            self._add_loop(node)
    
    def _add_loop(self, node: Node) -> None:
        for edge in node.out:
            if edge.dst is node:
                return
        
        self.aut.link(node, node, Zero())
    
    def _get_loop(self, node: Node) -> Edge:
        return next(
            e for e in self.aut.get_edges()
            if e.dst is node and e.src is node
        )
    
    def _step(self) -> None:
        target: Node = self._find_target()
        
        # print(f"> Step {target.key!r}:")
        # print(f"    {len(self.aut)} nodes left")
        
        # Copying to avoid messing up the iteration
        edges_in: typing.Iterable[Edge] = [
            e for e in self.aut.get_edges()
            if e.dst is target and e.src is not target
        ]
        
        edges_out: typing.Iterable[Edge] = target.out
        
        # print(f"    {len(edges_in) * len(edges_out)} edge pairs to handle")
        
        loop_regex: Regex = Star(self._get_loop(target).label)
        
        to_link: typing.List[typing.Tuple[Node, Node, Regex]] = []
        
        for edge_in, edge_out in itertools.product(edges_in, edges_out):
            edge_in: Edge
            edge_out: Edge
            
            # To avoid messing up the iterables
            to_link.append((
                edge_in.src,
                edge_out.dst,
                Concat(edge_in.label, loop_regex, edge_out.label)
            ))
        
        # TODO: This, apparently, may include target as src or dst!
        for src, dst, label in to_link:
            self.aut.link(src, dst, label)
        
        self.aut.remove_node(target)
        
        self._merge_parallel_edges()
    
    def _find_target(self) -> Node:
        # Will raise StopIteration if no targets are available,
        # but that shouldn't occur during normal operation
        return next(n for n in self.aut.get_nodes()
                    if n is not self.aut.start and not n.is_term)
    
    def _merge_parallel_edges(self) -> None:
        for src in self.aut.get_nodes():
            outs: typing.Dict[Node, typing.Set[Edge]] = {}
            
            for edge in src.out:
                outs.setdefault(edge.dst, set()).add(edge)
            
            for dst, edges in outs.items():
                if len(edges) <= 1:
                    continue
                
                self.aut.unlink_many(edges)
                self.aut.link(src, dst, Either(*map(lambda e: e.label, edges)))
    
    def _finalize(self) -> Regex:
        start: Node = self.aut.start
        
        if start.is_term:
            assert len(self.aut) == 1
            return Star(self._get_loop(start).label)
        
        if len(self.aut) == 1:
            assert not start.is_term
            return Zero()
        
        assert len(self.aut) == 2
        assert len(self.aut.get_edges()) <= 3
        
        non_start: Node = next(
            n for n in self.aut.get_nodes()
            if n is not start
        )
        
        # Shouldn't fail during normal operation
        edge: Edge = next(e for e in start.out if e.dst is non_start)
        
        assert not start.is_term and non_start.is_term
        
        return Concat(
            Star(self._get_loop(start).label),
            edge.label,
            Star(self._get_loop(non_start).label),
        )

       
def regex_to_automata(regex: Regex, alphabet: str | None = None) -> Automata:
    return RegexToAutomataConverter(alphabet=alphabet).apply(regex)


def automata_to_regex(aut: Automata) -> Regex:
    return AutomataToRegexConverter(aut).apply()
