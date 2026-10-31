# Wordle companion

A local Streamlit helper for Wordle, designed for a narrow phone screen as well
as a laptop. Play a word in Wordle, enter it here, tap the five tiles to match
the feedback, and apply it to see the remaining answers.

## Run on your Mac

Requires Python 3.12 (the existing `.venv` uses 3.12.1).

```sh
cd /Users/peternystrom/Documents/ChatGPT/wordletool
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local address printed by Streamlit, normally http://localhost:8501.

## Use on your phone

Connect the phone and Mac to the same trusted Wi-Fi network. Start the app with:

```sh
python -m streamlit run app.py --server.address 0.0.0.0
```

On your phone, open the **Network URL** printed by Streamlit, for example
`http://192.168.1.20:8501`. Keep your Mac awake and the app running. macOS may
ask you to allow incoming connections. Some guest Wi-Fi networks prevent
devices from reaching each other. No hosting account is required.

The interface has one column, five touch-sized feedback buttons, text and
symbols alongside colors, and a wrapping candidate list. No essential controls
are in a sidebar. Each tile starts unset; tap once for gray, twice for yellow,
and three times for green. Apply becomes available once all five are set.

## Word lists

- `data/solutions.txt`: 3,158 possible answers from Alex Selby's expanded list.
- `data/additional_solutions.txt`: local additions, currently WAZOO, included by
  default for a total of 3,159 possible answers.
- `data/core_solutions.txt`: the historical 2,309-word answer list, used only to
  distinguish core from expanded entries. Eight historical entries are absent
  from the upstream expanded answer list; it is not a strict superset.
- `data/accepted_guesses.txt`: 14,855 accepted guesses, including all solutions.
- `data/sources.json`: exact source revision, original URLs, and SHA-256 hashes.
- `data/LICENSE-wordlists.txt`: upstream MIT license.

Source: https://github.com/alex1770/wordle. These are community snapshots, not a
verified current official NYT answer list. Less familiar words, including WAZOO,
are included. Core/expanded labels describe list membership, not a measured
familiarity score. Previously used answers are retained. The app does not fetch
daily answers or make any network calls to retrieve dictionaries during play.

If a word is missing, use **Word lists & missing answers** to include it as a
possible answer for the session. If Wordle accepted an unknown guess, confirm
that fact to enter its feedback without treating it as a possible answer.
These two actions are deliberately separate. Guesses and additions live in
Streamlit's browser session; reloads, disconnections, and restarts may lose them.
**Start a new puzzle** clears guesses and feedback but keeps session word additions.

## Suggestions

**Find the answer** ranks remaining possible answers. **Gather information** can
also suggest guess-only words, which may conflict with hard-mode rules. On the
sixth turn, suggestions always come from the remaining answers.

The score is the expected number of remaining candidates after feedback,
assuming every candidate is equally likely; lower is better. At most 64 answers,
every eligible guess is compared. Larger pools use a shortlist of 160 guesses
selected by letter coverage and position frequency, plus up to 40 actual answers
in information mode. The UI discloses when a shortlist is used. This is one-step
scoring, not a guarantee of an optimal six-turn strategy. A score of 1 means
the answer will be identified, but may still require another guess to play it.

## Structure and verification

- `solver.py`: normalization, dictionary integrity, exact feedback and filtering.
- `ranking.py`: NumPy scoring, independent of the interface.
- `app.py` and `style.html`: Streamlit interface, session state, responsive styles.
- `tests/`: repeated-letter rules, candidate filtering, vectorized score parity,
  dictionary integrity, and Streamlit interaction tests.

```sh
python -m unittest discover -s tests -v
```

To explicitly refresh the bundled snapshots later, run `python fetch_data.py`
(requires `curl` and network access), review the dictionary changes, and rerun
the tests. The application never runs that script automatically.

The virtual environment and generated caches are excluded from Git. Nothing is
automatically committed, pushed, or deployed.

## VS Code workspace

Use **File → Open Workspace from File…** and choose
`wordletool.code-workspace` in this repository. This opens only the Wordle
project and prevents automatic discovery of repositories in parent folders.
It is useful if VS Code has also opened a repository rooted in your home folder
and is showing thousands of unrelated changes.

Feedback entry uses a Streamlit fragment: tapping a tile refreshes only the
editor. Applying feedback refreshes the board, candidate list, and suggestions.
