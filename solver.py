"""Wordle rules and dictionary loading, independent of Streamlit."""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re

DATA = Path(__file__).resolve().parent / "data"
GRAY, YELLOW, GREEN = 0, 1, 2


def normalize_word(word: str) -> str:
    word = word.strip().lower()
    if not re.fullmatch(r"[a-z]{5}", word):
        raise ValueError("Enter exactly five English letters (A–Z).")
    return word


def validate_pattern(pattern) -> tuple[int, ...]:
    pattern = tuple(pattern)
    if len(pattern) != 5 or any(type(c) is not int or c not in (0, 1, 2) for c in pattern):
        raise ValueError("Set all five tiles to gray, yellow, or green.")
    return pattern


@dataclass(frozen=True)
class Clue:
    guess: str
    pattern: tuple[int, ...]

    def __post_init__(self):
        object.__setattr__(self, "guess", normalize_word(self.guess))
        object.__setattr__(self, "pattern", validate_pattern(self.pattern))


def feedback(guess: str, answer: str) -> tuple[int, ...]:
    """Assign greens first, then consume unmatched letters left to right."""
    guess, answer = normalize_word(guess), normalize_word(answer)
    result = [GRAY] * 5
    remaining = Counter()
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = GREEN
        else:
            remaining[a] += 1
    for i, g in enumerate(guess):
        if result[i] != GREEN and remaining[g]:
            result[i] = YELLOW
            remaining[g] -= 1
    return tuple(result)


def filter_candidates(words, clues) -> tuple[str, ...]:
    return tuple(w for w in words if all(feedback(c.guess, w) == c.pattern for c in clues))


def load_words(filename: str) -> tuple[str, ...]:
    return tuple(sorted({normalize_word(w) for w in (DATA / filename).read_text().splitlines() if w.strip()}))


def load_dictionaries():
    solutions = tuple(sorted(set(load_words("solutions.txt")) | set(load_words("additional_solutions.txt"))))
    core = frozenset(load_words("core_solutions.txt"))
    accepted = frozenset(load_words("accepted_guesses.txt"))
    if not set(solutions) <= accepted:
        raise ValueError("The answer and guess dictionaries are inconsistent.")
    return solutions, core, accepted
