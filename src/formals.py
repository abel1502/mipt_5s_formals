from __future__ import annotations
from re import L
import typing
import argparse
import cmd
import pathlib

from formals_lib import *


parser = argparse.ArgumentParser(
    description="""
    A tool for various common manipulations related to the formal languages course
    """
)

# parser.add_argument()


def main():
    args = parser.parse_args()
    
    output_dir: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent.parent / "output"

    re: regex.Regex = regex_parser.parse("(ab+ba)*(1+a+ba)")
    aut: automata.Automata = regex_automata.regex_to_automata(re)
    aut = automata_determ.make_full_dfa(aut)
    automata_dot.dump(aut, output_dir / "task1.svg", key_repr=lambda k: repr(set(k)) if isinstance(k, frozenset) else repr(k))

    return 0


if __name__ == "__main__":
    exit(main())
