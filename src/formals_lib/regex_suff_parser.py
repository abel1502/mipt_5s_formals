from __future__ import annotations
import typing
import io
import dataclasses
import contextlib


from . import regex
from .regex_parser import RegexSyntaxError


class RegexSuffParser:
    _src: io.TextIOBase
    _stack: typing.List[regex.Regex]
    
    def __init__(self, src: str | io.TextIOBase):
        if isinstance(src, str):
            src = io.StringIO(src)
        
        self._src = src
        self._stack = []
    
    def _get_chars(self) -> typing.Generator[str, None, None]:
        def next_ch():
            nonlocal ch
            ch = self._src.read(1)

        def skip_space():
            nonlocal ch
            
            while ch.isspace():
                next_ch()

        ch: str = ""

        next_ch()
        while ch:
            skip_space()
            yield ch
            next_ch()
    
    def _push(self, re: regex.Regex) -> regex.Regex:
        self._stack.append(re)
        return re
    
    def _pop(self) -> regex.Regex:
        try:
            return self._stack.pop()
        except IndexError:
            raise RegexSyntaxError("Unbalanced operation: not enough values on stack to pop")
    
    def _pop_many(self, cnt: int = 2) -> typing.Tuple[regex.Regex, ...]:
        return tuple(self._pop() for i in range(cnt))[::-1]
    
    def _process_ch(self, ch: str) -> regex.Regex:
        assert len(ch) == 1
        
        if ch in "abc":
            return regex.Letter(ch)
        if ch == "1":
            return regex.One()
        if ch == "+":
            return regex.Either(*self._pop_many(2))
        if ch == ".":
            return regex.Concat(*self._pop_many(2))
        if ch == "*":
            return regex.Star(self._pop())
        
    
    def parse(self) -> regex.Regex:
        for ch in self._get_chars():
            self._push(self._process_ch(ch))
        
        if len(self._stack) != 1:
            raise RegexSyntaxError(f"Regex left the stack with {len(self._stack)} values where 1 was expected")
        
        return self._pop()


def parse_suff_regex(src: str | io.TextIOBase) -> regex.Regex:
    return RegexSuffParser(src).parse()


__all__ = [
    "RegexSyntaxError", "parse_suff_regex",
]
