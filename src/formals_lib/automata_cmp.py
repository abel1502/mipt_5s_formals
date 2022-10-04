from __future__ import annotations
import typing
from collections import deque

from .automata import *
from .automata_determ import make_full_dfa


class AutomataComparator:
    _auts: typing.Tuple[Automata, Automata]
    _visited: typing.Set[typing.Tuple[Node, Node]]
    _queue: typing.Deque[typing.Tuple[Node, Node]]
    
    def __init__(self, aut1: Automata, aut2: Automata) -> None:
        self._auts = (make_full_dfa(aut1), make_full_dfa(aut2))
        self._visited = set()
        self._queue = deque()
        
        self._queue.append((self._auts[0].start, self._auts[1].start))
    
    def compare(self) -> bool:
        while self._queue:
            node1, node2 = self._queue.popleft()
            
            if (node1, node2) in self._visited:
                continue
            
            self._visited.add((node1, node2))
            
            if node1.is_term != node2.is_term:
                return False
            
            for edge1 in node1.out:
                edge2 = node2.get_only_edge(edge1.label)
                
                self._queue.append((edge1.dst, edge2.dst))
        
        return True


def compare_automatas(aut1: Automata, aut2: Automata) -> bool:
    return AutomataComparator(aut1, aut2).compare()


__all__ = [
    'compare_automatas',
]
