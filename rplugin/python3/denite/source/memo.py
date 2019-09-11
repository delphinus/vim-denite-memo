# ============================================================================
# FILE: memo.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

import subprocess
from unicodedata import east_asian_width, normalize
import sys
from pathlib import Path
from typing import Dict

sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))

from vim_denite_memo.command import Memo
from denite.source.base import Base
from denite.util import Candidate, Candidates, UserContext, Nvim

HIGHLIGHT_SYNTAX = [
    {"name": "Prefix", "link": "String", "re": r"\[new title\]"},
    {"name": "File", "link": "String", "re": r"\v.*( : )@="},
    {"name": "Title", "link": "Function", "re": r"\v( : )@<=.*"},
]


class Source(Base):
    def __init__(self, vim: Nvim):
        super().__init__(vim)

        self.name = "memo"
        self.kind = "memo"
        self.vars = {"column": 20, "ambiwidth": vim.options["ambiwidth"]}

    def on_init(self, context: UserContext) -> None:
        context["__proc"] = None
        context["__memo"] = Memo()

    def gather_candidates(self, context: UserContext) -> Candidates:
        if context["args"] and context["args"][0] == "new":
            return self._is_new(context)

        if context["__proc"]:
            return self.__async_gather_candidates(context, context["async_timeout"])

        context["__proc"] = context["__memo"].proc(
            context, "list", "--format", "{{.Fullpath}}\t{{.File}}\t{{.Title}}"
        )
        return self.__async_gather_candidates(context, context["async_timeout"])

    def __async_gather_candidates(
        self, context: UserContext, timeout: int
    ) -> Candidates:
        outs, errs = context["__proc"].communicate(timeout=timeout)
        if errs:
            self.error_message(context, errs)
        context["is_async"] = not context["__proc"].eof()
        if context["__proc"].eof():
            context["__proc"] = None

        def make_candidates(row: str) -> Candidate:
            fullpath, filename, title = row.split("\t", 2)
            cut = self._stdwidthpart(filename, self.vars["column"])
            return {
                "word": filename,
                "abbr": "{0} : {1}".format(cut, title),
                "action__path": fullpath,
            }

        return list(map(make_candidates, outs))

    def _is_new(self, context: UserContext) -> Candidates:
        if "memo_dir" not in self.vars or not self.vars["memo_dir"]:
            try:
                self.vars["memo_dir"] = context["__memo"].get_memo_dir()
            except subprocess.CalledProcessError as err:
                self.error_message(
                    context, "command returned invalid response: " + str(err)
                )
                return []

        context["is_interactive"] = True
        title = context["input"]
        if not title:
            return []
        return [
            {
                "word": title,
                "abbr": "[new title] " + title,
                "action__memo_dir": self.vars["memo_dir"],
                "action__title": title,
                "action__is_new": True,
            }
        ]

    def _stdwidthpart(self, string: str, col: int) -> str:
        to_double = "FW" if self.vars["ambiwidth"] == "single" else "FWA"
        cache: Dict[str, int] = {}

        def east_asian_width_count(char: str) -> int:
            """
            this func returns 2 if it is Zenkaku string, 1 if other.  Each
            type, 'F', 'W', 'A', means below.

            * F -- Fullwidth
            * W -- Wide
            * A -- Ambiguous
            """
            if char not in cache:
                cache[char] = 2 if east_asian_width(char) in to_double else 1
            return cache[char]

        # normalize string for filenames in macOS
        norm = normalize("NFC", string)
        slen = sum(east_asian_width_count(x) for x in norm)
        if slen < col:
            return norm + " " * (col - slen)
        result = ""
        result_len = 0
        for char in norm:
            next_result = result + char
            next_len = result_len + east_asian_width_count(char)
            if next_len > col - 3:
                return result + ("...." if result_len < col - 3 else "...")
            elif next_len == col - 3:
                return next_result + "..."
            result = next_result
            result_len = next_len
        return ""

    def highlight(self) -> None:
        for syn in HIGHLIGHT_SYNTAX:
            self.vim.command(
                "syntax match {0}_{1} /{2}/ contained containedin={0}".format(
                    self.syntax_name, syn["name"], syn["re"]
                )
            )
            self.vim.command(
                "highlight default link {0}_{1} {2}".format(
                    self.syntax_name, syn["name"], syn["link"]
                )
            )
