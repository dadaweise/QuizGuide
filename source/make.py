"""Builds the single self-contained ../index.html for the QUIZINITIAL prep guide.

Run from anywhere:  python Guides/quiz-prep/source/make.py
Edit text in index.src.html, code in snippets.py and diagrams in diagrams.py, then run this again.
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diagrams  # noqa: E402
from snippets import S  # noqa: E402
from snippets_playbook import P  # noqa: E402
from snippets_options import O  # noqa: E402
from hints import H  # noqa: E402
from snippets_hints import X  # noqa: E402
from snippets_diagrams import D  # noqa: E402

S.update(P)
S.update(O)
S.update(D)

svgs = diagrams.build_all()

with open(os.path.join(HERE, "index.src.html"), encoding="utf-8") as f:
    page = f.read()

used_code, used_svg = set(), set()


def code(match):
    key, lang = match.group(1), match.group(2) or ""
    used_code.add(key)
    label = f'<span class="lang">{lang}</span>' if lang else ""
    return f'<div class="code">{label}<pre><code>{html.escape(S[key].strip(chr(10)))}</code></pre></div>'


def svg(match):
    key, alt = match.group(1), match.group(2)
    used_svg.add(key)
    s = svgs[key]
    prefix = re.sub(r"\W", "", key) + "-"
    s = re.sub(r"id='(open|filled|hollow)'", lambda m: f"id='{prefix}{m.group(1)}'", s)
    s = re.sub(r"url\(#(open|filled|hollow)\)", lambda m: f"url(#{prefix}{m.group(1)})", s)
    s = s.replace("role='img'", f"role='img' aria-label='{html.escape(alt, quote=True)}'", 1)
    return f'<div class="frame">{s}</div>'


used_ladder, used_example = set(), set()


def example(key):
    used_example.add(key)
    lang, src = X[key]
    return ('<p class="ex-label">Syntax example from another case (Library):</p>'
            f'<div class="code"><span class="lang">{lang}</span><pre><code>{html.escape(src.strip(chr(10)))}</code></pre></div>')


def hint_item(i, hint):
    title, text = hint[0], hint[1]
    codes = "".join(example(k) for k in (hint[2] if len(hint) > 2 else []))
    return f'<li class="hint"><strong>Hint {i} · {title}.</strong> {text}{codes}</li>'


def ladder(match):
    key = match.group(1)
    used_ladder.add(key)
    h = H[key]
    items = [hint_item(i, hint) for i, hint in enumerate(h["hints"], 1)]
    items.append('<li class="ans-step"><strong>Answer.</strong> The explanation and the answer are now shown below this box. '
                 'Compare them with what you found.</li>')
    items.append(f'<li class="new-step"><strong>New case.</strong> {h["new_case"]} '
                 f'Practise it: <a href="{h["link"]}">{h["link_text"]}</a>.</li>')
    title = f'<h3 class="ptitle-practice">{h["title"]}</h3>\n' if h["title"] else ""
    return (title + f'<p class="task"><strong>Task:</strong> {h["task"]}</p>\n'
            f'<div class="ladder"><p class="ladder-head">Hints, one at a time</p><ol>{"".join(items)}</ol>'
            '<button type="button" class="next">Show hint 1</button> '
            '<button type="button" class="reset" hidden>Start over</button></div>')


page = re.sub(r"<!--ladder:([\w-]+)-->", ladder, page)
page = re.sub(r"<!--code:([\w]+)(?:\|([\w ]+))?-->", code, page)
page = re.sub(r"<!--svg:([\w-]+)\|([^>]*?)-->", svg, page)

assert "<!--code:" not in page and "<!--svg:" not in page and "<!--ladder:" not in page, "a placeholder was not replaced"
missing = (set(S) - used_code) | (set(svgs) - used_svg) | (set(H) - used_ladder) | (set(X) - used_example)
assert not missing, f"defined but not placed: {sorted(missing)}"

with open(os.path.join(HERE, "..", "index.html"), "w", encoding="utf-8") as f:
    f.write(page)
print(f"index.html written: {len(used_code)} code blocks, {len(used_svg)} inline diagrams, {len(used_ladder)} hint ladders, {len(used_example)} hint examples")
