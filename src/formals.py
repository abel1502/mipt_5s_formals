from __future__ import annotations
from re import L
import typing
import argparse
import cmd
import pathlib
from collections import UserDict
import itertools

from formals_lib import *
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


def dump(aut: automata.Automata, output_dir: pathlib.Path, task_id: typing.Iterable[typing.Any]) -> None:
    if isinstance(task_id, str):
        raise TypeError("task_id must be a sequence, str would be interpreted as a sequence of chars")
    
    namer = Namer()
    
    automata_dot.dump(
        aut,
        output_dir / "task-{}.svg".format('-'.join(map(str, task_id))),
        key_repr=lambda k: namer[k]
    )


def solve_task_3_1(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("(ab+ba)*(1+a+ba)")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    aut = automata_determ.make_full_dfa(aut)
    
    dump(aut, output_dir, (3, 1))


def solve_task_3_2(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("(ab)*b* + ((a + b)^2)*")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    aut = automata_determ.make_full_dfa(aut)
    
    dump(aut, output_dir, (3, 2))


def solve_task_3_3(output_dir: pathlib.Path):
    re: regex.Regex = regex_parser.parse("a((ba)*a(ab)* + a)*")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    # aut = automata_determ.make_full_dfa(aut)
    aut = automata_complement.complement(aut)
    
    dump(aut, output_dir, (3, 3))


def solve_task_4_1(output_dir: pathlib.Path):
    aut = automata.Automata("ab")
    
    for i, j in itertools.product(range(3), range(3)):
        aut.make_node(key=(i, j), term=(i == j))
    
    aut.set_start((0, 0))
    aut.remove_node(0)
    
    for i, j in itertools.product(range(3), range(3)):
        aut.link((i, j), ((i + 1) % 3, j), "a")
        aut.link((i, j), (i, (j + 1) % 3), "b")
    
    dump(aut, output_dir, (4, 1, "pre"))
    
    aut = automata_minimize.minimize(aut)
    
    dump(aut, output_dir, (4, 1))


def main():
    args = parser.parse_args()
    
    output_dir: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    # solve_task_3_1(output_dir)
    # solve_task_3_2(output_dir)
    # solve_task_3_3(output_dir)
    solve_task_4_1(output_dir)
    
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
