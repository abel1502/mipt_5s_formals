from __future__ import annotations
import typing
import dataclasses
from collections import UserDict, deque

from .automata import *
from .automata_ops import *
from .automata_determ import *


class _ClassMapper(UserDict):
    _counter: int
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._counter = 0
    
    def __missing__(self, key):
        result: int = self._counter
        self._counter += 1
        self[key] = result
        return result
    
    def clear(self) -> None:
        self._counter = 0
        return super().clear()


class AutomataMinimizer(BaseAutomataTransform):
    _class_table: typing.List[typing.List[int]]
    _step_idx: int
    _aut_nodes: typing.Final[typing.List[Node]]
    _node_idx_lookup: typing.Final[typing.Mapping[Node, int]]
    _transitions: typing.Final[typing.Mapping[typing.Tuple[int, str], int]]
    
    def __init__(self, aut: Automata):
        super().__init__(make_full_dfa(aut))
        
        self._class_table = [
            [int(node.is_term) for node in self.aut.get_nodes()],
            [None] * len(self.aut)
        ]
        self._step_idx = 0
        self._aut_nodes = list(self.aut.get_nodes())
        self._node_idx_lookup = {
            node: i for i, node in enumerate(self._aut_nodes)
        }
        self._transitions = self._bake_transitions()
    
    def apply(self) -> Automata:
        while not self.is_table_identical():
            self.step()
        
        return self.make_automata()
            

    def _bake_transitions(self) -> typing.Mapping[typing.Tuple[int, str], int]:
        transitions: typing.Dict[typing.Tuple[int, str], int] = {}
        
        for src_i, src in enumerate(self._aut_nodes):
            for edge in src.out:
                state = (src_i, edge.label)
                assert len(edge.label) == 1
                assert state not in transitions, "Duplicate edge!"
                
                dst = edge.dst
                dst_i = self.node_idx(dst)
                
                transitions[state] = dst_i
        
        return transitions
    
    @property
    def cur_table(self) -> typing.List[int]:
        return self._class_table[self._step_idx % 2]
    
    @property
    def prev_table(self) -> typing.List[int]:
        return self._class_table[(self._step_idx - 1) % 2]
    
    @property
    def nodes_cnt(self) -> int:
        return len(self._aut_nodes)
    
    def transition(self, src_i: int, letter: str) -> int:
        return self._transitions[src_i, letter]
    
    def node_idx(self, node: Node) -> int:
        return self._node_idx_lookup[node]
    
    def is_table_identical(self):
        return self.cur_table == self.prev_table
    
    def step(self):
        for letter in self.aut.alphabet:
            self._step_idx += 1
            
            prev_table: typing.List[int] = self.prev_table
            letter_table: typing.List[int] = [
                prev_table[self.transition(i, letter)]
                for i in range(self.nodes_cnt)
            ]
            
            cur_table: typing.List[int] = self.cur_table
            
            mapper = _ClassMapper()
            for i, cls in enumerate(zip(prev_table, letter_table)):
                cur_table[i] = mapper[cls]
    
    def make_automata(self) -> Automata:
        result: Automata = Automata(self.aut.alphabet)
        obsolete_start = result.start
        result.change_key(obsolete_start, -1)
        
        cur_table = self.cur_table
        
        for node, class_i in zip(self._aut_nodes, cur_table):
            new_node: Node
            
            if class_i not in result:
                new_node = result.make_node(key=class_i, term=node.is_term)
            else:
                new_node = result.node(class_i)
            
            assert new_node.is_term == node.is_term
            
        result.set_start(cur_table[self.node_idx(self.aut.start)])
        result.remove_node(obsolete_start)
        
        for edge in self.aut.get_edges():
            class_src: int = cur_table[self.node_idx(edge.src)]
            class_dst: int = cur_table[self.node_idx(edge.dst)]
            
            result.link(class_src, class_dst, edge.label)
        
        return result


def minimize(aut: Automata) -> Automata:
    return AutomataMinimizer(aut).apply()
