"""A small, touch-friendly companion for solving Wordle."""
from html import escape
from pathlib import Path
import streamlit as st

from solver import Clue, feedback, filter_candidates, load_dictionaries, normalize_word
from ranking import rank_guesses

st.set_page_config(page_title="Wordle companion", page_icon="🟩", layout="centered")
st.markdown((Path(__file__).parent / "style.html").read_text(), unsafe_allow_html=True)

COLORS = {0: "gray", 1: "yellow", 2: "green", -1: "unset"}
SYMBOLS = {0: "−", 1: "?", 2: "✓", -1: "○"}
DESCRIPTIONS = {0: "absent / no more copies", 1: "wrong position", 2: "correct position", -1: "not set"}


@st.cache_data
def dictionaries():
    return load_dictionaries()


@st.cache_data(show_spinner=False, max_entries=128)
def candidates_for(words, history):
    return filter_candidates(words, tuple(Clue(w, p) for w, p in history))


@st.cache_data(show_spinner=False, max_entries=64)
def suggestions_for(candidates, accepted, core, mode, used):
    return rank_guesses(candidates, accepted, core, mode, used)


def clear_draft():
    st.session_state.draft = ""
    st.session_state.tiles = [-1] * 5
    st.session_state.allow_unknown = False


def reset_game():
    st.session_state.history = []
    clear_draft()


def undo():
    word, pattern = st.session_state.history.pop()
    st.session_state.draft = word.upper()
    st.session_state.tiles = list(pattern)
    st.session_state.allow_unknown = False


def cycle_tile(index):
    values = list(st.session_state.tiles)
    values[index] = (values[index] + 1) % 3
    st.session_state.tiles = values


def use_suggestion(word):
    st.session_state.draft = word.upper()
    st.session_state.tiles = [-1] * 5
    st.session_state.allow_unknown = False


def add_clue():
    word = normalize_word(st.session_state.draft)
    st.session_state.history.append((word, tuple(st.session_state.tiles)))
    clear_draft()
    st.session_state.feedback_applied = True


def add_extra():
    try:
        word = normalize_word(st.session_state.extra_word)
    except ValueError as error:
        st.session_state.extra_notice = str(error)
        return
    st.session_state.extra_solutions = sorted(set(st.session_state.extra_solutions) | {word})
    st.session_state.extra_word = ""
    st.session_state.extra_notice = f"{word.upper()} is now included as a possible answer for this session."


def board_html(history):
    rows = []
    for index, (word, pattern) in enumerate(history, 1):
        cells = "".join(
            f'<span class="board-tile {COLORS[color]}" aria-label="{letter.upper()}, {DESCRIPTIONS[color]}">{letter.upper()}<small>{SYMBOLS[color]}</small></span>'
            for letter, color in zip(word, pattern)
        )
        label = ", ".join(f"{c.upper()}: {COLORS[p]}" for c, p in zip(word, pattern))
        rows.append(f'<div class="board-row" role="img" aria-label="Guess {index}: {escape(label)}"><span class="row-number">{index}</span>{cells}</div>')
    return '<div class="board">' + "".join(rows) + "</div>"


@st.fragment
def feedback_editor(accepted, history):
    """Tile taps redraw only this editor; applying feedback refreshes results."""
    if st.session_state.pop("feedback_applied", False):
        st.rerun()
    with st.container(border=True):
        st.subheader(f"Your {'next' if history else 'first'} guess")
        st.text_input("Word you played in Wordle", key="draft", max_chars=5, placeholder="e.g. CRANE", on_change=lambda: st.session_state.update(tiles=[-1] * 5, allow_unknown=False))
        raw_word = st.session_state.draft.strip().lower()
        valid_word = False
        if raw_word:
            try:
                word = normalize_word(raw_word)
                valid_word = True
            except ValueError as error:
                st.caption(str(error))
        st.caption("Match the colors from Wordle. Tap a tile: gray → yellow → green.")
        with st.container(key="feedback"):
            columns = st.columns(5, gap="small")
            for i, column in enumerate(columns):
                color = st.session_state.tiles[i]
                letter = raw_word[i].upper() if valid_word else "·"
                with column, st.container(key=f"tile_{COLORS[color]}_{i}"):
                    st.button(f"{letter} {SYMBOLS[color]}", key=f"feedback_{i}", help=f"Position {i + 1}: {DESCRIPTIONS[color]}. Tap to change.", use_container_width=True, disabled=not valid_word, on_click=cycle_tile, args=(i,))
        if valid_word:
            st.caption(" · ".join(f"{c.upper()}: {COLORS[p]}" for c, p in zip(raw_word, st.session_state.tiles)))
        known = valid_word and raw_word in accepted
        if valid_word and not known:
            st.warning("This word is missing from the bundled guess list.")
            st.checkbox("Wordle accepted this word", key="allow_unknown")
        duplicate = any(w == raw_word for w, _ in history)
        if duplicate:
            st.caption("This guess is already on your board. Undo it to change its colors.")
        ready = valid_word and (known or st.session_state.allow_unknown) and min(st.session_state.tiles) >= 0 and not duplicate
        st.button("Apply feedback", key="apply", type="primary", use_container_width=True, disabled=not ready, on_click=add_clue)



solutions, core, accepted = dictionaries()
for name, value in {"history": [], "draft": "", "tiles": [-1] * 5, "allow_unknown": False, "extra_solutions": []}.items():
    if name not in st.session_state:
        st.session_state[name] = value

