from __future__ import annotations
from re import L
import typing
import argparse
import cmd
import pathlib
from collections import UserDict

from formals_lib import *
from formals_lib import automata_minimize
from formals_lib.automata import KeyType


parser = argparse.ArgumentParser(
    description="""
    A tool for various common manipulations related to the formal languages course
    """
)

# parser.add_argument()


class Namer(UserDict):
    _next_id: int
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._next_id = 0
    
    def __missing__(self, key: KeyType) -> int:
        result: int = self._next_id
        self._next_id += 1
        self[key] = result
        return result


def solve_task_1(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("(ab+ba)*(1+a+ba)")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    aut = automata_determ.make_full_dfa(aut)
    
    namer = Namer()
    automata_dot.dump(aut, output_dir / "task1.svg", key_repr=lambda k: namer[k])


def solve_task_2(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("(ab)*b* + ((a + b)^2)*")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    aut = automata_determ.make_full_dfa(aut)
    
    namer = Namer()
    automata_dot.dump(aut, output_dir / "task2.svg", key_repr=lambda k: namer[k])


def solve_task_3(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("a((ba)*a(ab)* + a)*")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    # aut = automata_determ.make_full_dfa(aut)
    aut = automata_complement.complement(aut)
    
    namer = Namer()
    automata_dot.dump(aut, output_dir / "task3.svg", key_repr=lambda k: namer[k])


def main():
    args = parser.parse_args()
    
    output_dir: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "output"

    solve_task_1(output_dir)
    solve_task_2(output_dir)
    solve_task_3(output_dir)
    
    # automata_dot.dump(
    #     automata_minimize.minimize(
    #         regex_automata.regex_to_automata(
    #             regex_parser.parse(
    #                 "(a+b+ab)*"
    #             )
    #         )
    #     ),
    #     output_dir / "tmp.svg"
    # )

    return 0


if __name__ == "__main__":
    exit(main())
