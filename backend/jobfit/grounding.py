"""Checks that a quote really appears in a source document.

Language models sometimes "quote" text that isn't there. Everything the model cites
as evidence is checked against the resume before it reaches the user, so the app
never shows a claim it cannot point to.

Matching ignores case, punctuation, bullet symbols and line breaks, but the words
must appear in the same order.

* For space-separated languages (English etc.) the quote must also start and end
  on word boundaries, so "Java" does not match inside "JavaScript".
* Chinese, Japanese and Korean don't put spaces between words, so a quote
  containing those characters only has to appear as a contiguous run.
"""

from __future__ import annotations

import re
import unicodedata

# \w is Unicode-aware, so letters in any script survive. Keep + and # for "C++" and "C#".
_NON_WORD = re.compile(r"[^\w+#]+")
_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]")


def normalize(text: str) -> str:
    """Lower-case, fold Unicode look-alikes (full-width letters, ligatures), and reduce punctuation and spacing to single spaces."""
    folded = unicodedata.normalize("NFKC", text).lower().replace("_", " ")
    return _NON_WORD.sub(" ", folded).strip()


class Grounder:
    """Answers "does this quote appear in the source?" for one source document."""

    def __init__(self, source: str) -> None:
        self._normalized = normalize(source)
        self._padded = f" {self._normalized} "
        # CJK text may be split by line breaks or spaces in a PDF; compare it with spacing removed.
        self._compact = self._normalized.replace(" ", "")

    def contains(self, quote: str) -> bool:
        needle = normalize(quote)
        if not needle:
            return False
        if _CJK.search(needle):
            return needle.replace(" ", "") in self._compact
        return f" {needle} " in self._padded
