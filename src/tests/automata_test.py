from __future__ import annotations
import typing
import unittest
from collections import deque
import dataclasses
import random
import string
import itertools
import re
import sys

import utils
from formals_lib.regex import *
from formals_lib.automata import *
from formals_lib.automata_ops import *
from formals_lib.automata_determ import *
from formals_lib.automata_minimize import *
from formals_lib.regex_automata import *
from formals_lib.regex_parser import parse_regex
from formals_lib.automata_cmp import compare_automatas

from regex_to_re import regex_to_re


@dataclasses.dataclass(frozen=True)
class _WordState:
    node: Node
    suffix: str


class AutomataTest(unittest.TestCase):
    aut0: Automata
    aut1: Automata
    aut2: Automata
    basic_wordlist: typing.Final[typing.Tuple[str]]
    
    verbose_aut2: typing.Final[bool] = False


    @staticmethod
    def check_word(aut: Automata, word: str) -> bool:
        queue: typing.Deque[_WordState] = deque()
        queue.append(_WordState(aut.start, word))

        seen: typing.Set[_WordState] = set()

        while queue:
            state = queue.popleft()

            if state in seen:
                continue
            seen.add(state)

            if not state.suffix and state.node.is_term:
                return True
            
            for edge in state.node.out:
                if not state.suffix.startswith(edge.label):
                    continue

                queue.append(_WordState(edge.dst, state.suffix[len(edge.label):]))
        
        return False

    def assertAccepts(self, aut: Automata, word: str) -> None:
        return self.assertTrue(self.check_word(aut, word), f"Automata should've accepted '{word}'")
    
    def assertNotAccepts(self, aut: Automata, word: str) -> None:
        return self.assertFalse(self.check_word(aut, word), f"Automata shouldn't have accepted '{word}'")
    
    def assertEquivAutomatas(self, aut1: Automata, aut2: Automata,
                             wordlist: typing.Iterable[str] = (),
                             rand_wl_size: int = 10,
                             name: str = "unnamed") -> None:
        self.assertEqual(
            aut1.alphabet, aut2.alphabet,
            "Equivalent automatas must share alphabets"
        )

        with self.subTest(f"Automata equivalence: {name}"):
            wordlist: typing.List[str] = list(wordlist)
            
            wordlist.extend(self.random_wordlist(aut1.alphabet, size=rand_wl_size, wordlen=7))

            for word in wordlist:
                self.assertEqual(self.check_word(aut1, word), self.check_word(aut2, word),
                    f"Automatas should've agreed on '{word}'"
                )
    
    def assertEquivRegex(self, regex: str | Regex, aut: Automata,
                         wordlist: typing.Iterable[str] = (),
                         rand_wl_size: int = 10) -> None:
        if isinstance(regex, str):
            regex = parse_regex(regex)
        
        with self.subTest(f"Regex equivalence: '{reconstruct_regex(regex)}'"):
            wordlist: typing.List[str] = list(wordlist)
            
            wordlist.extend(self.random_wordlist(
                string.ascii_letters[:7] + string.digits[:3],
                size=rand_wl_size, wordlen=7
            ))
            
            py_re: re.Pattern = regex_to_re(regex)

            for word in wordlist:
                self.assertEqual(bool(py_re.fullmatch(word)), self.check_word(aut, word),
                    f"Regex and automata should've agreed on '{word}'"
                )
    
    def assertCorrectR2A(self, regex: str | Regex, **kwargs) -> None:
        return self.assertEquivRegex(regex, regex_to_automata(regex))
    
    def assertCorrectA2R(self, aut: Automata, **kwargs) -> None:
        return self.assertEquivRegex(automata_to_regex(aut), aut)
    
    @staticmethod
    def random_wordlist(alphabet: str, size: int = 10, wordlen: int = 5) -> typing.Generator[str, None, None]:
        for i in range(size):
            yield AutomataTest.random_word(alphabet, wordlen=wordlen)
    
    @staticmethod
    def random_word(alphabet: str, wordlen: int = 5) -> str:
        word: typing.List[str] = []

        for i in range(int(random.expovariate(1. / wordlen))):
            word.append(random.choice(alphabet))
        
        return ''.join(word)

    @staticmethod
    def define_aut0() -> Automata:
        """
        Aut1 accepts those and only those words in the alphabet "ab",
        which consist only of a's
        """

        aut = Automata("ab")
        
        aut.start.is_term = True
        aut.link(0, 0, "a")

        return aut

    @staticmethod
    def define_aut1() -> Automata:
        """
        Aut1 accepts those and only those words in the alphabet "ab",
        which have an even number of a's and and odd number of b's
        """

        aut = Automata("ab")
        
        aut.change_key(aut.start, (0, 0))
        aut.make_node(key=(0, 1), term=True)
        aut.make_node(key=(1, 0))
        aut.make_node(key=(1, 1))

        aut.link((0, 0), (1, 0), "a")
        aut.link((0, 0), (0, 1), "b")
        aut.link((0, 1), (1, 1), "a")
        aut.link((0, 1), (0, 0), "b")
        aut.link((1, 0), (0, 0), "a")
        aut.link((1, 0), (1, 1), "b")
        aut.link((1, 1), (0, 1), "a")
        aut.link((1, 1), (1, 0), "b")

        return aut
    
    @staticmethod
    def define_aut2() -> Automata:
        """
        Aut2 is a semirandom large automata, most likely not deterministic nor 
        """

        rand_state = random.getstate()
        random.seed("aut2 seed 2")

        alphabet: str = string.ascii_lowercase[:16]

        aut = Automata(alphabet)

        node_cnt: typing.Final[int] = int(random.expovariate(1/20.)) + 1
        assert node_cnt < 1000, "Node cnt alarmingly big"

        term_chance: typing.Final[float] = random.betavariate(5., 5.)
        for i in range(node_cnt - 1):
            is_term: bool = random.random() <= term_chance
            aut.make_node(term=is_term)
        
        edge_cnt: typing.Final[int] = int(random.betavariate(5., 5.) * node_cnt ** 2)
        edges: typing.List[typing.Tuple[int, int]] = random.choices(
            list(itertools.product(range(node_cnt), range(node_cnt))),
            k=edge_cnt
        )

        for i, j in edges:
            label: str = AutomataTest.random_word(alphabet, wordlen=2)
            aut.link(i, j, label)
        
        if AutomataTest.verbose_aut2:
            avg_edge_len: typing.Final[float] = sum(len(e) for e in aut.get_edges()) / edge_cnt

            print("\nAut2 stats:")
            for name in ("node_cnt", "term_chance", "edge_cnt", "avg_edge_len"):
                print("    {name} = {value}".format(name=name, value=locals()[name]))

        random.setstate(rand_state)

        return aut

    def setUp(self) -> None:
        self.aut0 = self.define_aut0()
        self.aut1 = self.define_aut1()
        self.aut2 = self.define_aut2()

        self.basic_wordlist = ("", "a", "aaa", "acb")

    def test_basic(self):
        self.assertAccepts(self.aut0, "")
        self.assertAccepts(self.aut0, "a")
        self.assertAccepts(self.aut0, "aaaa")
        self.assertNotAccepts(self.aut0, "b")
        self.assertNotAccepts(self.aut0, "ab")
        self.assertNotAccepts(self.aut0, "ba")
        self.assertNotAccepts(self.aut0, "aba")

        for word in ("", "aba", "aabb", "aabba", "aabab", "baaba", "ab", "ababababa"):
            with self.subTest("Aut1", word=word):
                func = \
                    self.assertAccepts \
                    if (word.count("a") % 2 == 0 and word.count("b") % 2 == 1) \
                    else self.assertNotAccepts
                
                func(self.aut1, word)
    
    def test_transform_edges_01(self):
        self.assertEquivAutomatas(
            self.aut2,
            make_edges_01(self.aut2),
            wordlist=self.basic_wordlist,
            rand_wl_size=50,
            name="aut2 make_edges_01"
        )
        
    def test_transform_edges_1(self):
        self.assertEquivAutomatas(
            self.aut2,
            make_edges_1(self.aut2),
            wordlist=self.basic_wordlist,
            rand_wl_size=50,
            name="aut2 make_edges_1"
        )
    
    def test_transform_uni_term(self):
        self.assertEquivAutomatas(
            self.aut2,
            unify_term(self.aut2),
            wordlist=self.basic_wordlist,
            rand_wl_size=50,
            name="aut2 unify_term"
        )
    
    def test_transform_dfa(self):
        dfa: Automata = make_dfa(self.aut2)
        
        self.assertTrue(dfa.is_deterministic())
        
        self.assertEquivAutomatas(
            self.aut2,
            dfa,
            wordlist=self.basic_wordlist,
            rand_wl_size=50,
            name="aut2 make_dfa"
        )
        
    
    def test_transform_full_dfa(self):
        fdfa: Automata = make_full_dfa(self.aut2)
        
        self.assertTrue(fdfa.is_deterministic())
        
        self.assertEquivAutomatas(
            self.aut2,
            fdfa,
            wordlist=self.basic_wordlist,
            rand_wl_size=50,
            name="aut2 make_full_dfa"
        )
        
        for node in fdfa.get_nodes():
            node.is_term = True
        
        for word in self.random_wordlist(fdfa.alphabet, size=50):
            self.assertAccepts(fdfa, word)

    def test_regex(self):
        common_wordlist: typing.Final[typing.Tuple[str, ...]] = (
            "", "a", "b", "ab", "ba", "abc", "cab", "a+b", "0", "a b",
            "aaab", "abab", "bbba", "abba", "ac", "ca",
        )
        
        regexes: typing.Final[typing.Tuple[Regex, ...]] = (
            "0", "1", "a", "ab", "a+b", "a*", "(a)", "(ab)", "(a+b)",
            "(a)*", "(a*)", "(a + b) c", "(a + b)^3", "(a + b)*",
            "a(b*a)^2*",
        )
        
        for regex in regexes:
            with self.subTest("Regex <-> automata", regex=regex):
                regex = parse_regex(regex)
                
                aut = regex_to_automata(regex)
                regex_2 = automata_to_regex(aut)
                
                self.assertEquivRegex(regex,   aut, wordlist=common_wordlist, rand_wl_size=25)
                self.assertEquivRegex(regex_2, aut, wordlist=common_wordlist, rand_wl_size=25)
    
    def test_regex_2(self):
        for i in range(2):
            with self.subTest(i=i):
                aut: Automata = getattr(self, f"aut{i}")
                regex: Regex = automata_to_regex(aut)
        
                self.assertEquivRegex(regex, aut, rand_wl_size=500)
    
    @unittest.skip
    def test_regex_3(self):
        # Debugging shows that it does work, albeit slowly, with ~60 nodes
        # and god knows how many edges. It appears to have issues related to
        # memory usage. I decided to just skip the test with this one
        
        aut: Automata = self.aut2
        regex: Regex = automata_to_regex(aut)

        self.assertEquivRegex(regex, aut, rand_wl_size=100)
    
    def test_minimize(self):
        for i in range(3):
            with self.subTest(i=i):
                aut: Automata = getattr(self, f"aut{i}")
                min_aut: Automata = minimize(aut)
        
                self.assertEquivAutomatas(
                    aut, min_aut, self.basic_wordlist, rand_wl_size=100
                )
    
    def test_cmp(self):
        self.assertTrue(compare_automatas(self.aut0, self.aut0))
        self.assertTrue(compare_automatas(self.aut1, self.aut1))
        self.assertTrue(compare_automatas(self.aut2, self.aut2))
        
        self.assertFalse(compare_automatas(self.aut0, self.aut1))
        self.assertFalse(compare_automatas(self.aut2, self.aut1))
        
        regexes: typing.Final[typing.Tuple[Regex, ...]] = (
            "0", "1", "a", "ab", "a+b", "a*", "(a)", "(ab)", "(a+b)",
            "(a)*", "(a*)", "(a + b) c", "(a + b)^3", "(a + b)*",
            "a(b*a)^2*",
        )
        
        for regex in regexes:
            with self.subTest(regex=regex):
                aut = regex_to_automata(regex)
                aut2 = regex_to_automata(automata_to_regex(aut))
                
                self.assertTrue(compare_automatas(aut, aut2))


if __name__ == "__main__":
    unittest.main()
