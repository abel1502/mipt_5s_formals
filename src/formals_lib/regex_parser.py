from __future__ import annotations
import typing
import io
import dataclasses
import enum
import contextlib

from . import regex


class RegexSyntaxError(RuntimeError):
    pass


class RegexTokenType(enum.Enum):
    digit = enum.auto()
    letter = enum.auto()
    star = enum.auto()
    add = enum.auto()
    lpar = enum.auto()
    rpar = enum.auto()
    pow = enum.auto()
    eof = enum.auto()


@dataclasses.dataclass
class RegexToken:
    token_type: RegexTokenType
    value: typing.Any = None


class RegexParser:
    _src: io.TextIOBase
    _tokens: typing.Tuple[RegexToken, ...]
    _pos: int
    
    def __init__(self, src: str | io.TextIOBase):
        if isinstance(src, str):
            src = io.StringIO(src)
        
        self._src = src
    
    def tokenize(self):
        if not hasattr(self, "_tokens"):
            self._tokens = tuple(self._tokenize())
    
    def _tokenize(self) -> typing.Generator[RegexToken, None, None]:
        def next_ch():
            nonlocal ch
            ch = self._src.read(1)

        def skip_space():
            nonlocal ch
            
            while ch.isspace():
                next_ch()

        ch: str = ""

        lookup: typing.Final[typing.MappingView] = {
            "*": RegexTokenType.star,
            "+": RegexTokenType.add,
            "(": RegexTokenType.lpar,
            ")": RegexTokenType.rpar,
        }

        next_ch()
        while ch:
            skip_space()
            
            if ch in lookup:
                yield RegexToken(lookup[ch])
            elif ch.isdigit():
                yield RegexToken(RegexTokenType.digit, int(ch))
            elif ch.isalpha():
                yield RegexToken(RegexTokenType.letter, ch)
            elif ch == "^":
                next_ch()
                skip_space()
                power: int = 0
                if not ch.isdigit():
                    raise RegexSyntaxError("Expected a number after '^'")
                while ch.isdigit():
                    power = power * 10 + int(ch)
                    next_ch()
                yield RegexToken(RegexTokenType.pow, power)
                continue
            next_ch()
        
        yield RegexToken(RegexTokenType.eof)
    
    def is_eof(self) -> bool:
        return self._pos >= len(self._tokens)
    
    def cur(self) -> RegexToken:
        return self.peek(0)
    
    def peek(self, n: int = 1) -> RegexToken:
        pos = self._pos + n
        if pos not in range(len(self._tokens)):
            pos = -1
        return self._tokens[pos]
    
    def next(self) -> None:
        self._pos += 1
    
    def tell(self) -> int:
        return self._pos
    
    def seek(self, pos: int) -> None:
        self._pos = pos
    
    @contextlib.contextmanager
    def maybe(self):
        pos: int = self.tell()
        try:
            yield
        except RegexSyntaxError:
            self.seek(pos)
    
    def require_tok(self, token_type: RegexTokenType) -> typing.Any:
        cur: RegexToken = self.cur()
        if cur.token_type != token_type:
            raise RegexSyntaxError(f"Expected {token_type.name} token, got {cur.token_type.name} instead")
        self.next()
        return cur.value
    
    def parse(self) -> regex.Regex:
        self.tokenize()
        
        self._pos = 0
        
        result: regex.Regex = self.parse_either()

        self.require_tok(RegexTokenType.eof)
        assert self.is_eof()
        
        return result
    
    def parse_either(self) -> regex.Regex:
        items: typing.List[regex.Regex] = []
        items.append(self.parse_concat())
        while True:
            with self.maybe():
                self.require_tok(RegexTokenType.add)
                items.append(self.parse_concat())
                continue
            break
        if len(items) == 1:
            return items[0]
        return regex.Either(*items)
    
    def parse_concat(self) -> regex.Regex:
        items: typing.List[regex.Regex] = []
        items.append(self.parse_power())
        while True:
            with self.maybe():
                items.append(self.parse_power())
                continue
            break
        if len(items) == 1:
            return items[0]
        return regex.Concat(*items)
    
    def parse_power(self) -> regex.Regex:
        item: regex.Regex = self.parse_atomic()
        while True:
            cur: RegexToken = self.cur()
            if cur.token_type == RegexTokenType.star:
                item = regex.Star(item)
            elif cur.token_type == RegexTokenType.pow:
                if cur.value not in range(20):
                    raise RegexSyntaxError(f"Repeat count too big: {cur.value}")
                item = item.repeat(cur.value)
            else:
                break

            self.next()
        return item
    
    def parse_atomic(self) -> regex.Regex:
        cur: RegexToken = self.cur()
        if cur.token_type == RegexTokenType.lpar:
            return self.parse_par_expr()
        if cur.token_type == RegexTokenType.letter:
            self.next()
            return regex.Letter(cur.value)
        if cur.token_type != RegexTokenType.digit:
            raise RegexSyntaxError(f"Unexpected token: {cur.token_type.name}")
        self.next()
        if cur.value == 0:
            return regex.Zero()
        if cur.value == 1:
            return regex.One()
        raise RegexSyntaxError(f"{cur.value} is not a valid digit for regex")
    
    def parse_par_expr(self) -> regex.Regex:
        self.require_tok(RegexTokenType.lpar)
        result: regex.Regex = self.parse_either()
        self.require_tok(RegexTokenType.rpar)
        return result


def parse_regex(src: str | io.TextIOBase) -> regex.Regex:
    return RegexParser(src).parse()


__all__ = [
    "RegexSyntaxError", "parse_regex",
]
