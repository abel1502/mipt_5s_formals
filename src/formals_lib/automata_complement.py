from __future__ import annotations
import typing

from .automata import *
from .automata_determ import MakeFullDFA


class AutomataComplement(MakeFullDFA):
    def apply(self) -> Automata:
        result: Automata = super().apply()
        
        for node in result.get_nodes():
            node.is_term = not node.is_term
        
        return result


def complement(aut: Automata) -> Automata:
    return AutomataComplement(aut).apply()
