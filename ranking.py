"""Rank guesses by expected remaining candidates, with a bounded shortlist."""
from collections import Counter
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Suggestion:
    word: str
    expected: float
    worst_case: int
    is_solution: bool


def encode_words(words):
    return np.frombuffer("".join(words).encode("ascii"), dtype=np.uint8).reshape(-1, 5).astype(np.int16) - 97


def feedback_codes(guess, answers, answer_counts):
    """Vectorized feedback; each color is a digit in a base-three code."""
    equal = answers == guess
    counts = answer_counts.copy()
    rows = np.arange(len(answers))
    for i in range(5):
        counts[rows[equal[:, i]], guess[i]] -= 1
    colors = equal.astype(np.int16) * 2
    for i in range(5):
        yellow = ~equal[:, i] & (counts[:, guess[i]] > 0)
        colors[yellow, i] = 1
        counts[rows[yellow], guess[i]] -= 1
    return colors @ np.array([1, 3, 9, 27, 81], dtype=np.int16)


def rank_guesses(candidates, accepted, core=frozenset(), mode="answer", used=(), limit=5):
    """Return suggestions and whether exact scoring used a heuristic shortlist.

    All candidates have equal probability. Large pools are first shortlisted by
    unique-letter coverage and position frequency; no candidates are filtered out
    of the answer list. Scores are one-step expectations, not a full game search.
    """
    if mode not in ("answer", "information"):
        raise ValueError("Unknown suggestion mode.")
    candidates = tuple(sorted(set(candidates)))
    if not candidates:
        return (), False
    candidate_set = set(candidates)
    pool = candidate_set if mode == "answer" or len(candidates) == 1 else set(accepted) | candidate_set
    pool = sorted(pool - set(used))
    if not pool:
        return (), False
    bounded = len(candidates) > 64 and len(pool) > 160
    if bounded:
        counts = Counter(c for w in candidates for c in set(w))
        positions = [Counter(w[i] for w in candidates) for i in range(5)]

        def coverage(word):
            return sum(counts[c] for c in set(word)) + 0.25 * sum(positions[i][c] for i, c in enumerate(word))

        pool.sort(key=lambda w: (-coverage(w), w not in candidate_set, w not in core, w))
        pool = pool[:160]
        # Information mode always compares some actual answers as well.
        if mode == "information":
            best_answers = sorted(candidate_set, key=lambda w: (-coverage(w), w))[:40]
            pool = sorted(set(pool) | set(best_answers))
    answers = encode_words(candidates)
    answer_counts = np.zeros((len(answers), 26), dtype=np.int16)
    for i in range(5):
        answer_counts[np.arange(len(answers)), answers[:, i]] += 1
    result = []
    for word, encoded in zip(pool, encode_words(pool)):
        buckets = np.bincount(feedback_codes(encoded, answers, answer_counts), minlength=243)
        result.append(Suggestion(word, float(buckets @ buckets / len(candidates)), int(buckets.max()), word in candidate_set))
    result.sort(key=lambda r: (r.expected, not r.is_solution, r.word not in core, r.word))
    return tuple(result[:limit]), bounded
