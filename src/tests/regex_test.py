from __future__ import annotations
import typing
import unittest

import utils
from formals_lib import regex, regex_optimize, regex_parser, regex_suff_parser


class RegexTest(unittest.TestCase):
    regex1_tree: regex.Regex
    regex1: regex.Regex
    regex2: regex.Regex

    def setUp(self) -> None:
        self.regex1_tree = regex.Concat(
            regex.Letter("a"),
            regex.Star(
                regex.Either(
                    regex.Letter("b"),
                    regex.Letter("c"),
                )
            ),
            regex.Letter("d")
        )

        self.regex1 = regex_parser.parse_regex("a(b+c)*d")

        self.regex2 = regex_parser.parse_regex("a((b+1)^2d)*")

    def test_compare(self):
        self.assertEqual(self.regex1_tree, self.regex1)
        self.assertNotEqual(self.regex1_tree, self.regex2)
        self.assertNotEqual(self.regex1, self.regex2)

    def test_parse_reconstruct(self):
        parse = regex_parser.parse_regex
        reconstruct = regex.reconstruct_regex
        parse_back = lambda src: reconstruct(parse(src))

        self.assertEqual(parse("0"), regex.Zero())
        self.assertEqual(parse("1"), regex.One())
        self.assertRaises(regex_parser.RegexSyntaxError, parse, "2")
        self.assertRaises(regex_parser.RegexSyntaxError, parse, "9")
        
        for letter in "abcABCzZыъ":
            with self.subTest(letter=letter):
                self.assertEqual(parse(letter), regex.Letter(letter))
        
        self.assertEqual(parse("abc"), regex.Concat(
            regex.Letter("a"),
            regex.Letter("b"),
            regex.Letter("c"),
        ))

        self.assertEqual(parse(" a  b c     "), regex.Concat(
            regex.Letter("a"),
            regex.Letter("b"),
            regex.Letter("c"),
        ))

        self.assertEqual(parse("a*"), regex.Star(regex.Letter("a")))

        self.assertEqual(parse("a  *"), regex.Star(regex.Letter("a")))

        self.assertEqual(parse(" a + b+c "), regex.Either(
            regex.Letter("a"),
            regex.Letter("b"),
            regex.Letter("c"),
        ))

        self.assertEqual(parse("(a + b)c"), regex.Concat(
            regex.Either(regex.Letter("a"), regex.Letter("b")), regex.Letter("c")
        ))

        self.assertEqual(parse("a^2"), regex.Concat(
            regex.Letter("a"),
            regex.Letter("a"),
        ))

        for re in ("(a+b)c", "a", "b*", "ac*", "(ac)*", "01", "1a0"):
            with self.subTest(re=re):
                self.assertEqual(parse_back(re), re)
        
        self.assertEqual(parse_back("(a+0)^2"), "(a+0)(a+0)")
        self.assertEqual(parse_back("(a+0)^2*"), "((a+0)(a+0))*")
    
    def test_suff_parse(self):
        samples: typing.Final[typing.List[
            typing.Tuple[str, str]
        ]] = [
            ("a", "a"),
            ("a*", "a*"),
            ("ab+", "a+b"),
            # Somewhat bad test, because the order of letters doesn't have to be preserved.
            # But I've made sure my implementation does preserve it.
            ("ab+c+", "a+b+c"),
            ("ab.", "ab"),
            ("a*b.", "a*b"),
            ("ba+c.a+", "(b+a)c + a"),
            ("ab+c.aba.*.bac.+.+*", "((a+b)c + a(ba)* (b+ac))*"),
            ("acb..bab.c. * .ab.ba. + . + *a.", "(acb + b(abc)* (ab+ba))*a"),
        ]
        
        for suff, normal in samples:
            with self.subTest(suff=suff, normal=normal):
                suff_re: regex.Regex = regex_suff_parser.parse_suff_regex(suff)
                normal_re: regex.Regex = regex_parser.parse_regex(normal)
                
                suff_re = regex_optimize.optimize_regex(suff_re)
                normal_re = regex_optimize.optimize_regex(normal_re)
                
                self.assertEqual(suff_re, normal_re)


if __name__ == "__main__":
    unittest.main()

