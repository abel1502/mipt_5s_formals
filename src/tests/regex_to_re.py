from __future__ import annotations
import typing
import re
from formals_lib.regex import Reconstructor

import utils
from formals_lib.regex import *
from formals_lib.regex import Reconstructor
from formals_lib.itree import TreeVisitor


# Not the best practive, but we'll reuse the reconstructor's code this way
class RegexToRe(Reconstructor):
    warn_on_generic: typing.ClassVar[bool] = True
    
    
    def apply(self, regex: Regex) -> re.Pattern:
        return re.compile(self.visit(regex))
    
    @TreeVisitor.handler(Letter)
    def visit_letter(self, node: Letter) -> str:
        return node.letter
    
    @TreeVisitor.handler(Zero)
    def visit_zero(self, node: Zero) -> str:
        return "(?!)"
    
    @TreeVisitor.handler(One)
    def visit_one(self, node: One) -> str:
        return ""
    
    @TreeVisitor.handler(Concat)
    def visit_concat(self, node: Concat) -> str:
        result: typing.List[str] = []

        with self._set_par_level(self.ParLevel.either):
            for child in node.get_children():
                result.append(self.visit(child))
        
        result: str = "".join(result)
        if self._par_level >= self.ParLevel.concat:
            result = f"({result})"
        
        return result

    @TreeVisitor.handler(Star)
    def visit_star(self, node: Star) -> str:
        with self._set_par_level(self.ParLevel.concat):
            return self.visit(node.get_children()[0]) + "*"

    @TreeVisitor.handler(Either)
    def visit_either(self, node: Either) -> str:
        result: typing.List[str] = []

        with self._set_par_level(self.ParLevel.none):
            for child in node.get_children():
                result.append(self.visit(child))
        
        result: str = "|".join(result)
        if self._par_level >= self.ParLevel.either:
            result = f"({result})"
        
        return result


def regex_to_re(regex: Regex) -> re.Pattern:
    return RegexToRe().apply(regex)
