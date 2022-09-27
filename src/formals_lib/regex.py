from __future__ import annotations
import typing
import enum
import contextlib
import dataclasses

from . import itree


@dataclasses.dataclass(frozen=True)
class Regex(itree.ITree["Regex"]):
    def __add__(self, other):
        if not isinstance(other, Regex):
            return NotImplemented
        if isinstance(other, Either):
            return other.__radd__(self)
        return Either(self, other)
    
    def __radd__(self, other):
        if not isinstance(other, Regex):
            return NotImplemented
        return other.__add__(self)
    
    def __mul__(self, other):
        if not isinstance(other, Regex):
            return NotImplemented
        if isinstance(other, Concat):
            return other.__rmul__(self)
        return Concat(self, other)
    
    def __rmul__(self, other):
        if not isinstance(other, Regex):
            return NotImplemented
        return other.__mul__(self)
    
    def repeat(self, n: int) -> Regex:
        return Concat(*([self] * n))
    
    def __pow__(self, power):
        if isinstance(power, int):
            return self.repeat(power)
        return NotImplemented
    
    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        
        for child1, child2 in zip(self.get_children(), other.get_children()):
            if child1 != child2:
                return False
        
        return True


@dataclasses.dataclass(frozen=True)
class Letter(Regex):
    letter: str
    
    def __init__(self, letter: str):
        assert len(letter) == 1
        
        object.__setattr__(self, "letter", letter)
    
    def get_children(self) -> typing.Iterable[Regex]:
        return ()
    
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.letter == other.letter


class Zero(Regex):
    def get_children(self) -> typing.Iterable[Regex]:
        return ()


class One(Regex):
    def get_children(self) -> typing.Iterable[Regex]:
        return ()


@dataclasses.dataclass(frozen=True)
class Concat(Regex):
    _children: typing.List[Regex]
    
    def __init__(self, *children: Regex):
        object.__setattr__(self, "_children", children)
    
    def get_children(self) -> typing.Iterable[Regex]:
        return tuple(self._children)


# TODO: Maybe smart Repeat for optimization?


@dataclasses.dataclass(frozen=True)
class Star(Regex):
    _child: Regex
    
    def __init__(self, child: Regex):
        object.__setattr__(self, "_child", child)
    
    def get_children(self) -> typing.Iterable[Regex]:
        return (self._child,)


# TODO: Plus (as power)?


@dataclasses.dataclass(frozen=True)
class Either(Regex):
    _children: typing.List[Regex]
    
    def __init__(self, *children: Regex):
        object.__setattr__(self, "_children", children)
    
    def get_children(self) -> typing.Iterable[Regex]:
        return tuple(self._children)


class Reconstructor(itree.TreeVisitor[Regex]):
    warn_on_generic: typing.ClassVar[bool] = True
    
    
    class ParLevel(enum.IntEnum):
        none = 0
        either = 1
        concat = 2
    

    _par_level: ParLevel


    def __init__(self):
        super().__init__()

        self._par_level = self.ParLevel.none
    
    @contextlib.contextmanager
    def _set_par_level(self, level: ParLevel):
        old_level: self.ParLevel = self._par_level
        self._par_level = level
        yield
        self._par_level = old_level

    @itree.TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> str:
        return node.letter
    
    @itree.TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> str:
        return "0"
    
    @itree.TreeVisitor.handler(One)
    def visit_one(self, node: One) -> str:
        return "1"
    
    @itree.TreeVisitor.handler(Concat)
    def visit_concat(self, node: Concat) -> str:
        result: typing.List[str] = []

        with self._set_par_level(self.ParLevel.either):
            for child in node.get_children():
                result.append(self.visit(child))
        
        result: str = "".join(result)
        if self._par_level >= self.ParLevel.concat:
            result = f"({result})"
        
        return result

    @itree.TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> str:
        with self._set_par_level(self.ParLevel.concat):
            return self.visit(node.get_children()[0]) + "*"

    @itree.TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> str:
        result: typing.List[str] = []

        with self._set_par_level(self.ParLevel.none):
            for child in node.get_children():
                result.append(self.visit(child))
        
        result: str = "+".join(result)
        if self._par_level >= self.ParLevel.either:
            result = f"({result})"
        
        return result
    

def reconstruct(regex: Regex) -> str:
    return Reconstructor().visit(regex)




