from __future__ import annotations
import typing
import argparse
import cmd
import pathlib
from collections import UserDict
import itertools

from formals_lib import all as formals


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
    
    def __missing__(self, key: formals.KeyType) -> int:
        result: int = self._next_id
        self._next_id += 1
        self[key] = result
        return result


def _task_file_name(output_dir: pathlib.Path, task_id: typing.Iterable[typing.Any], ext: str) -> pathlib.Path:
    if isinstance(task_id, str):
        raise TypeError("task_id must be a sequence, str would be interpreted as a sequence of chars")
    
    return (
        output_dir / "task-{}.svg".format(
            '-'.join(map(str, task_id))
        )
    ).with_suffix("." + ext)


def dump(aut: formals.Automata,
         output_dir: pathlib.Path,
         task_id: typing.Iterable[typing.Any],
         key_repr: typing.Callable[[typing.Any], str] | None = None) -> None:
    if key_repr is None:
        namer = Namer()
        key_repr = lambda k: namer[k]
    
    formals.dump_automata(
        aut,
        _task_file_name(output_dir, task_id, "svg"),
        key_repr=key_repr
    )


def dump_regex(re: formals.Regex, output_dir: pathlib.Path, task_id: typing.Iterable[typing.Any]) -> None:
    with open(_task_file_name(output_dir, task_id, "txt"), "w") as f:
        print(formals.reconstruct_regex(re), file=f)


def solve_task_3_1(output_dir: pathlib.Path):
    re: formals.Regex = formals.parse_regex("(ab+ba)*(1+a+ba)")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.make_full_dfa(aut)
    
    dump(aut, output_dir, (3, 1))


def solve_task_3_2(output_dir: pathlib.Path):
    re: formals.Regex = formals.parse_regex("(ab)*b* + ((a + b)^2)*")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.make_full_dfa(aut)
    
    dump(aut, output_dir, (3, 2))


def solve_task_3_3(output_dir: pathlib.Path):
    re: formals.Regex = formals.parse_regex("a((ba)*a(ab)* + a)*")
    aut: formals.Automata = formals.regex_to_automata(re)
    # aut = formals.make_full_dfa(aut)
    aut = formals.complement(aut)
    
    dump(aut, output_dir, (3, 3))


def solve_task_4_1(output_dir: pathlib.Path):
    aut = formals.Automata("ab")
    
    for i, j in itertools.product(range(3), range(3)):
        aut.make_node(key=(i, j), term=(i == j))
    
    aut.set_start((0, 0))
    aut.remove_node(0)
    
    for i, j in itertools.product(range(3), range(3)):
        aut.link((i, j), ((i + 1) % 3, j), "a")
        aut.link((i, j), (i, (j + 1) % 3), "b")
    
    dump(aut, output_dir, (4, 1, "pre"))
    
    aut = formals.minimize(aut)
    
    dump(aut, output_dir, (4, 1))


def solve_task_4_2(output_dir: pathlib.Path):
    re = formals.parse_regex("a((ba)*a(ab)*+a)*")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.minimize(aut)
    
    dump(aut, output_dir, (4, 2))


def solve_task_4_3(output_dir: pathlib.Path):
    # NOTE: The last ^+ is missing, becuse it's not supported!
    re = formals.parse_regex("(a(ab+ba)*b(a+ba)*)")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.aut_pow_plus(aut)
    aut = formals.minimize(aut)
    
    dump(aut, output_dir, (4, 3))
    
    # TODO: If nodes are made with keys overlapping the next id, everything goes haywire
    # aut2 = formals.Automata("ab")
    # aut2.make_node(1)
    # aut2.make_node(2, term=True)
    
    # aut2.link(0, 1, "a")
    # aut2.link(1, 1, "ab")
    # aut2.link(1, 1, "ba")
    # aut2.link(1, 2, "b")
    # aut2.link(2, 2, "a")
    # aut2.link(2, 2, "ba")
    # aut2.link(2, 0, "")
    
    # aut2 = formals.minimize_aut(aut2)
    
    # dump(aut2, output_dir, (4, 3, "alt"))
    


def solve_task_4_4(output_dir: pathlib.Path):
    aut = formals.Automata("ab")
    aut.make_node(key=(0, 0), term=True)
    aut.make_node(key=(0, 1), term=True)
    aut.make_node(key=(1, 0))
    aut.make_node(key=(1, 1))
    
    aut.set_start((0, 0))
    aut.remove_node(0)
    
    for i in range(2):
        aut.link((i, 0), (i, 1), "a")
        aut.link((i, 0), (i, 0), "b")
        aut.link((i, 1), (1 - i, 1), "a")
        aut.link((i, 1), (i, 0), "b")
    
    dump(aut, output_dir, (4, 4, "aut"))
    re = formals.automata_to_regex(aut)
    re = formals.optimize_regex(re)
    dump_regex(re, output_dir, (4, 4))


