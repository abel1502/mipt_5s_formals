from __future__ import annotations
import typing
import abc
import warnings


T = typing.TypeVar("T", bound="ITree")


class ITree(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    def get_children(self) -> typing.Iterable[T]:
        pass


class TreeVisitor(typing.Generic[T]):
    warn_on_generic: typing.ClassVar[bool] = False

    _lookup: typing.ClassVar[typing.Mapping[typing.Type[T], typing.Callable[["TreeVisitor", T]]]]
    
    @staticmethod
    def handler(node_type: typing.Type[T]):
        assert issubclass(node_type, ITree), "Handlers can only be specified for node types"

        #pylint:disable=W0212
        def wrap(method: typing.Callable[["TreeVisitor", T]]) -> typing.Callable[["TreeVisitor", T]]:
            assert callable(method), "Only methods should be decorated with Visitor.handler"
            if not hasattr(method, "_visits_"):
                method._visits_ = set()
            assert isinstance(method._visits_, set)
            method._visits_.add(node_type)
            return method
        return wrap
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        cls._lookup = {}
        
        for member in cls.__dict__.values():
            if not hasattr(member, "_visits_"):
                continue
            assert callable(member)
            
            for node_type in member._visits_:
                assert node_type not in cls._lookup, f"Duplicate handler for {node_type.__name__}"
                cls._lookup[node_type] = member
    
    def __init__(self):
        pass

    def visit(self, node: T) -> typing.Any:
        for base in type(node).__mro__:
            if base in self._lookup:
                return self._lookup[base](self, node)
        
        if self.warn_on_generic:
            warnings.warn(f"Handler for {type(node).__qualname__} not specified, defaulting to iterating over children")
            assert False, "Comment this out if you don't want to be THIS pedantic"

        return self.generic_visit(node)
    
    def generic_visit(self, node: T) -> None:
        for child in node.get_children():
            self.visit(child)



__all__ = [
    "ITree", "TreeVisitor",
]
