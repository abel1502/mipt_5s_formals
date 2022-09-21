from __future__ import annotations
from gc import unfreeze
from hashlib import new
from re import A, L
import typing
import dataclasses
from collections import deque


KeyType = typing.Any


@dataclasses.dataclass
class Node:
    key: KeyType
    out: typing.Set["Edge"] = dataclasses.field(default_factory=lambda: set())
    is_term: bool = False

    def get_edges(self, *,
                  label_full:  str | None = None,
                  label_start: str | None = None) -> typing.Generator[Edge, None, None]:
        raise NotImplementedError()
    
    def get_unique_edge(self, *,
                        label_full:  str | None = None,
                        label_start: str | None = None,
                        or_none: bool = True) -> Edge | None:
        raise NotImplementedError()
    
    def is_deterministic(self) -> bool:
        return all(len(e) == 1 for e in self.out)
    
    def __hash__(self) -> int:
        # It's certainly fine here, since we never consider nodes 'equal'
        return id(self)


# TODO: ?
@dataclasses.dataclass(frozen=True)
class Edge:
    label: str
    src: "Node"
    dst: "Node"

    def __len__(self) -> int:
        return len(self.label)


class Automata:
    alphabet: str
    _nodes: typing.Set[Node]
    _node_lookup: typing.Dict[KeyType, Node]
    _next_id: int
    _edges: typing.Set[Edge]
    start: Node  # Attention: start's id isn't always zero!


    def __init__(self, alphabet: str):
        self.alphabet = alphabet
        self._nodes = set()
        self._node_lookup = {}
        self._next_id = 0
        self._edges = set()
        self.start = self.make_node()

    def make_node(self, key=None, term=False) -> Node:
        """
        If key is None, i is used by default
        """

        if key is None:
            key = self._get_next_id()

        node = Node(key, is_term=term)
        
        self._nodes.add(node)

        self.change_key(node, key)

        return node
    
    def set_start(self, new_start: Node | KeyType) -> None:
        """
        Changes the start to be new_start
        """

        if not isinstance(new_start, Node):
            new_start = self.node(new_start)

        self.start = new_start
    
    def node(self, key: KeyType) -> Node:
        return self._node_lookup[key]
    
    def __getitem__(self, key: KeyType) -> Node:
        return self.node(key)
    
    def __contains__(self, key: KeyType) -> Node:
        return key in self._node_lookup

    def link(self, src: Node | KeyType, dst: Node | KeyType, label: str) -> Edge:
        if not isinstance(src, Node):
            src = self.node(src)
        if not isinstance(dst, Node):
            dst = self.node(dst)
        
        edge: Edge = Edge(label, src, dst)
        self._edges.add(edge)
        src.out.add(edge)
        return edge
    
    def unlink(self, edge: Edge) -> Edge:
        assert edge in self.get_edges()

        self._edges.remove(edge)

        edge.src.out.remove(edge)

        return edge
    
    def remove_node(self, node: Node) -> Node:
        self.remove_nodes([node])
        return Node
    
    def remove_nodes(self, nodes: typing.Iterable[Node]) -> None:
        nodes: typing.Set[Node] = set(nodes)

        for node in nodes:
            assert node in self._nodes
            self._nodes.remove(node)

        # Copying to avoid messing up the iteration
        for edge in list(self.get_edges()):
            if edge.src in nodes or edge.dst in nodes:
                self.unlink(edge)
    
    def change_key(self, node: Node | KeyType | None, key: KeyType) -> None:
        if not isinstance(node, Node):
            node = self.node(node)
        
        # Copying to avoid messing up the iteration
        for k, v in list(self._node_lookup.items()):
            if v is node:
                self._node_lookup.pop(k)
        
        if key is None:
            key = self._get_next_id()

        assert key not in self._node_lookup, "Duplicate key detected"
        self._node_lookup[key] = node

        node.key = key

    def _get_next_id(self) -> int:
        result: int = self._next_id
        self._next_id += 1
        return result

    def get_nodes(self) -> typing.Iterable[Node]:
        return self._nodes

    def get_edges(self) -> typing.Iterable[Edge]:
        return self._edges
    
    def get_terms(self) -> typing.Iterable[Node]:
        return (node for node in self.get_nodes() if node.is_term)
    
    def is_deterministic(self) -> bool:
        return all(len(e) == 1 for e in self.get_edges())
    
    def copy(self) -> Automata:
        result = Automata(self.alphabet)

        result._next_id = self._next_id
        result.start.is_term = self.start.is_term
        result.start.key = self.start.key

        for node in self.get_nodes():
            if node is self.start:
                continue
            result.make_node(key=node.key, term=node.is_term)
        
        for edge in self.get_edges():
            result.link(edge.src.key, edge.dst.key, edge.label)
        
        return result

    def __copy__(self) -> Automata:
        return self.copy()
    
    def __deepcopy__(self) -> Automata:
        return self.copy()
    
    def __len__(self) -> int:
        return len(self._nodes)


class AutomataVisitor:
    _queue: typing.Deque[typing.Tuple[Edge | None, Node]]
    _seen: typing.Set[Node]


    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        self._queue = deque()
        self._seen = set()

    def visit(self, automata: Automata, start: Node | None = None) -> None:
        if start is None:
            start = automata.start

        self.enqueue(None, start)

        while self._queue:
            edge, node = self._queue.popleft()

            if self.was_seen(node):
                continue
            self.mark_seen(node)

            self.visit_node(edge, node)
    
    def visit_node(self, edge: Edge | None, node: Node) -> None:
        self.enqueue(node)
    
    def was_seen(self, node: Node) -> bool:
        return node in self._seen
    
    def mark_seen(self, node: Node) -> None:
        self._seen.add(node)

    @typing.overload
    def enqueue(self, edge: Edge | None, node: Node) -> None:
        ...
    
    @typing.overload
    def enqueue(self, edge: Edge) -> None:
        ...
    
    @typing.overload
    def enqueue(self, node: Node) -> None:
        """
        Note: enqueues all children of given node!
        """
        ...

    def enqueue(self, *args):
        edge: Edge
        node: Node

        if len(args) == 2:
            edge, node = args
            assert isinstance(edge, (Edge, type(None)))
            assert isinstance(node, Node)
            assert edge is None or edge.dst is node, "Invalid edge/node pair"

            self._queue.append((edge, node))
            return
        
        assert len(args) == 1

        if isinstance(args[0], Edge):
            edge = args[0]

            self._queue.append((edge, edge.dst))
            return
        
        if isinstance(args[0], Node):
            node = args[0]

            for edge in node.out:
                self.enqueue(edge)
            return
        
        assert False
    
    def popqueue(self) -> typing.Tuple[Edge | None, Node]:
        return self._queue.popleft()


# TODO: Maybe a Transformer class?
# class Transformer(Visitor):
#     pass

