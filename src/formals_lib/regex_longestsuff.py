from __future__ import annotations
import typing
import dataclasses

from .regex import *
from .itree import TreeVisitor


# Solves hw task 6.5, but encapsulated here to support unit-testing
class SuffixCounterVisitor(TreeVisitor[Regex]):
    warn_on_generic: typing.ClassVar[bool] = True
    
    _target_letter: str
    
    
    @dataclasses.dataclass
    class Result:
        # The longest an x-suffix can be
        # Can be integral or +inf
        best_suff_len: float
        # The longest the regex can be in the form of x^k (and nothing else)
        # Can be integral, +inf or None (if it cannot be expressed as x^k)
        best_full_len: float | None
        
        @property
        def can_be_full(self) -> bool:
            return self.best_full_len is not None
        
        def update_seq(self, other: "SuffixCounterVisitor.Result") -> None:
            """
            Note: Called right-to-left!
            """
            
            if not self.can_be_full:
                return
            
            self.best_suff_len = max(
                self.best_suff_len,
                self.best_full_len + other.best_suff_len
            )
            
            if not other.can_be_full:
                self.best_full_len = None
            else:
                self.best_full_len += other.best_full_len
        
        def update_alt(self, other: "SuffixCounterVisitor.Result") -> None:
            self.best_suff_len = max(
                self.best_suff_len,
                other.best_suff_len
            )
            
            self.best_full_len = max(
                self.best_full_len,
                other.best_full_len,
                key=lambda x: -1 if x is None else x
            )
    
    
    def __init__(self, target_letter: str):
        super().__init__()
        
        assert len(target_letter) == 1, f"Expected a single letter, got str of len {len(target_letter)}"
        
        self._target_letter = target_letter
    
    def apply(self, node: Regex, target_len: int) -> bool:
        assert target_len >= 0, "Target length must be non-negative"
        
        result_len: float = self.visit(node).best_suff_len
        
        return result_len >= target_len
    
    @TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> Result:
        if node.letter == self._target_letter:
            return self.Result(1, 1)
        return self.Result(0, None)
    
    @TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> Result:
        raise ValueError("Zero is not allowed in the regex")
    
    @TreeVisitor.handler(One)
    def visit_one(self, node: One) -> Result:
        return self.Result(0, 0)
    
    @TreeVisitor.handler(Concat)
    def visit_concat(self, node: Concat) -> Result:
        result: SuffixCounterVisitor.Result = self.Result(0, 0)
        
        for child in reversed(node.get_children()):
            result.update_seq(self.visit(child))
        
        return result

    @TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> Result:
        child_result: SuffixCounterVisitor.Result = self.visit(node.get_children()[0])
        
        if not child_result.can_be_full:
            return self.Result(child_result.best_suff_len, 0)
        
        if child_result.best_full_len > 0:
            return self.Result(float("+inf"), float("+inf"))
        
        return child_result

    @TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> Result:
        if len(node.get_children()) == 0:
            raise ValueError("Empty either (zero) is not allowed in the regex")
        
        result: SuffixCounterVisitor.Result = self.Result(0, None)
        
        for child in node.get_children():
            result.update_alt(self.visit(child))
        
        return result


def regex_has_suffix(regex: Regex, target_letter: str, target_len: int) -> bool:
    return SuffixCounterVisitor(target_letter).apply(regex, target_len)


__all__ = [
    "regex_has_suffix",
]