words = tuple(sorted(set(solutions) | set(st.session_state.extra_solutions)))
accepted = accepted | frozenset(st.session_state.extra_solutions)
history = tuple(st.session_state.history)
candidates = candidates_for(words, history)
solved = bool(history and history[-1][1] == (2, 2, 2, 2, 2) and all(feedback(w, history[-1][0]) == p for w, p in history))
if solved:
    candidates = (history[-1][0],)
finished = solved or len(history) >= 6

st.markdown('<div class="eyebrow"><span>■ ■ ■</span> A LITTLE HELP, ONE GUESS AT A TIME</div>', unsafe_allow_html=True)
st.title("Make your next\nguess count.")
st.markdown("Bring your Wordle clues. Find what fits.")
st.markdown(
    f'<div class="score-strip"><div><strong>{len(candidates):,}</strong><span>possible answers</span></div>'
    f'<div><strong>{len(history)} / 6</strong><span>guesses entered</span></div></div>', unsafe_allow_html=True,
)

if history:
    st.markdown(board_html(history), unsafe_allow_html=True)
    # Text alternative makes the board usable without relying on color.
    with st.expander("Read feedback as text"):
        for i, (word, pattern) in enumerate(history, 1):
            st.write(f"{i}. {word.upper()} — " + "; ".join(f"{c.upper()}: {COLORS[p]}" for c, p in zip(word, pattern)))
    st.button("Undo last guess", key="undo", on_click=undo)

if solved:
    st.success(f"Solved: {history[-1][0].upper()}. Nicely done!")
elif len(history) >= 6:
    st.info("Six guesses entered. You can still inspect the remaining answers, undo a guess, or start again.")

if not finished:
    feedback_editor(accepted, history)

if not solved:
    st.subheader("A good next move")
    if not candidates:
        st.warning("No bundled answers match these clues. Check repeated letters and tile colors, undo the last guess, or add a missing answer below.")
    else:
        mode = st.radio("What should the next guess do?", ["Find the answer", "Gather information"], key="mode", help="Find the answer recommends remaining answers. Gather information can also use accepted guesses to separate the possibilities.")
        information = mode == "Gather information" and len(history) < 5
        if mode == "Gather information" and len(history) >= 5:
            st.caption("On the final guess, suggestions are limited to possible answers.")
        with st.spinner("Comparing the possibilities…"):
            suggestions, bounded = suggestions_for(candidates, tuple(sorted(accepted)), core, "information" if information else "answer", tuple(w for w, _ in history))
        if len(candidates) == 1:
            st.info("One answer in this word list matches your clues.")
        if information:
            st.caption("Information guesses may conflict with Wordle’s hard-mode rules.")
        for index, suggestion in enumerate(suggestions):
            if suggestion.word in st.session_state.extra_solutions:
                origin = "Your addition"
            else:
                origin = "Core answer" if suggestion.word in core else "Expanded answer" if suggestion.is_solution else "Guess only"
            with st.container(border=True):
                st.markdown(f"**{index + 1}. {suggestion.word.upper()}** · {origin}")
                if len(candidates) > 1:
                    st.caption(f"About {suggestion.expected:.1f} possibilities left on average · at most {suggestion.worst_case}")
                else:
                    st.caption("Matches every clue you entered.")
                if not finished:
                    st.button(f"Use {suggestion.word.upper()}", key=f"use_{suggestion.word}", on_click=use_suggestion, args=(suggestion.word,), use_container_width=True)
        st.caption("Assumes each remaining answer is equally likely. " + ("Scores compare a shortlist chosen for letter coverage." if bounded else "Scores compare every eligible guess.") + " A score of 1 may still require one final guess.")

with st.expander(f"All {len(candidates):,} possible answers"):
    search = st.text_input("Find a possible answer", key="candidate_search", placeholder="Type part of a word")
    visible = [w for w in candidates if search.strip().lower() in w]
    st.caption(f"{len(visible):,} matching words · alphabetical order · expanded words included")
    # Plain text wraps naturally on a phone, without a wide table.
    st.markdown('<div class="word-cloud">' + "".join(f"<span>{w.upper()}</span>" for w in visible[:300]) + "</div>", unsafe_allow_html=True)
    if len(visible) > 300:
        st.caption("Showing the first 300. Search above or download the full list.")
    st.download_button("Download remaining answers", "\n".join(candidates) + "\n", file_name="remaining-answers.txt", mime="text/plain")

with st.expander("Word lists & missing answers"):
    st.write(f"{len(solutions):,} curated possible answers, including less familiar words, and {len(accepted):,} accepted guesses. Expanded answers are included by default.")
    st.caption("Core and expanded labels describe list membership, not a measured familiarity score. These are community snapshots, not a live official NYT answer list. WAZOO is included as a local addition. Previously used answers are kept, and no daily solution is downloaded.")
    st.markdown("Word lists: [Alex Selby’s Wordle analysis](https://github.com/alex1770/wordle), used under the MIT license. Source revisions and license are bundled with the app.")
    st.text_input("Include a missing word as a possible answer", key="extra_word", max_chars=5, placeholder="Five letters")
    st.button("Include answer", key="include_answer", on_click=add_extra)
    if "extra_notice" in st.session_state:
        st.info(st.session_state.extra_notice)
    if st.session_state.extra_solutions:
        st.caption("Your additions: " + ", ".join(w.upper() for w in st.session_state.extra_solutions))
    st.caption("Added words stay for this browser session. Guesses and additions may be lost when you reload or disconnect.")

st.button("Start a new puzzle", key="reset", on_click=reset_game, use_container_width=True)
st.caption("An independent Wordle helper. Enter your guesses here; play them in Wordle.")
