"""Build-time dictionary snapshot; the running app never downloads data."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def fetch(url):
    return subprocess.check_output(["curl", "--fail", "--location", "--silent", "--show-error", url])


commit = json.loads(fetch("https://api.github.com/repos/alex1770/wordle/commits/main"))["sha"]
base = f"https://raw.githubusercontent.com/alex1770/wordle/{commit}/"
sources = {}
for output, upstream in {
    "solutions.txt": "wordlist_hidden",
    "core_solutions.txt": "wordlist_nyt20220830_hidden",
    "accepted_guesses.txt": "wordlist_all",
    "LICENSE-wordlists.txt": "LICENSE",
}.items():
    content = fetch(base + upstream)
    if output.endswith(".txt") and not output.startswith("LICENSE"):
        words = sorted(set(content.decode().lower().split()))
        assert len(words) > 2000 and all(len(w) == 5 and w.isascii() and w.isalpha() for w in words)
        content = ("\n".join(words) + "\n").encode()
    (DATA / output).write_bytes(content)
    sources[output] = {"url": base + upstream, "sha256": hashlib.sha256(content).hexdigest()}
(DATA / "sources.json").write_text(json.dumps({"repository": "https://github.com/alex1770/wordle", "commit": commit, "files": sources}, indent=2) + "\n")
print({p.name: len(p.read_text().splitlines()) for p in DATA.glob("*.txt")})
