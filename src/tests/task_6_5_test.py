from __future__ import annotations
import typing
import unittest
import dataclasses
import itertools

import utils
from formals_lib import regex, regex_parser, regex_longestsuff


@dataclasses.dataclass
class TaskTestInfo:
    regex_str: str
    target_letter: str
    real_max_cnt: int | None
    
    @property
    def regex(self) -> regex.Regex:
        return regex_parser.parse_regex(self.regex_str)
    
    def get_real_answer(self, cnt: int) -> bool:
        return self.real_max_cnt is None or cnt <= self.real_max_cnt

    def get_relative_lengths(self, deltas: typing.Iterable[int]) -> typing.Generator[int, None, None]:
        if self.real_max_cnt is None:
            return
        
        for delta in deltas:
            yield self.real_max_cnt + delta


class Task65Test(unittest.TestCase):
    cases: typing.Final[typing.List[TaskTestInfo]] = [
        TaskTestInfo("ab", "a", 0),
        TaskTestInfo("ba", "a", 1),
        TaskTestInfo("a(b+c)*", "a", 1),
        TaskTestInfo("bc+a+a*", "a", None),
        TaskTestInfo("a(b+c)*d", "a", 0),
        TaskTestInfo("a+c+b+ccc+cccca", "c", 3),
        TaskTestInfo("a1*", "a", 1),
        
        # The following two tests are from the example
        TaskTestInfo("((a+b)c + a(ba)* (b+ac))*", "a", 0),
        TaskTestInfo("(acb + b(abc)* (ab+ba))*a", "c", 0),
    ]
    
    
    def assertSolutionGood(self, re: regex.Regex | str, target_letter: str, target_len: int, result: bool) -> None:
        if isinstance(re, str):
            re = regex_parser.parse_regex(re)
        re: regex.Regex
        
        predicted_result: bool = regex_longestsuff.regex_has_suffix(re, target_letter, target_len)
        self.assertEqual(predicted_result, result)
    
    
    def handle_case(self, case: TaskTestInfo) -> None:
        lengths: typing.Final[typing.Iterable[int]] = \
            (0, 1, 2, 3, 100) + tuple(case.get_relative_lengths((-2, -1, 0, 1, 100)))
        
        for length in lengths:
            if length < 0:
                continue
            
            with self.subTest(regex=case.regex_str, letter=case.target_letter, length=length):
                self.assertSolutionGood(case.regex, case.target_letter, length, case.get_real_answer(length))
    
    def test_simple(self):
        for case in self.cases:
            self.handle_case(case)


if __name__ == "__main__":
    unittest.main()

