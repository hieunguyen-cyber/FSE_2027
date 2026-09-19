"""A1: extracts observable facts; it receives no CVE, CWE, predicate, or target information."""
from __future__ import annotations

import re
from mira_mas.models import ReviewBundle, VisibleFact


class DiffAnalyst:
    _KEYWORDS = {
        "alignas", "auto", "bool", "break", "case", "catch", "char", "class", "const",
        "constexpr", "continue", "default", "delete", "do", "double", "else", "enum",
        "explicit", "extern", "false", "float", "for", "friend", "if", "inline", "int",
        "long", "namespace", "new", "nullptr", "operator", "private", "protected", "public",
        "register", "return", "short", "signed", "sizeof", "static", "struct", "switch",
        "template", "this", "throw", "true", "try", "typedef", "typename", "union", "unsigned",
        "using", "virtual", "void", "volatile", "while", "include", "define", "ifdef", "endif",
        "and", "or", "not", "the", "for", "from", "with", "error", "return", "null",
    }

    @classmethod
    def _rank_identifiers(cls, lines: list[str]) -> list[str]:
        """Return stable, human-meaningful anchors instead of arbitrary tokens.

        Short C/C++ keywords and incidental words from comments used to become
        message subjects (for example ``too``).  Prefer call/function-like
        identifiers, names repeated in the patch, and longer names.
        """
        counts: dict[str, int] = {}
        for line in lines:
            for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", line):
                low = token.lower()
                if low in cls._KEYWORDS or token.isupper() and len(token) <= 4:
                    continue
                if token.startswith(("http", "www")):
                    continue
                counts[token] = counts.get(token, 0) + 1
        def score(token: str) -> tuple[int, int, int, str]:
            function_like = int(any(x in token for x in ("_", "::")))
            return (counts[token], function_like, min(len(token), 32), token)
        return sorted(counts, key=score, reverse=True)

    def analyze(self, bundle: ReviewBundle) -> list[VisibleFact]:
        diff = bundle.diff
        facts: list[VisibleFact] = []
        added, removed = [], []
        for line in diff.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added.append(line[1:].strip())
            elif line.startswith("-"):
                removed.append(line[1:].strip())
        change_size = len(added) + len(removed)
        difficulty = "low" if change_size <= 4 else "medium" if change_size <= 14 else "high"
        facts.append(VisibleFact("f_difficulty", "difficulty",
                                 f"The visible patch has {difficulty} review complexity.",
                                 f"added={len(added)}, removed={len(removed)}"))
        if added:
            facts.append(VisibleFact("f_added", "changed-lines", "The change adds visible implementation lines.",
                                     " | ".join(added[:3])))
        if removed:
            facts.append(VisibleFact("f_removed", "changed-lines", "The change removes visible implementation lines.",
                                     " | ".join(removed[:3])))
        for identifier in self._rank_identifiers(added + removed):
            if len(facts) >= 8:
                break
            facts.append(VisibleFact(f"f_symbol_{len(facts)}", "symbol", f"The change touches `{identifier}`.", identifier))
        if not facts:
            facts.append(VisibleFact("f_diff", "diff", "The change updates the reviewed function.", "diff"))
        return facts
