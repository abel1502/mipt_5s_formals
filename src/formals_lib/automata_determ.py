from __future__ import annotations
import typing
import dataclasses
from collections import deque

from .automata import *
from .automata_ops import *


class MakeEdges01(BaseAutomataTransform):
    def apply(self) -> Automata:
        result: Automata = self.raw_copy()
        
        # Copying to avoid messing up the iteration
        for edge in list(result.get_edges()):
            edge: Edge

            self.split_edge(result, edge)

        return result
    
    @staticmethod
    def split_edge(aut: Automata, edge: Edge) -> None:
        if len(edge) <= 1:
            return
        
        aut.unlink(edge)
        
        prev: Node = edge.src
        cur: Node
        for i in range(len(edge) - 1):
            cur = aut.make_node()
            aut.link(prev, cur, edge.label[i])
            prev = cur
        aut.link(prev, edge.dst, edge.label[-1])


class MakeEdges1(MakeEdges01):
    def apply(self) -> Automata:
        result: Automata = super().apply()
        
        self.propagate_terms(result)

        for node in result.get_nodes():
            node: Node

            self.handle_epsilon_subtree(result, node)
        
        # Copying to avoid messing up the iteration
        for edge in list(result.get_edges()):
            edge: Edge

            if len(edge) > 0:
                continue
            
            result.unlink(edge)

        return result
    
    @staticmethod
    def propagate_terms(aut: Automata) -> None:
        reverse_edges: typing.Dict[Node, typing.List[Node]] = {}

        for edge in aut.get_edges():
            if len(edge) > 0:
                continue
            reverse_edges.setdefault(edge.dst, []).append(edge.src)
        
        queue: typing.Deque[Node] = deque()
        queue.extend(aut.get_terms())

        while queue:
            node: Node = queue.popleft()

            node.is_term = True

            for child in reverse_edges.get(node, []):
                if child.is_term:
                    continue
                queue.append(child)
        
        return aut
    
    @staticmethod
    def handle_epsilon_subtree(aut: Automata, start: Node) -> None:
        queue: typing.Deque[Node] = deque()
        queue.append(start)

        epsilon_reachable: typing.Set[Node] = set()

        while queue:
            node: Node = queue.popleft()

            if node in epsilon_reachable:
                continue
            epsilon_reachable.add(node)

            for edge in node.out:
                if len(edge) > 0:
                    continue
                queue.append(edge.dst)
        
        epsilon_reachable.remove(start)

        for node in epsilon_reachable:
            for edge in node.out:
                if len(edge) == 0:
                    continue
                aut.link(start, edge.dst, edge.label)


class UnifyTerm(BaseAutomataTransform):
    def apply(self) -> Automata:
        result: Automata = self.raw_copy()
        
        end: Node = result.make_node(term=True)

        for node in result.get_terms():
            if node is end:
                continue

            node.is_term = False
            result.link(node, end, "")

        return result


class MakeDeterministic(BaseAutomataTransform):
    @dataclasses.dataclass
    class _NodeInfo:
        members: typing.Set[Node] = dataclasses.field(default_factory=set)
        is_term: bool = False

        def frozen_members(self) -> typing.FrozenSet[Node]:
            return frozenset(self.members)
    

    def apply(self) -> Automata:
        if self.aut.is_deterministic():
            return self.aut.copy()  # TODO: Maybe not copy?

        # We'll use that for our guideline, not the result
        self.aut = MakeEdges1(self.aut).apply()
        self.aut = AutomataTrimmer(self.aut).apply()

        result = Automata(self.aut.alphabet)

        result.change_key(result.start, frozenset([self.aut.start.key]))
        result.start.is_term = self.aut.start.is_term

        return self.bfs(result)
    
    def bfs(self, result: Automata) -> Automata:
        queue: typing.Deque[Node] = deque()
        queue.append(result.start)

        while queue:
            node: Node = queue.popleft()

            edges = self.gather_edges(node)

            for label, dst_info in edges.items():
                label: str
                dst_info: self._NodeInfo

                dst_key = dst_info.frozen_members()

                dst: Node

                if dst_key not in result:
                    dst = result.make_node(key=dst_key, term=dst_info.is_term)
                    queue.append(dst)
                else:
                    dst = result.node(dst_key)
                
                result.link(node, dst, label)

        return result
    
    def gather_edges(self, node: Node) -> typing.Dict[str, _NodeInfo]:
        result: typing.Dict[str, self._NodeInfo] = {}

        for subkey in node.key:
            for edge in self.aut[subkey].out:
                cur_node_info: self._NodeInfo = result.setdefault(edge.label, self._NodeInfo())
                cur_node_info.members.add(edge.dst.key)
                cur_node_info.is_term = cur_node_info.is_term or edge.dst.is_term

        return result


class MakeFullDFA(MakeDeterministic):
    def apply(self) -> Automata:
        result: Automata = super().apply()

        end: Node = result.make_node()

        for node in result.get_nodes():
            missing_alphabet: typing.Set[str] = set(result.alphabet)

            for edge in node.out:
                missing_alphabet.discard(edge.label)
            
            for letter in missing_alphabet:
                result.link(node, end, letter)
        
        return trim(result)


def make_edges_01(aut: Automata) -> Automata:
    return MakeEdges01(aut).apply()


def make_edges_1(aut: Automata) -> Automata:
    return MakeEdges1(aut).apply()


def unify_term(aut: Automata) -> Automata:
    return UnifyTerm(aut).apply()


def make_dfa(aut: Automata) -> Automata:
    return MakeDeterministic(aut).apply()


def make_full_dfa(aut: Automata) -> Automata:
    return MakeFullDFA(aut).apply()
