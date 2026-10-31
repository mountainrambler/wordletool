from collections import Counter
from itertools import product
import unittest
import numpy as np

from solver import Clue, feedback, filter_candidates, load_dictionaries, normalize_word
from ranking import encode_words, feedback_codes, rank_guesses


class FeedbackTests(unittest.TestCase):
    def test_repeated_letters_and_green_priority(self):
        self.assertEqual(feedback("allee", "apple"), (2, 1, 0, 0, 2))
        self.assertEqual(feedback("eerie", "serve"), (0, 2, 2, 0, 2))
        self.assertEqual(feedback("belle", "level"), (0, 2, 1, 1, 1))
        self.assertEqual(feedback("apple", "apple"), (2,) * 5)
        self.assertEqual(feedback("crane", "sight"), (0,) * 5)

    def test_number_of_marked_copies_matches_available_letters(self):
        words = ["".join(p) for p in product("ab", repeat=5)]
        for guess in words:
            for answer in words:
                colors = feedback(guess, answer)
                marked = Counter(g for g, c in zip(guess, colors) if c)
                for letter in "ab":
                    self.assertEqual(marked[letter], min(guess.count(letter), answer.count(letter)))
                for g, a, c in zip(guess, answer, colors):
                    self.assertEqual(c == 2, g == a)

    def test_filtering_multiple_clues(self):
        pool = ("apple", "ample", "apply", "maple", "allee")
        clues = (Clue("allee", (2, 1, 0, 0, 2)), Clue("ample", (2, 0, 2, 2, 2)))
        self.assertEqual(filter_candidates(pool, clues), ("apple",))
        self.assertEqual(filter_candidates(pool, (Clue("apple", (0,) * 5), Clue("apple", (2,) * 5))), ())

    def test_input_validation(self):
        self.assertEqual(normalize_word(" CRANE "), "crane")
        for value in ("four", "sixsix", "caféx", "12345", "a bcd", "<div>"):
            with self.assertRaises(ValueError):
                normalize_word(value)
        for pattern in ((0,) * 4, (0, 0, 0, 0, 3), (False, 0, 0, 0, 0)):
            with self.assertRaises(ValueError):
                Clue("apple", pattern)


class RankingTests(unittest.TestCase):
    def test_vectorized_feedback_agrees_with_rules(self):
        words = tuple("".join(p) for p in product("ab", repeat=5))
        answers = encode_words(words)
        counts = np.zeros((len(words), 26), dtype=np.int16)
        for i, w in enumerate(words):
            for c in w:
                counts[i, ord(c) - 97] += 1
        for word, guess in zip(words, encode_words(words)):
            expected = [sum(c * 3 ** i for i, c in enumerate(feedback(word, answer))) for answer in words]
            np.testing.assert_array_equal(feedback_codes(guess, answers, counts), expected)

    def test_exact_ranking_and_candidate_tie_break(self):
        candidates = ("apple", "ample", "apply")
        results, bounded = rank_guesses(candidates, candidates + ("crane",), mode="information")
        self.assertFalse(bounded)
        for result in results:
            sizes = Counter(feedback(result.word, a) for a in candidates)
            self.assertAlmostEqual(result.expected, sum(n * n for n in sizes.values()) / len(candidates))
        self.assertTrue(results[0].is_solution)
        self.assertEqual(results[0].expected, 1)

    def test_empty_single_and_used_guesses(self):
        self.assertEqual(rank_guesses((), ("crane",)), ((), False))
        results, _ = rank_guesses(("apple",), ("crane",), mode="information")
        self.assertEqual([r.word for r in results], ["apple"])
        self.assertEqual(rank_guesses(("apple",), ("apple",), used=("apple",)), ((), False))


class DictionaryTests(unittest.TestCase):
    def test_integrity_and_expanded_answers(self):
        solutions, core, accepted = load_dictionaries()
        self.assertGreater(len(solutions), 3000)
        self.assertGreater(len(accepted), 14000)
        self.assertTrue(set(solutions) <= accepted)
        self.assertGreater(len(core & set(solutions)), 2200)
        self.assertGreater(len(set(solutions) - core), 800)
        self.assertIn("wazoo", solutions)
        self.assertIn("apple", core)
        self.assertEqual(len(set(solutions)), len(solutions))


if __name__ == "__main__":
    unittest.main()
