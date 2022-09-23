from __future__ import annotations
import typing

from .automata import *


class BaseAutomataBinOp:
    auts: typing.Tuple[Automata, Automata]


    def __init__(self, aut1: Automata, aut2: Automata):
        self.auts = (aut1, aut2)
    
    @property
    def aut1(self) -> Automata:
        return self.auts[0]
    
    @property
    def aut2(self) -> Automata:
        return self.auts[1]
    
    def apply(self) -> Automata:
        raise NotImplementedError()
    
    def common_alphabet(self) -> str:
        return ''.join(set(self.aut1.alphabet) | set(self.aut2.alphabet))
    
    def raw_merge(self) -> Automata:
        """
        Merges aut1 and aut2, removing term markers and introducing a new, unconnected starting node.
        The keys are created as tuples of (aut.id, node.key), aut.id being 0 or 1
        """

        result = Automata(self.common_alphabet())
        
        for i in range(2):
            for node in self.auts[i].get_nodes():
                result.make_node(key=(i, node.key))

            for edge in self.auts[i].get_edges():
                result.link(
                    (i, edge.src.key),
                    (i, edge.dst.key),
                    edge.label
                )
    
    def raw_cross(self) -> Automata:
        """
        Makes the cross product of aut1 and aut2,
        using the (0, 0) node as the starting one and
        marking only those nodes as term, which are term in both automatas
        The keys are created as tuples of (node1.key, node2.key)
        """

        result = Automata(self.common_alphabet())

        result.change_key(result.start, (0, 0))
        
        for node1 in self.aut1.get_nodes():
            for node2 in self.aut2.get_nodes():
                result.make_node(
                    key=(node1.key, node2.key),
                    term=node1.is_term and node2.is_term
                )
        
        for edge1 in self.aut1.get_edges():
            for node2 in self.aut2.get_nodes():
                result.link(
                    (edge1.src.key, node2.key),
                    (edge1.dst.key, node2.key),
                    edge1.label
                )
        
        for node1 in self.aut1.get_nodes():
            for edge2 in self.aut2.get_edges():
                result.link(
                    (node1.key, edge2.src.key),
                    (node1.key, edge2.dst.key),
                    edge2.label
                )


class BaseAutomataTransform:
    aut: Automata


    def __init__(self, aut: Automata):
        self.aut = aut
    
    def apply(self) -> Automata:
        raise NotImplementedError()
    
    def raw_copy(self) -> Automata:
        """
        Just copies the automata
        """

        return self.aut.copy()


# End of base classes, begin specific optimizations

class AutomataConcat(BaseAutomataBinOp):
    def apply(self) -> Automata:
        result: Automata = self.raw_merge()

        result.link(result.start, (0, 0), "")

        for node in self.aut1.get_terms():
            result.link((0, node.key), (1, 0), "")
        
        for node in self.aut2.get_terms():
            result.node((1, node.key)).is_term = True
        
        return result


class AutomataJoin(BaseAutomataBinOp):
    def apply(self) -> Automata:
        result: Automata = self.raw_merge()

        result.link(result.start, (0, 0), "")
        result.link(result.start, (1, 0), "")

        end: Node = result.make_node(term=True)

        for i in range(2):
            for node in self.aut[i].get_terms():
                result.link((i, node.key), end, "")
        
        return result


class AutomataIntersect(BaseAutomataBinOp):
    def apply(self) -> Automata:
        result: Automata = self.raw_cross()

        # No more work needed, actually
        
        return result


class AutomataStar(BaseAutomataTransform):
    def apply(self) -> Automata:
        result: Automata = self.raw_copy()

        new_start: Node = result.make_node(term=True)
        result.link(new_start, result.start, "")
        result.set_start(new_start)

        for node in result.get_terms():
            node.is_term = False
            result.link(node, new_start, "")
        
        return result


class AutomataPlusPow(BaseAutomataTransform):
    def apply(self) -> Automata:
        result: Automata = self.raw_copy()

        new_start: Node = result.make_node()
        result.link(new_start, result.start, "")
        result.set_start(new_start)

        for node in result.get_terms():
            result.link(node, new_start, "")
        
        return result


class AutomataTrimmer(BaseAutomataTransform):
    def apply(self) -> Automata:
        result = self.raw_copy()

        vis = AutomataVisitor()
        vis.visit(result)

        to_remove: typing.List[Node] = []
        for node in result.get_nodes():
            if not vis.was_seen(node):
                to_remove.append(node)
        
        result.remove_nodes(to_remove)

        return result


def concat(aut1: Automata, aut2: Automata) -> Automata:
    return AutomataConcat(aut1, aut2).apply()


def join(aut1: Automata, aut2: Automata) -> Automata:
    return AutomataJoin(aut1, aut2).apply()


def intersect(aut1: Automata, aut2: Automata) -> Automata:
    return AutomataIntersect(aut1, aut2).apply()


def star(aut: Automata) -> Automata:
    return AutomataStar(aut).apply()


def pow_plus(aut: Automata) -> Automata:
    return AutomataPlusPow(aut).apply()


def trim(aut: Automata) -> Automata:
    return AutomataTrimmer(aut).apply()


# AutomataComplement and complement() are implemented in a separate file, since they rely on make_full_dfa()