def solve_task_4_5(output_dir: pathlib.Path):
    # NOTE: The last ^+ is missing, becuse it's not supported!
    re = formals.parse_regex("(a(ab+ba)*b(a+ba)*)")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.complement(aut)
    
    re = formals.automata_to_regex(aut)
    re = formals.optimize_regex(re)
    dump_regex(re, output_dir, (4, 5))


def solve_task_4_6(output_dir: pathlib.Path):
    re = formals.parse_regex("a((ba)*a(ab)*+a)*")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.aut_pow_plus(aut)
    aut = formals.complement(aut)
    
    re = formals.automata_to_regex(aut)
    re = formals.optimize_regex(re)
    dump_regex(re, output_dir, (4, 6))


def solve_test_1_1(output_dir: pathlib.Path):
    aut = formals.Automata("abc")
    aut.start.is_term = True
    aut.make_node(term=True)
    aut.make_node(term=True)
    aut.make_node()
    
    aut.link(0, 0, "a")
    aut.link(0, 1, "b")
    aut.link(0, 0, "c")
    aut.link(1, 3, "a")
    aut.link(1, 3, "b")
    aut.link(1, 2, "c")
    aut.link(2, 2, "a")
    aut.link(2, 3, "b")
    aut.link(2, 2, "c")
    aut.link(3, 3, "a")
    aut.link(3, 3, "b")
    aut.link(3, 3, "c")
    
    dump(aut, output_dir, ("test", 1, 1, "aut"))
    re = formals.automata_to_regex(aut)
    re = formals.optimize_regex(re)
    dump_regex(re, output_dir, ("test", 1, 1))


def solve_test_1_2(output_dir: pathlib.Path):
    aut = formals.Automata("ab")
    for key in itertools.product(range(2), range(2), range(2)):
        aut.make_node(key, term=key[1])
    
    aut.set_start((0, 0, 0))
    aut.remove_node(0)
    
    for cnt_a, cnt_b in itertools.product(range(2), range(2)):
        aut.link((0, cnt_a, cnt_b), (1, 1 - cnt_a,     cnt_b), "a")
        aut.link((0, cnt_a, cnt_b), (1,     cnt_a,     cnt_b), "b")
        aut.link((1, cnt_a, cnt_b), (0,     cnt_a,     cnt_b), "a")
        aut.link((1, cnt_a, cnt_b), (0,     cnt_a, 1 - cnt_b), "b")
    
    dump(aut, output_dir, ("test", 1, 2), key_repr=lambda k: ' '.join(map(str, k)))


def solve_test_1_3(output_dir: pathlib.Path):
    # FDFA, MFDFA
    re = formals.parse_regex("(1+aa)(b+ba)*bb*aa*")
    # print(formals.reconstruct_regex(re))
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.make_full_dfa(aut)
    dump(aut, output_dir, ("test", 1, 3, "fdfa"))
    aut = formals.minimize(aut)
    dump(aut, output_dir, ("test", 1, 3, "mfdfa"), key_repr=str)


def solve_test_1_4(output_dir: pathlib.Path):
    # regex
    re = formals.parse_regex("(1+aa)(b+ba)*bb*aa*")
    aut: formals.Automata = formals.regex_to_automata(re)
    aut = formals.complement(aut)
    re = formals.automata_to_regex(aut)
    dump_regex(re, output_dir, ("test", 1, 4))


def solve_task_6_5():
    print("Task 6.5 - interactive solution")
    
    alpha, x, k = input().split()
    k = int(k)
    
    alpha: str
    x: str
    k: int
    
    regex: formals.Regex = formals.parse_suff_regex(alpha)
    
    result: bool = formals.regex_has_suffix(regex, x, k)
    
    print("YES" if result else "NO")


def main():
    args = parser.parse_args()
    
    output_dir: typing.Final[pathlib.Path] = pathlib.Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # solve_task_3_1(output_dir)
    # solve_task_3_2(output_dir)
    # solve_task_3_3(output_dir)
    # solve_task_4_1(output_dir)
    # solve_task_4_2(output_dir)
    # solve_task_4_3(output_dir)
    # solve_task_4_4(output_dir)
    # solve_task_4_5(output_dir)
    # solve_task_4_6(output_dir)
    # solve_test_1_1(output_dir)
    # solve_test_1_2(output_dir)
    # solve_test_1_3(output_dir)
    # solve_test_1_4(output_dir)
    
    solve_task_6_5()  # Interactive!

    return 0


if __name__ == "__main__":
    exit(main())
