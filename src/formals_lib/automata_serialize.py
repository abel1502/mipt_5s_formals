from __future__ import annotations
import typing
import dataclasses
from collections import deque
import pathlib
import io
from ast import literal_eval


from .automata import *


class AutomataSerializer:
    aut: Automata
    _buf: io.StringIO
    
    
    def __init__(self, aut: Automata):
        self.aut = aut
        self._buf = io.StringIO()
    
    def _write(self, data: str) -> None:
        self._buf.write(data)
    
    def _writeln(self, data: str = "") -> None:
        self._write(data)
        self._write("\n")
    
    def _get_result(self) -> str:
        return self._buf.getvalue()
    
    def serialize_file(self, fname: pathlib.Path | str) -> None:
        result: str = self.serialize()
        
        with open(fname, "w") as f:
            f.write(result)

    def serialize(self) -> str:
        self.serialize_header()
        self._writeln()
        self.serialize_nodes()
        self._writeln()
        self.serialize_edges()
        
        return self._get_result()

    def serialize_header(self) -> None:
        self._writeln(repr(self.aut.alphabet))
    
    def serialize_nodes(self) -> None:
        for node in self.aut.get_nodes():
            self.serialize_node(node)
    
    def serialize_edges(self) -> None:
        for edge in self.aut.get_edges():
            self.serialize_edge(edge)
    
    @staticmethod
    def _check_key_serializeable(key: KeyType) -> bool:
        if isinstance(key, (int, str)):
            return True
        
        if isinstance(key, tuple):
            return all(map(AutomataSerializer._check_key_serializeable, key))
        
        return False
    
    def serialize_node(self, node: Node) -> None:
        if not self._check_key_serializeable(node.key):
            raise TypeError(f"Keys of type {type(node.key).__qualname__} cannot be serialized")
        
        self._write(repr(node.key))
        if node.is_term:
            self._write(" T")
        self._writeln()
    
    def serialize_edge(self, edge: Edge) -> None:
        raise NotImplementedError()
